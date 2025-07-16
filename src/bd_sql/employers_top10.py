import requests
import time  # импортируем модуль time

companies = [
    "Альфа-Банк",
    "ВТБ",
    "X5 Group",
    "Газпромбанк",
    "Газпром нефть",
    "Яндекс",
    "Ozon",
    "Аэрофлот",
    "МТС",
    "Сбер",
    "Иви",
    "AGIMA",
    "RealWeb"
]

base_url = "https://api.hh.ru/employers"
company_ids = {}

for company in companies:
    response = requests.get(base_url, params={"text": company, "per_page": 1})
    data = response.json()

    if data.get("items"):
        employer = data["items"][0]
        company_ids[company] = employer["id"]
    else:
        company_ids[company] = None

    # Пауза в 0.5 секунды
    time.sleep(0.5)

print(company_ids)
