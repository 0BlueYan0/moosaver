# MooSaver

一個基於 Django 的 Moodle 資源下載工具，幫助用戶輕鬆下載和管理 Moodle 平台上的課程資源。

## 功能特色

- 🚀 **快速下載**：一鍵批量下載所有課程資源
- 📁 **智能整理**：自動按課程分類，檔案管理更清晰
- 🔍 **檔案搜尋**：快速搜尋和定位檔案
- 👥 **多用戶支援**：支援多個使用者獨立管理資源
- 🎨 **響應式設計**：支援桌面和行動裝置

## 技術架構

- **後端**：Django 5.x
- **前端**：Vue.js

## 安裝與部署

### 使用 Docker（推薦）

#### 快速啟動

```bash
docker run -p 8000:8000 -v /path/to/your/downloads:/app/users_data -e DATABASE_PATH=/app/users_data/db.sqlite3 0blueyan0/moosaver:latest
```

#### 詳細設定

1. **建立資料目錄**
```bash
mkdir downloads
```

2. **執行容器並掛載資料卷**
```bash
docker run -d \
  --name moosaver \
  -p 8000:8000 \
  -v /path/to/your/downloads:/app/users_data \
  -e DATABASE_PATH=/app/users_data/db.sqlite3 \
  0blueyan0/moosaver:latest
```

3. **開啟瀏覽器訪問**
```
http://localhost:8000
```

#### 環境變數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| `-p 8000:8000` | 埠號對應 (主機:容器) | 可改為其他埠號如 `-p 3000:8000` |
| `-v /path/to/your/downloads:/app/users_data` | 資料卷掛載 | 將下載檔案儲存到主機 |
| `-e DATABASE_PATH=/app/users_data/db.sqlite3` | database路徑 | 不知道怎麼改的請保持原樣 |

#### Docker Compose（推薦）

- Image 僅限 x86 平台 
- 建立 `docker-compose.yml` 檔案：

```yaml
services:
  moosaver:
    image: 0blueyan0/moosaver:latest
    ports:
      - "8000:8000"
    volumes:
      - /path/to/your/downloads:/app/users_data
    environment:
      - DATABASE_PATH=/app/users_data/db.sqlite3
    restart: unless-stopped
```

執行：
```bash
docker-compose up -d
```

### 本地開發

1. 安裝依賴
- 可以使用 python 虛擬環境
```bash
pip install -r requirements.txt
```

2. 執行資料庫遷移
- 會建立 db.sqlite3 在 Repo 根目錄
```bash
python manage.py migrate
```

3. 建立超級使用者
```bash
python manage.py createsuperuser
```

4. 啟動開發伺服器
```bash
python manage.py runserver
```

## 使用方法

1. 註冊帳號或使用管理員帳號登入
2. 在下載頁面輸入您的 Moodle 學號和密碼
3. 選擇 Moodle 平台網址
4. 點擊「開始下載」
5. 在檔案管理頁面查看和管理下載的資源

## 專案結構

```
moosaver/
├── download/           # 主要下載功能應用
├── users/             # 使用者管理應用
├── moosaver/          # Django 專案設定
├── templates/         # 前端模板
├── requirements.txt   # Python 依賴
├── Dockerfile        # Docker 配置
└── manage.py         # Django 管理命令
└── db.sqlite3        # Django Data Model DB (Generated)
```

## 開源專案致謝

本專案使用了以下開源專案和函式庫：

### 後端框架
- [Django](https://github.com/django/django) - BSD-3-Clause License
  - Python Web 框架

### 前端框架和元件
- [Vue.js 3](https://github.com/vuejs/core) - MIT License
  - 漸進式 JavaScript 框架
- [Font Awesome](https://github.com/FortAwesome/Font-Awesome) - Font Awesome Free License
  - 圖示字體庫

### 字體
- [Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC) - Open Font License
  - Google Fonts 繁體中文字體

### Moodle 下載核心
- [Moodle-DL](https://github.com/C0D3D3V/Moodle-DL) - GPL-3.0 license

## 授權條款

本專案採用 [GNU General Public License v3.0](LICENSE) 授權。

## 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案。

## 聯繫方式

如有問題或建議，請建立 Issue 或聯繫專案維護者。
