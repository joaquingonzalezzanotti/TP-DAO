from .base_dao import BaseDAO
from modelos.especialidad import Especialidad
from persistencia.persistencia_errores import DatabaseError, IntegridadError
import sqlite3 # Necesario para atrapar errores específicos de SQLite
class EspecialidadDAO(BaseDAO):
    def crear(self, especialidad: Especialidad):
        try:
            self.cur.execute(
                "INSERT INTO Especialidad (nombre, descripcion) VALUES (?, ?)",
                (especialidad.nombre, especialidad.descripcion)
            )
            especialidad.id_especialidad = self.cur.lastrowid
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al crear la especialidad: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al crear la especialidad: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Especialidad WHERE activo = 1")
        rows = self.cur.fetchall()
        return [Especialidad(row["id_especialidad"], row["nombre"], row["descripcion"]) for row in rows]

    def obtener_todos_inactivos(self):
        self.cur.execute("SELECT * FROM Especialidad WHERE activo = 0")
        rows = self.cur.fetchall()
        return [Especialidad(row["id_especialidad"], row["nombre"], row["descripcion"]) for row in rows]
     
    def obtener_por_id(self, id_especialidad):
        self.cur.execute("SELECT * FROM Especialidad WHERE id_especialidad=?", (id_especialidad,))
        row = self.cur.fetchone()
        if row:
            return Especialidad(row["id_especialidad"], row["nombre"], row["descripcion"], row["activo"])
        return None
    
    def obtener_por_nombre(self, nombre):
        self.cur.execute("SELECT * FROM Especialidad WHERE nombre LIKE ? AND activo = 1", (f"%{nombre}%",))
        row = self.cur.fetchone()
        if row:
            return Especialidad(row["id_especialidad"], row["nombre"], row["descripcion"], row["activo"])
        return None

    def actualizar(self, especialidad: Especialidad):
        try:
            self.cur.execute(
                "UPDATE Especialidad SET nombre=?, descripcion=? WHERE id_especialidad=? AND activo=1",
                (especialidad.nombre, especialidad.descripcion, especialidad.id_especialidad)
            )
            self.conn.commit()
            return self.obtener_por_id(especialidad.id_especialidad)
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al actualizar la especialidad: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al actualizar la especialidad: {e}")        

    def eliminar(self, id_especialidad):
        """Baja lógica del Medico"""
        try:
            self.cur.execute("UPDATE Especialidad SET activo = 0 WHERE id_especialidad=?", (id_especialidad,))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al eliminar la especialidad: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al eliminar la especialidad: {e}")
    
    def activar(self, id_especialidad):
        """Reactivar un médico inactivo"""
        try:
            self.cur.execute("UPDATE Especialidad SET activo = 1 WHERE id_especialidad=?", (id_especialidad,))
            self.conn.commit()

        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al activar la especialidad: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al activar la especialidad: {e}")