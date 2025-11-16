import re
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
        # --- Validación Nro de Matrícula ---
        if not isinstance(self.nro_matricula, int):
            raise ValueError("La matrícula del médico debe ser un número entero.")

        if self.nro_matricula <= 0 or self.nro_matricula > 999999:
            raise ValueError("La matrícula debe ser un número positivo y maximo 999999.")

        # --- Normalización ---
        if isinstance(self.nombre, str):
            self.nombre = self.nombre.strip()
        if isinstance(self.apellido, str):
            self.apellido = self.apellido.strip()
        if isinstance(self.email, str):
            self.email = self.email.strip()

        # --- Validación Nombre ---
        if not isinstance(self.nombre, str) or len(self.nombre) < 2:
            raise ValueError("El nombre debe ser una cadena válida con al menos 2 caracteres.")
        
        if len(self.nombre) > 50:
            raise ValueError("El nombre no puede superar 50 caracteres.")        

        # --- Validación Apellido ---
        if not isinstance(self.apellido, str) or len(self.apellido) < 2:
            raise ValueError("El apellido debe ser una cadena válida con al menos 2 caracteres.")

        if len(self.apellido) > 50:
            raise ValueError("El apellido no puede superar 50 caracteres.")

        # --- Validación Email (es opcional poner) ---
        if self.email is not None:
            if not isinstance(self.email, str):
                raise ValueError("El email debe ser texto.")

            if len(self.email) > 50:
                raise ValueError("El email no puede superar 50 caracteres.")

            email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.fullmatch(email_regex, self.email):
                raise ValueError("Formato de email inválido.")

        # --- Validación Especialidad ---
        if not isinstance(self.id_especialidad, int):
            raise ValueError("El ID de especialidad debe ser numérico.")

        if self.id_especialidad <= 0:
            raise ValueError("El ID de especialidad debe ser mayor que cero.")

        # --- Validación Activo ---
        if self.activo not in (0, 1):
            raise ValueError("El estado 'activo' debe ser 1 (activo) o 0 (inactivo).")
        
    def __repr__(self):
        return f"Medico({self.id}, {self.nombre}, {self.apellido}, esp={self.especialidad_id})"
