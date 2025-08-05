from django.contrib import admin
from django.urls import path
from barimt_zasvarlagch_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home),  # Үндсэн хаяг руу ороход home.html гарна
]
