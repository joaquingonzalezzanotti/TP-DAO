from persistencia.dao.base_dao import BaseDAO
from modelos.agenda import Agenda

class AgendaDAO(BaseDAO):
    def crear(self, agenda: Agenda):
        try:
            self.cur.execute(
                """INSERT INTO Agenda (nro_matricula_medico, mes, dias_semana, hora_inicio, hora_fin, duracion_minutos)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (agenda.nro_matricula_medico, agenda.mes, agenda.dias_semana,
                 agenda.hora_inicio, agenda.hora_fin, agenda.duracion_minutos)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo crear la agenda: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Agenda")
        rows = self.cur.fetchall()
        return [Agenda(**row) for row in rows]

    def obtener_por_medico_y_mes(self, nro_matricula_medico, mes):
        self.cur.execute(
            "SELECT * FROM Agenda WHERE nro_matricula_medico=? AND mes=?",
            (nro_matricula_medico, mes)
        )
        row = self.cur.fetchone()
        return Agenda(**row) if row else None

    def actualizar(self, agenda: Agenda):
        try:
            self.cur.execute(
                """UPDATE Agenda
                   SET dias_semana=?, hora_inicio=?, hora_fin=?, duracion_minutos=?
                   WHERE nro_matricula_medico=? AND mes=?""",
                (agenda.dias_semana, agenda.hora_inicio, agenda.hora_fin,
                 agenda.duracion_minutos, agenda.nro_matricula_medico, agenda.mes)
            )
            self.conn.commit()
            return self.obtener_por_medico_y_mes(agenda.nro_matricula_medico, agenda.mes)
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo actualizar la agenda: {e}")
            return None
    """
    No se debe eliminar agendas
    def eliminar(self, nro_matricula_medico, mes):
        try:
            self.cur.execute(
                "DELETE FROM Agenda WHERE nro_matricula_medico=? AND mes=?",
                (nro_matricula_medico, mes)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] No se pudo eliminar la agenda: {e}")
    """