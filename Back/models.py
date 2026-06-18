from datetime import date as date_type

from extensions import db

# Разрешённые статусы — в одном месте, как константа. Используются и в
# проверках при бронировании/возврате, и в ограничении базы (CheckConstraint).
STATUS_FREE = "Свободен"
STATUS_BUSY = "Занят"
STATUS_UNAVAILABLE = "Недоступен"
ALLOWED_STATUSES = {STATUS_FREE, STATUS_BUSY, STATUS_UNAVAILABLE}


class Teacher(db.Model):
    """Преподаватели — наш собственный справочник (таблица в нашей БД)."""

    __tablename__ = "teachers"

    id_pred = db.Column(db.Integer, primary_key=True)
    lname = db.Column(db.String(80), nullable=False)   # фамилия
    fname = db.Column(db.String(80), nullable=False)   # имя
    mname = db.Column(db.String(80))                   # отчество (может не быть)

    laptops = db.relationship("Laptop", back_populates="teacher")

    def full_name(self):
        # Собираем ФИО, пропуская отсутствующее отчество.
        parts = [self.lname, self.fname, self.mname]
        return " ".join(p for p in parts if p)

    def to_dict(self):
        return {
            "id_pred": self.id_pred,
            "lname": self.lname,
            "fname": self.fname,
            "mname": self.mname,
            "full_name": self.full_name(),
        }


class Laptop(db.Model):
    """Ноутбуки. Поля названы как в ERD."""

    __tablename__ = "laptops"

    id_laptop = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_FREE)

    # Настоящий внешний ключ на наш справочник преподавателей.
    # Хранит, за кем ноутбук закреплён прямо сейчас (NULL — если свободен).
    id_pred = db.Column(db.Integer, db.ForeignKey("teachers.id_pred"))
    fiostud = db.Column(db.String(100))
    nclass = db.Column(db.String(20))

    mouse = db.Column(db.Boolean, default=False)     # выдана ли мышь
    charger = db.Column(db.Boolean, default=False)   # выдана ли зарядка
    condition = db.Column(db.String(255))            # текущее состояние/заметка

    teacher = db.relationship("Teacher", back_populates="laptops")
    history = db.relationship(
        "History",
        back_populates="laptop",
        cascade="all, delete-orphan",
        order_by="History.date.desc()",
    )

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('Свободен', 'Занят', 'Недоступен')",
            name="ck_laptop_status",
        ),
    )

    def active_record(self):
        # Активная бронь — запись истории, где не проставлено время конца.
        for rec in self.history:
            if rec.ftime is None:
                return rec
        return None

    def to_dict(self):
        return {
            "id_laptop": self.id_laptop,
            "status": self.status,
            "id_pred": self.id_pred,
            "teacher_name": self.teacher.full_name() if self.teacher else None,
            "id_stud": self.id_stud,
            "nclass": self.nclass,
            "mouse": self.mouse,
            "charger": self.charger,
            "condition": self.condition,
        }


class History(db.Model):
    """История — журнал бронирований. Одна строка = один факт взятия ноутбука."""

    __tablename__ = "history"

    id_story = db.Column(db.Integer, primary_key=True)

    id_laptop = db.Column(
        db.Integer, db.ForeignKey("laptops.id_laptop"), nullable=False
    )
    id_pred = db.Column(db.Integer, db.ForeignKey("teachers.id_pred"))
    id_stud = db.Column(db.Integer)  # теоретический ключ, без ForeignKey

    date = db.Column(db.Date, nullable=False, default=date_type.today)
    stime = db.Column(db.Time, nullable=False)  # время начала (старт брони)
    # Время конца. NULL = бронь ещё активна (ноутбук на руках). Это признак
    # "не возвращён", по аналогии тому, как раньше работало returned_at.
    ftime = db.Column(db.Time)
    condition = db.Column(db.String(255))       # состояние на момент брони

    laptop = db.relationship("Laptop", back_populates="history")

    def to_dict(self):
        return {
            "id_story": self.id_story,
            "id_laptop": self.id_laptop,
            "id_pred": self.id_pred,
            "id_stud": self.id_stud,
            "date": self.date.isoformat() if self.date else None,
            "stime": self.stime.isoformat() if self.stime else None,
            "ftime": self.ftime.isoformat() if self.ftime else None,
            "condition": self.condition,
            "is_active": self.ftime is None,
        }
