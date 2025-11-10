from persistencia.dao.base_dao import BaseDAO
from modelos.medico import Medico

class MedicoDAO(BaseDAO):
    def crear(self, medico: Medico):
        try:
            self.cur.execute(
                "INSERT INTO Medico (nro_matricula, nombre, apellido, email, id_especialidad) VALUES (?, ?, ?, ?, ?)",
                (medico.nro_matricula, medico.nombre, medico.apellido, medico.email, medico.id_especialidad)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo crear el médico: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Medico WHERE activo = 1")
        rows = self.cur.fetchall()
        return [Medico(row["nro_matricula"], row["nombre"], row["apellido"], row["email"], row["id_especialidad"]) for row in rows]

    def obtener_por_id(self, nro_matricula):
        self.cur.execute("SELECT * FROM Medico WHERE nro_matricula=?", (nro_matricula,))
        row = self.cur.fetchone()
        if row:
            return Medico(row["nro_matricula"], row["nombre"], row["apellido"], row["email"], row["id_especialidad"], row["activo"])
        return None

    def actualizar(self, medico: Medico):
        try:
            self.cur.execute('''
                UPDATE Medico SET nombre=?, apellido=?, email=?, especialidad_id=? WHERE id=? AND activo = 1
            ''', (medico.nombre, medico.apellido, medico.email, medico.id_especialidad, medico.nro_matricula))
            self.conn.commit()
            return self.obtener_por_id(medico.nro_matricula)
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo actualizar el médico: {e}")
            return None

    def eliminar(self, nro_matricula):
        """Baja lógica del Medico"""
        try:
            self.cur.execute("UPDATE Medico SET activo = 0 WHERE nro_matricula=?", (nro_matricula,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo desactivar el paciente: {e}")