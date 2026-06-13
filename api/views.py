#from django.shortcuts import render

from rest_framework import viewsets

from .models import Product
from .serializers import ProductSerialier

class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD API for products
    """
    queryset = Product.objects.select_related(
        "category",
        "brand"
    ).prefetch_related(
        "images"
    )

    serializer_class = ProductSerialier
