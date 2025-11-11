from .base_dao import BaseDAO
from modelos.historial_clinico import HistorialClinico

class HistorialClinicoDAO(BaseDAO):
    def crear(self, historial: HistorialClinico):
        try:
            self.cur.execute(
                "INSERT INTO HistorialClinico (dni_paciente) VALUES (?)",
                (historial.dni_paciente,)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo crear el historial clínico: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM HistorialClinico")
        rows = self.cur.fetchall()
        return [HistorialClinico(**row) for row in rows]

    def obtener_por_dni(self, dni_paciente):
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
    # Implementación Requerida por BaseDAO: eliminar
    def eliminar(self, id):
        """
        Este método es requerido por BaseDAO. Sin embargo, la regla de negocio
        establece que los HC no deben ser eliminados.
        """
        # Puedes lanzar un error para indicar que la operación no está permitida:
        raise ValueError("La eliminación de historiales clinicos (operación DELETE) no está permitida por las reglas del sistema.")