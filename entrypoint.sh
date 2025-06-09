#!/bin/bash

# 執行資料庫遷移
python manage.py migrate

# 創建超級用戶（如果不存在）
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# 啟動 Django 開發服務器
python manage.py runserver 0.0.0.0:8000