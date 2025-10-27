#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции с NewsAPI
"""

import os
import requests
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
    
    # Тестируем получение топ-новостей
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': api_key,
            'category': 'technology',
            'country': 'us',
            'pageSize': 3
        }
        
        print("🔄 Тестируем получение новостей технологий...")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'ok':
            articles = data.get('articles', [])
            print(f"✅ Получено {len(articles)} новостей")
            
            for i, article in enumerate(articles[:2], 1):
                print(f"\n📰 Новость {i}:")
                print(f"   Заголовок: {article.get('title', 'Нет заголовка')}")
                print(f"   Источник: {article.get('source', {}).get('name', 'Неизвестно')}")
                print(f"   URL: {article.get('url', 'Нет ссылки')}")
                print(f"   Описание: {article.get('description', 'Нет описания')[:100]}...")
            
            return True
        else:
            print(f"❌ API вернул ошибку: {data.get('message', 'Неизвестная ошибка')}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_search_api():
    """Тестирование поиска через NewsAPI."""
    api_key = os.getenv('NEWS_API_KEY')
    
    if not api_key:
        print("❌ NEWS_API_KEY не найден")
        return False
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'apiKey': api_key,
            'q': 'artificial intelligence',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 2
        }
        
        print("\n🔍 Тестируем поиск по ключевому слову 'artificial intelligence'...")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'ok':
            articles = data.get('articles', [])
            print(f"✅ Найдено {len(articles)} статей")
            
            for i, article in enumerate(articles[:1], 1):
                print(f"\n📰 Статья {i}:")
                print(f"   Заголовок: {article.get('title', 'Нет заголовка')}")
                print(f"   Источник: {article.get('source', {}).get('name', 'Неизвестно')}")
                print(f"   URL: {article.get('url', 'Нет ссылки')}")
            
            return True
        else:
            print(f"❌ API вернул ошибку: {data.get('message', 'Неизвестная ошибка')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return False

def main():
    """Главная функция тестирования."""
    print("🧪 Тестирование интеграции с NewsAPI")
    print("=" * 50)
    
    # Тестируем получение новостей
    news_test = test_news_api()
    
    # Тестируем поиск
    search_test = test_search_api()
    
    print("\n" + "=" * 50)
    if news_test and search_test:
        print("✅ Все тесты прошли успешно! NewsAPI работает корректно.")
        print("🚀 Бот готов к использованию с реальными новостями.")
    else:
        print("❌ Некоторые тесты не прошли. Проверьте API ключ и подключение к интернету.")
    
    return news_test and search_test

if __name__ == '__main__':
    main()
