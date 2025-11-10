from persistencia.dao.base_dao import BaseDAO
from modelos.receta import Receta

class RecetaDAO(BaseDAO):
    def crear(self, receta: Receta):
        try:
            self.cur.execute(
                """INSERT INTO Receta (fecha_emision, medicamentos, detalle, id_consulta)
                   VALUES (?, ?, ?, ?)""",
                (receta.fecha_emision, receta.medicamentos, receta.detalle, receta.id_consulta)
            )
            receta.id_receta = self.cur.lastrowid
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo crear la receta: {e}")

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

    def eliminar(self, id_receta):
        try:
            self.cur.execute("DELETE FROM Receta WHERE id_receta=?", (id_receta,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo eliminar la receta: {e}")
