#!/usr/bin/env python3
"""
Тестирование интеграции с NewsAPI
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_news_api():
    """Тестирование NewsAPI."""
    api_key = os.getenv('NEWS_API_KEY')
    
    if not api_key:
        print("❌ NEWS_API_KEY не найден в переменных окружения")
        return False
    
    print(f"🔑 Используем API ключ: {api_key[:10]}...")
    
    # Тест 1: Получение топ-новостей
    print("\n📰 Тест 1: Получение топ-новостей...")
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': api_key,
            'country': 'us',
            'pageSize': 5
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == 'ok':
            articles = data.get('articles', [])
            print(f"✅ Получено {len(articles)} топ-новостей")
            
            for i, article in enumerate(articles[:3], 1):
                print(f"  {i}. {article.get('title', 'Без заголовка')}")
                print(f"     Источник: {article.get('source', {}).get('name', 'Неизвестно')}")
                print(f"     URL: {article.get('url', 'Нет ссылки')}")
                print()
        else:
            print(f"❌ Ошибка API: {data.get('message', 'Неизвестная ошибка')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении топ-новостей: {e}")
        return False
    
    # Тест 2: Поиск новостей по ключевому слову
    print("🔍 Тест 2: Поиск новостей по ключевому слову 'AI'...")
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'apiKey': api_key,
            'q': 'AI',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 3,
            'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == 'ok':
            articles = data.get('articles', [])
            print(f"✅ Найдено {len(articles)} новостей по запросу 'AI'")
            
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article.get('title', 'Без заголовка')}")
                print(f"     Описание: {article.get('description', 'Нет описания')[:100]}...")
                print(f"     Источник: {article.get('source', {}).get('name', 'Неизвестно')}")
                print(f"     URL: {article.get('url', 'Нет ссылки')}")
                print()
        else:
            print(f"❌ Ошибка API: {data.get('message', 'Неизвестная ошибка')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при поиске новостей: {e}")
        return False
    
    # Тест 3: Получение новостей по категориям
    print("🏷️ Тест 3: Получение новостей по категориям...")
    categories = ['technology', 'science', 'business']
    
    for category in categories:
        try:
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
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                print(f"✅ Категория '{category}': {len(articles)} новостей")
                
                for article in articles:
                    print(f"  - {article.get('title', 'Без заголовка')}")
            else:
                print(f"❌ Ошибка для категории '{category}': {data.get('message', 'Неизвестная ошибка')}")
                
        except Exception as e:
            print(f"❌ Ошибка для категории '{category}': {e}")
    
    print("\n🎉 Тестирование NewsAPI завершено!")
    return True

def test_bot_integration():
    """Тестирование интеграции с ботом."""
    print("\n🤖 Тестирование интеграции с ботом...")
    
    try:
        # Импортируем класс бота
        from bot import NewsBot
        
        # Создаем экземпляр бота
        bot = NewsBot()
        
        if bot.news_api_key:
            print(f"✅ API ключ загружен: {bot.news_api_key[:10]}...")
            
            # Тестируем получение новостей
            import asyncio
            
            async def test_fetch():
                news = await bot._fetch_news()
                print(f"✅ Бот получил {len(news)} новостей")
                
                for i, article in enumerate(news[:3], 1):
                    print(f"  {i}. {article['title']}")
                    print(f"     Категория: {article['category']}")
                    print(f"     Источник: {article['source']}")
                    print(f"     URL: {article['url']}")
                    print()
            
            asyncio.run(test_fetch())
            
        else:
            print("❌ API ключ не найден в боте")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании бота: {e}")
        return False
    
    return True

def main():
    """Главная функция."""
    print("🚀 Запуск тестирования NewsAPI интеграции...")
    print("=" * 50)
    
    # Тестируем NewsAPI
    api_success = test_news_api()
    
    # Тестируем интеграцию с ботом
    bot_success = test_bot_integration()
    
    print("\n" + "=" * 50)
    if api_success and bot_success:
        print("🎉 Все тесты прошли успешно! NewsAPI интегрирован корректно.")
    else:
        print("❌ Некоторые тесты не прошли. Проверьте настройки.")

if __name__ == '__main__':
    main()
