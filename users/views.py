from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
import json
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from .models import SiteUser, MoodleAccount
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from download.models import DownloadRecord

@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_view(request):
    # 處理GET請求 - 顯示登入頁面
    if request.method == 'GET':
        template = loader.get_template('login_page.html')
        return HttpResponse(template.render())
    
    # 處理POST請求 - 處理登入數據
    elif request.method == 'POST':
        content_type = request.headers.get('Content-Type', '')
        
        # 處理JSON請求 (來自前端的AJAX請求)
        if 'application/json' in content_type:
            try:
                # 解析JSON數據
                data = json.loads(request.body)
                
                # 提取數據
                username_or_email = data.get('username', '')
                password = data.get('password', '')
                remember_me = data.get('remember_me', False)

                # 嘗試用用戶名或電子郵件尋找用戶
                from django.contrib.auth import get_user_model
                UserModel = get_user_model()
                try:
                    if UserModel.objects.filter(username=username_or_email).exists():
                        user_obj = UserModel.objects.get(username=username_or_email)
                    elif UserModel.objects.filter(email=username_or_email).exists():
                        user_obj = UserModel.objects.get(email=username_or_email)
                    else:
                        user_obj = None
                except UserModel.DoesNotExist:
                    user_obj = None

                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
                else:
                    user = None

                if user is not None:
                    # 登入用戶
                    login(request, user)
                    if remember_me:
                        request.session.set_expiry(30* 24 * 60 * 60)  # 設置會話過期時間為30天
                    else:
                        request.session.set_expiry(0)  # 設置會話過期時間為瀏覽器關閉時
                    return JsonResponse({
                        'message': '登入成功',
                        'username': user.username
                    })
                else:
                    return JsonResponse({'error': '用戶名/信箱或密碼不正確'}, status=400)
                    
            except json.JSONDecodeError:
                return JsonResponse({'error': '無效的JSON格式'}, status=400)
                
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

# 修改register_view函數
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def register_view(request):
    # 處理GET請求 - 顯示註冊頁面
    if request.method == 'GET':
        return render(request, 'register_page.html')
    
    # 處理POST請求 - 處理註冊數據
    elif request.method == 'POST':
        # 檢查內容類型，確定是JSON還是表單提交
        content_type = request.headers.get('Content-Type', '')
        
        # 處理JSON請求 (來自Vue.js的AJAX請求)
        if 'application/json' in content_type:
            try:
                # 解析JSON數據
                data = json.loads(request.body)
                
                # 提取數據
                username = data.get('username', '')
                email = data.get('email', '')
                password = data.get('password', '')
                
                # 驗證數據
                errors = {}
                
                # 檢查用戶名是否存在
                if User.objects.filter(username=username).exists():
                    errors['username'] = '此用戶名已被使用'
                
                # 檢查電子郵件是否存在
                if User.objects.filter(email=email).exists():
                    errors['email'] = '此電子郵件已被使用'
                
                # 檢查密碼長度
                if len(password) < 6:
                    errors['password'] = '密碼必須至少包含6個字符'
                
                # 如果有錯誤，返回400錯誤
                if errors:
                    return JsonResponse(errors, status=400)
                
                # 創建用戶
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )

                # 註冊成功後建立使用者資料夾
                import os
                user_dir = os.path.join(settings.MEDIA_ROOT, user.username)
                os.makedirs(user_dir, exist_ok=True)
                
                # 登入新創建的用戶
                login(request, user)
                
                # 返回成功訊息
                return JsonResponse({
                    'message': '註冊成功',
                    'username': user.username
                }, status=201)
                
            except json.JSONDecodeError:
                return JsonResponse({'error': '無效的JSON格式'}, status=400)
            
            except Exception as e:
                # 捕獲其他未預期的錯誤
                return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    if request.method == 'POST':
        return JsonResponse({'message': '已成功登出'})
    return redirect('login')

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    """管理系統主頁面"""
    return render(request, 'users/admin_dashboard.html')

@user_passes_test(is_superuser)
def get_user_statistics(request):
    """獲取使用者統計數據的 API"""
    # 獲取總體統計
    total_users = User.objects.count()
    
    # 從新的 DownloadRecord 計算總數，這更準確
    total_stats = DownloadRecord.objects.aggregate(
        total_downloads=Count('id'),
        total_size=Sum('size')
    )
    total_downloads = total_stats['total_downloads'] or 0
    total_size = total_stats['total_size'] or 0
    
    # 獲取最近 7 天的下載趨勢
    today = datetime.now().date()
    last_week = today - timedelta(days=6)
    
    daily_records = DownloadRecord.objects.filter(
        timestamp__date__gte=last_week
    ).annotate(
        date=TruncDate('timestamp')
    ).values(
        'date'
    ).annotate(
        downloads=Count('id'),
        size=Sum('size')
    ).order_by('date')

    # 將結果轉換為字典以便快速查找
    stats_map = {item['date']: item for item in daily_records}
    
    # 建立包含過去 7 天的完整列表
    daily_stats = []
    for i in range(7):
        date = last_week + timedelta(days=i)
        stats_for_day = stats_map.get(date)
        if stats_for_day:
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'downloads': stats_for_day['downloads'],
                'size': round((stats_for_day['size'] or 0) / (1024 * 1024), 2) # MB
            })
        else:
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                    'downloads': 0,
                'size': 0
            })
    
    # 獲取使用者列表，包含所有平台的使用者
    users = User.objects.prefetch_related('siteuser', 'moodle_accounts').all()
    user_list = []
    
    for user in users:
        if hasattr(user, 'siteuser'):
            user_total_downloads = user.siteuser.total_downloads
            total_size_mb = user.siteuser.get_total_download_size_mb()
            last_download = user.siteuser.last_download_time.strftime('%Y-%m-%d %H:%M:%S') if user.siteuser.last_download_time else None
        else:
            user_total_downloads = 0
            total_size_mb = 0
            last_download = None

        moodle_accounts = list(user.moodle_accounts.values_list('student_id', flat=True))
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'total_downloads': user_total_downloads,
            'total_size': total_size_mb,
            'last_download': last_download,
            'moodle_accounts': moodle_accounts,
            'moodle_accounts_count': len(moodle_accounts)
        }
        user_list.append(user_data)
    
    # 計算所有平台的使用者總數
    total_moodle_accounts = MoodleAccount.objects.values('student_id').distinct().count()
    
    return JsonResponse({
        'total_users': total_users,
        'total_moodle_accounts': total_moodle_accounts,
        'total_downloads': total_downloads,
        'total_size': round(total_size / (1024 * 1024), 2),  # 轉換為 MB
        'daily_stats': daily_stats,
        'users': user_list
    })