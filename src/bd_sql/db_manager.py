import psycopg2
from psycopg2 import sql
from typing import List, Dict, Optional


class DBManager:
    """Класс для управления взаимодействием с базой данных PostgreSQL"""

    def __init__(self, dbname: str, user: str, password: str, host: str = "localhost"):
        """
        Инициализация подключения к базе данных

        :param dbname: имя базы данных
        :param user: имя пользователя
        :param password: пароль
        :param host: хост (по умолчанию localhost)
        """
        self.conn_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host
        }

    def _get_connection(self):
        """Устанавливает соединение с базой данных"""
        return psycopg2.connect(**self.conn_params)

    def get_companies_and_vacancies_count(self) -> List[Dict[str, int]]:
        """
        Получает список всех компаний и количество вакансий у каждой компании

        :return: список словарей {'company': название компании, 'count': количество вакансий}
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT employer_name, COUNT(*) as vacancy_count 
                    FROM vacancies 
                    GROUP BY employer_name
                    ORDER BY vacancy_count DESC
                """)
                result = []
                for row in cursor.fetchall():
                    result.append({
                        'company': row[0],
                        'count': row[1]
                    })
                return result

    def get_all_vacancies(self) -> List[Dict]:
        """
        Получает список всех вакансий с указанием компании, названия, зарплаты и ссылки

        :return: список словарей с информацией о вакансиях
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        employer_name, 
                        title, 
                        salary_from, 
                        salary_to, 
                        currency, 
                        link 
                    FROM vacancies
                    ORDER BY COALESCE(salary_from, 0) DESC
                """)
                result = []
                for row in cursor.fetchall():
                    salary = None
                    if row[2] or row[3]:  # Если указана хотя бы одна часть зарплаты
                        salary = f"{row[2] or ''}-{row[3] or ''} {row[4] or ''}".strip()

                    result.append({
                        'company': row[0],
                        'title': row[1],
                        'salary': salary,
                        'link': row[5]
                    })
                return result

    def get_avg_salary(self) -> float:
        """
        Рассчитывает среднюю зарплату по вакансиям

        :return: средняя зарплата (по нижней границе вилки)
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT AVG(salary_from) 
                    FROM vacancies 
                    WHERE salary_from IS NOT NULL
                """)
                return round(float(cursor.fetchone()[0]), 2)

    def get_vacancies_with_higher_salary(self) -> List[Dict]:
        """
        Получает список вакансий с зарплатой выше средней

        :return: список словарей с вакансиями
        """
        avg_salary = self.get_avg_salary()
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        employer_name, 
                        title, 
                        salary_from, 
                        salary_to, 
                        currency, 
                        link 
                    FROM vacancies
                    WHERE salary_from > %s
                    ORDER BY salary_from DESC
                """, (avg_salary,))

                result = []
                for row in cursor.fetchall():
                    salary = f"{row[2] or ''}-{row[3] or ''} {row[4] or ''}".strip()
                    result.append({
                        'company': row[0],
                        'title': row[1],
                        'salary': salary,
                        'link': row[5]
                    })
                return result

    def get_vacancies_with_keyword(self, keyword: str) -> List[Dict]:
        """
        Ищет вакансии по ключевому слову в названии

        :param keyword: ключевое слово для поиска
        :return: список найденных вакансий
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        employer_name, 
                        title, 
                        salary_from, 
                        salary_to, 
                        currency, 
                        link 
                    FROM vacancies
                    WHERE title ILIKE %s
                    ORDER BY COALESCE(salary_from, 0) DESC
                """, (f"%{keyword}%",))

                result = []
                for row in cursor.fetchall():
                    salary = f"{row[2] or ''}-{row[3] or ''} {row[4] or ''}".strip()
                    result.append({
                        'company': row[0],
                        'title': row[1],
                        'salary': salary,
                        'link': row[5]
                    })
                return result