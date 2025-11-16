from abc import ABC, abstractmethod
from persistencia.db_connection import DBConnection
import sqlite3
from persistencia.utils_fecha import format_date_for_db, format_datetime_for_db

class BaseDAO(ABC):
    def __init__(self):
        db = DBConnection()
        self.conn = db.conn
        self.cur = self.conn.cursor()

    @abstractmethod
    def crear(self, obj):
        pass

    @abstractmethod
    def obtener_todos(self):
        pass

    @abstractmethod
    def obtener_por_id(self, id):
        pass

    @abstractmethod
    def actualizar(self, obj):
        pass

    @abstractmethod
    def eliminar(self, id):
        pass

    # helpers reutilizables para DAOs hijos
    def _fmt_date(self, value):
        return format_date_for_db(value)

    def _fmt_datetime(self, value):
        return format_datetime_for_db(value)