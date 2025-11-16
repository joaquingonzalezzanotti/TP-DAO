from .base_dao import BaseDAO
from modelos.consulta import Consulta
from persistencia.persistencia_errores import DatabaseError, IntegridadError
import sqlite3 # Necesario para atrapar errores específicos de SQLite
class ConsultaDAO(BaseDAO):
    def crear(self, consulta: Consulta):
        try:
            fecha_hora_str = self._fmt_datetime(consulta.fecha_hora)
            self.cur.execute(
                """INSERT INTO Consulta (fecha_hora, diagnostico, observaciones, dni_paciente, nro_matricula_medico)
                   VALUES (?, ?, ?, ?, ?)""",
                (fecha_hora_str, consulta.diagnostico, consulta.observaciones,
                 consulta.dni_paciente, consulta.nro_matricula_medico)
            )
            consulta.id_consulta = self.cur.lastrowid
            self.conn.commit()

        # Captura errores específicos de integridad (como Foreign Key o NOT NULL)
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al crear la consulta: {e}")    
        # Captura cualquier otro error genérico de la DB
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al crear la consulta: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Consulta")
        rows = self.cur.fetchall()
        return [Consulta(**row) for row in rows]

    def obtener_por_id(self, id_consulta):
        self.cur.execute("SELECT * FROM Consulta WHERE id_consulta=?", (id_consulta,))
        row = self.cur.fetchone()
        return Consulta(**row) if row else None

    def actualizar(self, consulta: Consulta):
        try:
            self.cur.execute(
                """UPDATE Consulta
                   SET diagnostico=?, observaciones=?
                   WHERE id_consulta=?""",
                (consulta.diagnostico, consulta.observaciones, consulta.id_consulta)
            )
            self.conn.commit()
            return self.obtener_por_id(consulta.id_consulta)
        
        # Captura errores específicos de integridad (como Foreign Key o NOT NULL)
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            # Lanzamos una excepción más específica para la capa superior
            raise IntegridadError(f"Error de integridad al actualizar la consulta: {e}")
        # Captura cualquier otro error genérico de la DB
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al actualizar la consulta: {e}")

    """
    No se debe eliminar consultas
    def eliminar(self, id_consulta):
        try:
            self.cur.execute("DELETE FROM Consulta WHERE id_consulta=?", (id_consulta,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo eliminar la consulta: {e}")
    """
    # Implementación Requerida por BaseDAO: eliminar
    def eliminar(self, id):
        """
        Este método es requerido por BaseDAO. Sin embargo, la regla de negocio
        establece que las consultas no deben ser eliminadas.
        """
        # Puedes lanzar un error para indicar que la operación no está permitida:
        raise ValueError("La eliminación de consultas (operación DELETE) no está permitida por las reglas del sistema.")