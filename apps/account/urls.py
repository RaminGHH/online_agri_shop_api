from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    ProfileViewSet,
    AddressViewSet
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# =========================
# Router
# =========================
router = DefaultRouter()

# POST   /users/register/
# GET    /users/me/
# PUT    /users/me/
# PATCH  /users/me/
router.register(r"users", UserViewSet, basename="users")

# GET    /profile/
# PATCH  /profile/
router.register(r"profile", ProfileViewSet, basename="profile")

# GET     /addresses/
# POST    /addresses/
# GET     /addresses/{id}/
# PATCH   /addresses/{id}/
# PUT     /addresses/{id}/
# DELETE  /addresses/{id}/
# POST /addresses/{id}/set_default/
router.register(r"addresses", AddressViewSet, basename="addresses")

urlpatterns = [
    # ViewSets
    path("", include(router.urls)),

    # JWT Auth 
    # POST /login/
    path(
        "login/",
        TokenObtainPairView.as_view(),
        name="login"
    ),

    # POST /token/refresh/
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),
]