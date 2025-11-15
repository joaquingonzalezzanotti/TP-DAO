import re
from datetime import datetime, date

class Paciente:
    def __init__(self, dni, nombre, apellido, fecha_nacimiento, email, direccion, activo=1):
        # Asignamos los atributos y normalizamos cadenas
        self.dni = dni
        self.nombre = nombre.strip() if isinstance(nombre, str) else nombre
        self.apellido = apellido.strip() if isinstance(apellido, str) else apellido
        self.fecha_nacimiento = fecha_nacimiento
        self.email = email.strip() if isinstance(email, str) else email
        self.direccion = direccion.strip() if isinstance(direccion, str) else direccion
        self.activo = activo 

        # Ejecutamos la validación
        self._validar()

    def _validar(self):
        # Validación DNI
        if not isinstance(self.dni, int):
            raise ValueError("El DNI debe ser numérico.")
        if len(str(self.dni)) < 7 or len(str(self.dni)) > 8:
            raise ValueError("El DNI debe tener entre 7 y 8 dígitos.")
        
        # Nombre y Apellido: verifica tipo y que la longitud limpia sea >= 2
        if not isinstance(self.nombre, str) or len(self.nombre) < 2:
            raise ValueError("El nombre debe ser una cadena de texto válida y tener al menos 2 caracteres.")
        if len(self.nombre) > 50:
            raise ValueError("El nombre no puede superar 50 caracteres.")        
        if not isinstance(self.apellido, str) or len(self.apellido) < 2:
            raise ValueError("El apellido debe ser una cadena de texto válida y tener al menos 2 caracteres.")
        if len(self.apellido) > 50:
            raise ValueError("El apellido no puede superar 50 caracteres.")
                
        # --- Validación Direccion (es opcional poner) ---
        if self.direccion is not None:
            if not isinstance(self.direccion, str):
                raise ValueError("La direccion debe ser texto.")
            if len(self.direccion) > 50:
                raise ValueError("La direccion no puede superar los 50 caracteres.")
                   
        # Validación y Conversión: Fecha de Nacimiento
        try:
            fecha_nac = None
            if isinstance(self.fecha_nacimiento, str):
                 # Convertir el string a objeto date
                fecha_nac = datetime.strptime(self.fecha_nacimiento, '%Y-%m-%d').date()
            elif isinstance(self.fecha_nacimiento, (datetime, date)):
                fecha_nac = self.fecha_nacimiento.date() if isinstance(self.fecha_nacimiento, datetime) else self.fecha_nacimiento
            else:
                 raise ValueError("La fecha de nacimiento debe ser un string ('YYYY-MM-DD') o un objeto date/datetime.")

            # Validación Lógica
            if fecha_nac >= datetime.now().date():
                raise ValueError("La fecha de nacimiento no puede ser en el futuro.")
                
            # ESTANDARIZACIÓN: Reasignar el atributo con el tipo date() limpio
            self.fecha_nacimiento = fecha_nac 
            
        except ValueError as e:
            raise ValueError(f"Fecha de nacimiento inválida: {e}")
                    
        # Validación Email
        if not isinstance(self.email, str) or not self.email:
            raise ValueError("El email no puede estar vacío.")
            
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.fullmatch(email_regex, self.email):
            raise ValueError("Formato de email inválido.")

        if len(self.email) > 50:
            raise ValueError("El email no puede superar 50 caracteres.")
            
        # Validación Activo
        if not isinstance(self.activo, int) or self.activo not in [0, 1]:
            raise ValueError("El estado 'activo' debe ser 1 (True) o 0 (False).")