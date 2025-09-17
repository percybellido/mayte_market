from django.urls import path
from . import views

app_name='inicio_app'

urlpatterns=[
    path('', views.home, name='home'),
    path('contacto/', views.contacto, name='contacto'),
]
