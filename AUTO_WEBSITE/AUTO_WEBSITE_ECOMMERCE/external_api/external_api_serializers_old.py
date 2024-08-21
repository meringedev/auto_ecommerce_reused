from rest_framework import serializers
from phonenumber_field import serializerfields

class PayFastSerializer(serializers.Serializer):
    merchant_id = serializers.CharField(min_length=8, max_length=8)
    merchant_key = serializers.CharField(min_length=13, max_length=13)
    return_url = serializers.URLField()
    cancel_url = serializers.URLField()
    notify_url = serializers.URLField()
    name_first = serializers.CharField()
    name_last = serializers.CharField()
    email_address = serializers.EmailField()
    cell_number = serializerfields.PhoneNumberField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    item_name = serializers.CharField()
    security_signature = serializers.CharField(min_length=20, max_length=40)

class PayFastIncomingSerializer(serializers.Serializer):
    pf_payment_id = serializers.IntegerField()
    payment_status = serializers.CharField()
    item_name = serializers.CharField(max_length=100)
    amount_gross = serializers.DecimalField(max_digits=12, decimal_places=2)
    amount_fee = serializers.DecimalField(max_digits=12, decimal_places=2)
    amount_net = serializers.DecimalField(max_digits=12, decimal_places=2)
    merchant_id = serializers.IntegerField()
    signature = serializers.CharField()