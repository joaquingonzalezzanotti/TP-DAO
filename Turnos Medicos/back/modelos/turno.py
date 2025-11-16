from datetime import datetime
import re

class Turno:
    def __init__(self, id_turno=None, fecha_hora_inicio=None, motivo=None,
                 observaciones=None, estado="disponible", dni_paciente=None,
                 nro_matricula_medico=None):

        self.id_turno = id_turno
        self.fecha_hora_inicio = fecha_hora_inicio
        self.motivo = motivo.strip() if isinstance(motivo, str) else motivo
        self.observaciones = observaciones.strip() if isinstance(observaciones, str) else observaciones
        self.estado = estado.strip().lower() if isinstance(estado, str) else estado
        self.dni_paciente = dni_paciente
        self.nro_matricula_medico = nro_matricula_medico

        self._validar()

    def _validar(self):

        # fecha_hora_inicio (obligatoria)
        try:
            dt = None

            if isinstance(self.fecha_hora_inicio, str):
                # formato esperado: YYYY-MM-DD HH:MM o HH:MM:SS
                try:
                    dt = datetime.strptime(self.fecha_hora_inicio, "%Y-%m-%d %H:%M")
                except ValueError:
                    dt = datetime.strptime(self.fecha_hora_inicio, "%Y-%m-%d %H:%M:%S")

            elif isinstance(self.fecha_hora_inicio, datetime):
                dt = self.fecha_hora_inicio

            else:
                raise ValueError("fecha_hora_inicio debe ser un string o datetime válido.")

            # ESTANDARIZACIÓN
            self.fecha_hora_inicio = dt

            # No permitir crear turnos disponibles en el pasado
            if self.estado == "disponible" and dt < datetime.now():
                raise ValueError("Un turno disponible no puede crearse en el pasado.")

        except ValueError as e:
            raise ValueError(f"Fecha y hora inválida: {e}")

        # estado
        estados_validos = ["disponible", "programado", "ausente", "cancelado", "atendido"]

        if self.estado not in estados_validos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}.")

        # motivo (obligatorio si el turno no está disponible)
        if self.estado in ["programado", "cancelado", "ausente", "atendido"]:
            if not isinstance(self.motivo, str) or len(self.motivo.strip()) == 0:
                raise ValueError("El motivo es obligatorio para turnos no disponibles.")

        if self.motivo is not None:
            if len(self.motivo) > 200:
                raise ValueError("El motivo no puede superar los 200 caracteres.")

        # observaciones (opcional completar)
        if self.observaciones is not None:
            if not isinstance(self.observaciones, str):
                raise ValueError("Las observaciones deben ser texto.")
            if len(self.observaciones) > 500:
                raise ValueError("Las observaciones no pueden superar los 500 caracteres.")

        # dni_paciente (obligatorio si el turno no está disponible)
        if self.estado in ["reservado", "confirmado", "atendido"]:
            if not isinstance(self.dni_paciente, int):
                raise ValueError("dni_paciente es obligatorio y debe ser un entero válido.")

            if len(str(self.dni_paciente)) not in (7, 8):
                raise ValueError("dni_paciente debe tener entre 7 y 8 dígitos.")

        # nro_matricula_medico (obligatorio)
        if not isinstance(self.nro_matricula_medico, int):
            raise ValueError("nro_matricula_medico debe ser un entero válido.")

        if self.nro_matricula_medico <= 0 or self.nro_matricula_medico > 999999:
            raise ValueError("nro_matricula_medico debe ser un entero positivo y maximo 999999.")
