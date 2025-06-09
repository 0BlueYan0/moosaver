from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name='home'),
    path("home/", views.home_view, name='home/home'),
    path("download/", views.download_view, name='download'),
    path("api/download/", views.api_download, name='api_download'),
    path("api/download/progress/<str:stuid>/", views.api_download_progress, name='api_download_progress'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('files/', views.file_manage_view, name='file_manage'),
    path('files/download', views.download_file_view, name='download_file'),
    path('files/downloads/all/', views.download_all_user_files_view, name='download_all_files'),
    path('files/download_folder', views.download_folder_view, name='download_folder'),
]
