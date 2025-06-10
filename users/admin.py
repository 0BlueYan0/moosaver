from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import SiteUser

class SiteUserInline(admin.StackedInline):
    model = SiteUser
    can_delete = False
    verbose_name_plural = '下載統計'
    fields = ('total_downloads', 'total_download_size', 'last_download_time')

class CustomUserAdmin(UserAdmin):
    inlines = (SiteUserInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_total_downloads', 'get_total_size')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_total_downloads(self, obj):
        return obj.siteuser.total_downloads
    get_total_downloads.short_description = '總下載次數'

    def get_total_size(self, obj):
        return f"{obj.siteuser.get_total_download_size_mb()} MB"
    get_total_size.short_description = '總下載大小'

# 重新註冊 User 模型
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)