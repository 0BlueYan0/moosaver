from django.urls import path
from . import views
from download.views import api_user_permissions

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('permissions/', api_user_permissions, name='user_permissions'),
]
