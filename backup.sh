#!/bin/bash

# 1. Настройки

PROJECT_DIR="/home/Kinremtus/SiteCheck" 
BACKUP_DIR="/home/Kinremtus/backups"
CONTAINER_NAME="yamtrack-db"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
RETENTION_DAYS=7

# 2. Читаем переменные из .env файла

source $PROJECT_DIR/.env

# 3. Подготовка
mkdir -p $BACKUP_DIR

# 4. Бэкап с проверкой ошибок
echo "Starting backup for $POSTGRES_DB..."

if docker exec -e PGPASSWORD=$POSTGRES_PASSWORD $CONTAINER_NAME pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_DIR/db_$DATE.sql.gz; then
    echo "SUCCESS: Backup created at $BACKUP_DIR/db_$DATE.sql.gz"
    
    # 5. Ротация (удаляем старое только если новое создалось успешно)
    find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
else
    echo "ERROR: Backup failed!"
    
    exit 1
fi
