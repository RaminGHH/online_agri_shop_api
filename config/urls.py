
from django.contrib import admin
from django.urls import include, path

VERSION = 'api/v1/'

urlpatterns = [
    path('admin/', admin.site.urls),

    # path(
    #     "api/v1/", include("api.urls")
    # )
]
