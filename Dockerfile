FROM python:3.13.3-slim

# 設定工作目錄
WORKDIR /app

# 複製專案環境與相關檔案
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

VOLUME ["/app/users_data"]

# 創建資料庫檔案
RUN touch db.sqlite3

# 執行資料庫遷移和創建超級用戶的啟動腳本
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]