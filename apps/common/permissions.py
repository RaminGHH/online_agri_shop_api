from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsActiveUser(BasePermission):
    """
    Check that the user is active.

    Users with status 'suspended' or 'blocked' are not allowed to perform any action.
    """
    message = 'Your account is inactive'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.status == 'active'
        )


class IsAdminUser(BasePermission):
    """
    Allow only users with role == 'admin'.

    Note: `is_staff` alone is not sufficient (according to SRS Chapter 2.5).
    """
    message = 'This operation is allowed for admins only'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
            and request.user.status == 'active'
        )


class IsPersonnelUser(BasePermission):
    """
    Allow users with role == 'personnel' or 'admin'.

    This permission is used for sections that require staff-level access.
    """
    message = 'This section is for personnel only'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('personnel', 'admin')
            and request.user.status == 'active'
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission.

    Users can only access their own resources, unless they are admin.

    The model must have a `user` or `owner` field.

    Example:
        GET /orders/123/ → Only the order owner or an admin can access it.
    """
    message = 'You do not have permission to access this resource.'

    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.role == 'admin':
            return True

        # Check ownership: try 'user' field first, then 'owner'
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user


class ReadOnly(BasePermission):
    """
    Allow only safe HTTP methods (GET, HEAD, OPTIONS).

    Use this for public endpoints that should not modify data.
    """
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class HasAppPermission(BasePermission):
    """
    Check Django's custom (app-level) permissions.

    Example usage in a view:
        class SomeView(APIView):
            permission_classes = [IsActiveUser, HasAppPermission]
            required_permissions = ["products.publish_product"]

    Example custom permission definition in a model:
        class Product(models.Model):
            class Meta:
                permissions = [
                    ("publish_product", "Can publish product"),
                    ("archive_product", "Can archive product"),
                ]
    """
    def has_permission(self, request, view):
        # Read required permissions from the view (default to empty list)
        perms = getattr(view, "required_permissions", [])

        # If no permissions are required, allow access
        if not perms:
            return True

        # Check if the user has all required permissions
        return request.user.has_perms(perms)

# ── Custom Permissions تعریف‌شده در مدل‌ها ──
#
# این‌ها در Meta هر مدل تعریف می‌شوند:
#
# apps/catalog:
#   products.publish_product
#   products.archive_product
#   products.feature_product
#
# apps/inventory:
#   inventory.adjust_stock
#   inventory.view_cost_price
#
# apps/orders:
#   orders.change_status
#   orders.cancel_any_order
#   orders.view_all_orders
#
# apps/payments:
#   payments.refund_payment
#   payments.view_transactions
#   payments.manage_wallet
#
# apps/accounts:
#   accounts.block_user
#   accounts.change_user_role
#   accounts.view_sensitive_info