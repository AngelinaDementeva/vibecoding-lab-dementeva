#!/usr/bin/env python3
"""
Telegram News Bot
Бот для сбора и управления новостями по темам: технологии, наука, бизнес.
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
from dotenv import load_dotenv

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

class NewsBot:
    """Основной класс Telegram-бота для работы с новостями."""
    
    def __init__(self):
        """Инициализация бота."""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.data_dir = 'data'
        self.news_file = os.path.join(self.data_dir, 'news.json')
        self.users_file = os.path.join(self.data_dir, 'users.json')
        self.stats_file = os.path.join(self.data_dir, 'user_stats.json')
        
        # Создаем папку для данных если её нет
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Инициализируем файлы данных
        self._init_data_files()
        
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
        
        # Ссылка на форму обратной связи
        self.feedback_form_url = "https://forms.gle/m9AHSMgKHsmG437p9"
    
    def _init_data_files(self):
        """Инициализация файлов данных."""
        # Инициализация файла новостей
        if not os.path.exists(self.news_file):
            with open(self.news_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_update': None,
                    'news': []
                }, f, ensure_ascii=False, indent=2)
        
        # Инициализация файла пользователей
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'subscribers': [],
                    'favorites': {}
                }, f, ensure_ascii=False, indent=2)
        
        # Инициализация файла статистики
        if not os.path.exists(self.stats_file):
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'user_stats': {},
                    'total_commands': 0,
                    'last_update': None
                }, f, ensure_ascii=False, indent=2)
    
    def _load_data(self, file_path: str) -> Dict:
        """Загрузка данных из JSON файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка загрузки данных из {file_path}: {e}")
            return {}
    
    def _save_data(self, file_path: str, data: Dict):
        """Сохранение данных в JSON файл."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных в {file_path}: {e}")
    
    def _update_user_stats(self, user_id: int, command: str):
        """Обновление статистики пользователя."""
        try:
            stats_data = self._load_data(self.stats_file)
            user_stats = stats_data.get('user_stats', {})
            
            if str(user_id) not in user_stats:
                user_stats[str(user_id)] = {
                    'commands_count': 0,
                    'last_command': None,
                    'feedback_sent': False,
                    'commands_used': {}
                }
            
            user_stats[str(user_id)]['commands_count'] += 1
            user_stats[str(user_id)]['last_command'] = command
            
            if command not in user_stats[str(user_id)]['commands_used']:
                user_stats[str(user_id)]['commands_used'][command] = 0
            user_stats[str(user_id)]['commands_used'][command] += 1
            
            stats_data['user_stats'] = user_stats
            stats_data['total_commands'] = stats_data.get('total_commands', 0) + 1
            stats_data['last_update'] = datetime.now().isoformat()
            
            self._save_data(self.stats_file, stats_data)
            
            # Проверяем, нужно ли отправить форму обратной связи
            if user_stats[str(user_id)]['commands_count'] >= 10 and not user_stats[str(user_id)]['feedback_sent']:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
            return False
    
    async def _send_feedback_form(self, update: Update):
        """Отправка формы обратной связи пользователю."""
        try:
            feedback_text = f"""
🎉 Поздравляем! Вы использовали бота уже 10 раз!

📝 Помогите нам улучшить бота, заполнив короткую форму обратной связи:

🔗 {self.feedback_form_url}

Ваше мнение очень важно для нас! 💙
            """
            
            await update.message.reply_text(feedback_text)
            
            # Отмечаем, что форма отправлена
            stats_data = self._load_data(self.stats_file)
            user_stats = stats_data.get('user_stats', {})
            user_id = str(update.effective_user.id)
            
            if user_id in user_stats:
                user_stats[user_id]['feedback_sent'] = True
                stats_data['user_stats'] = user_stats
                self._save_data(self.stats_file, stats_data)
            
            log_user_action(update.effective_user.id, "feedback_form_sent")
            
        except Exception as e:
            log_error(e, "Ошибка отправки формы обратной связи")
    
    async def _fetch_news(self) -> List[Dict]:
        """Получение новостей с News API."""
        if not self.news_api_key:
            logger.warning("NEWS_API_KEY не настроен, используем тестовые данные")
            return self._get_test_news()
        
        news_list = []
        try:
            # Получаем новости из разных категорий
            for category in ['technology', 'science', 'business', 'health', 'sports']:
                url = f"https://newsapi.org/v2/top-headlines"
                params = {
                    'apiKey': self.news_api_key,
                    'category': category,
                    'country': 'us',
                    'pageSize': 3  # Уменьшили количество для каждой категории
                }
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                if data.get('status') == 'ok' and data.get('articles'):
                    for article in data.get('articles', []):
                        if article.get('title') and article.get('description') and article.get('url'):
                            # Проверяем, что URL валидный
                            if article['url'] != 'https://removed.com':
                                news_list.append({
                                    'title': article['title'],
                                    'description': article['description'] or 'Описание недоступно',
                                    'url': article['url'],
                                    'source': article['source']['name'],
                                    'category': self.categories.get(category, category),
                                    'published_at': article['publishedAt'],
                                    'timestamp': datetime.now().isoformat()
                                })
                else:
                    logger.warning(f"News API вернул пустой результат для категории {category}")
                
                # Небольшая пауза между запросами
                await asyncio.sleep(0.5)
            
            # Если получили мало новостей, попробуем получить общие новости
            if len(news_list) < 5:
                try:
                    url = "https://newsapi.org/v2/top-headlines"
                    params = {
                        'apiKey': self.news_api_key,
                        'country': 'us',
                        'pageSize': 10
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
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    
                                    if len(news_list) >= 15:  # Ограничиваем общее количество
                                        break
                except Exception as e:
                    logger.error(f"Ошибка получения общих новостей: {e}")
                
        except requests.RequestException as e:
            logger.error(f"Ошибка получения новостей: {e}")
            return self._get_test_news()
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении новостей: {e}")
            return self._get_test_news()
        
        # Если не получили новости, используем тестовые данные
        if not news_list:
            logger.warning("Не удалось получить новости с News API, используем тестовые данные")
            return self._get_test_news()
        
        logger.info(f"Получено {len(news_list)} новостей с News API")
        return news_list
    
    def _get_test_news(self) -> List[Dict]:
        """Тестовые новости для демонстрации."""
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
                'description': 'Ученые сделали важное открытие в области квантовых вычислений, которое может революционизировать криптографию.',
                'url': 'https://example.com/quantum-news',
                'source': 'ScienceDaily',
                'category': 'наука',
                'published_at': datetime.now().isoformat(),
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'Рост рынка криптовалют',
                'description': 'Аналитики прогнозируют значительный рост криптовалютного рынка в ближайшие месяцы.',
                'url': 'https://example.com/crypto-news',
                'source': 'BusinessToday',
                'category': 'бизнес',
                'published_at': datetime.now().isoformat(),
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'Разработка нового процессора',
                'description': 'Компания представила новый процессор с улучшенной производительностью и энергоэффективностью.',
                'url': 'https://example.com/processor-news',
                'source': 'TechWorld',
                'category': 'технологии',
                'published_at': datetime.now().isoformat(),
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'Прорыв в медицине',
                'description': 'Ученые разработали новый метод лечения, который показывает обнадеживающие результаты в клинических испытаниях.',
                'url': 'https://example.com/medical-news',
                'source': 'MedicalNews',
                'category': 'наука',
                'published_at': datetime.now().isoformat(),
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'Инвестиции в стартапы',
                'description': 'Венчурные фонды увеличивают инвестиции в технологические стартапы, особенно в области финтеха.',
                'url': 'https://example.com/startup-news',
                'source': 'VentureBeat',
                'category': 'бизнес',
                'published_at': datetime.now().isoformat(),
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    async def _update_news(self):
        """Обновление новостей."""
        try:
            news_data = self._load_data(self.news_file)
            current_time = datetime.now()
            
            # Обновляем новости если прошло больше 30 минут или новостей нет
            if (not news_data.get('last_update') or 
                datetime.fromisoformat(news_data['last_update']) < current_time - timedelta(minutes=30)):
                
                logger.info("Обновление новостей...")
                new_news = await self._fetch_news()
                
                news_data['news'] = new_news
                news_data['last_update'] = current_time.isoformat()
                
                self._save_data(self.news_file, news_data)
                logger.info(f"Обновлено {len(new_news)} новостей")
            
            return news_data['news']
        except Exception as e:
            logger.error(f"Ошибка обновления новостей: {e}")
            return []
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        user = update.effective_user
        log_user_action(user.id, "start_command", f"user_name={user.first_name}")
        
        # Обновляем статистику и проверяем форму обратной связи
        should_send_feedback = self._update_user_stats(user.id, "start")
        
        welcome_text = f"""
Привет, {user.first_name}! 👋

Я бот для новостей. Вот что я умею:

📰 /news - Показать свежие новости
🏷️ /category <категория> - Новости по категории
🔍 /filter <слово> - Найти новости по ключевому слову
⭐ /save <номер> - Сохранить новость в избранное
❤️ /favorites - Показать избранные новости
📬 /daily - Подписаться на ежедневную рассылку
❓ /help - Показать справку

Начнем с команды /news для просмотра свежих новостей!
        """
        await update.message.reply_text(welcome_text)
        
        # Отправляем форму обратной связи если нужно
        if should_send_feedback:
            await self._send_feedback_form(update)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help."""
        help_text = """
📖 Справка по командам:

📰 /news - Показать свежие новости за день
🏷️ /category <категория> - Новости по конкретной категории
🔍 /filter <слово> - Найти новости, содержащие указанное слово
⭐ /save <номер> - Сохранить новость с указанным номером в избранное
❤️ /favorites - Показать все сохраненные новости
📬 /daily - Подписаться/отписаться от ежедневной рассылки
❓ /help - Показать эту справку

Доступные категории: технологии, наука, бизнес, здоровье, спорт, развлечения

Примеры:
/category технологии
/filter ИИ
/save 1
        """
        await update.message.reply_text(help_text)
    
    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /news."""
        try:
            user = update.effective_user
            log_user_action(user.id, "news_command")
            
            # Обновляем статистику и проверяем форму обратной связи
            should_send_feedback = self._update_user_stats(user.id, "news")
            
            await update.message.reply_text("🔄 Загружаю свежие новости...")
            
            news_list = await self._update_news()
            
            if not news_list:
                await update.message.reply_text("❌ К сожалению, новости сейчас недоступны. Попробуйте позже.")
                return
            
            # Отправляем новости порциями
            for i, news in enumerate(news_list[:10], 1):  # Показываем максимум 10 новостей
                news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
                """
                
                # Создаем клавиатуру для сохранения
                keyboard = [[InlineKeyboardButton(f"⭐ Сохранить новость #{i}", callback_data=f"save_{i}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    news_text, 
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
                # Небольшая пауза между сообщениями
                await asyncio.sleep(0.5)
            
            await update.message.reply_text("✅ Вот все доступные новости! Используйте /save <номер> для сохранения.")
            
            # Отправляем форму обратной связи если нужно
            if should_send_feedback:
                await self._send_feedback_form(update)
            
        except Exception as e:
            logger.error(f"Ошибка в команде news: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке новостей.")
    
    async def filter_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /filter."""
        try:
            if not context.args:
                await update.message.reply_text("❌ Укажите слово для поиска.\nПример: /filter ИИ")
                return
            
            search_word = ' '.join(context.args).lower()
            await update.message.reply_text(f"🔍 Ищу новости по слову '{search_word}'...")
            
            # Сначала ищем в локальных новостях
            news_data = self._load_data(self.news_file)
            news_list = news_data.get('news', [])
            
            filtered_news = []
            for news in news_list:
                if (search_word in news.get('title', '').lower() or 
                    search_word in news.get('description', '').lower()):
                    filtered_news.append(news)
            
            # Если есть NewsAPI ключ, ищем дополнительные новости
            if self.news_api_key and len(filtered_news) < 3:
                try:
                    api_news = await self._search_news_api(search_word)
                    filtered_news.extend(api_news)
                except Exception as e:
                    logger.error(f"Ошибка поиска через NewsAPI: {e}")
            
            if not filtered_news:
                await update.message.reply_text(f"❌ Новости по слову '{search_word}' не найдены.")
                return
            
            await update.message.reply_text(f"✅ Найдено {len(filtered_news)} новостей:")
            
            for i, news in enumerate(filtered_news[:5], 1):  # Показываем максимум 5 результатов
                news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
                """
                
                keyboard = [[InlineKeyboardButton(f"⭐ Сохранить", callback_data=f"save_filtered_{i}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    news_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
                await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Ошибка в команде filter: {e}")
            await update.message.reply_text("❌ Произошла ошибка при поиске новостей.")
    
    async def _search_news_api(self, query: str) -> List[Dict]:
        """Поиск новостей через NewsAPI по ключевому слову."""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.news_api_key,
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 10,
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')  # Новости за последнюю неделю
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            news_list = []
            
            if data.get('status') == 'ok' and data.get('articles'):
                for article in data.get('articles', []):
                    if (article.get('title') and article.get('description') and 
                        article.get('url') and article['url'] != 'https://removed.com'):
                        news_list.append({
                            'title': article['title'],
                            'description': article['description'] or 'Описание недоступно',
                            'url': article['url'],
                            'source': article['source']['name'],
                            'category': 'поиск',
                            'published_at': article['publishedAt'],
                            'timestamp': datetime.now().isoformat()
                        })
            
            logger.info(f"Найдено {len(news_list)} новостей по запросу '{query}' через NewsAPI")
            return news_list
            
        except Exception as e:
            logger.error(f"Ошибка поиска через NewsAPI: {e}")
            return []
    
    async def category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /category."""
        try:
            if not context.args:
                categories_text = "🏷️ Доступные категории:\n\n"
                for eng, rus in self.categories.items():
                    categories_text += f"• {rus} (/{eng})\n"
                categories_text += "\nПример: /category технологии"
                await update.message.reply_text(categories_text)
                return
            
            category_input = ' '.join(context.args).lower()
            
            # Находим соответствующую английскую категорию
            category_key = None
            for eng, rus in self.categories.items():
                if rus.lower() == category_input or eng.lower() == category_input:
                    category_key = eng
                    break
            
            if not category_key:
                await update.message.reply_text(f"❌ Категория '{category_input}' не найдена.\nИспользуйте /category для просмотра доступных категорий.")
                return
            
            await update.message.reply_text(f"🔄 Загружаю новости категории '{self.categories[category_key]}'...")
            
            # Получаем новости через NewsAPI для конкретной категории
            if self.news_api_key:
                try:
                    url = f"https://newsapi.org/v2/top-headlines"
                    params = {
                        'apiKey': self.news_api_key,
                        'category': category_key,
                        'country': 'us',
                        'pageSize': 10
                    }
                    
                    response = requests.get(url, params=params, timeout=15)
                    response.raise_for_status()
                    
                    data = response.json()
                    news_list = []
                    
                    if data.get('status') == 'ok' and data.get('articles'):
                        for article in data.get('articles', []):
                            if (article.get('title') and article.get('description') and 
                                article.get('url') and article['url'] != 'https://removed.com'):
                                news_list.append({
                                    'title': article['title'],
                                    'description': article['description'] or 'Описание недоступно',
                                    'url': article['url'],
                                    'source': article['source']['name'],
                                    'category': self.categories[category_key],
                                    'published_at': article['publishedAt'],
                                    'timestamp': datetime.now().isoformat()
                                })
                    
                    if not news_list:
                        await update.message.reply_text(f"❌ Новости категории '{self.categories[category_key]}' сейчас недоступны.")
                        return
                    
                    await update.message.reply_text(f"📰 Новости категории '{self.categories[category_key]}' ({len(news_list)} шт.):")
                    
                    for i, news in enumerate(news_list[:8], 1):  # Показываем максимум 8 новостей
                        news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
                        """
                        
                        keyboard = [[InlineKeyboardButton(f"⭐ Сохранить новость #{i}", callback_data=f"save_category_{i}")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await update.message.reply_text(
                            news_text,
                            parse_mode='Markdown',
                            reply_markup=reply_markup,
                            disable_web_page_preview=True
                        )
                        
                        await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Ошибка получения новостей категории: {e}")
                    await update.message.reply_text(f"❌ Ошибка при получении новостей категории '{self.categories[category_key]}'.")
            else:
                await update.message.reply_text("❌ NewsAPI не настроен. Используйте /news для получения общих новостей.")
            
        except Exception as e:
            logger.error(f"Ошибка в команде category: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении новостей категории.")
    
    async def save_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /save."""
        try:
            if not context.args:
                await update.message.reply_text("❌ Укажите номер новости для сохранения.\nПример: /save 1")
                return
            
            try:
                news_number = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Номер новости должен быть числом.")
                return
            
            user_id = update.effective_user.id
            news_data = self._load_data(self.news_file)
            news_list = news_data.get('news', [])
            
            if news_number < 1 or news_number > len(news_list):
                await update.message.reply_text(f"❌ Новости с номером {news_number} не существует.")
                return
            
            # Загружаем данные пользователей
            users_data = self._load_data(self.users_file)
            favorites = users_data.get('favorites', {})
            
            if str(user_id) not in favorites:
                favorites[str(user_id)] = []
            
            # Проверяем, не сохранена ли уже эта новость
            news_to_save = news_list[news_number - 1]
            if any(saved['title'] == news_to_save['title'] for saved in favorites[str(user_id)]):
                await update.message.reply_text("❌ Эта новость уже сохранена в избранном.")
                return
            
            # Сохраняем новость
            favorites[str(user_id)].append(news_to_save)
            users_data['favorites'] = favorites
            self._save_data(self.users_file, users_data)
            
            await update.message.reply_text(f"✅ Новость '{news_to_save['title'][:50]}...' сохранена в избранное!")
            
        except Exception as e:
            logger.error(f"Ошибка в команде save: {e}")
            await update.message.reply_text("❌ Произошла ошибка при сохранении новости.")
    
    async def favorites_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /favorites."""
        try:
            user_id = update.effective_user.id
            logger.info(f"Пользователь {user_id} запросил избранные новости")
            
            users_data = self._load_data(self.users_file)
            logger.info(f"Загружены данные пользователей: {users_data}")
            
            favorites = users_data.get('favorites', {}).get(str(user_id), [])
            logger.info(f"Найдено избранных новостей для пользователя {user_id}: {len(favorites)}")
            
            if not favorites:
                await update.message.reply_text("❌ У вас нет сохраненных новостей.\nИспользуйте /save <номер> для сохранения новостей.")
                return
            
            await update.message.reply_text(f"❤️ Ваши избранные новости ({len(favorites)} шт.):")
            
            for i, news in enumerate(favorites, 1):
                try:
                    news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
                    """
                    
                    await update.message.reply_text(
                        news_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Ошибка при отправке новости {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Ошибка в команде favorites: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке избранных новостей.")
    
    async def daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /daily."""
        try:
            user_id = update.effective_user.id
            users_data = self._load_data(self.users_file)
            subscribers = users_data.get('subscribers', [])
            
            if user_id in subscribers:
                # Отписываемся
                subscribers.remove(user_id)
                users_data['subscribers'] = subscribers
                self._save_data(self.users_file, users_data)
                await update.message.reply_text("❌ Вы отписались от ежедневной рассылки новостей.")
            else:
                # Подписываемся
                subscribers.append(user_id)
                users_data['subscribers'] = subscribers
                self._save_data(self.users_file, users_data)
                await update.message.reply_text("✅ Вы подписались на ежедневную рассылку новостей!\nКаждое утро в 9:00 вы будете получать дайджест свежих новостей.")
            
        except Exception as e:
            logger.error(f"Ошибка в команде daily: {e}")
            await update.message.reply_text("❌ Произошла ошибка при управлении подпиской.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки."""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data.startswith('save_'):
                # Сохранение новости через кнопку
                parts = query.data.split('_')
                news_number = int(parts[1])
                user_id = update.effective_user.id
                
                # Определяем тип сохранения
                if len(parts) > 2 and parts[2] == 'filtered':
                    # Новость из поиска - пока не можем сохранить, так как нет доступа к результатам поиска
                    await query.edit_message_text(
                        query.message.text + "\n\n❌ Для сохранения новостей из поиска используйте команду /save",
                        parse_mode='Markdown'
                    )
                elif len(parts) > 2 and parts[2] == 'category':
                    # Новость из категории - пока не можем сохранить, так как нет доступа к результатам категории
                    await query.edit_message_text(
                        query.message.text + "\n\n❌ Для сохранения новостей из категории используйте команду /save",
                        parse_mode='Markdown'
                    )
                else:
                    # Обычная новость из /news
                    news_data = self._load_data(self.news_file)
                    news_list = news_data.get('news', [])
                    
                    if news_number <= len(news_list):
                        users_data = self._load_data(self.users_file)
                        favorites = users_data.get('favorites', {})
                        
                        if str(user_id) not in favorites:
                            favorites[str(user_id)] = []
                        
                        news_to_save = news_list[news_number - 1]
                        if not any(saved['title'] == news_to_save['title'] for saved in favorites[str(user_id)]):
                            favorites[str(user_id)].append(news_to_save)
                            users_data['favorites'] = favorites
                            self._save_data(self.users_file, users_data)
                            
                            await query.edit_message_text(
                                query.message.text + "\n\n✅ Новость сохранена в избранное!",
                                parse_mode='Markdown'
                            )
                        else:
                            await query.edit_message_text(
                                query.message.text + "\n\n❌ Эта новость уже в избранном!",
                                parse_mode='Markdown'
                            )
            
        except Exception as e:
            logger.error(f"Ошибка в обработчике кнопок: {e}")
            await query.edit_message_text("❌ Произошла ошибка при сохранении новости.")
    
    async def send_daily_digest(self):
        """Отправка ежедневного дайджеста подписчикам."""
        try:
            users_data = self._load_data(self.users_file)
            subscribers = users_data.get('subscribers', [])
            
            if not subscribers:
                logger.info("Нет подписчиков для ежедневной рассылки")
                return
            
            # Получаем свежие новости
            news_list = await self._update_news()
            
            if not news_list:
                logger.warning("Нет новостей для ежедневной рассылки")
                return
            
            digest_text = f"""
🌅 **Доброе утро! Ежедневный дайджест новостей**

📰 Сегодня у нас {len(news_list)} свежих новостей:

"""
            
            for i, news in enumerate(news_list[:5], 1):  # Показываем топ-5 новостей
                digest_text += f"**{i}. {news['title']}**\n"
                digest_text += f"📝 {news['description'][:100]}...\n"
                digest_text += f"🏷️ {news['category']} | 📰 {news['source']}\n"
                digest_text += f"🔗 [Читать далее]({news['url']})\n\n"
            
            digest_text += "Используйте /news для просмотра всех новостей или /favorites для избранного!"
            
            # Отправляем дайджест всем подписчикам
            for user_id in subscribers:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=digest_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    logger.info(f"Дайджест отправлен пользователю {user_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки дайджеста пользователю {user_id}: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки ежедневного дайджеста: {e}")
    
    def run(self):
        """Запуск бота."""
        try:
            # Создаем приложение
            application = Application.builder().token(self.token).build()
            
            # Добавляем обработчики команд
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("news", self.news_command))
            application.add_handler(CommandHandler("category", self.category_command))
            application.add_handler(CommandHandler("filter", self.filter_command))
            application.add_handler(CommandHandler("save", self.save_command))
            application.add_handler(CommandHandler("favorites", self.favorites_command))
            application.add_handler(CommandHandler("daily", self.daily_command))
            
            # Добавляем обработчик кнопок
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Запускаем бота
            logger.info("Запуск Telegram бота...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise
    
    async def run_async(self):
        """Асинхронный запуск бота."""
        try:
            # Создаем приложение
            application = Application.builder().token(self.token).build()
            
            # Добавляем обработчики команд
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("news", self.news_command))
            application.add_handler(CommandHandler("category", self.category_command))
            application.add_handler(CommandHandler("filter", self.filter_command))
            application.add_handler(CommandHandler("save", self.save_command))
            application.add_handler(CommandHandler("favorites", self.favorites_command))
            application.add_handler(CommandHandler("daily", self.daily_command))
            
            # Добавляем обработчик кнопок
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Запускаем бота
            logger.info("Запуск Telegram бота...")
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

def main():
    """Главная функция."""
    try:
        bot = NewsBot()
        bot.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    main()
