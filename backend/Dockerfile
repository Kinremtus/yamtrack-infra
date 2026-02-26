# Используем легкий Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Сначала копируем зависимости (для кэширования слоев Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Команда запуска (FastAPI на порту 8000)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
