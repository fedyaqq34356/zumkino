FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

# Установить только свои зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установить браузеры Playwright (они есть в образе, только подтянуть бинарники)
RUN playwright install --with-deps

# Скопировать весь код
COPY . .

# Запуск
CMD ["python", "main.py"]
