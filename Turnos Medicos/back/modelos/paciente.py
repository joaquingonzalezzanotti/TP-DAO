class Paciente:
    def __init__(self, dni, nombre, apellido, fecha_nacimiento, email, direccion, activo=1):
        self.dni = dni
        self.nombre = nombre
        self.apellido = apellido
        self.fecha_nacimiento = fecha_nacimiento
        self.email = email
        self.direccion = direccion
        self.activo = activo 

        self._validar()

    def _validar(self):
        if not isinstance(self.dni, int):
            raise ValueError("El DNI debe ser numérico.")
        if len(str(self.dni)) < 7 or len(str(self.dni)) > 8:
            raise ValueError("El DNI debe tener entre 7 y 8 dígitos.")
        if not self.nombre or not self.apellido:
            raise ValueError("El paciente debe tener nombre y apellido.")

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        return f"Paciente({self.dni}, {self.nombre}, {self.apellido}, {self.email})"
