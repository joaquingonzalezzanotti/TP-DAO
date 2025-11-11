from datetime import datetime, timedelta
import calendar

from persistencia.dao.agenda_dao import AgendaDAO
from persistencia.dao.turno_dao import TurnoDAO
from modelos.turno import Turno

class MedicoService:
    """
    Servicio que encapsula la lógica de negocio relacionada con los médicos.
    Coordina acceso a DAO y aplica reglas (baja cohesión, bajo acoplamiento).
    """

    def __init__(self):
        self.agenda_dao = AgendaDAO()
        self.turno_dao = TurnoDAO()

    def generar_turnos(self, nro_matricula_medico: int, mes: int, anio: int):
        """
        Genera los turnos de un médico para el mes especificado.
        Se basa en su agenda (días, horario y duración).

        Parámetros:
            nro_matricula_medico: int → ID del médico
            mes: int → número de mes (1-12)

        Retorna:
            lista de Turno creados
        """

        try:
            # Validar mes y año
            if not (1 <= mes <= 12):
                raise ValueError("El mes debe estar entre 1 y 12.")
            if anio < datetime.now().year:
                raise ValueError("No se pueden generar turnos en años anteriores.")

            agenda = self.agenda_dao.obtener_por_medico_y_mes(nro_matricula_medico, mes)
            if not agenda:
                raise ValueError(f"No existe agenda para el médico {nro_matricula_medico} en el mes {mes}")

            # Diccionario de traducción (inglés → español)
            dias_en = {
                "monday": "lunes",
                "tuesday": "martes",
                "wednesday": "miércoles",
                "thursday": "jueves",
                "friday": "viernes",
                "saturday": "sábado",
                "sunday": "domingo",
            }

            dias_semana = [d.strip().lower() for d in agenda.dias_semana.split(",")]
            turnos_creados = []
            _, dias_mes = calendar.monthrange(anio, mes)

            # Recorrer todos los días del mes
            for dia in range(1, dias_mes + 1):
                fecha = datetime(anio, mes, dia)

                # Verificar si el día actual está en los días de la agenda
                if fecha.strftime("%A").lower() in dias_semana:
                    hora_inicio = datetime.strptime(agenda.hora_inicio, "%H:%M").time()
                    hora_fin = datetime.strptime(agenda.hora_fin, "%H:%M").time()
                    actual = datetime.combine(fecha.date(), hora_inicio)

                    while actual.time() < hora_fin:
                        # Crear el objeto Turno mientras esté dentro del horario
                        turno = Turno(
                            fecha_hora_inicio=actual.strftime("%Y-%m-%d %H:%M:%S"),
                            estado="disponible",
                            nro_matricula_medico=nro_matricula_medico
                        )
                        # Insertar en DB mediante DAO
                        self.turno_dao.crear(turno)
                        turnos_creados.append(turno)
                        actual += timedelta(minutes=agenda.duracion_minutos)

            print(f"[OK] Se generaron {len(turnos_creados)} turnos para el médico {nro_matricula_medico} (mes {mes}).")
            return turnos_creados

        except ValueError as ve:
            print(f"[VALIDACIÓN] {ve}")
        except Exception as e:
            print(f"[ERROR] No se pudieron generar los turnos: {e}")

        
