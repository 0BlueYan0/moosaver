from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
import json
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout

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
                username = data.get('username', '')
                password = data.get('password', '')
                remember_me = data.get('remember_me', False)
                
                # 驗證用戶
                user = authenticate(request, username=username, password=password)
                
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
                    return JsonResponse({'error': '用戶名或密碼不正確'}, status=400)
                    
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
                user_dir = os.path.join('users', user.username)
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

@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return JsonResponse({'message': '已成功登出'})