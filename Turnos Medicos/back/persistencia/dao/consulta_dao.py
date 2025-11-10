from persistencia.dao.base_dao import BaseDAO
from modelos.consulta import Consulta

class ConsultaDAO(BaseDAO):
    def crear(self, consulta: Consulta):
        try:
            self.cur.execute(
                """INSERT INTO Consulta (fecha_hora, diagnostico, observaciones, id_historial_clinico, nro_matricula_medico)
                   VALUES (?, ?, ?, ?, ?)""",
                (consulta.fecha_hora, consulta.diagnostico, consulta.observaciones,
                 consulta.id_historial_clinico, consulta.nro_matricula_medico)
            )
            consulta.id_consulta = self.cur.lastrowid
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo crear la consulta: {e}")

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
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo actualizar la consulta: {e}")
            return None

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