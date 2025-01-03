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
from django.urls import path

from ninja import NinjaAPI
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
from ninja_extra import exceptions
from ninja_jwt.routers.obtain import obtain_pair_router
from ninja_jwt.routers.verify import verify_router

from accounts.api import register_router
from finances.api import router as managers_router

api = NinjaAPI(
    title="Myfin API",
    version="1",
    throttle=[
        AnonRateThrottle("10/s"),
        AuthRateThrottle("100/s"),
    ],
)


def api_exception_handler(request, exc):
    headers = {}

    if isinstance(exc.detail, (list, dict)):
        data = exc.detail
    else:
        data = {"detail": exc.detail}

    response = api.create_response(request, data, status=exc.status_code)
    for k, v in headers.items():
        response.setdefault(k, v)

    return response


api.exception_handler(exceptions.APIException)(api_exception_handler)
api.add_router("/token", tags=["Auth"], router=obtain_pair_router)
api.add_router("/token", tags=["Auth"], router=verify_router)
api.add_router("/user", managers_router)
api.add_router("/", register_router)

urlpatterns = [path("admin/", admin.site.urls), path("api/", api.urls, name="api")]

if settings.DEBUG:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
