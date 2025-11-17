from datetime import datetime, time
import re

class Agenda:
    
    # Días de la semana válidos (en español)
    DIAS_VALIDOS_ES = {
        "lunes", "martes", "miércoles", "miercoles", 
        "jueves", "viernes", "sábado", "sabado", "domingo"
    }
    
    def __init__(self, nro_matricula_medico, mes, dias_semana, hora_inicio, hora_fin, duracion_minutos):
        self.nro_matricula_medico = nro_matricula_medico
        self.mes = mes
        self.dias_semana = dias_semana.strip().lower() if isinstance(dias_semana, str) else dias_semana
        self.hora_inicio = hora_inicio.strip() if isinstance(hora_inicio, str) else hora_inicio
        self.hora_fin = hora_fin.strip() if isinstance(hora_fin, str) else hora_fin
        self.duracion_minutos = duracion_minutos

        self._validar()

    def _validar(self):
        # Validaciones Básicas de Tipos y Rangos      
        if not isinstance(self.nro_matricula_medico, int):
            raise ValueError("La matrícula del médico debe ser numérica.")
        if not (1 <= self.mes <= 12):
            raise ValueError("El mes debe estar entre 1 y 12.")
        if not (0 < self.duracion_minutos <= 480):
            raise ValueError("La duración del turno debe ser positiva y maximo 480.")
        if not isinstance(self.duracion_minutos, int):
            raise ValueError("La duración del turno debe ser un número entero de minutos.")
        
        # Validaciones de Días de la Semana
        if not isinstance(self.dias_semana, str) or not self.dias_semana:
            raise ValueError("Debe especificar los días de la semana como un texto separado por comas.")

        dias_ingresados = [d.strip() for d in self.dias_semana.split(",") if d.strip()]
        if not dias_ingresados:
            raise ValueError("Debe especificar al menos un día válido.")
        
        # Validar cada día individualmente
        dias_validos_finales = []
        for dia in dias_ingresados:
            if dia not in self.DIAS_VALIDOS_ES:
                raise ValueError(f"Día de la semana '{dia}' inválido. Días permitidos: {', '.join(self.DIAS_VALIDOS_ES)}")
            dias_validos_finales.append(dia)

        # *** NORMALIZACIÓN DEL ATRIBUTO INTERNO ***
        # Reasignamos self.dias_semana con la cadena limpia y estandarizada (sin espacios)
        #    Ej: ["lunes", "martes", "miércoles"] -> "lunes,martes,miércoles"
        self.dias_semana = ",".join(dias_validos_finales)

        # Validaciones y Estandarización de Horas (hora_inicio, hora_fin)
        hora_inicio_obj = self._validar_y_convertir_hora(self.hora_inicio, "inicio")
        hora_fin_obj = self._validar_y_convertir_hora(self.hora_fin, "fin")

        # Validación Lógica de Horas: Fin debe ser posterior a Inicio
        if hora_fin_obj <= hora_inicio_obj:
            raise ValueError("La hora de fin debe ser estrictamente posterior a la hora de inicio.")
            
        # ESTANDARIZACIÓN: Reasignar los atributos como objetos time() de Python
        self.hora_inicio = hora_inicio_obj
        self.hora_fin = hora_fin_obj


    def _validar_y_convertir_hora(self, valor_hora, nombre_campo) -> time:
        """Helper para validar el formato 'HH:MM' y convertir a objeto datetime.time."""
        if isinstance(valor_hora, time):
            return valor_hora
        
        if not isinstance(valor_hora, str) or not re.fullmatch(r"^\d{2}:\d{2}$", valor_hora):
            raise ValueError(f"La hora de {nombre_campo} debe ser una cadena de texto en formato 'HH:MM'.")
            
        try:
            # datetime.strptime(str, format) convierte a datetime, luego extraemos solo el time()
            return datetime.strptime(valor_hora, '%H:%M').time()
        except ValueError:
            # Esto captura si el formato HH:MM es válido pero los valores no lo son (ej: 30:00)
            raise ValueError(f"La hora de {nombre_campo} ('{valor_hora}') no es una hora real y válida (HH:MM).")