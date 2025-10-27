#!/usr/bin/env python3
"""
Webhook версия бота для деплоя с ngrok
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.ext import WebhookHandler
from dotenv import load_dotenv
from flask import Flask, request

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Дополнительное логирование для деплоя
def log_user_action(user_id: int, action: str, details: str = ""):
    """Логирование действий пользователей для аналитики."""
    logger.info(f"USER_ACTION: user_id={user_id}, action={action}, details={details}")

def log_error(error: Exception, context: str = ""):
    """Логирование ошибок для мониторинга."""
    logger.error(f"ERROR: {context} - {str(error)}", exc_info=True)

# Импортируем класс бота из основного файла
from bot import NewsBot

# Создаем Flask приложение
app = Flask(__name__)

# Глобальная переменная для бота
bot_instance = None
application = None

def init_bot():
    """Инициализация бота."""
    global bot_instance, application
    
    try:
        bot_instance = NewsBot()
        
        # Создаем приложение
        application = Application.builder().token(bot_instance.token).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", bot_instance.start_command))
        application.add_handler(CommandHandler("help", bot_instance.help_command))
        application.add_handler(CommandHandler("news", bot_instance.news_command))
        application.add_handler(CommandHandler("category", bot_instance.category_command))
        application.add_handler(CommandHandler("filter", bot_instance.filter_command))
        application.add_handler(CommandHandler("save", bot_instance.save_command))
        application.add_handler(CommandHandler("favorites", bot_instance.favorites_command))
        application.add_handler(CommandHandler("daily", bot_instance.daily_command))
        
        # Добавляем обработчик кнопок
        application.add_handler(CallbackQueryHandler(bot_instance.button_callback))
        
        logger.info("✅ Бот инициализирован для webhook")
        return True
        
    except Exception as e:
        log_error(e, "Ошибка инициализации бота")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик webhook."""
    try:
        if application is None:
            logger.error("Приложение не инициализировано")
            return "Error", 500
        
        # Получаем данные от Telegram
        update_data = request.get_json()
        
        if update_data:
            # Создаем объект Update
            update = Update.de_json(update_data, application.bot)
            
            # Обрабатываем обновление
            application.process_update(update)
            
            # Логируем действие пользователя
            if update.effective_user:
                log_user_action(update.effective_user.id, "webhook_update", f"update_type={update_data.get('message', {}).get('text', 'unknown')}")
        
        return "OK", 200
        
    except Exception as e:
        log_error(e, "Ошибка обработки webhook")
        return "Error", 500

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_initialized": bot_instance is not None,
        "news_api_configured": bot_instance.news_api_key is not None if bot_instance else False
    }

@app.route('/stats', methods=['GET'])
def get_stats():
    """Получение статистики бота."""
    try:
        if not bot_instance:
            return {"error": "Bot not initialized"}, 500
        
        # Загружаем данные пользователей
        users_data = bot_instance._load_data(bot_instance.users_file)
        subscribers = users_data.get('subscribers', [])
        
        # Загружаем данные новостей
        news_data = bot_instance._load_data(bot_instance.news_file)
        news_count = len(news_data.get('news', []))
        
        return {
            "subscribers_count": len(subscribers),
            "news_count": news_count,
            "last_update": news_data.get('last_update'),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log_error(e, "Ошибка получения статистики")
        return {"error": str(e)}, 500

@app.route('/', methods=['GET'])
def index():
    """Главная страница."""
    return """
    <h1>News Bot Webhook</h1>
    <p>Бот работает! 🚀</p>
    <ul>
        <li><a href="/health">Health Check</a></li>
        <li><a href="/stats">Статистика</a></li>
    </ul>
    """

def main():
    """Запуск webhook сервера."""
    print("🚀 Запуск News Bot с webhook...")
    
    # Инициализируем бота
    if not init_bot():
        print("❌ Не удалось инициализировать бота")
        return
    
    print("✅ Бот готов к работе")
    print("🌐 Webhook endpoint: /webhook")
    print("📊 Health check: /health")
    print("📈 Статистика: /stats")
    
    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=8000, debug=False)

if __name__ == '__main__':
    main()