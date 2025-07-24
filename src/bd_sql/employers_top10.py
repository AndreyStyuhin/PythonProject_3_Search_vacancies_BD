import requests
import json
import os
from db import DatabaseVacancyStorage
from src.models.vacancy import Vacancy
import time

# ✅ Подключение к БД
a = DatabaseVacancyStorage("hh_vacancies", "postgres", "1q2w3e4r5t", "127.0.0.1")

# ✅ Загружаем IDs компаний из JSON
file_path = "company_ids.json"
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Файл {file_path} не найден. Сначала запусти get_employers_id.py")

with open(file_path, "r", encoding="utf-8") as f:
    company_ids = json.load(f)

companies = [int(cid) for cid in company_ids.values() if cid is not None]

def get_employer_data(emp_id):
    """Запрашивает данные о работодателе по ID"""
    try:
        response = requests.get(f"https://api.hh.ru/employers/{emp_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Ошибка при запросе ID {emp_id}: {e}")
        return None

def get_vacancies_for_employer(emp_id):
    """Получает все вакансии работодателя по API HH"""
    vacancies = []
    page = 0
    while True:
        try:
            response = requests.get(
                "https://api.hh.ru/vacancies",
                params={"employer_id": emp_id, "page": page, "per_page": 100},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                vacancy = Vacancy(
                    hh_id=item.get("id"),
                    title=item.get("name"),
                    link=item.get("alternate_url"),
                    salary=item.get("salary"),
                    description=item.get("snippet", {}).get("responsibility"),
                    requirements=item.get("snippet", {}).get("requirement")
                )
                vacancies.append(vacancy)

            if page >= data.get("pages", 1) - 1:
                break
            page += 1
            time.sleep(0.3)  # Пауза, чтобы не попасть под блокировку API

        except requests.RequestException as e:
            print(f"❌ Ошибка при загрузке вакансий для {emp_id}: {e}")
            break

    return vacancies

# ✅ Основной цикл: работодатели + вакансии
total_employers = 0
total_vacancies = 0

for emp_id in companies:
    employer = get_employer_data(emp_id)
    if employer:
        try:
            a.add_employer(employer, source_id=1)
            total_employers += 1
            print(f"✅ Работодатель добавлен: {employer.get('name')} (ID {emp_id})")

            # Загружаем вакансии
            vacancies = get_vacancies_for_employer(emp_id)
            print(f"   Найдено вакансий: {len(vacancies)}")
            for vac in vacancies:
                try:
                    a.add_vacancy(vac)
                    total_vacancies += 1
                except Exception as e:
                    print(f"   ❌ Ошибка добавления вакансии {vac.title}: {e}")

        except Exception as db_error:
            print(f"❌ Ошибка при добавлении работодателя {emp_id}: {db_error}")
    else:
        print(f"Пропущен ID {emp_id} из-за ошибки запроса")

print(f"\n✅ Всего работодателей добавлено: {total_employers}")
print(f"✅ Всего вакансий добавлено: {total_vacancies}")
