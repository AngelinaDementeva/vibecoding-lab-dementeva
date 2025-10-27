# 🚀 Инструкция по деплою News Bot

## Подготовка к деплою

### 1. Проверка готовности

✅ **Код проверен и работает локально**
✅ **NewsAPI интегрирован с токеном**
✅ **Обработка ошибок настроена**
✅ **Логирование добавлено**
✅ **Файлы подготовлены:**
- `.gitignore` - исключения для Git
- `requirements.txt` - зависимости
- `webhook_bot.py` - webhook версия
- `deploy_ngrok.py` - скрипт деплоя
- `collect_feedback.py` - сбор обратной связи

## 🎯 Вариант деплоя: ngrok (локальный)

### Шаг 1: Установка ngrok

```bash
# Для macOS с Homebrew
brew install ngrok/ngrok/ngrok

# Или скачайте с https://ngrok.com/download
```

### Шаг 2: Регистрация и получение токена

1. Перейдите на [ngrok.com](https://ngrok.com)
2. Зарегистрируйтесь (бесплатно)
3. Получите auth token в [Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)

### Шаг 3: Настройка ngrok

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### Шаг 4: Запуск деплоя

```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите webhook версию бота
python3 webhook_bot.py

# В другом терминале запустите ngrok
python3 deploy_ngrok.py
```

### Шаг 5: Проверка работы

1. Скопируйте URL из ngrok (например: `https://abc123.ngrok.io`)
2. Откройте в браузере: `https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://abc123.ngrok.io/webhook`
3. Проверьте статус: `https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo`

## 📊 Мониторинг и статистика

### Health Check
```
GET https://your-ngrok-url.ngrok.io/health
```

### Статистика
```
GET https://your-ngrok-url.ngrok.io/stats
```

### Логи
```bash
tail -f bot.log
```

## 📝 Сбор обратной связи

### Запуск сбора фидбека
```bash
python3 collect_feedback.py
```

### Вопросы для пользователей

1. **Оценка бота (1-5)**
2. **Что понравилось?**
   - Реальные новости
   - Поиск по ключевым словам
   - Категории новостей
   - Сохранение в избранное
   - Интерфейс

3. **Что не понравилось?**
   - Медленная работа
   - Ошибки
   - Сложный интерфейс
   - Мало функций

4. **Предложения по улучшению**
   - Новые функции
   - Улучшения интерфейса
   - Дополнительные источники

## 🔧 Устранение проблем

### Проблема: Webhook не работает
```bash
# Проверьте статус webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Удалите webhook
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"

# Установите заново
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-url.ngrok.io/webhook"
```

### Проблема: ngrok URL изменился
- ngrok URL меняется при каждом перезапуске
- Нужно обновить webhook каждый раз
- Для продакшена используйте статический домен

### Проблема: Бот не отвечает
```bash
# Проверьте логи
tail -f bot.log

# Проверьте статус
curl https://your-ngrok-url.ngrok.io/health
```

## 📈 Анализ результатов

### Метрики для отслеживания

1. **Использование команд:**
   - `/news` - популярность новостей
   - `/category` - предпочитаемые категории
   - `/filter` - популярные поисковые запросы
   - `/favorites` - использование избранного

2. **Пользовательская активность:**
   - Количество уникальных пользователей
   - Частота использования
   - Время сессий

3. **Технические метрики:**
   - Время ответа API
   - Количество ошибок
   - Доступность сервиса

### Отчет по обратной связи

```bash
python3 collect_feedback.py
# Выберите опцию 3 для генерации отчета
```

## 🎉 Следующие шаги

После сбора обратной связи:

1. **Анализ фидбека** - выделите главные проблемы
2. **Приоритизация** - определите что исправлять в первую очередь
3. **Улучшения** - внесите изменения в код
4. **Тестирование** - проверьте улучшения
5. **Новый деплой** - обновите версию
6. **Повторный сбор фидбека** - убедитесь что проблемы решены

## ⚠️ Важные замечания

- **ngrok бесплатный план:** ограниченное количество туннелей
- **URL меняется:** при каждом перезапуске ngrok
- **Требует интернет:** ваш компьютер должен быть онлайн
- **Для продакшена:** используйте VPS или облачные сервисы

## 🔗 Полезные ссылки

- [ngrok Documentation](https://ngrok.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [NewsAPI Documentation](https://newsapi.org/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Удачи с деплоем! 🚀**
