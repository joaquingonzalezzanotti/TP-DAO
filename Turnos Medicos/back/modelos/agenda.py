class Agenda:
    def __init__(self, nro_matricula_medico, mes, dias_semana,
                 hora_inicio, hora_fin, duracion_minutos):
        self.nro_matricula_medico = nro_matricula_medico
        self.mes = mes
        self.dias_semana = dias_semana  # texto simulado, ej: "Lunes,Miércoles,Viernes"
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.duracion_minutos = duracion_minutos

        self._validar()

    def _validar(self):
        if not isinstance(self.nro_matricula_medico, int):
            raise ValueError("La matrícula del médico debe ser numérica.")
        if not (1 <= self.mes <= 12):
            raise ValueError("El mes debe estar entre 1 y 12.")
        if not self.dias_semana:
            raise ValueError("Debe especificar los días de la semana.")
        if self.duracion_minutos <= 0:
            raise ValueError("La duración del turno debe ser positiva.")

    def __repr__(self):
        return (f"Agenda(medico={self.nro_matricula_medico}, mes={self.mes}, "
                f"días={self.dias_semana}, {self.hora_inicio}-{self.hora_fin})")
