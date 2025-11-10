class Turno:
    def __init__(self, id_turno=None, fecha_hora_inicio=None, motivo=None,
                 observaciones=None, estado="disponible", dni_paciente=None,
                 nro_matricula_medico=None):
        self.id_turno = id_turno
        self.fecha_hora_inicio = fecha_hora_inicio
        self.motivo = motivo
        self.observaciones = observaciones
        self.estado = estado
        self.dni_paciente = dni_paciente
        self.nro_matricula_medico = nro_matricula_medico

        self._validar()

    def _validar(self):
        if self.estado not in ("disponible", "programado", "atendido", "cancelado", "ausente"):
            raise ValueError("El estado del turno no es válido.")
        if not self.fecha_hora_inicio:
            raise ValueError("El turno debe tener una fecha y hora de inicio.")
        if not isinstance(self.nro_matricula_medico, int):
            raise ValueError("El número de matrícula del médico debe ser numérico.")
        if self.dni_paciente is not None and not isinstance(self.dni_paciente, int):
            raise ValueError("El DNI del paciente debe ser numérico.")

    def __repr__(self):
        return (f"Turno(id={self.id_turno}, fecha={self.fecha_hora_inicio}, "
                f"estado={self.estado}, medico={self.nro_matricula_medico}, paciente={self.dni_paciente})")
