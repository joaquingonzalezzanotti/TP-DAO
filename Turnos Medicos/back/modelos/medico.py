class Medico:
    def __init__(self, nro_matricula, nombre, apellido, email, id_especialidad, activo=1):
        self.nro_matricula = nro_matricula
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.id_especialidad= id_especialidad
        self.activo = activo

        self._validar()

    def _validar(self):
        if not self.nombre or not self.apellido:
            raise ValueError("El médico debe tener nombre y apellido.")
        if not isinstance(self.especialidad_id, int):
            raise ValueError("La especialidad debe ser un ID numérico.")

    def __repr__(self):
        return f"Medico({self.id}, {self.nombre}, {self.apellido}, esp={self.especialidad_id})"
