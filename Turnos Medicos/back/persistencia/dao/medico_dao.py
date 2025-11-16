from .base_dao import BaseDAO
from modelos.medico import Medico
from persistencia.persistencia_errores import DatabaseError, IntegridadError
import sqlite3 # Necesario para atrapar errores específicos de SQLite
class MedicoDAO(BaseDAO):
    def crear(self, medico: Medico):
        try:
            self.cur.execute(
                "INSERT INTO Medico (nro_matricula, nombre, apellido, email, id_especialidad) VALUES (?, ?, ?, ?, ?)",
                (medico.nro_matricula, medico.nombre, medico.apellido, medico.email, medico.id_especialidad)
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al crear el médico: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al crear el médico: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Medico WHERE activo = 1")
        rows = self.cur.fetchall()
        return [Medico(row["nro_matricula"], row["nombre"], row["apellido"], row["email"], row["id_especialidad"]) for row in rows]

    def obtener_todos_inactivos(self):
        self.cur.execute("SELECT * FROM Medico WHERE activo = 0")
        rows = self.cur.fetchall()
        return [Medico(row["nro_matricula"], row["nombre"], row["apellido"], row["email"], row["id_especialidad"], row["activo"]) for row in rows]
    
    def obtener_por_id(self, nro_matricula):
        self.cur.execute("SELECT * FROM Medico WHERE nro_matricula=?", (nro_matricula,))
        row = self.cur.fetchone()
        if row:
            return Medico(row["nro_matricula"], row["nombre"], row["apellido"], row["email"], row["id_especialidad"], row["activo"])
        return None

    def obtener_por_especialidad(self, id_especialidad):
        self.cur.execute("SELECT * FROM Medico WHERE id_especialidad=? AND activo = 1", (id_especialidad,))
        rows = self.cur.fetchall()
        return [Medico(row["nro_matricula"], row["nombre"], row["apellido"], row["email"], row["id_especialidad"]) for row in rows]
    
    def obtener_por_apellido(self, apellido):
        self.cur.execute("SELECT * FROM Medico WHERE apellido LIKE ? AND activo = 1", (f"%{apellido}%",))
        rows = self.cur.fetchall()
        return [Medico(row["nro_matricula"], row["nombre"], row["apellido"], row["email"], row["id_especialidad"]) for row in rows]
    
    def actualizar(self, medico: Medico):
        try:
            self.cur.execute('''
                UPDATE Medico SET nombre=?, apellido=?, email=?, id_especialidad=? WHERE nro_matricula=? AND activo = 1
            ''', (medico.nombre, medico.apellido, medico.email, medico.id_especialidad, medico.nro_matricula))
            self.conn.commit()
            return self.obtener_por_id(medico.nro_matricula)
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al actualizar el médico: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al actualizar el médico: {e}")

    def eliminar(self, nro_matricula):
        """Baja lógica del Medico"""
        try:
            self.cur.execute("UPDATE Medico SET activo = 0 WHERE nro_matricula=?", (nro_matricula,))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al eliminar el médico: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al eliminar el médico: {e}")
    
    def activar(self, nro_matricula):
        """Reactivar un médico inactivo"""
        try:
            self.cur.execute("UPDATE Medico SET activo = 1 WHERE nro_matricula=?", (nro_matricula,))
            self.conn.commit()
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al activar el médico: {e}")   
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al activar el médico: {e}")