from datetime import datetime, date

class Receta:
    def __init__(self, id_receta=None, fecha_emision=None, medicamentos=None,
                 detalle=None, id_consulta=None):
        self.id_receta = id_receta
        self.fecha_emision = fecha_emision
        self.medicamentos = medicamentos.strip() if isinstance(medicamentos, str) else medicamentos
        self.detalle = detalle.strip() if isinstance(detalle, str) else detalle
        self.id_consulta = id_consulta
        self._validar()

    def _validar(self):

        # VALIDACIÓN FECHA_EMISION
        try:
            fecha = None

            if isinstance(self.fecha_emision, str):
                fecha = datetime.strptime(self.fecha_emision, "%Y-%m-%d").date()
            elif isinstance(self.fecha_emision, (datetime, date)):
                fecha = (self.fecha_emision.date()
                         if isinstance(self.fecha_emision, datetime)
                         else self.fecha_emision)
            else:
                raise ValueError("La fecha_emision debe ser string 'YYYY-MM-DD' o date/datetime.")

            # Validación lógica: no puede ser en el futuro
            if fecha > datetime.now().date():
                raise ValueError("La fecha de emisión no puede ser futura.")
            
            # Estándar: guardar formateada a date
            self.fecha_emision = fecha

        except ValueError as e:
            raise ValueError(f"Fecha de emisión inválida: {e}")

        # VALIDACIÓN MEDICAMENTOS
        if not isinstance(self.medicamentos, str) or len(self.medicamentos.strip()) == 0:
            raise ValueError("El campo 'medicamentos' es obligatorio y debe ser texto.")

        if len(self.medicamentos) > 200:
            raise ValueError("El campo 'medicamentos' no puede superar los 200 caracteres.")

        # VALIDACIÓN DETALLE (opcional completar)
        if self.detalle is not None:
            if not isinstance(self.detalle, str):
                raise ValueError("El detalle debe ser texto.")
            if len(self.detalle) > 500:
                raise ValueError("El detalle no puede superar 500 caracteres.")

        # VALIDACIÓN ID_CONSULTA (FK)
        if not isinstance(self.id_consulta, int):
            raise ValueError("id_consulta debe ser un entero válido.")
        if self.id_consulta <= 0:
            raise ValueError("id_consulta debe ser un entero positivo.")
