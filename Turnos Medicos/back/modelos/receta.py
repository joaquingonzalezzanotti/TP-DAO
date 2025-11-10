class Receta:
    def __init__(self, id_receta=None, fecha_emision=None, medicamentos=None,
                 detalle=None, id_consulta=None):
        self.id_receta = id_receta
        self.fecha_emision = fecha_emision
        self.medicamentos = medicamentos
        self.detalle = detalle
        self.id_consulta = id_consulta

        self._validar()

    def _validar(self):
        if not self.fecha_emision:
            raise ValueError("La receta debe tener una fecha de emisión.")
        if not self.medicamentos:
            raise ValueError("La receta debe incluir medicamentos.")
        if not isinstance(self.id_consulta, int):
            raise ValueError("El ID de consulta debe ser numérico.")

    def __repr__(self):
        return (f"Receta(id={self.id_receta}, consulta={self.id_consulta}, "
                f"fecha={self.fecha_emision}, meds={self.medicamentos})")
