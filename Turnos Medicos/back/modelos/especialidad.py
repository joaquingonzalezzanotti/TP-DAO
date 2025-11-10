class Especialidad:
    def __init__(self, id_especialidad=None, nombre=None, descripcion=None, activo=1):
        self.id_especialidad = id_especialidad
        self.nombre = nombre
        self.descripcion = descripcion
        self.activo = activo

        if not self.nombre:
            raise ValueError("La especialidad debe tener un nombre.")

    def __repr__(self):
        return f"Especialidad({self.id}, {self.nombre})"
