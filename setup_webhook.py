#!/usr/bin/env python3
"""
Скрипт для получения ngrok URL и настройки webhook
"""

import subprocess
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_ngrok_url():
    """Получаем URL ngrok."""
    try:
        # Запускаем ngrok в фоне
        process = subprocess.Popen(['ngrok', 'http', '8000'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Ждем запуска
        time.sleep(3)
        
        # Получаем URL
        response = requests.get('http://localhost:4040/api/tunnels')
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                public_url = tunnels[0]['public_url']
                print(f"✅ ngrok URL: {public_url}")
                return public_url, process
            else:
                print("❌ Не удалось получить URL туннеля")
                return None, process
        else:
            print("❌ Не удалось подключиться к ngrok API")
            return None, process
    except Exception as e:
        print(f"❌ Ошибка получения URL: {e}")
        return None, None

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
    """Главная функция."""
    print("🚀 Настройка webhook для бота")
    print("=" * 40)
    
    # Проверяем переменные окружения
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        return
    
    print(f"✅ Bot token найден: {bot_token[:10]}...")
    
    # Получаем ngrok URL
    public_url, ngrok_process = get_ngrok_url()
    if not public_url:
        print("❌ Не удалось получить ngrok URL")
        return
    
    # Настраиваем webhook
    if not setup_webhook(bot_token, public_url):
        print("❌ Не удалось настроить webhook")
        if ngrok_process:
            ngrok_process.terminate()
        return
    
    print("\n🎉 Webhook настроен!")
    print(f"📱 Ваш бот доступен по адресу: {public_url}")
    print("📊 Мониторинг ngrok: http://localhost:4040")
    print("\n⚠️  Важно:")
    print("- Держите этот терминал открытым")
    print("- ngrok URL изменится при перезапуске")
    
    try:
        print("\n🔄 Нажмите Ctrl+C для остановки...")
        if ngrok_process:
            ngrok_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Останавливаем ngrok...")
        if ngrok_process:
            ngrok_process.terminate()
        print("✅ ngrok остановлен")

if __name__ == '__main__':
    main()
