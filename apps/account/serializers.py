from rest_framework import serializers
from .models import User, Profile, Address

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta: 
        model = User

        fields = [
            "phone_number",
            "email",
            "full_name",
            "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
    
        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Profile

        fields = [
            "avatar",
            "bio",
            "birth_date"
        ]

class UserSerializer(serializers.ModelSerializer):

    # profile = ProfileSerializer(
    #     read_only=True
    # )

    class Meta: 
        model = User

        fields = [
            "id",
            "phone_number",
            "email",
            "full_name",
            "profile",
        ]

        read_only_fields = [
            "id",
            "phone_number"
        ]

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address

        fields = [
            "id",
            "full_name",
            "phone_number",
            "province",
            "city",
            "postal_code",
            "street_address",
            "is_default",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "is_default",
            "created_at",
            "updated_at",
        ]