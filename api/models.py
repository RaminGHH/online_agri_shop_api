# from django.db import models
# from django.utils.text import slugify

# # =================== CATEGORY MODEL =================== #
# class Category(models.Model):
#     """
#     Represents a product category in the store.

#     Categories are used to organize products into logical groups
#     and provide filtering, navigation, and SEO-friendly URLs.
#     Examples: Irrigation Equipment, Polyethylene Pipes, Fertilizers.
#     """
#     name = models.CharField(max_length=150)
#     slug = models.SlugField(max_length=120, unique=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     # OVERRIDE SAVE
#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.name)
#         super().save(*args, **kwargs)

#     # NAME OF OBJECT
#     def __str__(self):
#         return self.name

# # =================== BRAND MODEL =================== #
# class Brand(models.Model):
#     """
#     Represents a product manufacturer or brand.

#     Brands help customers identify product origins,
#     improve filtering capabilities, and enhance search accuracy.
#     Examples: Apple, Nike.
#     """
#     name = models.CharField(max_length=100)
#     slug = models.SlugField(max_length=120, unique=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     # OVERRIDE SAVE 
#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.name)
#         super().save(*args, **kwargs)

#     # NAME OF OBJECT
#     def __str__(self):
#         return self.name

# # =================== PRODUCT MODEL =================== #
# class Product(models.Model):
#     """
#     Represents a sellable product in the e-commerce platform.

#     Stores all essential product information including pricing,
#     inventory status, categorization, branding, descriptions,
#     images, and SEO-related metadata.

#     This model serves as the core entity of the catalog system
#     and is referenced by carts, orders, reviews, wishlists,
#     and inventory management modules.
#     """
#     name = models.CharField(max_length=200)
#     slug = models.SlugField(max_length=220, unique=True, blank=True)

#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     stock = models.PositiveIntegerField(default=0)

#     category = models.ForeignKey(Category, on_delete=models.PROTECT)
#     brand = models.ForeignKey(Brand, on_delete=models.PROTECT)

#     description = models.TextField(blank=True)

#     #unique code for product
#     sku = models.CharField(max_length=100, unique=True, null=True, blank=True)

#     discount_price = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         null=True,
#         blank=True
#     )

#     rating = models.DecimalField(
#         max_digits=3,
#         decimal_places=2,
#         default=0
#     )
#     is_active = models.BooleanField(default=True)

#     main_image = models.ImageField(upload_to='products/', null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     # OVERRIDE SAVE 
#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.name)
#         super().save(*args, **kwargs)

#     # NAME OBJECT
#     def __str__(self):
#         return self.name
    
# # =================== PRODUCT IMAGE MODEL =================== #
# class ProductImage(models.Model):
#     """
#     Stores additional images associated with a product.

#     Supports product galleries by allowing multiple images
#     to be linked to a single product. Images can be used for
#     product previews, zoom views, and detailed visual presentations.
#     """
#     product = models.ForeignKey(
#         Product, 
#         related_name='images',
#         on_delete=models.CASCADE
#     )

#     image = models.ImageField(upload_to='products/')
#     alt_text = models.CharField(max_length=150, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"Image of {self.product.name}"
    