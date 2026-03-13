# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости системы (нужны для сборки некоторых пакетов)
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Собираем статику (если нужно)
# RUN python manage.py collectstatic --noinput

# Запускаем приложение через Daphne (ASGI сервер для WebSockets)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "CodeInterview.asgi:application"]