from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name='home'),
    path("download/", views.download_view, name='download'),
]
