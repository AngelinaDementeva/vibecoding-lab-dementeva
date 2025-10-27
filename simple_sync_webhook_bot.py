#!/usr/bin/env python3
"""
Простая синхронная webhook версия бота
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List
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

# Создаем Flask приложение
app = Flask(__name__)

def log_user_action(user_id: int, action: str, details: str = ""):
    """Логирование действий пользователей для аналитики."""
    logger.info(f"USER_ACTION: user_id={user_id}, action={action}, details={details}")

def log_error(error: Exception, context: str = ""):
    """Логирование ошибок для мониторинга."""
    logger.error(f"ERROR: {context} - {str(error)}", exc_info=True)

class SimpleNewsBot:
    """Простой синхронный бот для новостей."""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.feedback_form_url = "https://forms.gle/m9AHSMgKHsmG437p9"
        
        # Категории новостей
        self.categories = {
            'technology': 'технологии',
            'science': 'наука', 
            'business': 'бизнес',
            'health': 'здоровье',
            'sports': 'спорт',
            'entertainment': 'развлечения',
            'general': 'общие'
        }
        
        # Файлы для хранения данных
        self.favorites_file = 'data/favorites.json'
        self.user_stats_file = 'data/user_stats.json'
        self.subscriptions_file = 'data/subscriptions.json'
        
        # Кэш последних новостей для каждого пользователя
        self.last_news_cache = {}
        
        # Инициализируем файлы данных
        self._init_data_files()
    
    def _init_data_files(self):
        """Инициализация файлов данных."""
        try:
            # Создаем директорию data если её нет
            os.makedirs('data', exist_ok=True)
            
            # Инициализируем файл избранного
            if not os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
            
            # Инициализируем файл статистики пользователей
            if not os.path.exists(self.user_stats_file):
                with open(self.user_stats_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
            
            # Инициализируем файл подписок
            if not os.path.exists(self.subscriptions_file):
                with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            log_error(e, "Ошибка инициализации файлов данных")
    
    def _load_favorites(self) -> Dict:
        """Загрузка избранных новостей."""
        try:
            with open(self.favorites_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_error(e, "Ошибка загрузки избранного")
            return {}
    
    def _save_favorites(self, favorites: Dict):
        """Сохранение избранных новостей."""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(e, "Ошибка сохранения избранного")
    
    def _load_user_stats(self) -> Dict:
        """Загрузка статистики пользователей."""
        try:
            with open(self.user_stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_error(e, "Ошибка загрузки статистики")
            return {}
    
    def _save_user_stats(self, stats: Dict):
        """Сохранение статистики пользователей."""
        try:
            with open(self.user_stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(e, "Ошибка сохранения статистики")
    
    def _load_subscriptions(self) -> Dict:
        """Загрузка подписок пользователей."""
        try:
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_error(e, "Ошибка загрузки подписок")
            return {}
    
    def _save_subscriptions(self, subscriptions: Dict):
        """Сохранение подписок пользователей."""
        try:
            with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(e, "Ошибка сохранения подписок")
    
    def _filter_saved_news(self, news_list: List[Dict], user_id: int) -> List[Dict]:
        """Фильтрация уже сохраненных новостей."""
        try:
            favorites = self._load_favorites()
            user_id_str = str(user_id)
            
            if user_id_str not in favorites:
                return news_list
            
            user_favorites = favorites[user_id_str]
            saved_titles = {news['title'] for news in user_favorites}
            
            # Фильтруем новости, исключая уже сохраненные
            filtered_news = []
            for news in news_list:
                if news['title'] not in saved_titles:
                    filtered_news.append(news)
            
            logger.info(f"Отфильтровано {len(news_list) - len(filtered_news)} уже сохраненных новостей")
            return filtered_news
            
        except Exception as e:
            log_error(e, "Ошибка фильтрации новостей")
            return news_list
    
    def _update_user_stats(self, user_id: int):
        """Обновление статистики пользователя."""
        try:
            stats = self._load_user_stats()
            user_id_str = str(user_id)
            
            if user_id_str not in stats:
                stats[user_id_str] = {'commands_count': 0, 'last_command': None}
            
            stats[user_id_str]['commands_count'] += 1
            stats[user_id_str]['last_command'] = datetime.now().isoformat()
            
            self._save_user_stats(stats)
            
            # Проверяем, нужно ли отправить форму обратной связи
            if stats[user_id_str]['commands_count'] == 10:
                self._send_feedback_form(user_id)
                
        except Exception as e:
            log_error(e, "Ошибка обновления статистики")
    
    def _send_feedback_form(self, user_id: int):
        """Отправка формы обратной связи."""
        try:
            feedback_text = f"""
🎉 Поздравляем! Вы использовали бота уже 10 раз! 

📝 Пожалуйста, поделитесь своим мнением о работе бота:
{self.feedback_form_url}

Ваш отзыв поможет нам улучшить бота! 🙏
            """
            self.send_message(user_id, feedback_text)
            log_user_action(user_id, "feedback_form_sent")
        except Exception as e:
            log_error(e, "Ошибка отправки формы обратной связи")
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = None, reply_markup: dict = None):
        """Отправка сообщения пользователю."""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            
            data = {
                'chat_id': chat_id,
                'text': text
            }
            
            if parse_mode:
                data['parse_mode'] = parse_mode
            
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Отправлено сообщение пользователю {chat_id}")
            return True
            
        except Exception as e:
            log_error(e, f"Ошибка отправки сообщения пользователю {chat_id}")
            return False
    
    def get_news(self) -> List[Dict]:
        """Получение новостей с NewsAPI."""
        if not self.news_api_key:
            logger.warning("NEWS_API_KEY не настроен, используем тестовые данные")
            return self.get_test_news()
        
        news_list = []
        try:
            # Добавляем случайность для получения разных новостей
            import random
            current_time = datetime.now()
            
            # Получаем новости из разных источников и категорий
            categories = ['technology', 'science', 'business', 'health', 'sports', 'entertainment']
            random.shuffle(categories)  # Перемешиваем категории для разнообразия
            
            for category in categories[:3]:  # Берем только 3 случайные категории
                url = "https://newsapi.org/v2/top-headlines"
                params = {
                    'apiKey': self.news_api_key,
                    'category': category,
                    'country': 'us',
                    'pageSize': 2,
                    'page': random.randint(1, 3)  # Случайная страница для разнообразия
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
                                'category': self.categories.get(category, category),
                                'published_at': article['publishedAt'],
                                'timestamp': current_time.isoformat()
                            })
            
            # Если получили мало новостей, добавляем общие с разными параметрами
            if len(news_list) < 5:
                try:
                    # Пробуем разные страны для разнообразия
                    countries = ['us', 'gb', 'ca', 'au']
                    random_country = random.choice(countries)
                    
                    url = "https://newsapi.org/v2/top-headlines"
                    params = {
                        'apiKey': self.news_api_key,
                        'country': random_country,
                        'pageSize': 8,
                        'page': random.randint(1, 2)
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
                                        'category': 'общие',
                                        'published_at': article['publishedAt'],
                                        'timestamp': current_time.isoformat()
                                    })
                                    
                                    if len(news_list) >= 10:  # Ограничиваем количество
                                        break
                                        
                except Exception as e:
                    logger.warning(f"Ошибка получения общих новостей: {e}")
            
            # Перемешиваем список новостей для случайного порядка
            random.shuffle(news_list)
            
            logger.info(f"Получено {len(news_list)} новостей с NewsAPI")
            return news_list[:8]  # Возвращаем максимум 8 новостей
            
        except Exception as e:
            log_error(e, "Ошибка получения новостей")
            return self.get_test_news()
    
    def get_test_news(self) -> List[Dict]:
        """Тестовые новости."""
        return [
            {
                'title': 'Новые технологии в области искусственного интеллекта',
                'description': 'Исследователи представили новую модель ИИ, способную решать сложные задачи машинного обучения.',
                'url': 'https://example.com/ai-news',
                'source': 'TechNews',
                'category': 'технологии',
                'published_at': datetime.now().isoformat(),
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'Открытие в области квантовой физики',
                'description': 'Ученые сделали важное открытие в области квантовых вычислений.',
                'url': 'https://example.com/quantum-news',
                'source': 'ScienceDaily',
                'category': 'наука',
                'published_at': datetime.now().isoformat(),
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def handle_start_command(self, chat_id: int, user_name: str):
        """Обработка команды /start."""
        log_user_action(chat_id, "start_command", f"user_name={user_name}")
        self._update_user_stats(chat_id)
        
        welcome_text = f"""
Привет, {user_name}! 👋

Я бот для новостей. Вот что я умею:

📰 /news - Показать свежие новости
🔍 /filter <слово> - Найти новости по ключевому слову
⭐ /save <номер> - Сохранить новость в избранное
❤️ /favorites - Показать избранные новости
📬 /daily - Подписаться на ежедневную рассылку
❓ /help - Показать справку

Начнем с команды /news для просмотра свежих новостей!
        """
        
        self.send_message(chat_id, welcome_text)
    
    def handle_news_command(self, chat_id: int):
        """Обработка команды /news."""
        log_user_action(chat_id, "news_command")
        self._update_user_stats(chat_id)
        
        self.send_message(chat_id, "🔄 Загружаю свежие новости...")
        
        news_list = self.get_news()
        
        if not news_list:
            self.send_message(chat_id, "❌ К сожалению, новости сейчас недоступны. Попробуйте позже.")
            return
        
        # Фильтруем уже сохраненные новости
        filtered_news = self._filter_saved_news(news_list, chat_id)
        
        if not filtered_news:
            self.send_message(chat_id, "✅ Все доступные новости уже сохранены в вашем избранном!\n\nИспользуйте /favorites для просмотра сохраненных новостей.")
            return
        
        # Кэшируем отфильтрованные новости для этого пользователя
        self.last_news_cache[chat_id] = filtered_news[:5]
        
        for i, news in enumerate(filtered_news[:5], 1):
            news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
            """
            
            # Создаем кнопку для сохранения
            keyboard = {
                "inline_keyboard": [[{
                    "text": f"⭐ Сохранить новость #{i}",
                    "callback_data": f"save_{i}"
                }]]
            }
            
            self.send_message(
                chat_id, 
                news_text, 
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        
        self.send_message(chat_id, "✅ Вот все доступные новости! Используйте кнопки '⭐ Сохранить' или команду /save <номер> для сохранения.")
    
    def handle_help_command(self, chat_id: int):
        """Обработка команды /help."""
        help_text = """
📖 Справка по командам:

📰 /news - Показать свежие новости за день
🔍 /filter <слово> - Найти новости, содержащие указанное слово
⭐ /save <номер> - Сохранить новость с указанным номером в избранное
❤️ /favorites - Показать все сохраненные новости
📬 /daily - Подписаться/отписаться от ежедневной рассылки
❓ /help - Показать эту справку

Примеры:
/filter ИИ
/save 1
        """
        self.send_message(chat_id, help_text)
    
    def handle_favorites_command(self, chat_id: int):
        """Обработка команды /favorites."""
        log_user_action(chat_id, "favorites_command")
        self._update_user_stats(chat_id)
        
        favorites = self._load_favorites()
        user_id_str = str(chat_id)
        
        if user_id_str not in favorites or not favorites[user_id_str]:
            self.send_message(chat_id, "❤️ У вас пока нет избранных новостей.\n\nИспользуйте команду /news для просмотра новостей и кнопки '⭐ Сохранить' для добавления в избранное.")
            return
        
        user_favorites = favorites[user_id_str]
        
        if not user_favorites:
            self.send_message(chat_id, "❤️ У вас пока нет избранных новостей.\n\nИспользуйте команду /news для просмотра новостей и кнопки '⭐ Сохранить' для добавления в избранное.")
            return
        
        self.send_message(chat_id, f"❤️ Ваши избранные новости ({len(user_favorites)} шт.):")
        
        for i, news in enumerate(user_favorites, 1):
            news_text = f"""
⭐ **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
📅 Сохранено: {news.get('saved_at', 'Неизвестно')}
            """
            
            self.send_message(chat_id, news_text, parse_mode='Markdown')
        
        self.send_message(chat_id, "✅ Это все ваши избранные новости!")
    
    def handle_save_command(self, chat_id: int, news_number: int):
        """Обработка команды /save <номер>."""
        log_user_action(chat_id, "save_command", f"news_number={news_number}")
        self._update_user_stats(chat_id)
        
        # Используем кэшированные новости или получаем новые
        if chat_id in self.last_news_cache:
            news_list = self.last_news_cache[chat_id]
        else:
            news_list = self.get_news()
            if news_list:
                self.last_news_cache[chat_id] = news_list[:5]
        
        if not news_list or news_number < 1 or news_number > len(news_list):
            self.send_message(chat_id, f"❌ Неверный номер новости. Доступны номера от 1 до {len(news_list) if news_list else 0}.\n\nИспользуйте /news для просмотра доступных новостей.")
            return
        
        news_to_save = news_list[news_number - 1]
        
        # Загружаем избранное
        favorites = self._load_favorites()
        user_id_str = str(chat_id)
        
        if user_id_str not in favorites:
            favorites[user_id_str] = []
        
        # Проверяем, не сохранена ли уже эта новость
        for existing in favorites[user_id_str]:
            if existing['title'] == news_to_save['title']:
                self.send_message(chat_id, "⚠️ Эта новость уже сохранена в избранном!")
                return
        
        # Добавляем новость в избранное
        news_to_save['saved_at'] = datetime.now().isoformat()
        favorites[user_id_str].append(news_to_save)
        
        # Сохраняем избранное
        self._save_favorites(favorites)
        
        self.send_message(chat_id, f"✅ Новость '{news_to_save['title'][:50]}...' сохранена в избранное!\n\nИспользуйте /favorites для просмотра всех сохраненных новостей.")
    
    def handle_daily_command(self, chat_id: int):
        """Обработка команды /daily."""
        log_user_action(chat_id, "daily_command")
        self._update_user_stats(chat_id)
        
        subscriptions = self._load_subscriptions()
        user_id_str = str(chat_id)
        
        if user_id_str in subscriptions and subscriptions[user_id_str].get('subscribed', False):
            # Пользователь уже подписан - предлагаем отписаться
            daily_text = """
📬 Ежедневная рассылка новостей

✅ Вы уже подписаны на ежедневную рассылку!

📅 Подписка активна с: {subscription_date}

Хотите отписаться? Нажмите кнопку ниже.
            """.format(subscription_date=subscriptions[user_id_str].get('subscribed_at', 'Неизвестно'))
            
            keyboard = {
                "inline_keyboard": [[{
                    "text": "❌ Отписаться от рассылки",
                    "callback_data": "unsubscribe_daily"
                }]]
            }
            
            self.send_message(chat_id, daily_text, reply_markup=keyboard)
        else:
            # Пользователь не подписан - предлагаем подписаться
            daily_text = """
📬 Ежедневная рассылка новостей

🎯 Получайте ежедневную подборку самых интересных новостей прямо в Telegram!

📰 Что вы получите:
• Топ-5 новостей дня
• Разные категории (технологии, наука, бизнес)
• Только свежие и актуальные новости
• Удобные кнопки для сохранения

Хотите подписаться? Нажмите кнопку ниже.
            """
            
            keyboard = {
                "inline_keyboard": [[{
                    "text": "✅ Подписаться на рассылку",
                    "callback_data": "subscribe_daily"
                }]]
            }
            
            self.send_message(chat_id, daily_text, reply_markup=keyboard)
    
    def handle_filter_command(self, chat_id: int, search_word: str):
        """Обработчик команды /filter."""
        try:
            log_user_action(chat_id, "filter_command", f"search_word={search_word}")
            
            if not search_word.strip():
                self.send_message(chat_id, "❌ Укажите слово для поиска.\nПример: /filter ИИ")
                return
            
            search_word = search_word.lower()
            self.send_message(chat_id, f"🔍 Ищу новости по слову '{search_word}'...")
            
            # Получаем свежие новости
            news_list = self.get_news()
            
            if not news_list:
                self.send_message(chat_id, "❌ К сожалению, новости сейчас недоступны. Попробуйте позже.")
                return
            
            filtered_news = []
            for news in news_list:
                if (search_word in news.get('title', '').lower() or 
                    search_word in news.get('description', '').lower()):
                    filtered_news.append(news)
            
            if not filtered_news:
                self.send_message(chat_id, f"❌ Новости по слову '{search_word}' не найдены.")
                return
            
            self.send_message(chat_id, f"✅ Найдено {len(filtered_news)} новостей:")
            
            for i, news in enumerate(filtered_news[:5], 1):  # Показываем максимум 5 результатов
                news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
                """
                
                keyboard = {
                    'inline_keyboard': [[{
                        'text': '⭐ Сохранить',
                        'callback_data': f'save_filtered_{i}'
                    }]]
                }
                
                self.send_message(chat_id, news_text, parse_mode='Markdown', reply_markup=keyboard)
                
                # Небольшая задержка между сообщениями
                import time
                time.sleep(0.5)
            
        except Exception as e:
            log_error(e, "Ошибка в команде filter")
            self.send_message(chat_id, "❌ Произошла ошибка при поиске новостей.")

    def handle_callback_query(self, chat_id: int, callback_data: str):
        """Обработка callback запросов от inline кнопок."""
        log_user_action(chat_id, "callback_query", f"callback_data={callback_data}")
        
        if callback_data.startswith('save_'):
            try:
                news_number = int(callback_data.split('_')[1])
                self.handle_save_command(chat_id, news_number)
            except (ValueError, IndexError):
                self.send_message(chat_id, "❌ Ошибка при сохранении новости. Попробуйте команду /save <номер>")
        
        elif callback_data.startswith('save_filtered_'):
            try:
                news_number = int(callback_data.split('_')[2])
                self.handle_save_command(chat_id, news_number)
            except (ValueError, IndexError):
                self.send_message(chat_id, "❌ Ошибка при сохранении отфильтрованной новости.")
        
        elif callback_data == 'subscribe_daily':
            self._subscribe_to_daily(chat_id)
        
        elif callback_data == 'unsubscribe_daily':
            self._unsubscribe_from_daily(chat_id)
        
        else:
            self.send_message(chat_id, "❌ Неизвестная команда кнопки.")
    
    def _subscribe_to_daily(self, chat_id: int):
        """Подписка на ежедневную рассылку."""
        try:
            subscriptions = self._load_subscriptions()
            user_id_str = str(chat_id)
            
            subscriptions[user_id_str] = {
                'subscribed': True,
                'subscribed_at': datetime.now().isoformat(),
                'last_sent': None
            }
            
            self._save_subscriptions(subscriptions)
            
            success_text = """
✅ Вы успешно подписались на ежедневную рассылку!

📅 С завтрашнего дня вы будете получать:
• Топ-5 новостей дня
• Разные категории новостей
• Только свежие и актуальные материалы

📬 Рассылка приходит каждый день в 9:00 по московскому времени.

Используйте /daily для управления подпиской.
            """
            
            self.send_message(chat_id, success_text)
            log_user_action(chat_id, "daily_subscribed")
            
        except Exception as e:
            log_error(e, "Ошибка подписки на рассылку")
            self.send_message(chat_id, "❌ Ошибка при подписке. Попробуйте позже.")
    
    def _unsubscribe_from_daily(self, chat_id: int):
        """Отписка от ежедневной рассылки."""
        try:
            subscriptions = self._load_subscriptions()
            user_id_str = str(chat_id)
            
            if user_id_str in subscriptions:
                subscriptions[user_id_str]['subscribed'] = False
                subscriptions[user_id_str]['unsubscribed_at'] = datetime.now().isoformat()
                self._save_subscriptions(subscriptions)
            
            success_text = """
❌ Вы отписались от ежедневной рассылки.

📰 Вы по-прежнему можете получать новости вручную:
• Используйте /news для просмотра свежих новостей
• Сохраняйте интересные новости с помощью /save <номер>
• Просматривайте сохраненные новости с помощью /favorites

Используйте /daily для повторной подписки.
            """
            
            self.send_message(chat_id, success_text)
            log_user_action(chat_id, "daily_unsubscribed")
            
        except Exception as e:
            log_error(e, "Ошибка отписки от рассылки")
            self.send_message(chat_id, "❌ Ошибка при отписке. Попробуйте позже.")

# Создаем экземпляр бота
bot = SimpleNewsBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик webhook."""
    try:
        update_data = request.get_json()
        
        if update_data:
            # Обработка обычных сообщений
            if 'message' in update_data:
                message = update_data['message']
                chat_id = message['chat']['id']
                user_name = message['from'].get('first_name', 'Пользователь')
                text = message.get('text', '')
                
                log_user_action(chat_id, "webhook_update", f"text={text}")
                
                if text == '/start':
                    bot.handle_start_command(chat_id, user_name)
                elif text == '/news':
                    bot.handle_news_command(chat_id)
                elif text == '/help':
                    bot.handle_help_command(chat_id)
                elif text == '/favorites':
                    bot.handle_favorites_command(chat_id)
                elif text == '/daily':
                    bot.handle_daily_command(chat_id)
                elif text.startswith('/filter '):
                    try:
                        search_word = ' '.join(text.split()[1:])
                        bot.handle_filter_command(chat_id, search_word)
                    except IndexError:
                        bot.send_message(chat_id, "❌ Укажите слово для поиска.\nПример: /filter ИИ")
                elif text.startswith('/save '):
                    try:
                        news_number = int(text.split()[1])
                        bot.handle_save_command(chat_id, news_number)
                    except (ValueError, IndexError):
                        bot.send_message(chat_id, "❌ Неверный формат команды. Используйте: /save <номер>\n\nПример: /save 1")
                else:
                    bot.send_message(chat_id, "Неизвестная команда. Используйте /help для справки.")
            
            # Обработка callback запросов от inline кнопок
            elif 'callback_query' in update_data:
                callback_query = update_data['callback_query']
                chat_id = callback_query['message']['chat']['id']
                callback_data = callback_query.get('data', '')
                
                log_user_action(chat_id, "webhook_update", f"callback_data={callback_data}")
                
                # Отвечаем на callback query
                try:
                    url = f"https://api.telegram.org/bot{bot.token}/answerCallbackQuery"
                    data = {
                        'callback_query_id': callback_query['id'],
                        'text': 'Обрабатываю...'
                    }
                    requests.post(url, json=data, timeout=5)
                except Exception as e:
                    log_error(e, "Ошибка ответа на callback query")
                
                # Обрабатываем callback
                bot.handle_callback_query(chat_id, callback_data)
        
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
        "bot_token_configured": bool(bot.token),
        "news_api_configured": bool(bot.news_api_key)
    }

@app.route('/', methods=['GET'])
def index():
    """Главная страница."""
    return """
    <h1>Simple News Bot Webhook</h1>
    <p>Бот работает! 🚀</p>
    <ul>
        <li><a href="/health">Health Check</a></li>
    </ul>
    """

def main():
    """Запуск webhook сервера."""
    print("🚀 Запуск простого синхронного News Bot с webhook...")
    print("✅ Бот готов к работе")
    print("🌐 Webhook endpoint: /webhook")
    print("📊 Health check: /health")
    
    app.run(host='0.0.0.0', port=8000, debug=False)

if __name__ == '__main__':
    main()
