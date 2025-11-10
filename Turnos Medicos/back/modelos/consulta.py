class Consulta:
    def __init__(self, id_consulta=None, fecha_hora=None, diagnostico=None,
                 observaciones=None, id_historial_clinico=None,
                 nro_matricula_medico=None):
        self.id_consulta = id_consulta
        self.fecha_hora = fecha_hora
        self.diagnostico = diagnostico
        self.observaciones = observaciones
        self.id_historial_clinico = id_historial_clinico
        self.nro_matricula_medico = nro_matricula_medico

        self._validar()

    def _validar(self):
        if not self.fecha_hora:
            raise ValueError("La consulta debe tener una fecha y hora.")
        if not isinstance(self.id_historial_clinico, int):
            raise ValueError("El historial clínico debe ser un ID numérico.")
        if not isinstance(self.nro_matricula_medico, int):
            raise ValueError("El número de matrícula debe ser numérico.")

    def __repr__(self):
        return (f"Consulta(id={self.id_consulta}, fecha={self.fecha_hora}, "
                f"historial={self.id_historial_clinico}, medico={self.nro_matricula_medico})")
