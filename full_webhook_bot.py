#!/usr/bin/env python3
"""
Полнофункциональный webhook бот с NewsAPI
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

# Создаем Flask приложение
app = Flask(__name__)

# Глобальная переменная для бота
bot_instance = None
application = None

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
                    'pageSize': 3
                }
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                if data.get('status') == 'ok' and data.get('articles'):
                    for article in data.get('articles', []):
                        if article.get('title') and article.get('description') and article.get('url'):
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
                                    
                                    if len(news_list) >= 15:
                                        break
                except Exception as e:
                    logger.error(f"Ошибка получения общих новостей: {e}")
                
        except requests.RequestException as e:
            logger.error(f"Ошибка получения новостей: {e}")
            return self._get_test_news()
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении новостей: {e}")
            return self._get_test_news()
        
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
            }
        ]
    
    async def _update_news(self):
        """Обновление новостей."""
        try:
            news_data = self._load_data(self.news_file)
            current_time = datetime.now()
            
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
        
        if should_send_feedback:
            await self._send_feedback_form(update)
    
    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /news."""
        try:
            user = update.effective_user
            log_user_action(user.id, "news_command")
            
            should_send_feedback = self._update_user_stats(user.id, "news")
            
            await update.message.reply_text("🔄 Загружаю свежие новости...")
            
            news_list = await self._update_news()
            
            if not news_list:
                await update.message.reply_text("❌ К сожалению, новости сейчас недоступны. Попробуйте позже.")
                return
            
            for i, news in enumerate(news_list[:10], 1):
                news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
                """
                
                keyboard = [[InlineKeyboardButton(f"⭐ Сохранить новость #{i}", callback_data=f"save_{i}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    news_text, 
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
                await asyncio.sleep(0.5)
            
            await update.message.reply_text("✅ Вот все доступные новости! Используйте /save <номер> для сохранения.")
            
            if should_send_feedback:
                await self._send_feedback_form(update)
            
        except Exception as e:
            logger.error(f"Ошибка в команде news: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке новостей.")

async def init_bot():
    """Инициализация бота."""
    global bot_instance, application
    
    try:
        bot_instance = NewsBot()
        
        application = Application.builder().token(bot_instance.token).build()
        
        application.add_handler(CommandHandler("start", bot_instance.start_command))
        application.add_handler(CommandHandler("news", bot_instance.news_command))
        
        # Инициализируем приложение
        await application.initialize()
        
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
        
        update_data = request.get_json()
        
        if update_data:
            update = Update.de_json(update_data, application.bot)
            
            # Обрабатываем обновление асинхронно
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(application.process_update(update))
            finally:
                loop.close()
            
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

def main():
    """Запуск webhook сервера."""
    print("🚀 Запуск полнофункционального News Bot с webhook...")
    
    # Инициализируем бота асинхронно
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(init_bot())
        if not success:
            print("❌ Не удалось инициализировать бота")
            return
        
        print("✅ Бот готов к работе")
        print("🌐 Webhook endpoint: /webhook")
        print("📊 Health check: /health")
        
        # Запускаем Flask сервер
        app.run(host='0.0.0.0', port=8000, debug=False)
        
    finally:
        loop.close()

if __name__ == '__main__':
    main()
