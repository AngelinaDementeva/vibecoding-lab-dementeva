#!/usr/bin/env python3
"""
Тестовый скрипт для проверки команды /favorites
"""

import json
import os

def test_favorites():
    """Тестирование загрузки избранных новостей."""
    try:
        users_file = 'data/users.json'
        
        # Загружаем данные пользователей
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        print("Данные пользователей:")
        print(json.dumps(users_data, ensure_ascii=False, indent=2))
        
        # Тестируем для пользователя 5624684741
        user_id = "5624684741"
        favorites = users_data.get('favorites', {}).get(user_id, [])
        
        print(f"\nИзбранные новости для пользователя {user_id}:")
        print(f"Количество: {len(favorites)}")
        
        for i, news in enumerate(favorites, 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Описание: {news['description']}")
            print(f"   Категория: {news['category']}")
            print(f"   Источник: {news['source']}")
            print(f"   URL: {news['url']}")
        
        print("\n✅ Тест прошел успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    test_favorites()

