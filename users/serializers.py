from rest_framework import serializers
from .models import User, Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street_address', 'city', 'division', 'postal_code', 'additional_info', 'is_primary']

class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'password', 'address', 'addresses']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password =  validated_data.pop('password')
        user = User(**validated_data)
        # username is unique on AbstractUser but not exposed by the API; mirror the email.
        user.username = user.email
        user.set_password(password)
        
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
