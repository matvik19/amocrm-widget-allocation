FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /fastapi_app

# Копируем файл зависимостей в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/ docker/

# Дает разрешение для запуска файла
RUN chmod a+x docker/*.sh

# Копируем все файлы проекта в контейнер
COPY . .

# Указываем команду запуска
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
