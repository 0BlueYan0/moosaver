from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
import json
import os
import requests
from django.conf import settings
from urllib.parse import urlparse
from .moodle_dl_utils import start_moodle_download, get_download_progress
from django.contrib.auth.models import User
from users.forms import UserEditForm
from users.models import SiteUser, MoodleAccount
from django.db import transaction
import shutil
import mimetypes
import zipfile
import io
import datetime
from .models import DownloadRecord

def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'home_page.html', {
            'username': request.user.username,
            'is_admin': request.user.is_staff or request.user.is_superuser
        })
    else:
        return redirect('login')

def api_user_permissions(request):
    """提供使用者權限資訊的API端點"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '未登入'}, status=401)
    
    return JsonResponse({
        'username': request.user.username,
        'is_admin': request.user.is_staff or request.user.is_superuser,
        'is_superuser': request.user.is_superuser
    })

def download_view(request):
    if request.user.is_authenticated:
        return render(request, 'download_page.html', {
            'username': request.user.username,
            'is_admin': request.user.is_staff or request.user.is_superuser
        })
    else:
        return redirect('login')
    
def api_download(request):
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type', '')
        
        # 處理JSON請求 (來自前端的AJAX請求)
        if 'application/json' in content_type:
            try:
                # 解析JSON數據
                data = json.loads(request.body)
                
                # 提取數據
                stuid = data.get('student_id', '')
                password = data.get('password', '')
                moodle_url = data.get('moodle_url', '')

                parsed_url = urlparse(moodle_url)
                moodle_domain = parsed_url.netloc
                moodle_path = parsed_url.path

                # 執行類似 curl 的請求
                token_url = f"https://{moodle_domain}/login/token.php"
                params = {
                    'username': stuid,
                    'password': password,
                    'service': 'moodle_mobile_app'
                }
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                }
                response = requests.get(token_url, params=params, headers=headers, verify=False)
                token_result = response.json()
                # 檢查是否有 error
                if 'error' in token_result:
                    return JsonResponse({'status': 'error', 'message': token_result.get('error')}, status=400)
                token = token_result.get('token', '')
                privatetoken = token_result.get('privatetoken', '')

                # 記錄 Moodle 帳號
                MoodleAccount.objects.get_or_create(user=request.user, student_id=stuid)

                # 取得使用者專屬資料夾路徑（加上 stuid 子資料夾）
                user_folder = os.path.join(settings.MEDIA_ROOT, request.user.username, stuid)
                os.makedirs(user_folder, exist_ok=True)

                # 建立 config.json 檔案
                config_path = os.path.join(user_folder, 'config.json')
                config_data = {
                    'token': token,
                    'privatetoken': privatetoken,
                    'moodle_domain': moodle_domain,
                    'moodle_path': moodle_path,
                    "download_submissions": True,
                    "download_descriptions": True,
                    "download_links_in_descriptions": False,
                    "download_databases": False,
                    "download_forums": True,
                    "download_quizzes": True,
                    "download_lessons": False,
                    "download_workshops": True,
                    "download_books": False,
                    "download_calendars": False,
                    "download_linked_files": False,
                    "download_also_with_cookie": False
                }
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4)
                    
                # 啟動 Moodle 下載
                start_moodle_download(request.user, stuid)
                return JsonResponse({"status": "started"})
            except json.JSONDecodeError:
                return JsonResponse({'error': '無效的JSON格式'}, status=400)

def api_download_progress(request, stuid):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '未登入', 'percent': 0})
    progress = get_download_progress(request.user, stuid)
    return JsonResponse(progress)

def profile_view(request):
    if request.user.is_authenticated:
        site_user = User.objects.get(username=request.user.username)
        return render(request, 'profile.html', {
            'site_user': site_user,
            'username': request.user.username,
            'is_admin': request.user.is_staff or request.user.is_superuser
        })
    else:
        return redirect('login')  # 如果未登入，重定向到登入頁面

def edit_profile_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    try:
        site_user = SiteUser.objects.get(user=user)
    except SiteUser.DoesNotExist:
        site_user = None

    if request.method == 'POST':
        old_username = user.username  # 取得舊的使用者名稱
        form = UserEditForm(request.POST, instance=user)
        display_name = request.POST.get('display_name', '')
        if form.is_valid():
            new_username = form.cleaned_data.get('username')
            new_email = form.cleaned_data.get('email')
            # 檢查新使用者名稱是否已存在（且不是自己）
            username_exists = User.objects.filter(username=new_username).exclude(pk=user.pk).exists()
            email_exists = User.objects.filter(email=new_email).exclude(pk=user.pk).exists()
            if username_exists:
                form.add_error('username', '此使用者名稱已被使用，請選擇其他名稱。')
            if email_exists:
                form.add_error('email', '此信箱已被使用，請選擇其他信箱。')
            if username_exists or email_exists:
                # 有重複就不繼續
                pass
            else:
                with transaction.atomic():
                    user = form.save(commit=False)
                    password = form.cleaned_data.get('password')
                    username_changed = old_username != new_username
                    if password:
                        user.set_password(password)
                    user.save()
                    # 同步更新 display_name
                    if site_user:
                        site_user.display_name = display_name
                        site_user.save()
                    # 檢查使用者名稱是否有變更
                    if username_changed:
                        old_folder = os.path.join(settings.MEDIA_ROOT, old_username)
                        new_folder = os.path.join(settings.MEDIA_ROOT, new_username)
                        if os.path.exists(old_folder):
                            # 若新資料夾已存在，合併內容
                            if os.path.exists(new_folder):
                                for item in os.listdir(old_folder):
                                    s = os.path.join(old_folder, item)
                                    d = os.path.join(new_folder, item)
                                    if os.path.isdir(s):
                                        shutil.move(s, d)
                                    else:
                                        shutil.move(s, d)
                                os.rmdir(old_folder)
                            else:
                                shutil.move(old_folder, new_folder)
                    # 重新登入，避免修改帳號密碼後被登出
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, user)
                return redirect('profile')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'edit_profile.html', {
        'form': form,
        'site_user': site_user
    })

def format_file_size(size_bytes):
    """格式化檔案大小"""
    if size_bytes == 0:
        return "0 B"
    elif size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def build_tree(path, rel_path='', is_root=False):
    """建構檔案樹，包含最後修改時間和檔案大小"""
    if is_root:
        # 如果是根目錄，使用特定的名稱
        node = {'name': f'{os.path.basename(path)} 的檔案'}
    else:
        # 替換特殊字符，避免顯示問題
        node_name = os.path.basename(path)
        node_name = node_name.replace('⧸', '/')  # 替換大斜線為普通斜線
        node_name = node_name.replace('⧹', '\\')
        node = {'name': node_name}
    
    # 獲取最後修改時間
    try:
        mod_time = os.path.getmtime(path)
        mod_datetime = datetime.datetime.fromtimestamp(mod_time)
        formatted_time = mod_datetime.strftime('%Y-%m-%d %H:%M')
    except OSError:
        formatted_time = "未知"
    
    node['modified_time'] = formatted_time
    
    if os.path.isdir(path):
        node['type'] = 'folder'
        node['children'] = []
        # 為資料夾也添加 path 屬性
        if not is_root:
            node['path'] = rel_path.replace('\\', '/')
        
        # 定義要隱藏的檔案列表
        hidden_files = {'config.json', 'moodle_state.db', 'progress.json'}
        
        try:
            items = os.listdir(path)
        except PermissionError:
            items = []
        
        for x in sorted(items):
            # 過濾隱藏檔案（以.開頭的檔案）和特定的系統檔案
            if not x.startswith('.') and x not in hidden_files:
                child_path = os.path.join(path, x)
                # 修正相對路徑計算邏輯
                if is_root:
                    child_rel_path = x
                else:
                    child_rel_path = os.path.join(rel_path, x) if rel_path else x
                
                try:
                    child_node = build_tree(child_path, child_rel_path, is_root=False)
                    node['children'].append(child_node)
                except (OSError, PermissionError):
                    # 跳過無法訪問的檔案/資料夾
                    continue
    else:
        node['type'] = 'file'
        # 修正檔案路徑計算
        node['path'] = rel_path.replace('\\', '/')
        
        # 獲取檔案大小
        try:
            file_size = os.path.getsize(path)
            node['size'] = format_file_size(file_size)
        except OSError:
            node['size'] = "未知"
    
    return node

def file_manage_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_folder = os.path.join(settings.MEDIA_ROOT, request.user.username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    tree = build_tree(user_folder, "", is_root=True)
    return render(request, 'file_manage.html', {
        'username': request.user.username,
        'is_admin': request.user.is_staff or request.user.is_superuser,
        'file_tree_json': json.dumps([tree], ensure_ascii=False)
    })

def download_file_view(request):
    """處理單一檔案的下載"""
    if not request.user.is_authenticated:
        raise Http404
    
    file_path = request.GET.get('path', '')
    base_path = os.path.join(settings.MEDIA_ROOT, request.user.username)
    full_path = os.path.join(base_path, file_path)

    # 安全性檢查，確保檔案路徑在使用者目錄內
    if not os.path.abspath(full_path).startswith(os.path.abspath(base_path)):
        raise Http404

    if os.path.exists(full_path) and os.path.isfile(full_path):
        # 更新使用者下載統計
        site_user, created = SiteUser.objects.get_or_create(user=request.user)
        file_size = os.path.getsize(full_path)
        site_user.total_downloads += 1
        site_user.total_download_size += file_size
        site_user.last_download_time = datetime.datetime.now()
        site_user.save()

        # 建立下載記錄
        DownloadRecord.objects.create(
            user=request.user,
            file_path=file_path,
            size=file_size
        )
        
        return FileResponse(open(full_path, 'rb'), as_attachment=True)
    else:
        raise Http404

def download_all_user_files_view(request):
    """下載指定學號的所有檔案"""
    if not request.user.is_authenticated:
        raise Http404
    
    stuid = request.GET.get('stuid')
    if not stuid:
        raise Http404
    
    # 建立目標資料夾路徑
    user_folder = os.path.join(settings.MEDIA_ROOT, request.user.username, stuid)
    
    # 安全性檢查
    base_path = os.path.join(settings.MEDIA_ROOT, request.user.username)
    if not os.path.abspath(user_folder).startswith(os.path.abspath(base_path)):
        raise Http404
    
    if not os.path.isdir(user_folder):
        raise Http404
    
    # 計算資料夾總大小
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(user_folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    # 更新使用者下載統計
    site_user, created = SiteUser.objects.get_or_create(user=request.user)
    site_user.total_downloads += 1  # 整個資料夾算一次下載
    site_user.total_download_size += total_size
    site_user.last_download_time = datetime.datetime.now()
    site_user.save()

    # 建立下載記錄
    DownloadRecord.objects.create(
        user=request.user,
        file_path=f"All files for {stuid}",
        size=total_size
    )

    # 建立 ZIP 檔案
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(user_folder):
            for file in files:
                file_path = os.path.join(root, file)
                # 建立相對路徑，避免在 ZIP 中包含完整路徑
                rel_path = os.path.relpath(file_path, user_folder)
                zf.write(file_path, rel_path)
    
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{stuid}_files.zip"'
    return response

def download_folder_view(request):
    """處理資料夾下載（壓縮為ZIP）"""
    if not request.user.is_authenticated:
        raise Http404
    
    folder_path = request.GET.get('path', '')
    base_path = os.path.join(settings.MEDIA_ROOT, request.user.username)
    full_path = os.path.join(base_path, folder_path)
    
    # 安全性檢查
    if not os.path.abspath(full_path).startswith(os.path.abspath(base_path)):
        raise Http404
    
    if not os.path.isdir(full_path):
        raise Http404

    # 計算資料夾總大小
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(full_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    # 更新使用者下載統計
    site_user, created = SiteUser.objects.get_or_create(user=request.user)
    site_user.total_downloads += 1
    site_user.total_download_size += total_size
    site_user.last_download_time = datetime.datetime.now()
    site_user.save()
    
    # 建立下載記錄
    DownloadRecord.objects.create(
        user=request.user,
        file_path=folder_path,
        size=total_size
    )

    # 建立 ZIP 檔案
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(full_path):
            # 建立 ZIP 內的根目錄
            zip_root = os.path.basename(full_path)
            for file in files:
                file_path = os.path.join(root, file)
                # 建立 ZIP 內的相對路徑
                rel_path = os.path.relpath(file_path, os.path.dirname(full_path))
                zf.write(file_path, rel_path)
    
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    # 使用資料夾名稱命名 ZIP 檔案
    folder_name = os.path.basename(folder_path)
    response['Content-Disposition'] = f'attachment; filename="{folder_name}.zip"'
    return response
