from datetime import datetime

class Consulta:
    def __init__(self, id_consulta=None, fecha_hora=None, diagnostico=None,
                 observaciones=None, dni_paciente=None,
                 nro_matricula_medico=None):
        self.id_consulta = id_consulta
        self.fecha_hora = fecha_hora
        self.diagnostico = diagnostico.strip() if isinstance(diagnostico, str) else diagnostico
        self.observaciones = observaciones.strip() if isinstance(observaciones, str) else observaciones
        self.dni_paciente = dni_paciente
        self.nro_matricula_medico = nro_matricula_medico

        self._validar()

    def _validar(self):
        """
        Valida la información de la consulta médica.
        """

        # Validación fecha/hora
        if isinstance(self.fecha_hora, str):
            try:
                self.fecha_hora = datetime.strptime(self.fecha_hora, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    # Intento alternativo con segundos
                    self.fecha_hora = datetime.strptime(self.fecha_hora, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(
                        "La fecha de la consulta debe tener formato 'YYYY-MM-DD HH:MM' o 'YYYY-MM-DD HH:MM:SS'."
                    )
        elif not isinstance(self.fecha_hora, datetime):
            raise ValueError("La fecha y hora de la consulta debe ser un datetime o un string válido.")

        if self.fecha_hora > datetime.now():
            raise ValueError("Una consulta no puede tener una fecha futura.")

        # Validación Diagnóstico
        if not isinstance(self.diagnostico, str) or len(self.diagnostico) < 5:
            raise ValueError("El diagnóstico debe ser una cadena de texto de al menos 5 caracteres.")

        if len(self.diagnostico) > 500:
            raise ValueError("El diagnóstico no puede exceder los 500 caracteres.")

        # Validación Observaciones (opcional completar)
        if self.observaciones is not None:
            if not isinstance(self.observaciones, str):
                raise ValueError("Las observaciones deben ser texto.")
            if len(self.observaciones) > 1000:
                raise ValueError("Las observaciones no pueden superar los 1000 caracteres.")

        # Validación dni_paciente
        if not isinstance(self.dni_paciente, int):
            raise ValueError("El DNI del paciente debe ser numérico.")
        if len(str(self.dni_paciente)) not in (7, 8):
            raise ValueError("El DNI debe tener entre 7 y 8 dígitos.")

        # Validación FK: nro_matricula_medico
        if not isinstance(self.nro_matricula_medico, int) or self.nro_matricula_medico <= 0 or self.nro_matricula_medico > 999999:
            raise ValueError("El número de matrícula del médico debe ser un entero positivo y maximo 999999.")