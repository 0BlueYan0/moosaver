import os
import json
import asyncio
import sys
from django.conf import settings
from moodle_dl.config import ConfigHelper
from moodle_dl.types import MoodleDlOpts
from moodle_dl.moodle.moodle_service import MoodleService
from moodle_dl.database import StateRecorder
from moodle_dl.downloader.download_service import DownloadService
from moodle_dl.types import MoodleDlOpts
from users.models import SiteUser
from download.models import DownloadRecord
from django.utils import timezone
from asgiref.sync import sync_to_async

def get_user_path(user, stuid):
    # 取得每位用戶的 moodle_dl 專屬目錄（在 MEDIA_ROOT 下）
    return os.path.join(settings.MEDIA_ROOT, user.username, stuid)

def strip_extra_opts(config_dict):
    allowed_keys = set(MoodleDlOpts.__dataclass_fields__.keys())
    return {k: v for k, v in config_dict.items() if k in allowed_keys}

async def update_user_download_stats(user, stuid, files_downloaded, bytes_downloaded):
    # 只有在實際下載了檔案時才更新統計數據
    if files_downloaded > 0:
        # 使用 get_or_create 確保 SiteUser 存在，避免錯誤
        site_user, _ = await sync_to_async(SiteUser.objects.get_or_create)(user=user)
        
        # 將整個 Moodle 同步操作視為一次下載
        site_user.total_downloads += 1
        site_user.total_download_size += bytes_downloaded
        site_user.last_download_time = timezone.now()
        await sync_to_async(site_user.save)()

        # 為這次同步操作建立一個統一的 DownloadRecord，使統計一致
        await sync_to_async(DownloadRecord.objects.create)(
            user=user,
            size=bytes_downloaded,
            file_path=f"Moodle Sync: {stuid}"  # 記錄是哪個學號的同步
        )

def start_moodle_download(user, stuid):
    user_path = get_user_path(user, stuid)
    os.makedirs(user_path, exist_ok=True)
    opts = MoodleDlOpts(
        path=user_path,
        init=False,
        config=None,
        new_token=None,
        change_notification_mail=None,
        change_notification_telegram=None,
        change_notification_discord=None,
        change_notification_ntfy=None,
        change_notification_xmpp=None,
        manage_database=False,
        delete_old_files=False,
        log_responses=False,
        add_all_visible_courses=False,
        sso=False,
        username=None,
        password=None,
        token=None,
        max_parallel_api_calls=5,
        max_parallel_downloads=3,
        max_parallel_yt_dlp=1,
        download_chunk_size=1048576,
        ignore_ytdl_errors=False,
        without_downloading_files=False,
        max_path_length_workaround=False,
        allow_insecure_ssl=True,
        use_all_ciphers=True,
        skip_cert_verify=True,
        verbose=False,
        quiet=False,
        log_to_file=False,
        log_file_path=None
    )
    config = ConfigHelper(opts)
    config.load()

    moodle = MoodleService(config, opts)
    database = StateRecorder(config, opts)
    progress_file = os.path.join(user_path, "progress.json")

    # 每次新下載任務都覆寫進度檔
    with open(progress_file, "w") as f:
        json.dump({"status": "start", "message": "開始下載", "percent": 0}, f, ensure_ascii=False)

    async def report_progress_task(download_service):
        """定期將進度寫入 progress.json"""
        while not getattr(download_service, "all_done", False):
            status = download_service.status
            percent = int(status.bytes_downloaded * 100 / status.bytes_to_download) if status.bytes_to_download else 0
            progress = {
                "status": "downloading",
                "message": f"已下載 {status.files_downloaded}/{status.files_to_download} 檔案",
                "percent": percent
            }
            with open(progress_file, "w") as f:
                json.dump(progress, f, ensure_ascii=False)
            await asyncio.sleep(1)  # 每1秒更新一次

    async def do_download():
        changed_courses = await moodle.fetch_state(database)

        # 如果沒有任何變動，直接回報已同步
        if not changed_courses:
            with open(progress_file, "w") as f:
                json.dump({"status": "synced", "message": "所有課程都已是最新狀態。", "percent": 100}, f, ensure_ascii=False)
            return

        download_service = DownloadService(
            changed_courses, config, opts, database
        )
        # 啟動進度同步背景任務
        progress_task = asyncio.create_task(report_progress_task(download_service))
        
        try:
            await download_service.real_run()
        finally:
            # 無論下載成功或失敗，都確保進度回報任務被取消
            # 這樣可以避免孤立的任務在背景繼續運行
            download_service.all_done = True # 溫和地通知任務結束
            progress_task.cancel() # 強制取消任務
            try:
                await progress_task # 等待任務確實被取消
            except asyncio.CancelledError:
                pass # 取消是預期行為

        # 更新下載統計
        status = download_service.status
        await update_user_download_stats(user, stuid, status.files_downloaded, status.bytes_downloaded)

        # 最後寫入完成
        with open(progress_file, "w") as f:
            json.dump({"status": "done", "message": "下載完成！", "percent": 100}, f)

    # Windows 下修正 event loop
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(do_download())

def get_download_progress(user, stuid):
    user_path = get_user_path(user, stuid)
    progress_file = os.path.join(user_path, "progress.json")
    if not os.path.exists(progress_file):
        return {"status": "not_started", "message": "尚未啟動下載", "percent": 0}
    with open(progress_file, "r") as f:
        return json.load(f)