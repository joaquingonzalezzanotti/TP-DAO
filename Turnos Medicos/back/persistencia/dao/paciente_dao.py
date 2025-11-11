from datetime import datetime
from .base_dao import BaseDAO
from modelos.paciente import Paciente

class PacienteDAO(BaseDAO):
    def crear(self, paciente: Paciente):
        try:
            self.cur.execute(
                "INSERT INTO Paciente (dni, nombre, apellido, fecha_nacimiento, email, direccion) VALUES (?, ?, ?, ?, ?, ?)",
                (paciente.dni, paciente.nombre, paciente.apellido, paciente.fecha_nacimiento, paciente.email, paciente.direccion)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo crear el paciente: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Paciente WHERE activo = 1")
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
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo actualizar el paciente: {e}")
            return None

    def eliminar(self, dni):
        """Baja lógica del paciente"""
        try:
            self.cur.execute("UPDATE Paciente SET activo = 0 WHERE dni=?", (dni,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo desactivar el paciente: {e}")