#!/usr/bin/env python3
"""
Скрипт для отправки новостей пользователю напрямую с использованием NewsAPI
"""

import os
import json
import asyncio
import requests
from datetime import datetime, timedelta
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def fetch_real_news():
    """Получение реальных новостей с NewsAPI."""
    api_key = os.getenv('NEWS_API_KEY')
    
    if not api_key:
        print("❌ NEWS_API_KEY не найден")
        return []
    
    news_list = []
    try:
        # Получаем новости из разных категорий
        categories = ['technology', 'science', 'business', 'health', 'sports']
        
        for category in categories:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': api_key,
                'category': category,
                'country': 'us',
                'pageSize': 2
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'ok' and data.get('articles'):
                for article in data.get('articles', []):
                    if (article.get('title') and article.get('description') and 
                        article.get('url') and article['url'] != 'https://removed.com'):
                        news_list.append({
                            'title': article['title'],
                            'description': article['description'] or 'Описание недоступно',
                            'url': article['url'],
                            'source': article['source']['name'],
                            'category': category,
                            'published_at': article['publishedAt'],
                            'timestamp': datetime.now().isoformat()
                        })
        
        # Если получили мало новостей, добавляем общие
        if len(news_list) < 5:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': api_key,
                'country': 'us',
                'pageSize': 5
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'ok' and data.get('articles'):
                for article in data.get('articles', []):
                    if (article.get('title') and article.get('description') and 
                        article.get('url') and article['url'] != 'https://removed.com'):
                        
                        # Проверяем, что новость еще не добавлена
                        if not any(existing['title'] == article['title'] for existing in news_list):
                            news_list.append({
                                'title': article['title'],
                                'description': article['description'] or 'Описание недоступно',
                                'url': article['url'],
                                'source': article['source']['name'],
                                'category': 'general',
                                'published_at': article['publishedAt'],
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            if len(news_list) >= 10:
                                break
        
        print(f"✅ Получено {len(news_list)} реальных новостей с NewsAPI")
        return news_list
        
    except Exception as e:
        print(f"❌ Ошибка получения новостей: {e}")
        return []

async def send_news_to_user(user_id: int):
    """Отправка реальных новостей пользователю."""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN не найден")
            return
        
        bot = Bot(token=token)
        
        # Получаем реальные новости
        news_list = await fetch_real_news()
        
        if not news_list:
            await bot.send_message(chat_id=user_id, text="❌ Не удалось получить новости с NewsAPI")
            return
        
        await bot.send_message(chat_id=user_id, text=f"🌍 Вот {len(news_list)} свежих новостей из реальных источников:")
        
        for i, news in enumerate(news_list, 1):
            news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
            """
            
            await bot.send_message(
                chat_id=user_id,
                text=news_text,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            await asyncio.sleep(0.5)
        
        print("✅ Реальные новости отправлены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def send_favorites_to_user(user_id: int):
    """Отправка избранных новостей пользователю."""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN не найден")
            return
        
        bot = Bot(token=token)
        
        # Загружаем избранные новости
        with open('data/users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        favorites = users_data.get('favorites', {}).get(str(user_id), [])
        
        if not favorites:
            await bot.send_message(chat_id=user_id, text="❌ У вас нет сохраненных новостей")
            return
        
        await bot.send_message(chat_id=user_id, text=f"❤️ Ваши избранные новости ({len(favorites)} шт.):")
        
        for i, news in enumerate(favorites, 1):
            news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
            """
            
            await bot.send_message(
                chat_id=user_id,
                text=news_text,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            await asyncio.sleep(0.5)
        
        print("✅ Избранные новости отправлены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def main():
    """Главная функция."""
    user_id = 5624684741  # ID пользователя из файла users.json
    
    print("Выберите действие:")
    print("1. Отправить реальные новости с NewsAPI")
    print("2. Отправить избранные новости")
    
    choice = input("Введите номер (1 или 2): ")
    
    if choice == "1":
        await send_news_to_user(user_id)
    elif choice == "2":
        await send_favorites_to_user(user_id)
    else:
        print("❌ Неверный выбор")

if __name__ == '__main__':
    asyncio.run(main())

