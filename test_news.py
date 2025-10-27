#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки новостей
"""

import json
import os

def test_news():
    """Тестирование загрузки новостей."""
    try:
        news_file = 'data/news.json'
        
        # Загружаем данные новостей
        with open(news_file, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
        
        print("Данные новостей:")
        print(json.dumps(news_data, ensure_ascii=False, indent=2))
        
        news_list = news_data.get('news', [])
        print(f"\nКоличество новостей: {len(news_list)}")
        
        for i, news in enumerate(news_list, 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Описание: {news['description']}")
            print(f"   Категория: {news['category']}")
            print(f"   Источник: {news['source']}")
            print(f"   URL: {news['url']}")
        
        print("\n✅ Тест загрузки новостей прошел успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    test_news()

