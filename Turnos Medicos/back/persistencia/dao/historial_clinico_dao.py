from .base_dao import BaseDAO
from modelos.historial_clinico import HistorialClinico
from persistencia.persistencia_errores import DatabaseError, IntegridadError
import sqlite3 # Necesario para atrapar errores específicos de SQLite
class HistorialClinicoDAO(BaseDAO):
    def crear(self, historial: HistorialClinico):
        try:
            self.cur.execute(
                "INSERT INTO HistorialClinico (dni_paciente) VALUES (?)",
                (historial.dni_paciente,)
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al crear el historial clínico: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al crear el historial clínico: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM HistorialClinico")
        rows = self.cur.fetchall()
        return [HistorialClinico(**row) for row in rows]

    def obtener_por_id(self, dni_paciente):
        self.cur.execute("SELECT * FROM HistorialClinico WHERE dni_paciente=?", (dni_paciente,))
        row = self.cur.fetchone()
        return HistorialClinico(**row) if row else None

    """
    No se debe eliminar historiales clínicos
    def eliminar(self, dni_paciente):
        try:
            self.cur.execute("DELETE FROM HistorialClinico WHERE dni_paciente=?", (dni_paciente,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo eliminar el historial clínico: {e}")
    """
    # Implementación Requerida por BaseDAO: actualizar
    def actualizar(self, historial: HistorialClinico):
        """
        Este método es requerido por BaseDAO. Sin embargo, la regla de negocio
        establece que los HC no deben ser actualizados.
        """
        # Puedes lanzar un error para indicar que la operación no está permitida:
        raise ValueError("La actualizacion de historiales clinicos (operación UPDATE) no está permitida por las reglas del sistema.")
    
    # Implementación Requerida por BaseDAO: eliminar
    def eliminar(self, id):
        """
        Este método es requerido por BaseDAO. Sin embargo, la regla de negocio
        establece que los HC no deben ser eliminados.
        """
        # Puedes lanzar un error para indicar que la operación no está permitida:
        raise ValueError("La eliminación de historiales clinicos (operación DELETE) no está permitida por las reglas del sistema.")
    
    