
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# --------------API URLS ------------ #
api_version = "api/v1/"

urlpatterns += [
    path(
        api_version + "accounts/",
        include(
            "apps.account.urls"
        )
    ),
]
