from typing import Dict, Any, Optional

class Vacancy:
    """Класс для представления вакансии."""

    def __init__(
            self,
            title: str,
            link: str,
            salary: Optional[Dict[str, Optional[int]]],
            description: str,
            requirements: str,
            hh_id: Optional[str] = None  # <-- добавлено
    ):
        self.title = title
        self.link = link
        self.salary = salary
        self.description = description
        self.requirements = requirements
        self.hh_id = hh_id  # <-- добавлено

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект Vacancy в словарь."""
        return {
            "title": self.title,
            "link": self.link,
            "salary": self.salary,
            "description": self.description,
            "requirements": self.requirements,
            "hh_id": self.hh_id,  # <-- добавлено
        }

    @classmethod
    def validate_and_create(cls, data: Dict[str, Any]) -> "Vacancy":
        """Валидирует данные и создает экземпляр Vacancy."""
        title = data.get("title") or data.get("name", "")
        if not title:
            raise ValueError("Title/name is required")

        salary = data.get("salary")
        if salary is not None:
            if not isinstance(salary, dict):
                raise ValueError("Salary must be a dictionary or None")
            valid_keys = {"from", "to", "currency"}
            if not any(key in valid_keys for key in salary.keys()):
                raise ValueError("Invalid salary structure")

        return cls(
            title=title,
            link=data.get("alternate_url", "") or data.get("link", ""),
            salary=salary,
            description=data.get("description", ""),
            requirements=data.get("snippet", {}).get("requirement", "") if isinstance(data.get("snippet"), dict)
            else data.get("requirements", ""),
            hh_id=data.get("id")  # <-- добавлено
        )
