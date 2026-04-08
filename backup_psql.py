#!/usr/bin/env python3

import os
import shutil
import subprocess
import datetime
import glob
import requests
from pathlib import Path
from dotenv import load_dotenv

# --- Настройки ---
PROJECT_DIR = "/home/Kinremtus/SiteCheck"
BACKUP_DIR = "/home/Kinremtus/backups"
CONTAINER_NAME = "yamtrack-db"
RETENTION_DAYS = 7
MIN_FREE_SPACE_GB = 1

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

def send_telegram_notification(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram credentials missing in .env")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status() # Проверка, что запрос прошел успешно
    except Exception as e:
        print(f"Failed to send Telegram: {e}")

def check_free_space(path):
    stat = shutil.disk_usage(path)
    return stat.free / (1024**3)

def run_backup():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"--- Backup session started: {now_str} ---")

    # 1. Проверка места
    free_gb = check_free_space(BACKUP_DIR)
    print(f"Free disk space: {free_gb:.2f} GB")

    if free_gb < MIN_FREE_SPACE_GB:
        error_msg = f"⚠️ <b>ALARM: Low Disk Space!</b>\nFree space: <code>{free_gb:.2f} GB</code>\nBackup aborted!"
        print(f"ABORTED: {error_msg}")
        send_telegram_notification(error_msg)
        return

    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"db_{date_str}.sql.gz"
    file_path = os.path.join(BACKUP_DIR, file_name)
    
    db_user = os.getenv("POSTGRES_USER")
    db_name = os.getenv("POSTGRES_DB")
    db_password = os.getenv("POSTGRES_PASSWORD")

    cmd = [
    "docker", "exec",
    "-e", f"PGPASSWORD={db_password}",
    CONTAINER_NAME,
    "pg_dump", "-U", db_user, db_name
    ]
    with open(file_path, "wb") as f:
        dump = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)
        f.write(gzip.compress(dump.stdout))
    
    try:
        print(f"Running dump for database: {db_name}...")
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        
        # Считаем размер созданного файла
        file_size_mb = os.path.getsize(file_path) / (1024**2)
        
        success_msg = f"✅ <b>Backup Success</b>\nFile: <code>{file_name}</code>\nSize: <code>{file_size_mb:.2f} MB</code>"
        print(f"SUCCESS: {file_name} ({file_size_mb:.2f} MB)")
                
        send_telegram_notification(success_msg)
        
        rotate_backups()
        
    except subprocess.CalledProcessError as e:
        err_out = e.stderr.decode()[:100]
        error_msg = f"❌ <b>Backup Failed!</b>\nError: <code>{err_out}</code>"
        print(f"ERROR: {err_out}")
        send_telegram_notification(error_msg)

    print(f"--- Session finished ---\n")

def rotate_backups():
    now = datetime.datetime.now()
    files = glob.glob(os.path.join(BACKUP_DIR, "*.sql.gz"))
    for file in files:
        file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file))
        if (now - file_mtime).days > RETENTION_DAYS:
            print(f"Removing old backup: {os.path.basename(file)}")
            os.remove(file)

if __name__ == "__main__":
    run_backup()
