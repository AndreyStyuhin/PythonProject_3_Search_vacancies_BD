import json
import os
import time
import requests
from src.bd_sql.db import DatabaseVacancyStorage

# --- Константы ---
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


# --- Базовые функции работы с БД ---
def get_db():
    return DatabaseVacancyStorage("hh_vacancies", "postgres", "1q2w3e4r5t", "127.0.0.1")


# --- HH API методы ---
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
        time.sleep(1)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(company_ids, f, ensure_ascii=False, indent=4)
    print(f"✅ Сохранено в {JSON_FILE}")


def save_employers_to_db():
    """Загружает работодателей по ID из JSON в БД"""
    if not os.path.exists(JSON_FILE):
        print(f"Файл {JSON_FILE} не найден! Сначала выполните пункт 6 (получение ID работодателей).")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        company_ids = json.load(f)

    companies = [int(cid) for cid in company_ids.values() if cid]
    db = get_db()

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


# --- Отчеты из БД ---
def show_companies_and_counts():
    db = get_db()
    data = db.get_companies_and_vacancies_count()
    print("\nКомпании и количество вакансий:")
    for company, count in data:
        print(f"{company}: {count}")


def show_all_vacancies():
    db = get_db()
    vacancies = db.get_all_vacancies()
    for v in vacancies:
        print(f"{v[0]} | {v[1]} | {v[2]}-{v[3]} {v[4]}")


def show_avg_salary():
    db = get_db()
    avg = db.get_avg_salary()
    print(f"\nСредняя зарплата: {avg if avg else 'Нет данных'}")


def show_vacancies_above_avg():
    db = get_db()
    vacancies = db.get_vacancies_with_higher_salary()
    for v in vacancies:
        print(f"{v[0]} | {v[1]} | {v[2]}-{v[3]} {v[4]}")


def show_vacancies_by_keyword():
    keyword = input("Введите ключевое слово: ")
    db = get_db()
    vacancies = db.get_vacancies_with_keyword(keyword)
    for v in vacancies:
        print(f"{v[0]} | {v[1]} | {v[2]}-{v[3]} {v[4]}")


# --- Главное меню ---
def _display_menu():
    print("\nМеню:")
    print("1. Показать компании и количество их вакансий")
    print("2. Показать все вакансии")
    print("3. Показать среднюю зарплату по всем вакансиям")
    print("4. Показать вакансии с зарплатой выше средней")
    print("5. Найти вакансии по ключевому слову")
    print("6. Получить ID работодателей и сохранить в JSON")
    print("7. Загрузить работодателей в БД")
    print("8. Выход")


def main():
    while True:
        _display_menu()
        choice = input("Выберите действие (1-8): ")

        if choice == "1":
            show_companies_and_counts()
        elif choice == "2":
            show_all_vacancies()
        elif choice == "3":
            show_avg_salary()
        elif choice == "4":
            show_vacancies_above_avg()
        elif choice == "5":
            show_vacancies_by_keyword()
        elif choice == "6":
            get_company_ids()
        elif choice == "7":
            save_employers_to_db()
        elif choice == "8":
            print("Выход...")
            break
        else:
            print("Неверный выбор. Пожалуйста, введите число от 1 до 8.")


if __name__ == "__main__":
    main()
