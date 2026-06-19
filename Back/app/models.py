from datetime import datetime, timezone, timedelta

from app.extensions import db

# Статусы — ровно те, что ждёт фронтенд (App.vue): "free" / "issued".
# Перевод на русский ("Свободен"/"Занят") делает сам фронт при отрисовке.
STATUS_FREE = "free"
STATUS_ISSUED = "issued"


def utcnow():
    # Функция, а не значение: иначе время вычислилось бы один раз при загрузке.
    return datetime.now(timezone.utc)


class Teacher(db.Model):
    """Преподаватели — наш собственный справочник."""

    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    lname = db.Column(db.String(80), nullable=False)  # фамилия
    fname = db.Column(db.String(80))                  # имя
    mname = db.Column(db.String(80))                  # отчество
    # lesson был в твоём ERD. Фронт его не использует (там название пары
    # задаётся в каждой выдаче отдельно — subject_name), но поле оставлено.
    lesson = db.Column(db.String(120))

    def full_name(self):
        return " ".join(p for p in [self.lname, self.fname, self.mname] if p)

    def to_dict(self):
        # Фронту достаточно id и полного имени для выпадающего списка.
        return {"id": self.id, "full_name": self.full_name()}


class Classroom(db.Model):
    """Аудитории. Новая сущность: фронт запрашивает их списком для формы."""

    __tablename__ = "classrooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)  # например, "А-101"

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Laptop(db.Model):
    """Ноутбук. Сам по себе хранит только номер и статус — всё остальное
    (кто держит, аудитория, мышь и т.д.) берётся из активной позиции выдачи."""

    __tablename__ = "laptops"

    id = db.Column(db.Integer, primary_key=True)
    # Номер выводится на фронте как NB-001 (через padStart). Храним числом.
    number = db.Column(db.Integer, unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_FREE)
    # Состояние устройства (как изначально в ERD). Показывается в таблице
    # для всех ноутбуков; при выдаче обновляется значением из формы.
    condition = db.Column(db.String(255))

    items = db.relationship("IssueItem", back_populates="laptop")

    def active_item(self):
        # Активная позиция — та, по которой ноутбук ещё не вернули.
        return IssueItem.query.filter_by(
            laptop_id=self.id, returned_at=None
        ).first()

    def to_dict(self):
        # Собираем "плоский" объект ровно в той форме, что ждёт таблица фронта.
        data = {
            "id": self.id,
            "number": self.number,
            "status": self.status,
            "condition": self.condition,
            "student_full_name": None,
            "student_group": None,
            "classroom": None,
            "subject_name": None,
            "teacher": None,
            "teacher_id": None,
            # None у свободного ноутбука — фронт покажет прочерк вместо ✓/✕.
            "has_mouse": None,
            "has_charger": None,
        }
        item = self.active_item()
        if item:
            issue = item.issue
            data.update({
                "student_full_name": item.student_full_name,
                "student_group": item.student_group,
                "classroom": issue.classroom.name if issue.classroom else None,
                "subject_name": issue.subject_name,
                "teacher": issue.teacher.full_name() if issue.teacher else None,
                "teacher_id": issue.teacher_id,
                "has_mouse": item.has_mouse,
                "has_charger": item.has_charger,
            })
        return data


class Issue(db.Model):
    """Выдача — один факт: преподаватель в аудитории на паре выдал
    от 1 до 10 ноутбуков. Содержит позиции (IssueItem)."""

    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id"), nullable=False
    )
    classroom_id = db.Column(
        db.Integer, db.ForeignKey("classrooms.id"), nullable=False
    )
    subject_name = db.Column(db.String(160), nullable=False)  # название пары

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    returned_at = db.Column(db.DateTime)  # NULL = выдача ещё открыта
    # Срок хранения в истории — 7 дней (из бизнес-правил проекта).
    expires_at = db.Column(db.DateTime)

    teacher = db.relationship("Teacher")
    classroom = db.relationship("Classroom")
    items = db.relationship(
        "IssueItem", back_populates="issue", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "teacher": self.teacher.full_name() if self.teacher else None,
            "teacher_id": self.teacher_id,
            "classroom": self.classroom.name if self.classroom else None,
            "subject_name": self.subject_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "items": [it.to_dict() for it in self.items],
        }


class IssueItem(db.Model):
    """Позиция выдачи: один ноутбук + один ученик + мышь/зарядка/клавиши."""

    __tablename__ = "issue_items"

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(
        db.Integer, db.ForeignKey("issues.id"), nullable=False
    )
    laptop_id = db.Column(
        db.Integer, db.ForeignKey("laptops.id"), nullable=False
    )
    # Ученик — это сущность из платформы, у нас её таблицы нет, поэтому
    # храним просто текстом (ФИО + группа), без внешнего ключа.
    student_full_name = db.Column(db.String(160), nullable=False)
    student_group = db.Column(db.String(80), nullable=False)

    # Состояние ноутбука на момент этой выдачи (снимок для истории).
    condition = db.Column(db.String(255))
    has_mouse = db.Column(db.Boolean, default=False)
    has_charger = db.Column(db.Boolean, default=False)
    # Своё время возврата у позиции нужно, чтобы можно было освободить
    # один ноутбук из выдачи отдельно (кнопка "Очистить" в таблице).
    returned_at = db.Column(db.DateTime)

    issue = db.relationship("Issue", back_populates="items")
    laptop = db.relationship("Laptop", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "laptop_id": self.laptop_id,
            "laptop_number": self.laptop.number if self.laptop else None,
            "student_full_name": self.student_full_name,
            "student_group": self.student_group,
            "condition": self.condition,
            "has_mouse": self.has_mouse,
            "has_charger": self.has_charger,
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
        }
