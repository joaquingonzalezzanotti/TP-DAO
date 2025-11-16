from .base_dao import BaseDAO
from modelos.receta import Receta
from persistencia.persistencia_errores import DatabaseError, IntegridadError
import sqlite3 # Necesario para atrapar errores específicos de SQLite
class RecetaDAO(BaseDAO):
    def crear(self, receta: Receta):
        try:
            fecha_emision_str = self._fmt_date(receta.fecha_emision)

            self.cur.execute(
                """INSERT INTO Receta (fecha_emision, medicamentos, detalle, id_consulta)
                   VALUES (?, ?, ?, ?)""",
                (fecha_emision_str, receta.medicamentos, receta.detalle, receta.id_consulta)
            )
            receta.id_receta = self.cur.lastrowid
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al crear la receta: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al crear la receta: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Receta")
        rows = self.cur.fetchall()
        return [Receta(**row) for row in rows]

    def obtener_por_id(self, id_receta):
        self.cur.execute("SELECT * FROM Receta WHERE id_receta=?", (id_receta,))
        row = self.cur.fetchone()
        return Receta(**row) if row else None

    def obtener_por_consulta(self, id_consulta):
        self.cur.execute("SELECT * FROM Receta WHERE id_consulta=?", (id_consulta,))
        row = self.cur.fetchone()
        return Receta(**row) if row else None

    """
    Una vez creada, una receta no se debe modificar
    def actualizar(self, receta: Receta):
        try:
            self.cur.execute(
                ""UPDATE Receta
                   SET fecha_emision=?, medicamentos=?, detalle=?
                   WHERE id_receta=?"",
                (receta.fecha_emision, receta.medicamentos, receta.detalle, receta.id_receta)
            )
            self.conn.commit()
            return self.obtener_por_id(receta.id_receta)
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo actualizar la receta: {e}")
            return None
    """
    # Implementación Requerida por BaseDAO: actualizar
    def actualizar(self, receta: Receta):
        """
        Este método es requerido por BaseDAO. Sin embargo, la regla de negocio
        establece que las recetas no deben ser actualizadas.
        """
        # Puedes lanzar un error para indicar que la operación no está permitida:
        raise ValueError("La actualizacion de recetas (operación UPDATE) no está permitida por las reglas del sistema.")

    def eliminar(self, id_receta):
        try:
            self.cur.execute("DELETE FROM Receta WHERE id_receta=?", (id_receta,))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al eliminar la receta: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al eliminar la receta: {e}")
