Telegram Reminder Bot (готовый для Render)

Содержимое архива:
- main.py         — основной код бота
- requirements.txt — зависимости

Инструкция по деплою на Render:
1) Залогинься на https://render.com и создай новый Web Service.
2) Подключи репозиторий (заливаем этот проект на GitHub и подключаем).
3) В настройках Render укажи:
   - Environment: Python 3
   - Build command: pip install -r requirements.txt
   - Start command: python main.py
4) В разделе Environment > Environment Variables добавь:
   TOKEN = <твой_токен_от_BotFather>
   (опционально) BOT_NAME = tvoyanapominalka_bot

5) Нажми Deploy. Бот начнёт работать в облаке — он будет принимать команды из Telegram и сохранять напоминания в SQLite.

Примечания:
- База reminders.db будет сохраняться в файловой системе контейнера Render. На бесплатных планах контейнеры иногда пересоздаются — если хочется устойчивого хранения,
  используй внешнюю БД (Postgres) или сохраняй бэкапы. Для простых задач SQLite обычно хватает.
- Если возникнут проблемы — отправь лог ошибок, помогу разобраться.