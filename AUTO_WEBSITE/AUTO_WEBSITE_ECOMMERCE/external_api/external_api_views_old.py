from rest_framework import viewsets, status, views, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from . import external_api_serializers
import hashlib, urllib.parse, base64, requests
from socket import gethostbyname_ex
from ..reg import reg_models, reg_model_serializers
from ..auth.auth_models import Invoices, InvoiceItems
from ..auth.auth_model_serializers import InvoicesSerializer, InvoiceItemsSerializer
from ..standard import st_models, st_model_serializers
from .. import utils, exceptions
from django.db.models import Prefetch
from celery import shared_task
import json

payfast_exc = exceptions.ServerPayFastError

class PayfastIntegration(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    # ex_api_instance_type = None
    # ex_api_instance_model = None
    # ex_api_instance_serializer = None
    # ex_api_instance_id_field = None
    # ex_api_instance_id = None
    # ex_api_instance = None
    # ex_api_user_details_instance = None

    def generate_signature(self, data_array, pass_phrase = ''):
        payload = ''
        for key in data_array:
            payload += key + '=' + urllib.parse.quote_plus(data_array[key].replace('+', ' ')) + '&'
        payload = payload[:-1]
        if pass_phrase != '':
            payload += f'&passphrase={pass_phrase}'
        return hashlib.md5(payload.encode()).hexdigest()

    def initialize_form(self, request, **kwargs):
        '''
        initialize html form for payment on frontend
        SEE BELOW FOR NOTES vvvv

        !!!note!!!
        while PayFast does have integration for API available,
        this requires storage of sensitive credit card information on our services,
        of which we DO NOT have the security to facilitate
        and yes, while this does violate some REST API principles, I'd rather that than risk someone's credit card information being exposed
        ~ sincerely, the original backend dev
        '''
        temp = kwargs.get('temp', None)
        if temp is not None:
            user = request.user
            user_details = temp.checkout_instance_user_details
            if temp.checkout_instance_type == 'repair':
                amount = temp.checkout_instance.shipping_price_incl
            if temp.checkout_instance_type == 'order':
                amount = temp.checkout_instance.order_total
            else:
                raise exceptions.invalid_error('checkout type')
            data = {
                'merchant_id': settings.PAYFAST_ID,
                'merchant_key': settings.PAYFAST_KEY,
                'return_url': f'{settings.FRONTEND_URL}/conf/{temp.checkout_instance_type}/{temp.checkout_instance_id}/',
                'cancel_url': f'{settings.FRONTEND_URL}/checkout/cancel/{temp.checkout_instance_type}/{temp.checkout_instance_id}/',
                'notify_url': f'https://{settings.API_URL}/auth/checkout/{temp.checkout_instance_id}/recieve/',
                'name_first': user_details.name,
                'name_last': user_details.surname,
                'email_address': user.email,
                'cell_number': user.mobile_no,
                'amount': amount,
                'item_name': temp.checkout_instance_id
            }
            pass_phrase = settings.PAYFAST_PASS_PHRASE
            data['security_signature'] = self.generate_signature(data, pass_phrase)
            request.session['initialized_data'] = data
            serializer = external_api_serializers.PayFastSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                return Response(serializer.data, status=status.HTTP_200_OK)

    def recieve_data(self, request):
        data = request.data
        request.session['recieve_data'] = data
        return Response(status=status.HTTP_200_OK)

    def convert_incoming_data_to_params(self, data):
        param_string = ''
        for [key] in data:
            if [key] != 'signature':
                param_string += [key] + '=' + urllib.parse.quote_plus(data[key].replace('+', ' ')) + '&'
        param_string = param_string[:-1]
        return param_string
    
    def validate_signature(self, data, param_string):
        signature = hashlib.md5(param_string.encode()).hexdigest()
        if data.get('signature') != signature:
            raise payfast_exc.failure('signature')
            # raise exceptions.payfast_invalid_error('signature')

    def validate_ip(self):
        valid_hosts = [
            'www.payfast.co.za',
            'sandbox.payfast.co.za',
            'w1w.payfast.co.za',
            'w2w.payfast.co.za'
        ]
        valid_ips = []
        for item in valid_hosts:
            ips = gethostbyname_ex(item)
            if ips:
                for ip in ips:
                    if ip:
                        valid_ips.append(ip)
        clean_valid_ips = []
        for item in valid_ips:
            if isinstance(item, list):
                for prop in item:
                    if prop not in clean_valid_ips:
                        clean_valid_ips.append(prop)
            else:
                if item not in clean_valid_ips:
                    clean_valid_ips.append(item)
        
        if urllib.parse.urlparse(request.headers.get('Referrer')).hostname not in clean_valid_ips:
            raise exceptions.payfast_invalid_error('IP')

    def validate_payment_data(self, rec_data, ini_data):
        amount = ini_data['amount']
        amount_gross = rec_data.get('amount_gross')
        if not (abs(amount) - amount_gross) > 0.01:
            raise exceptions.payfast_invalid_error('gross amount')

    def validate_server_confirmation(self, param_string, host = 'sandbox.payfast.co.za'):
        url = f'https://{host}/eng/query/validate'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(url, data=param_string, headers=headers)
        if response.text != 'VALID':
            raise exceptions.payfast_invalid_error('server response')

    def conduct_security_checks(self, request):
        rec_data = request.session['recieve_data']
        ini_data = request.session['initialized_data']
        param_string = self.convert_incoming_data_to_params(rec_data)
        self.validate_signature(rec_data, param_string)
        self.validate_ip()
        self.validate_payment_data(rec_data, ini_data)
        self.validate_server_confirmation(param_string)
        return True