import argparse
import json
import os
import time
import requests
from db import DatabaseVacancyStorage

# ✅ Список компаний
COMPANIES = [
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

BASE_URL = "https://api.hh.ru/employers"
JSON_FILE = "company_ids.json"


def get_company_ids():
    """Получает ID работодателей по именам и сохраняет в JSON"""
    company_ids = {}
    for company in COMPANIES:
        try:
            response = requests.get(BASE_URL, params={"text": company, "per_page": 1}, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("items"):
                employer = data["items"][0]
                company_ids[company] = employer["id"]
            else:
                company_ids[company] = None
            print(f"{company}: {company_ids[company]}")
        except requests.RequestException as e:
            print(f"Ошибка при запросе {company}: {e}")
            company_ids[company] = None
        time.sleep(0.5)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(company_ids, f, ensure_ascii=False, indent=4)
    print(f"✅ Сохранено в {JSON_FILE}")


def save_employers_to_db():
    """Загружает работодателей по ID из JSON в БД"""
    if not os.path.exists(JSON_FILE):
        print(f"Файл {JSON_FILE} не найден! Сначала выполните --get-ids")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        company_ids = json.load(f)

    companies = [int(cid) for cid in company_ids.values() if cid]

    db = DatabaseVacancyStorage("hh_vacancies", "postgres", "1q2w3e4r5t", "127.0.0.1")

    for emp_id in companies:
        try:
            response = requests.get(f"https://api.hh.ru/employers/{emp_id}", timeout=10)
            response.raise_for_status()
            employer = response.json()
            db.add_employer(employer, source_id=1)
            print(f"✅ Добавлен: {employer.get('name')} (ID {emp_id})")
        except requests.RequestException as e:
            print(f"Ошибка при запросе ID {emp_id}: {e}")
        except Exception as db_error:
            print(f"Ошибка при добавлении работодателя {emp_id}: {db_error}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Скрипт для работы с работодателями HH")
    parser.add_argument("--get-ids", action="store_true", help="Получить ID компаний и сохранить в JSON")
    parser.add_argument("--save-employers", action="store_true", help="Сохранить работодателей в БД")

    args = parser.parse_args()

    if args.get_ids:
        get_company_ids()
    elif args.save_employers:
        save_employers_to_db()
    else:
        parser.print_help()
