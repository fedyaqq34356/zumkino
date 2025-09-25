FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

# Скопировать зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установить браузеры Playwright
RUN playwright install --with-deps

# Скопировать весь код
COPY . .

# Запуск
CMD ["python", "main.py"]
