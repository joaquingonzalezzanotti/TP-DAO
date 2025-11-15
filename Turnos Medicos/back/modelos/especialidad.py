import re
class Especialidad:
    def __init__(self, id_especialidad=None, nombre=None, descripcion=None, activo=1):
        self.id_especialidad = id_especialidad
        self.nombre = nombre
        self.descripcion = descripcion
        self.activo = activo

        self._validar()

    def _validar(self):
        # --- Normalización ---
        if isinstance(self.nombre, str):
            self.nombre = self.nombre.strip()

        if isinstance(self.descripcion, str):
            self.descripcion = self.descripcion.strip()

        # --- Validación Nombre ---
        if not isinstance(self.nombre, str) or not self.nombre:
            raise ValueError("El nombre de la especialidad es obligatorio y debe ser texto.")

        if len(self.nombre) < 3:
            raise ValueError("El nombre de la especialidad debe tener al menos 3 caracteres.")
        
        if len(self.nombre) > 50:
            raise ValueError("El nombre no puede superar 50 caracteres.")

        # Evitar caracteres inválidos
        if not re.fullmatch(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+", self.nombre):
            raise ValueError("El nombre de la especialidad contiene caracteres no permitidos.")

        # --- Validación Descripción (es opcional poner descripcion) ---
        if self.descripcion is not None:
            if not isinstance(self.descripcion, str):
                raise ValueError("La descripción debe ser texto.")
            if len(self.descripcion) > 255:
                raise ValueError("La descripción no puede superar los 255 caracteres.")

        # --- Validación Activo ---
        if not isinstance(self.activo, int) or self.activo not in (0, 1):
            raise ValueError("El campo 'activo' debe ser 0 o 1.")     
        
    def __repr__(self):
        return f"Especialidad({self.id}, {self.nombre})"

