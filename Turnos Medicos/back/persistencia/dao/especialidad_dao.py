from persistencia.dao.base_dao import BaseDAO
from modelos.especialidad import Especialidad

class EspecialidadDAO(BaseDAO):
    def crear(self, especialidad: Especialidad):
        try:
            self.cur.execute(
                "INSERT INTO Especialidad (nombre, descripcion) VALUES (?, ?)",
                (especialidad.nombre, especialidad.descripcion)
            )
            especialidad.id_especialidad = self.cur.lastrowid
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo crear la especialidad: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Especialidad WHERE activo = 1")
        rows = self.cur.fetchall()
        return [Especialidad(row["id_especialidad"], row["nombre"], row["descripcion"]) for row in rows]

    def obtener_por_id(self, id_especialidad):
        self.cur.execute("SELECT * FROM Especialidad WHERE id_especialidad=?", (id_especialidad,))
        row = self.cur.fetchone()
        if row:
            return Especialidad(row["id_especialidad"], row["nombre"], row["descripcion"], row["activo"])
        return None

    def actualizar(self, especialidad: Especialidad):
        try:
            self.cur.execute(
                "UPDATE Especialidad SET nombre=? descripcion=? WHERE id_especialidad=? AND activo=1",
                (especialidad.nombre, especialidad.descripcion, especialidad.id_especialidad)
            )
            self.conn.commit()
            return self.obtener_por_id(especialidad.id_especialidad)
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo actualizar la especialidad: {e}")
            return None

    def eliminar(self, id_especialidad):
        """Baja lógica del Medico"""
        try:
            self.cur.execute("UPDATE Especialidad SET activo = 0 WHERE id_especialidad=?", (id_especialidad,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo desactivar el paciente: {e}")