import psycopg2
from psycopg2 import sql
from typing import List, Optional
from src.models.vacancy import Vacancy


class DatabaseVacancyStorage:
    """Класс для работы с PostgreSQL: вакансии и работодатели"""

    def __init__(self, db_name: str, user: str, password: str, host: str = "localhost"):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.conn_params = {
            "dbname": db_name,
            "user": user,
            "password": password,
            "host": host
        }
        self._create_db_if_not_exists()
        self._ensure_tables_exist()

    def _create_db_if_not_exists(self):
        """Создает базу данных, если она отсутствует"""
        try:
            conn = psycopg2.connect(**self.conn_params)
            conn.close()
            print(f"✅ База '{self.db_name}' существует.")
        except psycopg2.OperationalError:
            print(f"⚠ База '{self.db_name}' не найдена. Создаю...")
            conn = psycopg2.connect(dbname="postgres", user=self.user, password=self.password, host=self.host)
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name)))
            conn.close()
            print(f"✅ База '{self.db_name}' создана.")

    def _connect(self):
        return psycopg2.connect(**self.conn_params)

    def _ensure_tables_exist(self):
        """Создает таблицы и добавляет недостающие колонки"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                # Таблица вакансий
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vacancies (
                        id SERIAL PRIMARY KEY,
                        hh_id VARCHAR(50) UNIQUE,
                        title VARCHAR(255) NOT NULL,
                        link VARCHAR(255) NOT NULL,
                        salary_from INTEGER,
                        salary_to INTEGER,
                        currency VARCHAR(10),
                        description TEXT,
                        requirements TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Таблица работодателей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS employers (
                        id SERIAL PRIMARY KEY,
                        hh_id VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Добавляем колонку source_id, если её нет
                cursor.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='employers' AND column_name='source_id'
                        ) THEN
                            ALTER TABLE employers ADD COLUMN source_id INTEGER NOT NULL DEFAULT 1;
                        END IF;
                    END
                    $$;
                """)
                conn.commit()

    # ------------------- Методы для работы с данными -------------------

    def add_employer(self, employer: dict, source_id: int):
        """Добавляет работодателя в БД"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                hh_id = employer.get("id")
                name = employer.get("name")
                if not hh_id or not name:
                    print("Пропущен работодатель: нет hh_id или name")
                    return
                cursor.execute("""
                    INSERT INTO employers (hh_id, name, source_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (hh_id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        source_id = EXCLUDED.source_id
                """, (hh_id, name, source_id))
            conn.commit()

    def add_vacancy(self, vacancy: Vacancy):
        """Добавляет вакансию в БД"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                salary_from = vacancy.salary.get('from') if vacancy.salary else None
                salary_to = vacancy.salary.get('to') if vacancy.salary else None
                currency = vacancy.salary.get('currency') if vacancy.salary else None
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

    # ------------------- Методы для отчетов -------------------

    def get_companies_and_vacancies_count(self):
        """Компании и количество вакансий"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT e.name, COUNT(v.id)
                    FROM employers e
                    LEFT JOIN vacancies v ON e.hh_id = v.hh_id
                    GROUP BY e.name
                    ORDER BY COUNT(v.id) DESC
                """)
                return cursor.fetchall()

    def get_all_vacancies(self):
        """Все вакансии"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT title, link, salary_from, salary_to, currency, description, requirements
                    FROM vacancies
                    ORDER BY created_at DESC
                """)
                return cursor.fetchall()

    def get_avg_salary(self):
        """Средняя зарплата"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT AVG((COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2.0)
                    FROM vacancies
                    WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
                """)
                result = cursor.fetchone()
                return round(result[0], 2) if result and result[0] else None

    def get_vacancies_with_higher_salary(self):
        """Вакансии с зарплатой выше средней"""
        avg_salary = self.get_avg_salary()
        if not avg_salary:
            return []
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT title, link, salary_from, salary_to, currency, description, requirements
                    FROM vacancies
                    WHERE (COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2.0 > %s
                    ORDER BY (COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2.0 DESC
                """, (avg_salary,))
                return cursor.fetchall()

    def get_vacancies_with_keyword(self, keyword: str):
        """Вакансии по ключевому слову"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT title, link, salary_from, salary_to, currency, description, requirements
                    FROM vacancies
                    WHERE description ILIKE %s OR requirements ILIKE %s
                """, (f"%{keyword}%", f"%{keyword}%"))
                return cursor.fetchall()
