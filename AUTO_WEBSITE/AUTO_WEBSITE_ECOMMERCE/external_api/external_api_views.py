from rest_framework import viewsets, status, views, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from . import external_api_serializers
import hashlib, urllib.parse, base64, requests, re
from socket import gethostbyname_ex
from ..reg import reg_models, reg_model_serializers
from ..auth.auth_models import Invoices, InvoiceItems
from ..auth.auth_model_serializers import InvoicesSerializer, InvoiceItemsSerializer
from ..standard import st_models, st_model_serializers
from .. import utils, exceptions
from django.db.models import Prefetch
from celery import shared_task
import json
from thefuzz import fuzz
from statistics import mean
from celery import Task
    
class GoCardlessIntegration(views.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    base_url = f'{settings.GC_URL}'
    headers = {
        'Content-Type': 'application/json',
        'Content-Length': '3495',
        'Accept': 'application/json',
        'Authorization': settings.GC_API_KEY,
        'GoCardless-Version': settings.GC_VER
    }
    # def check_actions(self, actions):
    #     actions_required = []
    #     actions_optional = []
    #     for action in actions:
    #         action_type = {'type': action['type']}
    #         required = action['required']
    #         if required & action['pending'] == 'pending':
    #             actions_required.append(action_type)
    #         else:
    #             if required == False:
    #                 actions_optional.append(action_type)
    #     return [actions_required, actions_optional]

    def __check_customer_record(self, request, **kwargs):
        data = request.data
        billing_details = data.get('gc_billing_details', None)
        if billing_details is not None:
            fields = {'user_id': request.user.user_id, 'gc_address_line_1__icontains': billing_details['address_line_1']}
            queryset = reg_models.UserBillingDetails.objects.filter(**fields)
            if queryset:
                fields_to_match = ['gc_address_line_1', 'gc_city', 'gc_postal_code', 'gc_country_code', 'gc_region']
                matches = []
                for query in queryset:
                    perc = []
                    for field in fields_to_match:
                        inputted = billing_details[field]
                        match = query[field]
                        perc.append(fuzz.partial_ratio(inputted, match))
                    avg = mean(perc)
                    avg = round(avg, 2)
                    matches.append(avg)
                highest = matches(max)
                if highest < 80:
                    i = matches.index(highest)
                    customer_id = queryset[i].gc_customer_id
                    return [True, customer_id]
            return [False]
    
    def billing_request_process(self, request, **kwargs):
        temp = kwargs.get('temp', None)
        if temp is not None:
            billing_params = {
                'temp': temp
            }
            create_new_account = request.data.get('create_new_account', False)
            if create_new_account:
                customer_record_check = self.__check_customer_record(request)
                customer_record_exist = customer_record_check[0]
                if customer_record_exist:
                    billing_params['customer'] = customer_record_check[1]
            else:
                inputted = request.data
                billing_params['customer'] = inputted.get('gc_customer_id')
                billing_params['customer_bank_account'] = inputted.get('gc_customer_bank_account_id')
            obj_type = kwargs.get('obj_type', None)
            utils.check_task(request, obj_type=obj_type)
            data = self.create_billing_request(request, temp=temp)
            main = data['billing_requests']
            billing_request_id = main['id']
            temp.gc_billing_request_id = billing_request_id
            set_temp = kwargs.get('set_temp', None)
            if set_temp is not None:
                set_temp(request, temp)
            customer_id = main['links']['customer']
            default_params = {
                'billing_request_id': billing_request_id
            }
            utils.check_task(request, obj_type=obj_type)
            if create_new_account:
                default_params.update({'customer_id': customer_id})
                if not customer_record_exist:
                    self.collect_customer_details(request, temp=temp, **default_params)
                self.collect_bank_account_details(request, **default_params)
                utils.check_task(request, obj_type=obj_type)
            self.confirm_payer_details(request, **default_params)
            utils.check_task(request, obj_type=obj_type)
            self.fulfil_payment(request, temp=temp, **default_params)
            return True

    def create_billing_request(self, request, **kwargs):
        temp = kwargs.get('temp', None)
        if temp is not None:
            url = f'{self.base_url}/billing_requests'
            desc = f'{temp.checkout_instance_type}_{temp.checkout_instance_id}'
            if temp.checkout_instance_type == 'repair':
                amount = temp.checkout_instance.shipping_price_incl
            if temp.checkout_instance_type == 'order':
                amount = temp.checkout_instance.order_total
            amount = 24 * amount
            data = {
                'billing_requests': {
                    'payment_request': {
                        'description': desc,
                        'amount': amount,
                        'currency': 'GBP'
                    },
                    'mandate_request': {
                        'scheme': 'BACS'
                    }
                }
            }
            params = ['customer', 'customer_bank_account']
            for param in params:
                data['billing_requests']['links'] = {param: kwargs.get(param, None)}
            req = requests.post(url=url, data=data, headers=self.headers)
            if req.status_code == '201':
                req_data = req.json()
                return req_data
    
    def __create_customer_record(self, request, **kwargs):
        main_data = kwargs.get('customer_id', None)
        data = request.data.get('gc_billing_details', None)
        if data is not None:
            if main_data is not None:
                customer_id = main_data['resources']['customer']['id']
                data['user_id'] = request.user.user_id
                data['gc_customer_id'] = main_data
                serializer = reg_model_serializers.UserBillingDetailsSerializer(data=data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return serializer.data

    def collect_customer_details(self, request, **kwargs):
        billing_request_id = kwargs.get('billing_request_id', None)
        temp = kwargs.get('temp', None)
        if billing_request_id is not None:
            data = self.__create_customer_record(request, **kwargs)
            url = f'{self.base_url}/billing_requests/{billing_request_id}/actions/collect_customer_details'
            if temp is not None:
                user = request.user
                user_details = temp.checkout_instance_user_details
                customer_billing_detail = {}
                for key, value in data.kwargs():
                    if key != 'user_id' or 'gc_customer_id':
                        updated = re.sub('gc_', '', key, 1)
                        customer_billing_detail.update({updated: value})
                gc_data = {
                    'customer': {
                        'company_name': user_details.company,
                        'email': user.email,
                        'given_name': user_details.name,
                        'family_name': user_details.surname,
                        'phone_number': user.mobile_no
                    },
                    'customer_billing_detail': customer_billing_detail,
                }
                req = requests.post(url=url, data=gc_data, headers=self.headers)
                if req.status_code == '200':
                    return True
                
    def __create_bank_account_record(self, request, **kwargs):
        data = request.data.get('gc_bank_account_details', None)
        res = kwargs.get('res', None)
        if data is not None:
            if res is not None:
                data['gc_customer_bank_account_id'] = res['resources']['customer_bank_account']['id']
                data['gc_customer_id'] = kwargs.get('customer_id', None)
                data['user_id'] = request.user.user_id
                serializer = reg_model_serializers.UserBankAccountDetailsSerializer(data=data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

    def collect_bank_account_details(self, request, **kwargs):
        billing_request_id = kwargs.get('billing_request_id', None)
        if billing_request_id is not None:
            url = f'{self.base_url}/billing_requests/{billing_request_id}/actions/collect_bank_account'
            data = request.data.get('gc_bank_account_details')
            if data is not None:
                gc_data = {}
                for key, value in data.kwargs():
                    updated = re.sub('gc_', '', key, 1)
                    gc_data.update({updated: value})
                    pass
                gc_data = {
                    'data': gc_data
                }
                req = requests.post(url=url, data=gc_data, headers=self.headers)
                if req.status_code == '200':
                    return self.__create_bank_account_record(request, customer_id=kwargs.get('customer_id', None), res=req.json()['billing_requests'])

    def confirm_payer_details(self, **kwargs):
        billing_request_id = kwargs.get('billing_request_id', None)
        if billing_request_id is not None:
            url = f'{self.base_url}/billing_requests/{billing_request_id}/actions/collect_customer_details'
            req = requests.post(url=url, headers=self.headers)
            if req.status_code == '200':
                return True

    def fulfil_payment(self, request, **kwargs):
        billing_request_id = kwargs.get('billing_request_id', None)
        temp = kwargs.get('temp', None)
        set_temp = kwargs.get('temp', None)
        if billing_request_id is not None:
            temp.is_fullfilling = True
            if set_temp is not None:
                set_temp(request, temp)
            url = f'{self.base_url}/billing_requests/{billing_request_id}/actions/fulfil'
            req = requests.post(url=url, headers=self.headers)
            if req.status_code == '200':
                return True

    def cancel_billing_request(self, **kwargs):
        temp = kwargs.get('temp', None)
        if temp is not None:
            billing_request_id = temp.gc_billing_request_id
            if billing_request_id is not None:
                url = f'{self.base_url}/billing_requests/{billing_request_id}/actions/cancel'
                requests.post(url=url, headers=self.headers)
                return True

class GoCardlessIntegrationTaskOverride(GoCardlessIntegration, Task):

    def run(self, request, **kwargs):
        run_type = kwargs.get('run_type', None)
        if run_type is not None:
            if run_type == 'create':
                return super().billing_request_process(request, **kwargs)
            if run_type == 'cancel':
                return super().cancel_billing_request(request, **kwargs)

class SageAccountingIntegration(views.APIView):
    base_url = f'{settings.SAGE_URL}/api/{settings.SAGE_VER}'

    def encode_to_base64(self, input_val):
        input_val = input_val.encode('ascii')
        base64_val = base64.b64encode(input_val)
        base64_val = base64_val.decode('ascii')
        return base64_val

    def authorization(self):
        username = self.encode_to_base64(settings.SAGE_USERNAME)
        password = self.encode_to_base64(settings.SAGE_PASSWORD)
        encoded_credentials = username + ':' + password

        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Basic {encoded_credentials}'
        }
        return headers

    def send_request(self, data, service_name, method_name, **params):
        headers = self.authorization()
        url = f'{base_url}/{service_name}/{method_name}/{str(**params)}'
        if method_name == 'Save':
            return requests.post(url=url, data=data, headers=headers)
        if method_name == 'Get':
            return requests.get(url=url, headers=headers)

    def get_customer(self, user_id, **kwargs):
        user_obj = reg_models.UserDetails.objects.select_related('user_id').filter(user_id=user_id)
        user_sage_id = user_obj.sage_id
        if user_sage_id is not None:
            params = f'{user_sage_id}'
            get_customer_request = self.send_request(data=None, service_name='Customer', method_name='Get', **params)
            if get_customer_request.status_code != '200' or '202':
                return self.save_customer(user_id=user_id)
            else:
                return user_sage_id
        else:
            return self.save_customer(user_obj=user_obj)

    def save_customer(self, **kwargs):
        user_obj = kwargs.get('user_obj', None)
        if user_obj is not None:
            if user_obj.user_id.is_verified == True:
                # contact_name = user_details_object['name'] + user_details_object['surname']
                contact_name = f'{user_obj.name} {user_obj.surname}'
                if user_obj.company is None:
                    company_name = contact_name
                else:
                    company_name = user_id.company
                data = {
                    'Name': company_name,
                    'TaxReference': user_obj.vat_no,
                    'Mobile': user_obj.user_id.mobile_no,
                    'Email': user_obj.user_id.email,
                    'ContactName': contact_name
                }
                serializer = external_api_serializers.SageCustomerSerializer(data=data)
                params = 'Save'
                save_customer_request = self.send_request(data=serializer.data, service_name='Customer', method_name=params, **params)
                if save_customer_request.status_code == '201':
                    save_customer_request_data = save_customer_request.json()
                    sage_id = save_customer_request_data['ID']
                    user_id.sage_id = sage_id
                    user_id.is_synced = True
                    user_id.save()
                    return sage_id
                    # return user_details_object.update(sage_id=sage_id, is_synced=True)

    def get_item(self, sku_no):
        # item_details = st_models.ProductConfig.objects.filter(products_id=products_id).values('sage_id')
        sku_obj = st_models.ProductStock.objects.select_related('product_config_id__product_id', 'product_config_id__variation_id').filter(sku_no=sku_no)
        if sku_obj.product_config_id.sage_id is not None:
            params = f'{item_details}'
            get_item_request = self.send_request(data=None, service_name='Item', method_name='Get', **params)
            if get_item_request.status_code != '200' or '202':
                return self.save_item(products_id=products_id)
            else:
                return sku_obj.sage_id

    def save_item(self, sku_obj):
        name = sku_obj.product_config_id.product_id.name
        variation = sku_obj.product_config_id.variation_id.variation_value
        description = f'{name} {variation}'
        data = {
            # 'Code': item_details_values['sage_item_code'],
            'Code': sku_obj.product_config_id.sage_item_code,
            'Description': description,
            'PriceExclusive': sku_obj.product_config_id.price
        }
        serializer = external_api_serializers.SageItemSerializer(data=data)
        save_item_request = self.send_request(data=serializer.data, service_name='Item', method_name='Save')
        if save_item_request.status_code == '201':
            save_item_request_data = save_item_request.json()
            sage_id = save_item_request_data['ID']
            sku_obj.product_config_id.sage_id = sage_id
            sku_obj.save()
            return sage_id

    def get_invoice(self, invoice_id):
        if invoice_id.sage_id is not None:
            params = f'{invoice_id.sage_id}'
            get_invoice_request = self.send_request(data=None, service_name='TaxInvoice', method_name='Get', **params)
            if get_invoice_request.status_code != '200' or '202':
                return self.save_invoice(invoice_id=invoice_id)
            else:
                return True

    def save_invoice(self, invoice_obj, customer_id):
        invoice_id = invoice_obj.pk
        invoice_items_prefetch_queryset = Prefetch('order_item_id__sku_no__product_config_id', queryset=st_models.ProductConfig.objects.select_related('product_id', 'variation_id'))
        invoice_items = InvoiceItems.objects.prefetch_related(invoice_items_prefetch_queryset).filter(invoice_id=invoice_id)
        invoice_items_list = []
        for item in invoice_items:
            sku_details = item.order_item_id.sku_no
            product_config_details = sku_details.product_config_id
            sage_item_id = product_config_details.sage_id
            sage_item_id = self.get_item(sku_no=sku_details.pk)
            invoice_items_dict = {
                'SelectionId': product_config_details.sage_item_code,
                'Description': sku_details.pk,
                'Exclusive': item.order_item_id.order_item_excl,
                'Quantity': 1
            }
            invoice_items_list.append(invoice_items_dict)
        order_details = invoice_obj.order_id
        data = {
            'CustomerId': customer_id,
            'Date': order_details.order_date,
            'Reference': f'{order_details.pk} [{invoice_id}]',
            'Exclusive': order_details.order_subtotal_excl,
            'Tax': order_details.order_tax,
            'Total': order_details.order_total,
            'Lines': invoice_items_list
        }
        serializer = external_api_serializers.SageInvoiceSerializer(data=data)
        save_invoice_request = self.send_request(data=serializer.data, service_name='TaxInvoice', method_name='Save')
        if save_invoice_request.status_code == '201':
            save_invoice_request_data = save_invoice_request.json()
            sage_id = save_invoice_request_data['ID']
            sage_doc_no = save_invoice_request_data['DocumentNumber']
            invoice_obj.update(is_synced=True, sage_id=sage_id, sage_doc_no=sage_doc_no)
            return sage_id

    def bulk_invoice_sync(self):
        invoices = Invoices.objects.prefetch_related('invoice_id__order_id').filter(is_synced=False)
        for invoice in invoices:
            customer = self.get_customer(user_id=invoice.user_id)
            self.save_invoice(invoice, customer)

class BobGoIntegration(viewsets.ViewSet):
    ex_api_bobgo_parcels = None

    def configure_user_address(self, **kwargs):
        '''
        configure user address to BobGo API Format
        '''
        temp = kwargs.get('temp', None)
        if temp is not None:
            user_address_obj = temp.checkout_user_address
            if user_address_obj.unit_number != None or 'null':
                street_address = f'{user_address_obj.unit_number} {user_address_obj.address_line_1}'
            else:
                street_address = f'{user_address_obj.address_line_1}'
            user_address_data = {
                'name': user_address_obj.name,
                'mobile_no': user_address_obj.contact_number,
                'street_address': street_address,
                'local_area': user_address_obj.area,
                'city': user_address_obj.city,
                'zone': user_address_obj.province,
                'code': user_address_obj.postal_code
            }
            if user_address_obj.company != None or 'null':
                user_address_data['company'] = user_address_obj.company
            if user_address_obj.email_address != None or 'null':
                user_address_data['email'] = user_address_obj.email_address
            return user_address_data

    def address_order(self, user_address_data, **kwargs):
        '''
        configure address order of user address + autolectronix address, based on if the checkout type is repair or order
        '''
        is_shipment = kwargs.get('is_shipment', False)
        temp = kwargs.get('temp', None)
        if temp is not None:
            if temp.checkout_instance_type == 'repair':
                collection_address = user_address_data
                delivery_address = settings.BOBGO_DEFAULT_COLLECTION_ADDRESS
            else:
                collection_address = settings.BOBGO_DEFAULT_COLLECTION_ADDRESS
                delivery_address = user_address_data
            addresses = [collection_address, delivery_address]
            contact_vals = ['name', 'mobile_no', 'email', 'company']
            if is_shipment == False:
                for item in contact_vals:
                    for address in addresses:
                        try:
                            del address[item]
                        except KeyError:
                            continue
            return addresses

    def initialize_parcels(self, **kwargs):
        '''
        interate through checkout items -> append with necessary data based on quantity
        '''
        temp = kwargs.get('temp', None)
        if temp is not None:
            checkout_items = temp.checkout_items
            # checkout_items = json.dumps(list(checkout_items))
            items = {}
            is_shipment = kwargs.get('is_shipment', False)
            for item in checkout_items:
                if temp.checkout_instance_type == 'order':
                    quantity = item.quantity
                    product_id = item.product_config_id.product_id
                if temp.checkout_instance_type == 'repair':
                    quantity = 1
                    product_id = item
                # quantity = item['quantity']
                # product_id = product_id.pk
                weight = product_id.weight
                weight_type = getattr(product_id, 'weight_type', None)
                # weight_type = product_id.weight_type
                if weight_type is not None:
                    if weight_type.lower() != 'kg':
                        weight = weight / 1000
                for i in range(quantity):
                    data = {
                        'description': '',
                        'submitted_length_cm': round(product_id.dimension_l),
                        'submitted_width_cm': round(product_id.dimension_w),
                        'submitted_height_cm': round(product_id.dimension_h),
                        'submitted_weight_kg': round(weight),
                        # 'custom_parcel_reference': ''
                    }
                    # data = {
                    #     'submitted_length_cm': 2.00,
                    #     'submitted_width_cm': 2.00,
                    #     'submitted_height_cm': 2.00,
                    #     'submitted_weight_kg': 2.00
                    # }
                    items.update(**data)
            print(items)
            return items

    def get_courier_rates_for_products(self):
        '''
        function to auto populate shipping rate data of individual products, scheduled on weekly basis
        '''
        url = f'${settings.BOBGO_URL}/rates'
        products = st_models.Products.objects.all()
        cities = st_models.Cities.objects.all()
        base_shipping_rate_data = []
        for product in products:
            if product.weight_type != 'kg' or 'KG' or 'Kg':
                product_weight = product.weight / 1000
            else:
                product_weight = product.weight
            for city in cities:
              data = {
                'collection_address': settings.BOBGO_DEFAULT_COLLECTION_ADDRESS,
                'delivery_address': {
                    'street_address': city.ram_address_1,
                    'local_area': city.local_area,
                    'city': city.city_value,
                    'zone': city.region_code,
                    'code': city.postal_code
                },
                'parcels': [
                    {
                        'description': '',
                        'submitted_length_cm': product.dimension_l,
                        'submitted_width_cm': product.dimension_w,
                        'submitted_height_cm': product.dimension_h,
                        'submitted_weight_kg': product_weight,
                        'custom_parcel_reference': ''
                    }
                ],
                'declared_value': 0,
                'timeout': 10000,
                'providers': ['RAM'],
                'service_levels': ['ECO']
              }
              print(data)
              serializer = external_api_serializers.BobGoCourierRateSerializer(data=data)
              if serializer.is_valid(raise_exception=True):
                courier_rate_request = requests.post(url=url, data=serializer.data, headers=settings.BOBGO_DEFAULT_HEADERS)
                if courier_rate_request.status_code == '201':
                    courier_rate_request_data = courier_rate_request.json()
                    if courier_rate_request_data['provider_rate_requests'][0]['status'] == 'success':
                        data2 = {
                            'city_id': city.city_id,
                            'product_id': product.product_id,
                            'base_charge': courier_rate_request_data['provider_rate_requests'][0]['responses'][0]['rate_amount'],
                        }
                        base_shipping_rate_data.append(data2)
                    else:
                        break
                else:
                    break
        serializer2 = st_model_serializers.BaseShippingRatesSerializer(data=base_shipping_rate_data, many=True)
        if serializer2.is_valid(raise_exception=True):
            st_models.BaseShippingRates.objects.all().delete()
            return serializer2.save()
    
    def get_checkout_rate(self, request, **kwargs):
        '''
        get rate of shipping at checkout (order/repair)
        '''
        temp = kwargs.get('temp', None)
        if temp is not None:
            url = f'{settings.BOBGO_URL}/rates'
            user_address_data = self.configure_user_address(temp=temp)
            print(user_address_data)
            address = self.address_order(user_address_data, temp=temp)
            parcels = self.initialize_parcels(temp=temp)
            temp.ex_api_bobgo_parcels = parcels
            data = {
                'collection_address': address[0],
                'delivery_address': address[1],
                'parcels': [
                    parcels
                ],
                'timeout': 10000,
                'providers': ['demo'],
                'service_levels': ['ECO']
            }
            print(data)
            data = json.dumps(data)
            print(data)
            courier_rate_request = requests.post(url=url, data=data, headers=settings.BOBGO_DEFAULT_HEADERS)
            print(courier_rate_request.status_code)
            print(courier_rate_request.text)
            if courier_rate_request.status_code == '201' or '200':
                courier_rate_request_data = courier_rate_request.json()
                if courier_rate_request_data['provider_rate_requests'][0]['status'] == 'success':
                    data2 = courier_rate_request_data['provider_rate_requests'][0]['responses'][0]['rate_amount_excl_vat']
                    return data2
            # serializer = external_api_serializers.BobGoCourierRateSerializer(data=data)
            # if serializer.is_valid(raise_exception=True):
            #     print(serializer.data)
            #     print(settings.BOBGO_DEFAULT_HEADERS)
            #     courier_rate_request = requests.post(url=url, data=serializer.data, headers=settings.BOBGO_DEFAULT_HEADERS)
            #     print(courier_rate_request.status_code)
            #     print(courier_rate_request.text)
            #     if courier_rate_request.status_code == '201' | '200':
            #         courier_rate_request_data = courier_rate_request.json()
            #         if courier_rate_request_data['provider_rate_requests'][0]['status'] == 'success':
            #             data2 = {
            #                 'shipping_price': courier_rate_request_data['provider_rate_requests'][0]['responses'][0]['rate_amount_excl_vat']
            #             }
            #             return data

    def create_shipment(self, request, **kwargs):
        '''
        create shipment at checkout (order/repair) after successful payment
        '''
        temp = kwargs.get('temp', None)
        if temp is not None:
            url = f'${settings.BOBGO_URL}/shipments'
            parcels = temp.ex_api_bobgo_parcels
            if temp.checkout_instance is not None:
                if self.checkout_user_address is not None:
                    user_address_data = self.configure_user_address()
                    address = self.address_order(user_address_data, is_shipment=True)
                    addresses = {'collection_address': address[0], 'delivery_address': address[1]}
                    for parcel in parcels:
                        parcel.pop('description', '')
                        parcel.pop('custom_parcel_reference', '')
                    address_vals = ['name', 'mobile_no', 'email', 'company']
                    address_data = {}
                    for item in address_vals:
                        for key, value in addresses.items():
                            val = value.pop(item, '')
                            address_data[f'{key}_{item}'] = val
                    instance_id_field = f'{temp.checkout_instance_type}_id'
                    instance_date_field = f'{temp.checkout_instance_type}_date'
                    instance_id = instance[instance_id_field]
                    instance_date = instance[instance_date]
                    data = {
                        **addresses,
                        **address_data,
                        'timeout': 10000,
                        'parcels': [
                            parcels
                        ],
                        'delcared_value': 0,
                        'custom_order_number': instance_id,
                        'service_level_code': 'ECO',
                        'provider_slug': 'RAM',
                        'collection_min_date': instance_date,
                        'collection_after': '08:00',
                        'collection_before': '16:00',
                    }
                    serializer = external_api_serializers.BobGoCheckoutSerializer(data=data)
                    if serializer.is_valid(raise_exception=True):
                        courier_shipment_request = requests.post(url=url, data=serializer.data, headers=settings.BOBGO_DEFAULT_HEADERS)
                        if courier_shipment_request.status_code == '201':
                            courier_shipment_request_data = courier_shipment_request.json()
                            if courier_shipment_request_data['submission_status'] == 'success':
                                shipping_tracking_id = courier_shipment_request_data['provider_tracking_reference']
                                temp.checkout_instance.shipping_tracking_id = shipping_tracking_id
                                temp.checkout_instance.save()