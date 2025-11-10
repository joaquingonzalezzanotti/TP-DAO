from abc import ABC, abstractmethod
from persistencia.db_connection import DBConnection

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
