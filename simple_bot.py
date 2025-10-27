#!/usr/bin/env python3
"""
Упрощенный Telegram-бот для новостей
"""

import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleNewsBot:
    """Упрощенный бот для новостей."""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        
        self.data_dir = 'data'
        self.news_file = os.path.join(self.data_dir, 'news.json')
        self.users_file = os.path.join(self.data_dir, 'users.json')
    
    def _load_data(self, file_path: str):
        """Загрузка данных из JSON файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка загрузки данных из {file_path}: {e}")
            return {}
    
    def _save_data(self, file_path: str, data):
        """Сохранение данных в JSON файл."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных в {file_path}: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        user = update.effective_user
        welcome_text = f"""
Привет, {user.first_name}! 👋

Я бот для новостей. Вот что я умею:

📰 /news - Показать свежие новости
🔍 /filter <слово> - Найти новости по ключевому слову
⭐ /save <номер> - Сохранить новость в избранное
❤️ /favorites - Показать избранные новости
📬 /daily - Подписаться на ежедневную рассылку
❓ /help - Показать справку

Начнем с команды /news для просмотра свежих новостей!
        """
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help."""
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
        await update.message.reply_text(help_text)
    
    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /news."""
        try:
            await update.message.reply_text("🔄 Загружаю свежие новости...")
            
            # Загружаем новости из файла
            news_data = self._load_data(self.news_file)
            news_list = news_data.get('news', [])
            
            if not news_list:
                await update.message.reply_text("❌ К сожалению, новости сейчас недоступны. Попробуйте позже.")
                return
            
            await update.message.reply_text(f"✅ Вот {len(news_list)} свежих новостей:")
            
            # Отправляем новости порциями
            for i, news in enumerate(news_list, 1):
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
            
            news_data = self._load_data(self.news_file)
            news_list = news_data.get('news', [])
            
            filtered_news = []
            for news in news_list:
                if (search_word in news.get('title', '').lower() or 
                    search_word in news.get('description', '').lower()):
                    filtered_news.append(news)
            
            if not filtered_news:
                await update.message.reply_text(f"❌ Новости по слову '{search_word}' не найдены.")
                return
            
            await update.message.reply_text(f"✅ Найдено {len(filtered_news)} новостей:")
            
            for i, news in enumerate(filtered_news, 1):
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
            favorites = users_data.get('favorites', {}).get(str(user_id), [])
            
            if not favorites:
                await update.message.reply_text("❌ У вас нет сохраненных новостей.\nИспользуйте /save <номер> для сохранения новостей.")
                return
            
            await update.message.reply_text(f"❤️ Ваши избранные новости ({len(favorites)} шт.):")
            
            for i, news in enumerate(favorites, 1):
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
                news_number = int(query.data.split('_')[1])
                user_id = update.effective_user.id
                
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
    
    def run(self):
        """Запуск бота."""
        try:
            # Создаем приложение
            application = Application.builder().token(self.token).build()
            
            # Добавляем обработчики команд
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("news", self.news_command))
            application.add_handler(CommandHandler("filter", self.filter_command))
            application.add_handler(CommandHandler("save", self.save_command))
            application.add_handler(CommandHandler("favorites", self.favorites_command))
            application.add_handler(CommandHandler("daily", self.daily_command))
            
            # Добавляем обработчик кнопок
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Запускаем бота
            logger.info("Запуск упрощенного Telegram бота...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

def main():
    """Главная функция."""
    try:
        bot = SimpleNewsBot()
        bot.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    import asyncio
    main()

