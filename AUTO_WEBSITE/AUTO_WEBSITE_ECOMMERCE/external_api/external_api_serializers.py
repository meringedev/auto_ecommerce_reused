from rest_framework import serializers
from phonenumber_field import serializerfields
from .. import utils

class SageCustomerSerializer(serializers.Serializer):
    CustomerId = serializers.IntegerField(required=False, allow_null=True)
    Name = serializers.CharField()
    TaxReference = serializers.CharField(max_length=30, required=False, allow_null=True)
    Mobile = serializers.CharField(max_length=30)
    Email = serializers.CharField(max_length=30)
    ContactName = serializers.CharField(max_length=100)

    def get_fields(self):
        result = super().get_fields()
        return utils.get_fields_overrider(result, CustomerId)

class SageInvoiceLinesSerializer(serializers.Serializer):
    SelectionId = serializers.IntegerField()
    TaxTypeId = serializers.IntegerField(required=False, allow_null=True)
    Description = serializers.CharField(required=False, allow_null=True)
    Exclusive = serializers.DecimalField(max_digits=12, decimal_places=2)
    Quantity = serializers.DecimalField(max_digits=12, decimal_places=2, default=1)

class SageInvoiceSerializer(serializers.Serializer):
    CustomerId = serializers.IntegerField()
    InvoiceId = serializers.IntegerField(required=False, allow_null=True)
    DocumentNumber = serializers.CharField(required=False, allow_null=True, max_length=100)
    # TaxReference = serializers.CharField(max_length=30, required=False, allow_null=True)
    Date = serializers.DateTimeField()
    Inclusive = serializers.BooleanField(default=False)
    Reference = serializers.CharField(max_length=100)
    Exclusive = serializers.DecimalField(max_digits=12, decimal_places=2)
    Tax = serializers.DecimalField(max_digits=12, decimal_places=2)
    Total = serializers.DecimalField(max_digits=12, decimal_places=2)
    Lines = SageInvoiceLinesSerializer(many=True)

    def get_fields(self):
        result = super().get_fields()
        return utils.get_fields_overrider(result, InvoiceId)

class SageItemSerializer(serializers.Serializer):
    ItemId = serializers.IntegerField(required=False, allow_null=True)
    Code = serializers.CharField(max_length=100)
    Description = serializers.CharField(max_length=100)
    Active = serializers.BooleanField(default=True)
    PriceExclusive = serializers.DecimalField(max_digits=12, decimal_places=2)
    Physical = serializers.BooleanField(default=True)
    TaxTypeIdPurchases = serializers.IntegerField(required=False, allow_null=True)
    TaxTypeIdSales = serializers.IntegerField(required=False, allow_null=True)

    def get_fields(self):
        result = super().get_fields()
        return utils.get_fields_overrider(result, ItemId)

class BobGoAddressSerializer1(serializers.Serializer):
    company = serializers.CharField(required=False, allow_null=True)
    street_address = serializers.CharField()
    local_area = serializers.CharField()
    city = serializers.CharField()
    zone = serializers.CharField()
    code = serializers.CharField()

# class BobGoItemSerializer1(serializers.Serializer):
#     description = serializers.CharField(allow_blank=True)
#     price = serializers.DecimalField(max_digits=12, decimal_places=2)
#     quantity = serializers.IntegerField()
#     length_cm = serializers.DecimalField(max_digits=12, decimal_places=2)
#     width_cm = serializers.DecimalField(max_digits=12, decimal_places=2)
#     height_cm = serializers.DecimalField(max_digits=12, decimal_places=2)
#     weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2)

class BobGoItemSerializer1(serializers.Serializer):
#    description = serializers.CharField(allow_blank=True)
   submitted_length_cm = serializers.DecimalField(max_digits=12, decimal_places=2)
   submitted_width_cm = serializers.DecimalField(max_digits=12, decimal_places=2)
   submitted_height_cm = serializers.DecimalField(max_digits=12, decimal_places=2)
   submitted_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2)
#    custom_parcel_reference = serializers.CharField(allow_blank=True)

class BobGoCourierRateSerializer(serializers.Serializer):
    collection_address = BobGoAddressSerializer1()
    delivery_address = BobGoAddressSerializer1()
    parcels = BobGoItemSerializer1(many=True)
    declared_value = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    timeout = serializers.IntegerField()
    providers = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    service_levels = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )

class BobGoCheckoutSerializer(serializers.Serializer):
    timeout = serializers.IntegerField()
    collection_address = BobGoAddressSerializer1()
    collection_contact_company = serializers.CharField(allow_blank=True)
    collection_contact_name = serializers.CharField()
    collection_contact_mobile_no = serializers.CharField()
    collection_contact_email = serializers.EmailField()
    delivery_address = BobGoAddressSerializer1()
    delivery_contact_company = serializers.CharField(allow_blank=True)
    delivery_contact_name = serializers.CharField()
    delivery_contact_mobile_no = serializers.CharField()
    delivery_contact_email = serializers.EmailField()
    parcels = BobGoItemSerializer1(many=True)
    declared_value =  serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    custom_tracking_reference = serializers.CharField(allow_blank=True)
    custom_order_number = serializers.CharField()
    instructions_collection = serializers.CharField(allow_blank=True)
    instructions_delivery = serializers.CharField(allow_blank=True)
    service_level_code = serializers.CharField()
    provider_slug = serializers.CharField()
    collection_min_date = serializers.DateTimeField()
    collection_after = serializers.TimeField()
    collection_before = serializers.TimeField()