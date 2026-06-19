from flask_sqlalchemy import SQLAlchemy

# db вынесен в отдельный модуль, чтобы и models.py, и __init__.py могли его
# импортировать, не завися друг от друга (иначе вышел бы циклический импорт).
db = SQLAlchemy()
