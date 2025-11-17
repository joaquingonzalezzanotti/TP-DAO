from .base_dao import BaseDAO
from modelos.turno import Turno
from persistencia.persistencia_errores import DatabaseError, IntegridadError
import sqlite3 # Necesario para atrapar errores específicos de SQLite
class TurnoDAO(BaseDAO):
    def crear(self, turno: Turno):
        try:
            fecha_str = self._fmt_datetime(turno.fecha_hora_inicio)
            self.cur.execute(
                """INSERT INTO Turno (fecha_hora_inicio, motivo, observaciones, estado, dni_paciente, nro_matricula_medico)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (fecha_str, turno.motivo, turno.observaciones,
                 turno.estado, turno.dni_paciente, turno.nro_matricula_medico)
            )
            turno.id_turno = self.cur.lastrowid
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al crear el turno: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al crear el turno: {e}")

    def obtener_todos(self):
        self.cur.execute("SELECT * FROM Turno")
        rows = self.cur.fetchall()
        return [Turno(**row) for row in rows]

    def obtener_por_id(self, id_turno):
        self.cur.execute("SELECT * FROM Turno WHERE id_turno=?", (id_turno,))
        row = self.cur.fetchone()
        return Turno(**row) if row else None

    def actualizar(self, turno: Turno):
        try:
            self.cur.execute(
                """UPDATE Turno
                   SET motivo=?, observaciones=?, estado=?, dni_paciente=?
                   WHERE id_turno=?""",
                (turno.motivo, turno.observaciones, turno.estado, turno.dni_paciente, turno.id_turno)
            )
            self.conn.commit()
            return self.obtener_por_id(turno.id_turno)
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise IntegridadError(f"Error de integridad al actualizar el turno: {e}")
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Error de base de datos no especificado al actualizar el turno: {e}")
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
    # Implementación Requerida por BaseDAO: eliminar
    def eliminar(self, id):
        """
        Este método es requerido por BaseDAO. Sin embargo, la regla de negocio
        establece que los turnos no deben ser eliminados.
        """
        # Puedes lanzar un error para indicar que la operación no está permitida:
        raise ValueError("La eliminación de turnos (operación DELETE) no está permitida por las reglas del sistema.")
    
    def existen_turnos_generados(self, nro_matricula_medico: int, mes: int, anio: int) -> bool:
        """
        Retorna True si ya existen turnos generados para ese médico en ese mes.
        """
        query = """
            SELECT COUNT(*)
            FROM Turno
            WHERE nro_matricula_medico = ?
                AND strftime('%m', fecha_hora_inicio) = ?
                AND strftime('%Y', fecha_hora_inicio) = ?
        """

        self.cursor.execute(query, (
            nro_matricula_medico,
            f"{mes:02d}",
            str(anio)
        ))

        cantidad = self.cursor.fetchone()[0]
        return cantidad > 0
    
    def obtener_turnos_disponibles_por_medico_y_fecha(self, nro_matricula_medico, fecha):
        # Convertir siempre el date → 'YYYY-MM-DD'
        try:
            fecha_str = self._fmt_date(fecha)
        except ValueError as e:
            raise ValueError(f"Fecha inválida: {e}")

        self.cur.execute(
            "SELECT * FROM Turno WHERE nro_matricula_medico=? AND date(fecha_hora_inicio)=?",
            (nro_matricula_medico, fecha_str)
        )
        rows = self.cur.fetchall()
        return [Turno(**row) for row in rows]
    
    def obtener_turnos_disponibles_por_medico_y_mes(self, nro_matricula_medico, mes_actual, anio_actual):
        """
        Retorna una lista de turnos disponibles para un médico en un mes y año específicos.
        """
        mes_str = f"{mes_actual:02d}"
        anio_str = str(anio_actual)

        self.cur.execute(
            """SELECT * FROM Turno
               WHERE nro_matricula_medico=?
                 AND strftime('%m', fecha_hora_inicio)=?
                 AND strftime('%Y', fecha_hora_inicio)=?
                 AND estado='disponible'""",
            (nro_matricula_medico, mes_str, anio_str)
        )
        rows = self.cur.fetchall()
        return [Turno(**row) for row in rows]
    
    def obtener_turnos_disponibles_por_especialidad_y_fecha(self, id_especialidad, fecha):
        """
        Retorna una lista de turnos disponibles para una especialidad en una fecha específica.
        """
        try:
            fecha_str = self._fmt_date(fecha)
        except ValueError as e:
            raise ValueError(f"Fecha inválida: {e}")

        self.cur.execute(
            """SELECT t.* FROM Turno t
               JOIN Medico m ON t.nro_matricula_medico = m.nro_matricula
               WHERE m.id_especialidad=?
                 AND date(t.fecha_hora_inicio)=?
                 AND t.estado='disponible'""",
            (id_especialidad, fecha_str)
        )
        rows = self.cur.fetchall()
        return [Turno(**row) for row in rows]
    
    def obtener_turnos_disponibles_por_especialidad_y_mes(self, id_especialidad, mes_actual, anio_actual):
        """
        Retorna una lista de turnos disponibles para una especialidad en un mes y año específicos.
        """
        mes_str = f"{mes_actual:02d}"
        anio_str = str(anio_actual)

        self.cur.execute(
            """SELECT t.* FROM Turno t
               JOIN Medico m ON t.nro_matricula_medico = m.nro_matricula
               WHERE m.id_especialidad=?
                 AND strftime('%m', t.fecha_hora_inicio)=?
                 AND strftime('%Y', t.fecha_hora_inicio)=?
                 AND t.estado='disponible'""",
            (id_especialidad, mes_str, anio_str)
        )
        rows = self.cur.fetchall()
        return [Turno(**row) for row in rows]
    
    def obtener_turnos_por_medico_en_un_periodo(self, nro_matricula_medico, fecha_inicio, fecha_fin):
        """
        Retorna una lista de turnos para un médico específico dentro de un período determinado.
        """
        fecha_inicio_str = self._fmt_date(fecha_inicio)
        fecha_fin_str = self._fmt_date(fecha_fin)

        self.cur.execute(
            """SELECT * FROM Turno
               WHERE nro_matricula_medico=?
                 AND date(fecha_hora_inicio) BETWEEN ? AND ?""",
            (nro_matricula_medico, fecha_inicio_str, fecha_fin_str)
        )
        rows = self.cur.fetchall()
        return [Turno(**row) for row in rows]
    
    def obtener_cantidad_turnos_por_estado_y_especialidad(self, id_especialidad):
        """
        Retorna un diccionario con la cantidad de turnos por estado para una especialidad médica específica.
        """
        self.cur.execute(
            """SELECT t.estado, COUNT(*) as cantidad
               FROM Turno t
               JOIN Medico m ON t.nro_matricula_medico = m.nro_matricula
               WHERE m.id_especialidad=?
               AND m.activo = 1
               GROUP BY t.estado""",
            (id_especialidad,)
        )
        rows = self.cur.fetchall()
        return {row["estado"]: row["cantidad"] for row in rows}
    
    def obtener_pacientes_atendidos_por_periodo(self, fecha_inicio: str, fecha_fin: str):
        """
        Retorna una lista de diccionarios/modelos Paciente (debe unirse con PacienteDAO si es necesario)
        que tuvieron al menos un turno en estado 'atendido' en el periodo dado.
        """
        # Utiliza un JOIN para obtener los datos completos del paciente
        # y DISTINCT para asegurar que cada paciente aparezca solo una vez.
        try:
            self.cur.execute(
                """
                SELECT DISTINCT
                    p.dni, p.nombre, p.apellido, p.fecha_nacimiento, p.email, p.direccion, p.activo
                FROM Turno t
                JOIN Paciente p ON t.dni_paciente = p.dni
                WHERE t.estado = 'atendido'
                AND p.activo = 1
                AND t.fecha BETWEEN ? AND ?
                """,
                (fecha_inicio, fecha_fin)
            )
            rows = self.cur.fetchall()
            
            from modelos.paciente import Paciente # Necesitas importar el modelo Paciente
            
            # Mapeo a objetos Paciente
            return [
                Paciente(
                    dni=row["dni"],
                    nombre=row["nombre"],
                    apellido=row["apellido"],
                    fecha_nacimiento=row["fecha_nacimiento"],
                    email=row["email"],
                    direccion=row["direccion"],
                    activo=row["activo"]
                ) for row in rows
            ]
        except Exception as e:
            # Re-lanzar como error de persistencia
            raise DatabaseError(f"Error de base de datos al obtener pacientes atendidos: {e}")
    
    def cantidad_turnos_atendido():
        pass