from datetime import datetime
from .base_dao import BaseDAO
from modelos.paciente import Paciente
from persistencia.persistencia_errores import DatabaseError, IntegridadError
import sqlite3 # Necesario para atrapar errores específicos de SQLite
class PacienteDAO(BaseDAO):
    def crear(self, paciente: Paciente):
        try:
            fecha_nacimiento_str = self._fmt_date(paciente.fecha_nacimiento)
            self.cur.execute(
                "INSERT INTO Paciente (dni, nombre, apellido, fecha_nacimiento, email, direccion) VALUES (?, ?, ?, ?, ?, ?)",
                (paciente.dni, paciente.nombre, paciente.apellido, fecha_nacimiento_str, paciente.email, paciente.direccion)
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al crear el paciente: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al crear el paciente: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Paciente WHERE activo = 1")
        rows = self.cur.fetchall()
        return [Paciente(row["dni"], row["nombre"], row["apellido"], datetime.strptime(row["fecha_nacimiento"], '%Y-%m-%d').date(), row["email"], row["direccion"], row["activo"]) for row in rows]

    def obtener_todos_inactivos(self):
        self.cur.execute("SELECT * FROM Paciente WHERE activo = 0")
        rows = self.cur.fetchall()
        return [Paciente(row["dni"], row["nombre"], row["apellido"], datetime.strptime(row["fecha_nacimiento"], '%Y-%m-%d').date(), row["email"], row["direccion"], row["activo"]) for row in rows]
 
    def obtener_por_id(self, dni):
        self.cur.execute("SELECT * FROM Paciente WHERE dni = ?", (dni,))
        row = self.cur.fetchone()
        if row:
            return Paciente(row["dni"], row["nombre"], row["apellido"], datetime.strptime(row["fecha_nacimiento"], '%Y-%m-%d').date(), row["email"], row["direccion"], row["activo"])
        return None

    def actualizar(self, paciente: Paciente):
        try:
            self.cur.execute('''
                UPDATE Paciente SET nombre=?, apellido=?, email=?, direccion=? WHERE dni=? AND activo = 1
            ''', (paciente.nombre, paciente.apellido, paciente.email, paciente.direccion, paciente.dni))
            self.conn.commit()
            return self.obtener_por_id(paciente.dni)
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al actualizar el paciente: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al actualizar el paciente: {e}")

    def eliminar(self, dni):
        """Baja lógica del paciente"""
        try:
            self.cur.execute("UPDATE Paciente SET activo = 0 WHERE dni=?", (dni,))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al eliminar el paciente: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al eliminar el paciente: {e}")
    
    def activar(self, dni):
        """Reactivar un paciente inactivo"""
        try:
            self.cur.execute("UPDATE Paciente SET activo = 1 WHERE dni=?", (dni,))
            self.conn.commit()

        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al activar el paciente: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al activar el paciente: {e}")