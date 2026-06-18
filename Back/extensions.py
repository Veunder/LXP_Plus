from flask_sqlalchemy import SQLAlchemy

# Почему db живёт в отдельном файле, а не в app.py:
# модели (models.py) должны импортировать db, а app.py импортирует модели.
# Если объявить db прямо в app.py, получится циклический импорт
# (app -> models -> app). Вынос db в нейтральный модуль разрывает этот круг:
# и app.py, и models.py импортируют его отсюда, не завися друг от друга.
db = SQLAlchemy()
