# 🚀 Быстрый старт

## 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 2. Настройка токенов

Скопируйте файл конфигурации:
```bash
cp env.example .env
```

Отредактируйте `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
NEWS_API_KEY=your_news_api_key_here
```

## 3. Получение токенов

### Telegram Bot Token
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

### News API Key (опционально)
1. Зарегистрируйтесь на https://newsapi.org/
2. Получите бесплатный ключ
3. Добавьте в `.env`

## 4. Запуск

```bash
# Простой запуск
python bot.py

# Запуск с планировщиком (рекомендуется)
python run_bot.py
```

## 5. Тестирование

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Попробуйте команды:
   - `/news` - свежие новости
   - `/filter ИИ` - поиск по слову
   - `/save 1` - сохранить новость
   - `/favorites` - избранное
   - `/daily` - подписка на рассылку

## 🎉 Готово!

Ваш бот работает! Проверьте логи в файле `bot.log`.

