from django.contrib import admin
from .models import User, Profile, Address

class ProfileInLine(admin.StackedInline):
    model = Profile
    extra = 0

class AddressInLine(admin.StackedInline):
    model = Address
    extra = 0 

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone_number",
        "email",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "is_staff",
        "is_active",
    )

    search_fields = (
        "city",
        "province",
        "is_default",
    )

    inlines = [
        ProfileInLine,
        AddressInLine
    ]

