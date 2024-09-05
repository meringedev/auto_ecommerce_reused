# @method_decorator(never_cache, name='dispatch')
# class CheckoutOld(OrdersViewSet, RepairsViewSet, ShoppingCartViewSet, external_api_views.GoCardlessIntegration, external_api_views.BobGoIntegration, custom_mixins.DefaultCacheMixin, custom_mixins.TempMixin, viewsets.ViewSet):
#     lookup_field = 'instance_type'
#     lookup_url_kwargs = 'instance_type'

#     permission_classes = [permissions.IsAuthenticated]
#     checkout_backend_load = False
#     checkout_on_load = False
#     checkout_instance_super = None

#     def __get_private(self, *args):
#         get_private = getattr(self.checkout_instance_super, 'get_private')
#         return get_private(*args)

#     def __initialize_super(self, instance_type=None):
#         if instance_type == 'repair':
#             instance_super = [OrdersViewSet, self]
#         if instance_type == 'order':
#             instance_super = []
#         self.checkout_instance_super = instance_super
    
#     def __initialize_view(self, instance_type=None):
#         instance_class = globals()[f'{instance_type.capitalize()}sViewSet']
#         return instance_class

#     def initialize_new(self, request, instance_type=None, **kwargs):
#         '''
#         get checkout type from client, get checkout items, initalize model, serializer and ID field associated
#         '''
#         checkout_type = instance_type
#         temp = kwargs.get('temp', None)
#         if checkout_type is not None:
#             self.initialize(checkout_type, temp=temp)
#             if checkout_type == 'repair':
#                 product_id = request.query_params.get('product_id', None)
#                 if product_id is not None:
#                     product_instance = st_models.Products.objects.get(pk=product_id)
#                     if product_instance.is_active == False:
#                         raise custom_exceptions.item_non_active_error('product')
#                     else:
#                         temp.checkout_items = [product_instance]
#                 else:
#                     raise custom_exceptions.invalid_or_none_error('product_id')
#             elif checkout_type == 'order':
#                 super(RepairsViewSet, self).list(request, backend_req=True)
#                 if temp.shopping_cart_items_obj is not None:
#                     temp.checkout_items = temp.shopping_cart_items_obj
#             else:
#                 raise custom_exceptions.invalid_type_error('checkout')
#         else:
#             raise custom_exceptions.none_not_allowed_error('checkout type')

#     # def initialize(self, instance_type, **kwargs):
#     #     temp = kwargs.get('temp', None)
#     #     if temp is not None:
#     #         temp.checkout_instance_type = instance_type
#     #         self.__initialize_super(instance_type=temp.checkout_instance_type)
#     #         temp_view = self.__initialize_view(instance_type=temp.checkout_instance_type)()
#     #         temp.checkout_instance_model, temp.checkout_instance_serializer, temp.checkout_id_field = temp_view.get_private(['parent_model', 'parent_serializer', 'parent_id_field'])
#     #         return True

#     def initialize(self, instance_type, **kwargs):
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             temp.checkout_instance_type = instance_type
#             self.__initialize_super(instance_type=temp.checkout_instance_type)
#             temp.checkout_instance_model, temp.checkout_instance_serializer, temp.checkout_id_field = self.__get_private(['parent_model', 'parent_serializer', 'parent_id_field'])
#             return True

#     def initialize_saved(self, instance, **kwargs):
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             temp.checkout_instance = instance
#             temp.checkout_instance_id = instance.pk

#     def __get_user_address(self, request, **kwargs):
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             checkout_instance = getattr(temp, 'checkout_instance', None)
#             shipping_address_id = request.data.get('shipping_address_id', getattr(checkout_instance, 'shipping_address_id', None))
#             if shipping_address_id is None:
#                 default_address_id = getattr(temp.checkout_instance_user_details, 'default_address_id', None)
#                 shipping_address_id = default_address_id
#             if shipping_address_id is not None:
#                 try:
#                     fields = {'user_id': request.user.user_id}
#                     queryset = super().get_or_set(model='_user_addresses', extra_fields=fields, queryset=reg_models.UserAddresses.objects)
#                     print(queryset)
#                     user_address_obj = super().filter_cache(queryset, fields=[{'pk': shipping_address_id, 'data_type': 'int'}])[0]
#                 except Exception:
#                     user_address_obj = None
#                 temp.checkout_user_address = user_address_obj
#             data = {'shipping_address_id': getattr(temp.checkout_user_address, 'address_id', None)}
#             return data

#     @action(detail=False, methods=['post'])
#     def get_shipping_method(self, request, **kwargs):
#         temp = kwargs.get('temp', super().get_temp(request))
#         checkout_instance = getattr(temp, 'checkout_instance', None)
#         shipping_method_id = request.data.get('shipping_method_id', getattr(checkout_instance, 'shipping_method_id', None))
#         print(shipping_method_id)
#         request.session['shipping_method_id'] = shipping_method_id
#         if temp is not None:
#             data = {}
#             if shipping_method_id is None:
#                 shipping_rate = 0
#             else:
#                 if int(shipping_method_id) == 1:
#                     shipping_address_id = self.__get_user_address(request, temp=temp)
#                     data.update(**shipping_address_id)
#                     shipping_rate = super().get_checkout_rate(request, temp=temp)
#                 else:
#                     shipping_rate = 0
#             data.update({
#                 'checkout_shipping_rate': dec(shipping_rate), 
#                 'shipping_method_id': shipping_method_id
#             })
#             if self.checkout_on_load or self.checkout_backend_load:
#                 if self.checkout_on_load:
#                     data.pop('shipping_method_id', None)
#                 return data
#             return self.calculate_total(request, checkout_shipping_rate=data.get('checkout_shipping_rate', 0), temp=temp)

#     def calculate_product_vat(self, **kwargs):
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             if temp.checkout_items is not None:
#                 for item in temp.checkout_items:
#                     price = item.sku_no.product_config_id.price
#                     vat = round((price * vat_perc), 2)
#                     data = {
#                         'order_item_excl': price,
#                         'order_item_vat': vat,
#                         'order_item_incl': price + vat
#                     }
#                     item.update(data)
#                     item.reload_from_db()
#             return True

#     def calculate_total(self, request, **kwargs):
#         '''
#         calculate total incl shipping
#         note: 
#         - if not on saved checkout:
#         product calculations for VAT are not redone, rather, they are taken from the shopping cart viewset
#         - else:
#         product calculations are redone to match the product config price
#         '''
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             checkout_shipping_rate = kwargs.get('checkout_shipping_rate', 0)
#             if temp.checkout_saved_instance:
#                 total_quantity = temp.checkout_items.count()
#                 subtotal_excl = 0
#                 if temp.checkout_instance == 'order':
#                     for item in temp.checkout_items:
#                         subtotal_excl += item.order_item_excl
#             else:
#                 if temp.checkout_items is not None:
#                     if temp.checkout_instance_type == 'order':
#                         subtotal_excl = temp.shopping_cart_obj.subtotal
#                         total_quantity = temp.shopping_cart_obj.total_quantity
#                     if temp.checkout_instance_type == 'repair':
#                         subtotal_excl = 0
#                         total_quantity = 0
#             shipping = checkout_shipping_rate
#             subtotal_incl = subtotal_excl + shipping
#             vat = round((subtotal_incl * vat_perc), 2)
#             total = vat + subtotal_incl
#             data = {
#                 'total_quantity': total_quantity,
#                 'subtotal_excl': subtotal_excl,
#                 'shipping': shipping,
#                 'subtotal_incl': subtotal_incl,
#                 'vat': vat,
#                 'total': total
#             }
#             if self.checkout_on_load or self.checkout_backend_load:
#                 return data
#             else:
#                 super().set_temp(request, temp=temp)
#                 return Response(data, status=status.HTTP_200_OK)

#     def initialize_user_addresses(self, request):
#         fields = {'user_id': request.user.user_id}
#         queryset = super().get_or_set(model='_user_addresses', extra_fields=fields, queryset=reg_models.UserAddresses.objects)
#         serializer = reg_model_serializers.UserAddressesSerializer(queryset, many=True)
#         return serializer.data

#     def initialize_user(self, request, **kwargs):
#         '''
#         initializes user details, from queryset or cache
#         '''
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             fields = {'user_id': request.user.user_id}
#             queryset = super().get_or_set(model='_user_details', extra_fields=fields, queryset=reg_models.UserDetails.objects)
#             temp.checkout_instance_user_details = queryset[0]

#     def serialized_checkout_items(self, request, **kwargs):
#         '''
#         returns serialized versions of products
#         '''
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             if temp.checkout_instance_type == 'order':
#                 if temp.checkout_saved_instance:
#                     super().retrieve_items(request, pk=temp.checkout_instance_id)
#                 else:
#                     data = super().serialized_response(request, backend_req=True, exclude='shopping_cart', temp=temp)
#             if temp.checkout_instance_type == 'repair':
#                 serializer = st_model_serializers.ProductsSerializer(temp.checkout_items, context={'request': request}, many=True)
#                 data = serializer.data
#             return data

#     def check_active(self, **kwargs):
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             if temp.checkout_instance_type == 'repair':
#                 items = [temp.checkout_items]
#             else:
#                 items = temp.checkout_items
#                 temp.checked_ex_unit = False
#                 temp.contains_ex = False
#             for item in items:
#                 if temp.checkout_instance_type == 'order':
#                     if temp.checkout_saved_instance:
#                         product_config_id = item.sku_no.product_config_id
#                         product_id = product_config_id.product_id
#                     else:
#                         product_config_id = item.product_config_id
#                         product_id = item.product_config_id.product_id
#                     quantity = [i for i in items if i.product_config_id == product_config_id]
#                     quantity = quantity.count(len(quantity))
#                     if temp.checked_ex_unit == False:
#                         if product_config_id.variation_id == 2:
#                             temp.contains_ex = True
#                             temp.checked_ex_unit = True
#                     if (product_config_id.stock_available - 2) > quantity:
#                         return Exception
#                 else:
#                     product_id = item[0]
#                 if product_id.is_active == False:
#                     return custom_exceptions.item_non_active_error('product')
#             return True
        
#     def return_saved_ex_unit_files(self, pk=None):
#         file_model, file_serializer = self.__get_private(['file_model', 'file_serializer'])
#         if pk is not None:
#             queryset = file_model.objects.filter(pk=pk, uploaded_by='user')
#             if len(queryset) != 0:
#                 serializer = file_serializer(queryset, many=True)
#                 if serializer.is_valid(raise_exception=True):
#                     return {'saved_ex_unit_files': serializer.data}
#             else:
#                 return None

#     def run_checks(self, request, instance_type=None, pk=None, **kwargs):
#         '''
#         used for the retrieve() and payment_initialize_data() methods
#         '''
#         temp = kwargs.get('temp', None)
#         self.initialize_user(request, temp=temp)
#         if temp is not None:
#             checkout_saved_instance = getattr(temp, 'checkout_saved_instance', False)
#             temp.checkout_saved_instance = checkout_saved_instance
#             if temp.checkout_saved_instance:
#                 if self.checkout_backend_load:
#                     self.continue_saved_checkout(request, pk=pk, instance_type=instance_type, temp=temp)
#             else:
#                 self.initialize_new(request, instance_type=instance_type, temp=temp)
#             shipping_rate = self.get_shipping_method(request, temp=temp)
#             checkout_total = self.calculate_total(request, temp=temp, checkout_shipping_rate=shipping_rate.get('checkout_shipping_rate', 0))
#             data = {
#                 'checkout_total': checkout_total
#             }
#             self.check_active(temp=temp)
#             if temp.checkout_instance_type == 'order':
#                 data['checkout_contains_ex'] = temp.contains_ex
#             if self.checkout_on_load:
#                 data['checkout_items'] = self.serialized_checkout_items(request, temp=temp)
#                 data['user_addresses'] = self.initialize_user_addresses(request)
#                 data['active_address'] = getattr(temp, 'checkout_user_address', None)
#             if self.checkout_backend_load:
#                 shipping_rate.pop('checkout_shipping_rate', '')
#                 data.append(**shipping_rate)
#                 if temp.checkout_instance_type == 'repair':
#                     data['checkout_item_id'] = temp.checkout_items.pk
#             super().set_temp(request, temp=temp)
#             print(temp.__dict__)
#             return data

#     def retrieve(self, request, instance_type=None, **kwargs):
#         '''
#         return initial values on page load
#         '''
#         self.checkout_on_load = True
#         temp = kwargs.get('temp', super().get_temp(request))
#         data = self.run_checks(request, instance_type=instance_type, temp=temp)
#         extra_vals = kwargs.get('extra_vals', None)
#         if extra_vals is not None:
#             data.append(**extra_vals)
#         self.checkout_on_load = False
#         return Response(data, status=status.HTTP_200_OK)

#     @action(detail=True, methods=['get'], url_path=r'(?P<pk>\d+)/initialize')
#     def payment_initialize_data(self, request, instance_type=None, pk=None):
#         ''' 
#         initialize data process for payfast, including running checks and creating instance
#         '''
#         self.checkout_backend_load = True
#         temp = super().get_temp(request)
#         data = self.run_checks(request, instance_type=instance_type, pk=pk, temp=temp)
#         initial = {'initial': data}
#         if temp.checkout_saved_instance:
#             initial.append(**{f'{temp.checkout_instance_type}': temp.checkout_instance})
#             action = 'update'
#         else:
#             action = 'create'
#         instance = getattr(temp.checkout_instance_super, action)
#         self.initialize_saved(instance(request, **initial))
#         if temp.checkout_instance_type == 'order':
#             if action == 'create':
#                 self.create_order_items(request, initial_data_items=temp.checkout_items, order_instance=temp.checkout_instance)
#             if action == 'update':
#                 self.update_order_items(request, fields={'is_pending': True}, order_instance=temp.checkout_instance)
#             if instance.contains_ex == True:
#                 self.update_or_delete_ex_images(request, order_instance=temp.checkout_instance)
#         self.checkout_backend_load = False
#         return super().initialize_form(request, temp=temp)

#     @action(detail=True, methods=['get'], url_path=r'(?P<pk>\d+)')
#     def continue_saved_checkout(self, request, pk=None, instance_type=None, **kwargs):
#         if pk is not None:
#             temp = kwargs.get('temp', None)
#             if temp is None:
#                 temp = super().get_temp(request)
#             temp.checkout_saved_instance = True
#             self.initialize(instance_type=instance_type, temp=temp)
#             self.initialize_saved(self.checkout_instance_model.objects.get(pk=pk), temp=temp)
#             if instance_type == 'order':
#                 # child_model = getattr(temp.checkout_instance_super, 'child_model')
#                 # get_private = getattr(temp.checkout_instance_super, 'get_private')
#                 # child_model = get_private(['child_model'])
#                 child_model = self.__get_private(['child_model'])
#                 prefetch_qs = getattr(temp.checkout_instance_super, 'def_prefetch_queryset')
#                 temp.checkout_items = child_model.objects.prefetch_related(prefetch_qs).filter(order_id=pk)
#                 extra_vals = self.return_saved_ex_unit_files(pk=pk)
#             if instance_type == 'repair':
#                 temp.checkout_items = temp.checkout_instance.product_id
#                 extra_vals = {'saved_reason_repair': temp.checkout_instance.reason_repair, 'saved_error_codes': temp.checkout_instance.error_codes}
#             super().set_temp(request, temp=temp)
#             return self.retrieve(request, instance_type=instance_type, extra_vals=extra_vals)

#     def __return_bank_accounts(self, request):
#         fields = {'user_id': request.user.user_id}
#         queryset = reg_models.UserBankAccountDetails.objects.filter(**fields)
#         serializer = reg_model_serializers.UserBankAccountDetailsSerializer(queryset, many=True)
#         return serializer.data

#     @action(detail=True, methods=['post'], url_path=r'(?P<pk>\d+)/init/pre_transaction')
#     def payment_pre_transaction(self, request, instance_type=None, pk=None):
#         self.checkout_backend_load = True
#         temp = super().get_temp(request)
#         data = self.run_checks(request, instance_type=instance_type, pk=pk, temp=temp)
#         initial = {'initial': data}
#         if temp.checkout_saved_instance:
#             initial.append(**{f'{temp.checkout_instance_type}': temp.checkout_instance})
#             action = 'update'
#         else:
#             action = 'create'
#         temp.checkout_instance_action = action
#         temp.checkout_instance_initial = initial
#         user_bank_accounts = self.__return_bank_accounts(request)
#         return Response(user_bank_accounts, status=status.HTTP_200_OK)
    
#     def __payment_initialize_data(self, request, **kwargs):
#         self.checkout_backend_load = True
#         temp = kwargs.get('temp', None)
#         if temp is not None:
#             action = temp.checkout_instance_action
#             initial = temp.checkout_instance_initial
#             self.__initialize_super(instance_type=temp.checkout_instance_type)
#             instance = getattr(self.checkout_instance_super, action)
#             self.initialize_saved(instance(request, **initial), temp=temp)
#             if temp.checkout_instance_type == 'order':
#                 if action == 'create':
#                     self.create_order_items(request, initial_data_items=temp.checkout_items, order_instance=temp.checkout_instance)
#                 if action == 'update':
#                     self.update_order_items(request, fields={'is_pending': True}, order_instance=temp.checkout_instance)
#                 if temp.checkout_instance.contain_ex == True:
#                     self.update_or_delete_ex_images(request, order_instance=temp.checkout_instance)
#             self.checkout_backend_load = False

#     def __send_conf(self, request, **kwargs):
#         temp = kwargs.get('temp')
#         if temp is not None:
#             data = kwargs.get('conf_data', None)
#             instance_type = temp.checkout_instance_type
#             subject = f'{instance_type} {temp.checkout_instance_id} is confirmed'
#             comment = subject
#             status_data = {
#                 'subject': subject,
#                 'comment': comment,
#                 'instance': self.checkout_instance,
#                 'comm_method': 'SMS, email'
#             }
#             conf_data = status_data
#             conf_data.pop('comm_method')
#             conf_data.append(**{'serializer_data': data})
#             send_conf = getattr(self.checkout_instance_super, 'send_conf')
#             update_status = getattr(self.checkout_instance_super, 'update_status')
#             if instance_type == 'order':
#                 status_data['current_status_id'] = 1
#             if instance_type == 'repair':
#                 status_data['current_status_id'] = 2
#             send_conf(request, **conf_data)
#             update_status(request, **status_data)

#     def __cancel_transaction(self, request):
#         temp = super().get_temp(request)
#         super().cancel_billing_request(temp=temp)
#         current_status_id = {'current_status_id': 3}
#         fields = {
#             **current_status_id,
#             'current_status_date': ''
#         }
#         status_data = {
#             **current_status_id,
#             'subject': f'Your {temp.checkout_instance_type} {temp.checkout_instance_id} has been saved for future payment',
#             'comment': '',
#             'instance': self.checkout_instance,
#             'comm_method': ''
#         }
#         update_status = getattr(self.checkout_instance_super, 'update_status')
#         update_status(request, **status_data)
#         if temp.checkout_instance_type == 'order':
#             self.update_order_items(request, pk=temp.checkout_instance_id, fields=fields)
#         return Response({'message': f'successfully cancelled {temp.checkout_instance_type}'}, status=status.HTTP_200_OK)

#     @action(detail=True, methods=['post'], url_path=r'(?P<pk>\d+)/init/post_transaction')
#     def payment_post_transaction(self, request, instance_type=None, pk=None):
#         try:
#             global checkout_transaction_status
#             temp = super().get_temp(request)
#             self.__payment_initialize_data(request, temp=temp)
#             super().billing_request_process(request, temp=temp, global_var=checkout_transaction_status, obj_type='checkout_cancellation')
#             if True:
#                 html_conf = getattr(temp.checkout_instance_super, 'render_conf')
#                 data = html_conf(request, instance=temp.checkout_instance, user_details=temp.checkout_instance_user_details)
#                 self.__send_conf(request, temp=temp, conf_data=data)
#                 return Response(data, status=status.HTTP_201_CREATED)
#         except Exception:
#             return self.__cancel_transaction(request)

#     @action(detail=False, methods=['get'], url_path=r'(?P<pk>\d+)/cancel')
#     def payment_cancel(self, request, pk=None, **kwargs):
#         '''
#         if pk matches, sets instance (and items) to 'saved'
#         '''
#         global checkout_transaction_status
#         checkout_transaction_status = 'cancelled'
#         return Response({'message': 'sent cancellation'}, status=status.HTTP_200_OK)
    
    # @action(detail=False, methods=['delete'], url_path=r'(?P<pk>\d+)/recieve')
    # def payment_recieve_data(self, request, pk=None):
    #     '''
    #     if pk matches, recieve data
    #     '''
    #     if temp.checkout_instance_id == int(pk):
    #         return super().recieve_data(request)

    # @action(detail=False, url_path=r'(?P<pk>\d+)/render-conf')
    # def render_conf(self, request, pk=None):
    #     '''
    #     process data through payfast security checks with conduct_security_checks()
    #     if successful, continue process
    #     render and serialize data in render_conf(), return to user
    #     if shipping_method_id '1' was selected, create shipment from BobGo API
    #     pass serialized data to send_conf()
    #     send confirmed status using update_status()

    #     will send a response to the client in the instance the security checks weren't successful for the admin/technical department to investigate

    #     '''
    #     temp = super().get_temp()
    #     if temp.checkout_instance_id == pk:
    #         super().conduct_security_checks(request)
    #         if True:
    #             html_conf = getattr(temp.checkout_instance_super, 'render_conf')
    #             data = html_conf(request, instance=temp.checkout_instance, user_details=temp.checkout_instance_user_details)
    #             if temp.checkout_instance.shipping_method_id == 1:
    #                 super().create_shipment(request)
    #                 temp.checkout_instance.refresh_from_db()
    #             subject = f'Your {temp.checkout_instance_type} {temp.checkout_instance_id} is confirmed'
    #             comment = subject
    #             status_data = {
    #                 'subject': subject,
    #                 'comment': comment,
    #                 'instance': self.checkout_instance,
    #                 'comm_method': 'SMS, email'
    #             }
    #             conf_data = status_data
    #             conf_data.pop('comm_method')
    #             conf_data.append(**{'serializer_data': data})
    #             send_conf = getattr(temp.checkout_instance_super, 'send_conf')
    #             update_status = getattr(temp.checkout_instance_super, 'update_status')
    #             if temp.checkout_instance_type == 'order':
    #                 status_data['current_status_id'] = 1
    #             if temp.checkout_instance_type == 'repair':
    #                 status_data['current_status_id'] = 2
    #             send_conf(request, **conf_data)
    #             update_status(request, **status_data)
    #             return Response(data, status=status.HTTP_201_CREATED)  
    #         else:
    #             return self.payment_cancel(request, pk=temp.checkout_instance_id, temp=temp)
    #             # return Response({'message': 'Payment Failed'}, status=status.HTTP_400_BAD_REQUEST)
    #     else:
    #         return Response({'message': 'Invalid Checkout Instance ID'}, status=status.HTTP_400_BAD_REQUEST)