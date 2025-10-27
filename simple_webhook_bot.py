#!/usr/bin/env python3
"""
Простая webhook версия бота для тестирования
"""

import os
import logging
from flask import Flask, request
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик webhook."""
    try:
        # Получаем данные от Telegram
        update_data = request.get_json()
        
        if update_data:
            logger.info(f"Получено обновление: {update_data}")
            
            # Простая обработка команды /start
            if 'message' in update_data and 'text' in update_data['message']:
                text = update_data['message']['text']
                chat_id = update_data['message']['chat']['id']
                
                if text == '/start':
                    # Отправляем приветствие
                    send_message(chat_id, "Привет! Я webhook бот! 🚀")
                elif text == '/news':
                    send_message(chat_id, "📰 Новости работают через webhook!")
                else:
                    send_message(chat_id, f"Получено: {text}")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return "Error", 500

def send_message(chat_id, text):
    """Отправка сообщения пользователю."""
    try:
        import requests
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': text
        }
        
        response = requests.post(url, json=data)
        logger.info(f"Отправлено сообщение: {text}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса."""
    return {
        "status": "healthy",
        "message": "Webhook bot is running!",
        "bot_token_configured": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
        "news_api_configured": bool(os.getenv('NEWS_API_KEY'))
    }

@app.route('/', methods=['GET'])
def index():
    """Главная страница."""
    return """
    <h1>News Bot Webhook</h1>
    <p>Бот работает! 🚀</p>
    <ul>
        <li><a href="/health">Health Check</a></li>
    </ul>
    """

if __name__ == '__main__':
    logger.info("🚀 Запуск простого webhook бота...")
    logger.info("🌐 Webhook endpoint: /webhook")
    logger.info("📊 Health check: /health")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
