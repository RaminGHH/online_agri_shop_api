from rest_framework import serializers
from .models import Product, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product galley image
    """
    class Meta:
        model = ProductImage
        fields = (
            "id",
            "image",
            "alt_text"
        )

class ProductSerialier(serializers.ModelSerializer):
    """
    Serializer for product data
    """
    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    brand_name = serializers.CharField(
        source="brand.name",
        read_only=True
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "discount_price",
            "stock",
            "is_active",
            "description",
            "main_image",
            "rating",
            "category",
            "category_name",
            "brand",
            "brand_name",
            "images",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "slug",
            "rating",
            "created_at",
            "updated_at"
        )