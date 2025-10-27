#!/usr/bin/env python3
"""
Скрипт для деплоя бота с использованием ngrok
"""

import os
import subprocess
import time
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_ngrok_installed():
    """Проверяем, установлен ли ngrok."""
    try:
        result = subprocess.run(['ngrok', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ngrok установлен: {result.stdout.strip()}")
            return True
        else:
            print("❌ ngrok не найден")
            return False
    except FileNotFoundError:
        print("❌ ngrok не установлен")
        return False

def install_ngrok():
    """Устанавливаем ngrok."""
    print("📥 Устанавливаем ngrok...")
    
    # Для macOS
    if os.system("which brew") == 0:
        os.system("brew install ngrok/ngrok/ngrok")
        print("✅ ngrok установлен через Homebrew")
        return True
    else:
        print("❌ Homebrew не найден. Установите ngrok вручную:")
        print("1. Перейдите на https://ngrok.com/download")
        print("2. Скачайте ngrok для macOS")
        print("3. Распакуйте и добавьте в PATH")
        return False

def setup_ngrok_auth():
    """Настройка аутентификации ngrok."""
    auth_token = input("Введите ваш ngrok auth token (получите на https://dashboard.ngrok.com/get-started/your-authtoken): ")
    if auth_token:
        os.system(f"ngrok config add-authtoken {auth_token}")
        print("✅ ngrok аутентификация настроена")
        return True
    else:
        print("❌ Токен не введен")
        return False

def start_ngrok(port=8000):
    """Запускаем ngrok."""
    print(f"🚀 Запускаем ngrok на порту {port}...")
    
    # Запускаем ngrok в фоне
    process = subprocess.Popen(['ngrok', 'http', str(port)], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
    
    # Ждем запуска
    time.sleep(3)
    
    # Получаем URL
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                public_url = tunnels[0]['public_url']
                print(f"✅ ngrok запущен: {public_url}")
                return public_url, process
            else:
                print("❌ Не удалось получить URL туннеля")
                return None, process
        else:
            print("❌ Не удалось подключиться к ngrok API")
            return None, process
    except Exception as e:
        print(f"❌ Ошибка получения URL: {e}")
        return None, process

def setup_webhook(bot_token, webhook_url):
    """Настройка webhook для бота."""
    webhook_endpoint = f"{webhook_url}/webhook"
    set_webhook_url = f"https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_endpoint}"
    
    print(f"🔗 Настраиваем webhook: {webhook_endpoint}")
    
    try:
        response = requests.get(set_webhook_url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ Webhook настроен успешно")
                return True
            else:
                print(f"❌ Ошибка настройки webhook: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка настройки webhook: {e}")
        return False

def main():
    """Главная функция деплоя."""
    print("🚀 Деплой бота с ngrok")
    print("=" * 40)
    
    # Проверяем переменные окружения
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        return
    
    print(f"✅ Bot token найден: {bot_token[:10]}...")
    
    # Проверяем ngrok
    if not check_ngrok_installed():
        if not install_ngrok():
            return
        if not check_ngrok_installed():
            return
    
    # Настраиваем аутентификацию
    if not setup_ngrok_auth():
        return
    
    # Запускаем ngrok
    public_url, ngrok_process = start_ngrok()
    if not public_url:
        print("❌ Не удалось запустить ngrok")
        return
    
    # Настраиваем webhook
    if not setup_webhook(bot_token, public_url):
        print("❌ Не удалось настроить webhook")
        ngrok_process.terminate()
        return
    
    print("\n🎉 Деплой завершен!")
    print(f"📱 Ваш бот доступен по адресу: {public_url}")
    print("📊 Мониторинг ngrok: http://localhost:4040")
    print("\n⚠️  Важно:")
    print("- Держите этот терминал открытым")
    print("- ngrok URL изменится при перезапуске")
    print("- Для продакшена используйте VPS или облачные сервисы")
    
    try:
        print("\n🔄 Нажмите Ctrl+C для остановки...")
        ngrok_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Останавливаем ngrok...")
        ngrok_process.terminate()
        print("✅ Деплой остановлен")

if __name__ == '__main__':
    main()
