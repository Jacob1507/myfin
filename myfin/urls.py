"""
URL configuration for myfin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "budgets-summary-list": reverse(
                "budgets-summary-list", request=request, format=format
            ),
            "budget-create": reverse("budget-create", request=request, format=format),
            "budget-delete": reverse("budget-delete", request=request, format=format),
            "bank-aliases-list": reverse(
                "bank-aliases-list", request=request, format=format
            ),
            "bank-alias-create": reverse(
                "bank-alias-create", request=request, format=format
            ),
            "bank-alias-delete": reverse(
                "bank-alias-delete", request=request, format=format
            ),
            "transactions-list": reverse(
                "transactions-list", request=request, format=format
            ),
            "transaction-create": reverse(
                "transaction-create", request=request, format=format
            ),
            "transaction-delete": reverse(
                "transaction-delete", request=request, format=format
            ),
            "transaction-categories-list": reverse(
                "transaction-categories-list", request=request, format=format
            ),
            "transaction-category-create": reverse(
                "transaction-category-create", request=request, format=format
            ),
            "transaction-category-delete": reverse(
                "transaction-category-delete", request=request, format=format
            ),
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("finances.urls")),
    path("api/", api_root),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
