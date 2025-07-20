import requests
import time
import json
import os

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
    try:
        response = requests.get(base_url, params={"text": company, "per_page": 1}, timeout=10)
        response.raise_for_status()  # выбросит исключение, если код ответа не 200
        data = response.json()

        if data.get("items"):
            employer = data["items"][0]
            company_ids[company] = employer["id"]
        else:
            company_ids[company] = None  # если не нашли компанию
        print(f"{company}: {company_ids[company]}")

    except requests.RequestException as e:
        print(f"Ошибка при запросе {company}: {e}")
        company_ids[company] = None

    time.sleep(0.5)  # пауза между запросами

# ✅ Сохраняем результат в JSON
file_path = "company_ids.json"
try:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(company_ids, f, ensure_ascii=False, indent=4)
    print(f"\nСохранено в файл: {os.path.abspath(file_path)}")
except Exception as e:
    print(f"Ошибка сохранения файла: {e}")
