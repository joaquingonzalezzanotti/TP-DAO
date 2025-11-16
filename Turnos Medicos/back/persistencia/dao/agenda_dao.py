from .base_dao import BaseDAO
from modelos.agenda import Agenda
from datetime import datetime
from persistencia.persistencia_errores import DatabaseError, IntegridadError
import sqlite3 # Necesario para atrapar errores específicos de SQLite
class AgendaDAO(BaseDAO):
    def crear(self, agenda: Agenda):
        try:
            horario_inicio_str = agenda.hora_inicio.strftime('%H:%M')
            horario_fin_str = agenda.hora_fin.strftime('%H:%M')
            self.cur.execute(
                """INSERT INTO Agenda (nro_matricula_medico, mes, dias_semana, hora_inicio, hora_fin, duracion_minutos)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (agenda.nro_matricula_medico, agenda.mes, agenda.dias_semana,
                 horario_inicio_str, horario_fin_str, agenda.duracion_minutos)
            )
            self.conn.commit()
        # Captura errores específicos de integridad (como Foreign Key o NOT NULL)
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al crear la agenda: {e}")    
        # Captura cualquier otro error genérico de la DB
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al crear la agenda: {e}")
    
    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Agenda")
        rows = self.cur.fetchall()
        
        return [Agenda(nro_matricula_medico=row["nro_matricula_medico"], mes=row["mes"],
                dias_semana=row["dias_semana"], hora_inicio=datetime.strptime(row["hora_inicio"], '%H:%M').time(),
                hora_fin=datetime.strptime(row["hora_fin"], '%H:%M').time(), duracion_minutos=row["duracion_minutos"]) 
            for row in rows
        ]

    def obtener_por_medico_y_mes(self, nro_matricula_medico, mes):
        self.cur.execute(
            "SELECT * FROM Agenda WHERE nro_matricula_medico=? AND mes=?",
            (nro_matricula_medico, mes)
        )
        row = self.cur.fetchone()
        if not row:
            return None
        
        return Agenda(nro_matricula_medico=row["nro_matricula_medico"], mes=row["mes"], dias_semana=row["dias_semana"],
            hora_inicio=datetime.strptime(row["hora_inicio"], '%H:%M').time(),
            hora_fin=datetime.strptime(row["hora_fin"], '%H:%M').time(), duracion_minutos=row["duracion_minutos"])

    def actualizar(self, agenda: Agenda):
        try:
            hora_inicio_str = agenda.hora_inicio.strftime('%H:%M')
            hora_fin_str = agenda.hora_fin.strftime('%H:%M')

            self.cur.execute(
                """UPDATE Agenda
                   SET dias_semana=?, hora_inicio=?, hora_fin=?, duracion_minutos=?
                   WHERE nro_matricula_medico=? AND mes=?""",
                (agenda.dias_semana, hora_inicio_str, hora_fin_str,
                 agenda.duracion_minutos, agenda.nro_matricula_medico, agenda.mes)
            )
            self.conn.commit()
            return self.obtener_por_medico_y_mes(agenda.nro_matricula_medico, agenda.mes)
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al actualizar la agenda: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al actualizar la agenda: {e}")
        
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

    # Implementación Requerida por BaseDAO: obtener_por_id
    def obtener_por_id(self, id):
        """
        Este método es requerido por BaseDAO. Sin embargo, la Agenda se identifica
        por una clave compuesta (nro_matricula_medico y mes), no por un ID único.
        """
        raise NotImplementedError("AgendaDAO no soporta la búsqueda por ID único. Utilice 'obtener_por_medico_y_mes(nro_matricula_medico, mes)'.")

    # Implementación Requerida por BaseDAO: eliminar
    def eliminar(self, id):
        """
        Este método es requerido por BaseDAO. Sin embargo, la regla de negocio
        establece que las agendas no deben ser eliminadas.
        """
        # Puedes lanzar un error para indicar que la operación no está permitida:
        raise ValueError("La eliminación de agendas (operación DELETE) no está permitida por las reglas del sistema.")