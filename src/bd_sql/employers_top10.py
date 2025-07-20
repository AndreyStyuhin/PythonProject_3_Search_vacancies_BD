import requests
import json
import os
from db import DatabaseVacancyStorage

# Подключение к БД
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
        print(f"Ошибка при запросе ID {emp_id}: {e}")
        return None

# ✅ Сохраняем работодателей в БД
for emp_id in companies:
    employer = get_employer_data(emp_id)
    if employer:
        try:
            a.add_employer(employer, source_id=1)
            print(f"✅ Добавлен: {employer.get('name')} (ID {emp_id})")
        except Exception as db_error:
            print(f"Ошибка при добавлении работодателя {emp_id}: {db_error}")
    else:
        print(f"Пропущен ID {emp_id} из-за ошибки запроса")
