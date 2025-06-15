import os
from dotenv import load_dotenv
from src.bd_sql.db_manager import DBManager
# Загружаем переменные окружения из .env файла
load_dotenv()

# Определяем конфигурационные переменные
DB_NAME = os.getenv("DB_NAME", "hh_vacancies")  # Значение по умолчанию "hh_vacancies"
DB_USER = os.getenv("DB_USER", "postgres")      # Значение по умолчанию "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD", "")      # Пустой пароль по умолчанию
DB_HOST = os.getenv("DB_HOST", "localhost")     # localhost по умолчанию

# Для удобства можно добавить функцию получения всех настроек
def get_db_config():
    return {
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "host": DB_HOST
    }

db = DBManager(
    dbname="hh_vacancies",
    user="postgres",
    password="1q2w3e4r5t",
    host="localhost"
)
