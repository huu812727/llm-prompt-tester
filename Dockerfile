# 1. Берем официальный "легкий" образ Python
FROM python:3.10-slim

# 2. Указываем рабочую папку внутри контейнера
WORKDIR /app

# 3. Копируем список зависимостей в контейнер
COPY requirements.txt .

# 4. Устанавливаем все библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копируем все файлы проекта (код, .env, CSV) в контейнер
COPY . .

# 6. Команда, которая выполнится при запуске контейнера
CMD ["python", "judge.py"]