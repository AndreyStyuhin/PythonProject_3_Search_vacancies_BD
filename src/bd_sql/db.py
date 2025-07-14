from typing import List, Optional
import psycopg2
from psycopg2 import sql
from src.models.vacancy import Vacancy


class DatabaseVacancyStorage:
    """Класс для работы с вакансиями в PostgreSQL"""

    def __init__(self, db_name: str, user: str, password: str, host: str = "localhost"):
        self.conn_params = {
            "dbname": db_name,
            "user": user,
            "password": password,
            "host": host
        }
        self._ensure_tables_exist()

    def _connect(self):
        """Устанавливает соединение с БД"""
        return psycopg2.connect(**self.conn_params)

    def _ensure_tables_exist(self):
        """Создает необходимые таблицы с правильными ограничениями"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                # Таблица работодателей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS employers (
                        id SERIAL PRIMARY KEY,
                        hh_id VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        CONSTRAINT unique_employer UNIQUE(hh_id)
                    )
                """)

                # Таблица вакансий с явным указанием UNIQUE для link
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vacancies (
                        id SERIAL PRIMARY KEY,
                        hh_id VARCHAR(50) UNIQUE NOT NULL,
                        employer_id INTEGER REFERENCES employers(id),
                        title VARCHAR(255) NOT NULL,
                        link VARCHAR(255) UNIQUE NOT NULL,
                        salary_from INTEGER,
                        salary_to INTEGER,
                        currency VARCHAR(10),
                        description TEXT,
                        requirements TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT unique_vacancy UNIQUE(link, hh_id)
                    )
                """)
                conn.commit()

    def add_vacancy(self, vacancy: Vacancy):
        """Добавляет вакансию в БД с проверкой уникальности"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                # Получаем данные о зарплате
                salary_from = vacancy.salary.get('from') if vacancy.salary else None
                salary_to = vacancy.salary.get('to') if vacancy.salary else None
                currency = vacancy.salary.get('currency') if vacancy.salary else None

                try:
                    # Вставляем или обновляем вакансию
                    cursor.execute("""
                        INSERT INTO vacancies (
                            hh_id, title, link, salary_from, salary_to, 
                            currency, description, requirements
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (hh_id)
                        DO UPDATE SET
                            title = EXCLUDED.title,
                            link = EXCLUDED.link,
                            salary_from = EXCLUDED.salary_from,
                            salary_to = EXCLUDED.salary_to,
                            currency = EXCLUDED.currency,
                            description = EXCLUDED.description,
                            requirements = EXCLUDED.requirements
                    """, (
                        vacancy.hh_id,
                        vacancy.title,
                        vacancy.link,
                        salary_from,
                        salary_to,
                        currency,
                        vacancy.description,
                        vacancy.requirements
                    ))

                    conn.commit()
                except psycopg2.Error as e:
                    conn.rollback()
                    raise Exception(f"Ошибка при добавлении вакансии: {e}")

    def get_vacancies(self, keyword: Optional[str] = None, top_n: Optional[int] = None) -> List[Vacancy]:
        """Получает вакансии из БД с возможностью фильтрации"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                query = "SELECT title, link, salary_from, salary_to, currency, description, requirements FROM vacancies"
                params = []

                if keyword:
                    query += " WHERE description LIKE %s OR requirements LIKE %s"
                    params.extend([f"%{keyword}%", f"%{keyword}%"])

                query += " ORDER BY COALESCE(salary_from, 0) DESC"

                if top_n:
                    query += " LIMIT %s"
                    params.append(top_n)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                vacancies = []
                for row in rows:
                    salary = None
                    if row[2] or row[3]:  # Если есть salary_from или salary_to
                        salary = {
                            "from": row[2],
                            "to": row[3],
                            "currency": row[4]
                        }

                    vacancy = Vacancy(
                        title=row[0],
                        link=row[1],
                        salary=salary,
                        description=row[5],
                        requirements=row[6]
                    )
                    vacancies.append(vacancy)

                return vacancies

    def clear_vacancies(self):
        """Очищает таблицу вакансий"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE vacancies")
                conn.commit()