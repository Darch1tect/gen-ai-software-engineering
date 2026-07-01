# Transactions API

Базовий REST API для транзакцій на FastAPI з зберіганням даних в пам'яті (без бази даних).

## Структура

```
transactions_api/
├── src/
│   ├── app.py                          # Точка входу: FastAPI app, middleware, обробка помилок, підключення роутерів
│   ├── routes/
│   │   ├── transactions.py             # /transactions, /transactions/export, /transactions/{id}
│   │   └── accounts.py                 # /accounts/{accountId}/balance, /summary, /interest
│   ├── models/
│   │   └── transaction.py              # Pydantic-моделі (схеми запитів/відповідей)
│   ├── validators/
│   │   └── transaction_validator.py    # Правила валідації amount/currency/account
│   └── utils/
│       ├── storage.py                  # In-memory сховище транзакцій
│       └── rate_limiter.py             # Базовий in-memory rate limiter (per-IP)
├── tests/
│   ├── test_transactions.py
│   ├── test_filters.py
│   ├── test_export.py
│   ├── test_balance.py
│   ├── test_summary.py
│   ├── test_interest.py
│   └── test_rate_limit.py
├── demo/
│   ├── run.sh / run.bat        # Запуск застосунку одним скриптом
│   ├── sample-requests.sh      # curl-приклади для всіх ендпойнтів
│   └── sample-data.json        # Приклади транзакцій для затравки даних
├── docs/
│   └── screenshots/            # Скріншоти процесу виконання завдання
├── requirements.txt
├── .gitignore
├── HOWTORUN.md
└── README.md
```

## Демо

У `demo/` лежать готові скрипти для швидкого знайомства з API: `run.sh`/`run.bat` піднімають сервер, `sample-requests.sh` проганяє приклади запитів по всіх ендпойнтах (включно з помилковими кейсами), `sample-data.json` — приклади транзакцій для затравки. Деталі — у [HOWTORUN.md](HOWTORUN.md).

## Встановлення та запуск

```bash
cd transactions_api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

uvicorn src.app:app --reload
```

API буде доступний на `http://127.0.0.1:8000`, інтерактивна документація — на `http://127.0.0.1:8000/docs`.

## Тести

```bash
pytest -v
```

> Примітка: у поточному пісочниковому середовищі (без доступу до PyPI) встановити залежності й запустити `pytest` не вдалося. Код перевірено вручну (`py_compile` пройшов без помилок) — рекомендую прогнати тести локально перед використанням.

## Ендпойнти

| Метод | Шлях | Опис |
|---|---|---|
| POST | `/transactions` | Створити транзакцію → `201` |
| GET | `/transactions` | Список транзакцій, з опційними фільтрами → `200` |
| GET | `/transactions/export` | Експорт транзакцій у CSV, з тими ж фільтрами → `200` |
| GET | `/transactions/{id}` | Отримати транзакцію за id → `200` / `404` |
| GET | `/accounts/{accountId}/balance` | Баланс рахунку по валютах → `200` / `404` |
| GET | `/accounts/{accountId}/summary` | Зведення по транзакціях рахунку → `200` / `404` |
| GET | `/accounts/{accountId}/interest` | Прості відсотки на поточний баланс → `200` / `404` |

### Фільтрація `GET /transactions`

Усі query-параметри опційні та комбінуються через AND:

| Параметр | Приклад | Опис |
|---|---|---|
| `accountId` | `?accountId=ACC-12345` | Транзакції, де рахунок фігурує як `fromAccount` або `toAccount` |
| `type` | `?type=transfer` | `deposit` \| `withdrawal` \| `transfer` |
| `from` | `?from=2024-01-01` | Початкова дата діапазону (включно), формат `YYYY-MM-DD` |
| `to` | `?to=2024-01-31` | Кінцева дата діапазону (включно), формат `YYYY-MM-DD` |

```bash
curl "http://127.0.0.1:8000/transactions?accountId=ACC-12345&type=transfer&from=2024-01-01&to=2024-01-31"
```

Некоректні значення фільтрів (поганий формат рахунку/дати, невідомий `type`, `from` пізніше за `to`) повертають `400` у тому ж форматі `{"error", "details"}`.

### `GET /transactions/export`

Експорт транзакцій у файл. Підтримує ті самі фільтри, що й `GET /transactions` (`accountId`, `type`, `from`, `to`), тож можна експортувати, наприклад, лише трансфери одного рахунку за певний період.

```bash
curl "http://127.0.0.1:8000/transactions/export?format=csv&accountId=ACC-12345" -o transactions.csv
```

- `format` — опційний, за замовчуванням `csv`. Наразі підтримується лише `csv`; інше значення → `400`.
- Відповідь — `text/csv` з заголовком `Content-Disposition: attachment` (браузер/curl збереже як файл).
- Колонки: `id, fromAccount, toAccount, amount, currency, type, timestamp, status`. `amount` форматується з 2 знаками після коми.
- Якщо транзакцій немає (з урахуванням фільтрів) — повертається CSV лише з заголовком, `200`.

### `GET /accounts/{accountId}/summary`

Зведення по історії транзакцій рахунку:

```json
{
  "accountId": "ACC-12345",
  "totalDeposits": {"USD": 250.0},
  "totalWithdrawals": {"USD": 40.0},
  "transactionCount": 5,
  "mostRecentTransactionDate": "2024-06-15T08:30:00+00:00"
}
```

- `totalDeposits` / `totalWithdrawals` — суми по кожній валюті, рахуються лише по `completed` транзакціях. `transfer` зараховується як deposit для рахунку-отримувача (`toAccount`) і як withdrawal для рахунку-відправника (`fromAccount`) — та сама логіка напрямку, що й у `/balance`.
- `transactionCount` — кількість усіх транзакцій, де рахунок фігурує як `fromAccount` або `toAccount` (незалежно від статусу).
- `mostRecentTransactionDate` — timestamp найновішої з цих транзакцій.
- Помилки: `400` — невалідний формат `accountId`; `404` — рахунок жодного разу не зустрічався в транзакціях.

### `GET /accounts/{accountId}/interest`

Прості відсотки на поточний баланс рахунку (`principal` обчислюється так само, як у `/balance`):

```
GET /accounts/ACC-12345/interest?rate=0.05&days=30
```

```json
{
  "accountId": "ACC-12345",
  "rate": 0.05,
  "days": 30,
  "principal": {"USD": 1000.0},
  "interest": {"USD": 4.11},
  "totalAmount": {"USD": 1004.11}
}
```

- Формула (по кожній валюті окремо): `interest = principal * rate * (days / 365)`, `totalAmount = principal + interest`. Рік умовно прийнято за 365 днів.
- `rate` — обов'язковий, десятковий дріб (`0.05` = 5% річних), не може бути від'ємним.
- `days` — обов'язковий, кількість днів, не може бути від'ємним.
- Помилки: `400` — від'ємні `rate`/`days`, відсутні query-параметри, або невалідний формат `accountId`; `404` — рахунок не знайдено.

### Приклад створення транзакції

```bash
curl -X POST http://127.0.0.1:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount": "ACC-00001", "amount": 100, "currency": "USD", "type": "deposit"}'
```

## Валідація

- **Amount**: повинна бути додатнім числом (`> 0`) і мати не більше 2 знаків після коми. `-5`, `0` і `10.999` відхиляються.
- **Account (`fromAccount`/`toAccount`)**: формат `ACC-XXXXX`, де `X` — будь-який алфавітно-цифровий символ (рівно 5 штук), наприклад `ACC-00001`, `ACC-AbC12`. Те саме правило діє і для `:accountId` у `/accounts/{accountId}/balance`.
- **Currency**: 3-літерний код, що входить до переліку дійсних кодів ISO 4217 (USD, EUR, GBP, JPY, UAH тощо — повний перелік у `src/validators/transaction_validator.py`). Регістр нормалізується (`usd` → `USD`).
- **Залежність полів від типу**: `deposit` вимагає `toAccount`, `withdrawal` — `fromAccount`, `transfer` — обидва (і вони мають відрізнятись).

### Формат помилки валідації (`400`)

Усі помилки з одного запиту повертаються разом, кожна — з назвою поля та повідомленням:

```json
{
  "error": "Validation failed",
  "details": [
    {"field": "amount", "message": "Amount must be a positive number"},
    {"field": "currency", "message": "Invalid currency code"}
  ]
}
```

## Rate limiting

Базовий ліміт запитів: **максимум 100 запитів за хвилину на один IP**, застосовується глобально до всіх ендпойнтів.

- Реалізація — fixed-window лічильник в пам'яті процесу (`src/utils/rate_limiter.py`), без зовнішніх залежностей (Redis тощо). Лічильник скидається через 60 секунд від першого запиту у вікні.
- IP визначається з `request.client.host` (підходить для прямого підключення; за реверс-проксі знадобиться враховувати `X-Forwarded-For`).
- Кожна успішна відповідь містить заголовки `X-RateLimit-Limit` і `X-RateLimit-Remaining`.
- При перевищенні ліміту — `429 Too Many Requests` із заголовком `Retry-After` (секунди до скидання вікна) і тілом:

```json
{
  "error": "Too Many Requests",
  "details": [
    {"field": "general", "message": "Rate limit exceeded: max 100 requests per 60 seconds. Try again later."}
  ]
}
```

> Обмеження: стан зберігається лише в пам'яті одного процесу — не переживає перезапуск і не синхронізується між кількома воркерами/інстансами. Для продакшн-навантаження зі скейлінгом знадобиться спільне сховище (наприклад, Redis) замість словника в пам'яті.

## Ключові рішення

- **Статус**: нові транзакції одразу отримують статус `completed` (немає асинхронної обробки в цій базовій реалізації).
- **Баланс рахунку**: рахується "на льоту" з усіх `completed` транзакцій, окремо по кожній валюті (`{"USD": 100, "EUR": 50}`), бо змішувати суми різних валют в одне число некоректно. Якщо рахунок жодного разу не згадувався в транзакціях — `404`; якщо формат `accountId` некоректний — `400`.
- **Коди помилок**: `400` — некоректні дані (валідація, формат), `404` — транзакцію/рахунок не знайдено. Стандартні FastAPI `422` для помилок валідації переозначені на `400` зі структурованим тілом `{"error", "details"}` через кастомний exception handler.
