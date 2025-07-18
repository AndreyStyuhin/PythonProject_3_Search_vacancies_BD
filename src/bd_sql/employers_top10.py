import requests
import time  # импортируем модуль time
from db import DatabaseVacancyStorage
a = DatabaseVacancyStorage("hh_vacancies", "postgres", "1q2w3e4r5t", "127.0.0.1")

# companies = [
#     "Альфа-Банк",
#     "ВТБ",
#    "X5 Group",
#    "Газпромбанк",
#    "Газпром нефть",
#    "Яндекс",
#     "Ozon",
#     "Аэрофлот",
#     "МТС",
#     "Сбер",
#     "Иви",
#     "AGIMA",
#     "RealWeb"
# ]
companies = [9694561, 2180]

def get_employer_date (id):
    base_url = f"https://api.hh.ru/employers/{id}"
    response = requests.get(base_url)
    return response.json()

for e in companies:
    employer = get_employer_date(e)
    a.add_employer(employer, 1)

# company_ids = {}
#
# for company in companies:
#     response = requests.get(base_url, params={"text": company, "per_page": 1})
#     data = response.json()
#
#     if data.get("items"):
#         employer = data["items"][0]
#         company_ids[company] = employer["id"]
#     else:
#         company_ids[company] = None
#
#     # Пауза в 0.5 секунды
#     time.sleep(0.5)

# print(company_ids)
