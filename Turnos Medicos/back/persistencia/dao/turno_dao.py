from persistencia.dao.base_dao import BaseDAO
from modelos.turno import Turno

class TurnoDAO(BaseDAO):
    def crear(self, turno: Turno):
        try:
            self.cur.execute(
                """INSERT INTO Turno (fecha_hora_inicio, motivo, observaciones, estado, dni_paciente, nro_matricula_medico)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (turno.fecha_hora_inicio, turno.motivo, turno.observaciones,
                 turno.estado, turno.dni_paciente, turno.nro_matricula_medico)
            )
            turno.id_turno = self.cur.lastrowid
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo crear el turno: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Turno")
        rows = self.cur.fetchall()
        return [Turno(**row) for row in rows]

    def obtener_por_id(self, id_turno):
        self.cur.execute("SELECT * FROM Turno WHERE id_turno=?", (id_turno,))
        row = self.cur.fetchone()
        return Turno(**row) if row else None

    #### VER SI DEJO ESTO O NO ####
    def actualizar(self, turno: Turno):
        try:
            self.cur.execute(
                """UPDATE Turno
                   SET motivo=?, observaciones=?, estado=?,
                   WHERE id_turno=?""",
                (turno.motivo, turno.observaciones, turno.estado, turno.id_turno)
            )
            self.conn.commit()
            return self.obtener_por_id(turno.id_turno)
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo actualizar el turno: {e}")
            return None
    """
    No se debe eliminar turnos, solo cambiar su estado a 'cancelado' o 'reprogramado' y crear nuevo en estado dispible
    def eliminar(self, id_turno):
        try:
            self.cur.execute("DELETE FROM Turno WHERE id_turno=?", (id_turno,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo eliminar el turno: {e}")
    """