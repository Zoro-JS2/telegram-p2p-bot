# P2P Telegram Bot v2

## Функции

- 📥 Покупка и 📤 продажа криптовалюты (USDT)
- 📄 Просмотр всех заявок
- ⏱ Автоудаление заявок через 24 часа
- 💱 Получение курса USDT/UAH с Binance
- 🔔 Уведомления при нужном курсе (alert)

## Команды

- `/buy USDT 1000 Monobank 38.5`
- `/sell USDT 500 PrivatBank 39.2`
- `/orders`
- `/alert USDT Monobank 38.9`
- `/rate`

## Установка

```bash
pip install -r requirements.txt
python bot.py
```

Не забудь вставить свой токен в `config.py`.