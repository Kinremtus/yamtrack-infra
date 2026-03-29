# 🚀 Self-Hosted Media Infrastructure (Yamtrack)
<img width="1871" height="870" alt="image" src="https://github.com/user-attachments/assets/1d9181c0-7042-4099-b6fb-18c436ae501f" />

![CI/CD Status](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![IaC](https://img.shields.io/badge/IaC-Ansible-EE0000?logo=ansible)
![Monitoring](https://img.shields.io/badge/Monitoring-Prometheus%20%2B%20Grafana-orange)

Инфраструктурный проект для развертывания системы трекинга медиа-контента (Yamtrack) на одном VPS.
Реализован принцип **Infrastructure as Code**, настроен **CI/CD пайплайн**, **мониторинг** и **автоматические бэкапы**.

---

## 🏗 Архитектура и Сеть

Главная особенность — разделение трафика на уровне портов для обхода блокировок и обеспечения безопасности веб-сервисов.

   **Порт 8443 (HTTPS):** Nginx (Reverse Proxy). Обслуживает веб-интерфейсы (Yamtrack, Grafana). (Порт 443 занят другим сервисом, поэтому Nginx слушает на 8443)
   * SSL-терминация через Cloudflare Origin CA.  
   * Проксирование в Docker-сеть.

### 🛠 Технологический стек

| Категория | Инструменты | Описание |
| :--- | :--- | :--- |
| **App** | Django, Gunicorn, Python | Бэкенд приложения Yamtrack(https://github.com/FuzzyGrim/Yamtrack) |
| **DB & Cache** | PostgreSQL 17, Redis 8 | База данных и брокер сообщений для фоновых задач (Celery) |
| **Proxy** | Nginx | Реверс-прокси, SSL, маршрутизация по поддоменам |
| **Observability(Метрики)** | Prometheus, Grafana | Сбор метрик хоста (Node Exporter) и контейнеров (cAdvisor) |\
| **Observability (Логи)** | Loki, Promtail | Централизованный сбор логов через интеграцию с Docker API (`docker.sock`) |
| **IaC** | Ansible | Настройка "голого" сервера, установка Docker, прав доступа |
| **CI/CD** | GitHub Actions | Автоматический деплой при пуше в `main` |
| **Backup** | Bash + Cron | Ежедневные дампы БД с ротацией и отправкой отчетов |

---

## 📊 Мониторинг (Observability)

Система полностью прозрачна для администратора. Реализован классический **PLG-стек** (Prometheus, Loki, Grafana).
### 1. Сбор метрик (Metrics)  
*   **Node Exporter:** Контроль состояния железа (CPU, RAM, Disk I/O, Network).
*   **cAdvisor:** Мониторинг потребления ресурсов каждым отдельным микросервисом в Docker.
*   **Prometheus:** Таймсерьез база данных, собирающая метрики каждые 15 секунд.  
<img width="1540" height="784" alt="image" src="https://github.com/user-attachments/assets/24db3df1-749a-419d-9fe4-4af79bd9a86d" />
<img width="1545" height="774" alt="image" src="https://github.com/user-attachments/assets/c77c63bb-2217-436d-9e24-e0d52130f6f5" />

### 2. Централизованное логирование (Logs)  
*   **Promtail** подключен напрямую к демону Docker (через `/var/run/docker.sock`). Он автоматически обнаруживает новые контейнеры (Service Discovery), парсит их логи, добавляет метаданные (имя контейнера, сервис) и отправляет в **Loki**.
*   **Loki** индексирует лейблы и позволяет выполнять быстрые запросы (LogQL) через единый интерфейс Grafana Explore.  
<img width="1816" height="873" alt="image" src="https://github.com/user-attachments/assets/f6777eb1-7d5b-45ba-9397-17df90ecc493" />

> *Дашборд состояния сервера: CPU, RAM, Network I/O и потребление ресурсов контейнерами.*

---

## 🚀 Деплой и Установка

### 1. Предварительная настройка сервера (Ansible)
Используется Ansible для приведения чистого VPS в боевое состояние (установка Docker, создание пользователей, настройка папок).

```bash
# Запуск плейбука
ansible-playbook -i hosts.ini setup_server.yml
```
### 2. Запуск сервисов (Docker Compose)
Вся инфраструктура описана в docker-compose.yml. Сервисы изолированы в сети app_net. База данных недоступна извне.
```bash
docker-compose up -d
```
### 3. Автоматический деплой (CI/CD)  
- Настроен GitHub Actions Workflow.  
- Срабатывает триггер push в ветку main.  
- Runner подключается к серверу по SSH.  
- Обновляет код (git pull).  
- Пересобирает контейнеры (docker-compose up -d --build).  
- Чистит старые образы (docker image prune).  

🛡 Безопасность (Security Measures)  
* Network Isolation: PostgreSQL и Redis не имеют проброшенных портов (ports) на хост, доступны только внутри Docker Network.  
* SSL/TLS: Строгий режим шифрования (Full Strict) через Cloudflare.  
* Firewall: Настроены правила UFW (разрешены только SSH, 443, 8443).  
* Secrets Management: Все чувствительные данные (.env) исключены из репозитория (.gitignore) и доставляются на сервер отдельно.  

Лицензия и авторство  
Этот проект является инфраструктурной оберткой для приложения Yamtrack, созданного FuzzyGrim. Оригинальный проект и данный репозиторий распространяются на условиях лицензии AGPL-3.0.
