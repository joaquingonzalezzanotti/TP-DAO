class HistorialClinico:
    def __init__(self, dni_paciente):
        self.dni_paciente = dni_paciente
        self._validar()

    def _validar(self):
        if not isinstance(self.dni_paciente, int):
            raise ValueError("El DNI del paciente debe ser numérico.")
        if len(str(self.dni_paciente)) not in (7, 8):
            raise ValueError("El DNI debe tener entre 7 y 8 dígitos.")

    def __repr__(self):
        return f"HistorialClinico(paciente_dni={self.dni_paciente})"
