#!/usr/bin/env python3
"""
Скрипт для сбора обратной связи от пользователей
"""

import json
import os
from datetime import datetime
from typing import Dict, List

class FeedbackCollector:
    """Класс для сбора и анализа обратной связи."""
    
    def __init__(self):
        self.feedback_file = "feedback.json"
        self.stats_file = "user_stats.json"
        self.feedback_data = self._load_feedback()
        self.stats_data = self._load_stats()
    
    def _load_feedback(self) -> List[Dict]:
        """Загружаем данные обратной связи."""
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Ошибка загрузки обратной связи: {e}")
            return []
    
    def _load_stats(self) -> Dict:
        """Загружаем статистику пользователей."""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "total_users": 0,
                "active_users": 0,
                "commands_used": {},
                "last_update": None
            }
        except Exception as e:
            print(f"Ошибка загрузки статистики: {e}")
            return {"total_users": 0, "active_users": 0, "commands_used": {}, "last_update": None}
    
    def _save_feedback(self):
        """Сохраняем данные обратной связи."""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения обратной связи: {e}")
    
    def _save_stats(self):
        """Сохраняем статистику."""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения статистики: {e}")
    
    def add_feedback(self, user_id: int, user_name: str, rating: int, 
                    likes: str, dislikes: str, suggestions: str):
        """Добавляем новую обратную связь."""
        feedback = {
            "user_id": user_id,
            "user_name": user_name,
            "rating": rating,
            "likes": likes,
            "dislikes": dislikes,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_data.append(feedback)
        self._save_feedback()
        
        print(f"✅ Обратная связь от {user_name} добавлена")
    
    def update_stats(self, user_id: int, command: str):
        """Обновляем статистику использования команд."""
        if "commands_used" not in self.stats_data:
            self.stats_data["commands_used"] = {}
        
        if command not in self.stats_data["commands_used"]:
            self.stats_data["commands_used"][command] = 0
        
        self.stats_data["commands_used"][command] += 1
        self.stats_data["last_update"] = datetime.now().isoformat()
        
        self._save_stats()
    
    def get_feedback_summary(self) -> Dict:
        """Получаем сводку по обратной связи."""
        if not self.feedback_data:
            return {"message": "Обратная связь пока не получена"}
        
        total_feedback = len(self.feedback_data)
        avg_rating = sum(f["rating"] for f in self.feedback_data) / total_feedback
        
        # Анализируем лайки
        likes_count = {}
        for feedback in self.feedback_data:
            likes = feedback["likes"].lower()
            if "новости" in likes:
                likes_count["Новости"] = likes_count.get("Новости", 0) + 1
            if "поиск" in likes:
                likes_count["Поиск"] = likes_count.get("Поиск", 0) + 1
            if "категории" in likes:
                likes_count["Категории"] = likes_count.get("Категории", 0) + 1
            if "избранное" in likes:
                likes_count["Избранное"] = likes_count.get("Избранное", 0) + 1
        
        # Анализируем проблемы
        problems_count = {}
        for feedback in self.feedback_data:
            dislikes = feedback["dislikes"].lower()
            if "медленно" in dislikes or "медленный" in dislikes:
                problems_count["Медленная работа"] = problems_count.get("Медленная работа", 0) + 1
            if "ошибк" in dislikes:
                problems_count["Ошибки"] = problems_count.get("Ошибки", 0) + 1
            if "интерфейс" in dislikes:
                problems_count["Интерфейс"] = problems_count.get("Интерфейс", 0) + 1
        
        return {
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 2),
            "top_likes": sorted(likes_count.items(), key=lambda x: x[1], reverse=True),
            "top_problems": sorted(problems_count.items(), key=lambda x: x[1], reverse=True),
            "command_stats": self.stats_data.get("commands_used", {}),
            "last_update": self.stats_data.get("last_update")
        }
    
    def generate_report(self) -> str:
        """Генерируем отчет по обратной связи."""
        summary = self.get_feedback_summary()
        
        if "message" in summary:
            return summary["message"]
        
        report = f"""
📊 ОТЧЕТ ПО ОБРАТНОЙ СВЯЗИ
{'=' * 50}

📈 Общая статистика:
• Всего отзывов: {summary['total_feedback']}
• Средняя оценка: {summary['average_rating']}/5
• Последнее обновление: {summary['last_update']}

👍 Что нравится пользователям:
"""
        
        for feature, count in summary['top_likes'][:3]:
            report += f"• {feature}: {count} упоминаний\n"
        
        report += "\n👎 Основные проблемы:\n"
        for problem, count in summary['top_problems'][:3]:
            report += f"• {problem}: {count} упоминаний\n"
        
        report += "\n📱 Статистика команд:\n"
        for command, count in sorted(summary['command_stats'].items(), 
                                   key=lambda x: x[1], reverse=True)[:5]:
            report += f"• /{command}: {count} использований\n"
        
        return report

def collect_feedback_interactive():
    """Интерактивный сбор обратной связи."""
    collector = FeedbackCollector()
    
    print("📝 Сбор обратной связи от пользователей")
    print("=" * 40)
    
    while True:
        print("\nВыберите действие:")
        print("1. Добавить отзыв")
        print("2. Показать сводку")
        print("3. Сгенерировать отчет")
        print("4. Выход")
        
        choice = input("\nВведите номер (1-4): ")
        
        if choice == "1":
            print("\n📝 Добавление нового отзыва:")
            user_name = input("Имя пользователя: ")
            user_id = input("ID пользователя (или Enter для пропуска): ")
            user_id = int(user_id) if user_id.isdigit() else 0
            
            print("\nОцените бота от 1 до 5:")
            rating = int(input("Оценка (1-5): "))
            
            print("\nЧто вам понравилось?")
            likes = input("Понравилось: ")
            
            print("\nЧто не понравилось?")
            dislikes = input("Не понравилось: ")
            
            print("\nВаши предложения по улучшению:")
            suggestions = input("Предложения: ")
            
            collector.add_feedback(user_id, user_name, rating, likes, dislikes, suggestions)
            
        elif choice == "2":
            summary = collector.get_feedback_summary()
            print("\n📊 Сводка по обратной связи:")
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            
        elif choice == "3":
            report = collector.generate_report()
            print("\n" + report)
            
            # Сохраняем отчет в файл
            with open("feedback_report.txt", "w", encoding="utf-8") as f:
                f.write(report)
            print("\n📄 Отчет сохранен в feedback_report.txt")
            
        elif choice == "4":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор")

def main():
    """Главная функция."""
    collect_feedback_interactive()

if __name__ == '__main__':
    main()
