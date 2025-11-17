import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

import matplotlib.pyplot as plt
from io import BytesIO

from persistencia.dao.turno_dao import TurnoDAO
from persistencia.dao.medico_dao import MedicoDAO
from turno_service import TurnoService
from medico_service import MedicoService

from datetime import datetime, date

class ReporteService:
    def __init__(self):
        self.turno_service = TurnoService()
        self.medico_service = MedicoService()
        self._root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self._report_dir = os.path.join(self._root, "front", "salidas", "reportes")
        os.makedirs(self._report_dir, exist_ok=True)

    def _output_path(self, nombre_archivo):
        return os.path.join(self._report_dir, nombre_archivo)

    def _format_date_for_filename(self, date_obj):
        """Helper para formatear la fecha a string para el nombre del archivo (solo YYYY-MM-DD)."""
        if isinstance(date_obj, (datetime, date)):
            return date_obj.strftime("%Y-%m-%d")
        elif isinstance(date_obj, str) and len(date_obj) >= 10:
             return date_obj[:10] # Asumiendo formato YYYY-MM-DD
        return "fecha_invalida"

    def listado_turnos_por_medico_en_un_periodo(self, nro_matricula_medico, fecha_inicio, fecha_fin):
        """Genera un listado pdf de turnos para un médico específico dentro de un período determinado."""
        try:
            medico = self.medico_service.obtener_medico_por_matricula(nro_matricula_medico)
        except Exception as e:
            print(f"[ERROR] Fallo al obtener medico por matricula: {e}")
            raise RuntimeError("Ocurrió un error técnico al obtener los datos del médico.")
        
        try:
            turnos = self.turno_service.obtener_turnos_por_medico_en_un_periodo(nro_matricula_medico, fecha_inicio, fecha_fin)
        except Exception as e:
            print(f"[ERROR] Fallo al generar el listado de turnos por medico en un periodo: {e}")
            raise RuntimeError("Ocurrió un error técnico al generar el listado de turnos por médico en un período.")

        fecha_inicio_str = self._format_date_for_filename(fecha_inicio)
        fecha_fin_str = self._format_date_for_filename(fecha_fin)
        
        # Nombre del archivo
        nombre_archivo = f"turnos_{nro_matricula_medico}_{fecha_inicio_str}_al_{fecha_fin_str}.pdf"
        ruta_salida = self._output_path(nombre_archivo)
        doc = SimpleDocTemplate(ruta_salida, pagesize=A4)
        
        # Crear estilos y elementos
        styles = getSampleStyleSheet()
        elements = []
        
        # Encabezado
        title = "Listado de Turnos por Médico en un Período"
        elements.append(Paragraph(title, styles['Title']))
        
        text = (f"Turnos del Dr/a. {medico.apellido}, Matrícula: {medico.nro_matricula}, "
                f"desde: {fecha_inicio_str} hasta: {fecha_fin_str}.")
        elements.append(Paragraph(text, styles['Normal']))
        elements.append(Paragraph("<br/>", styles['Normal'])) # Espacio
        
        # Datos de la tabla
        data = [['ID', 'Fecha y Hora Inicio','Motivo', 'Observaciones', 'Estado', 'DNI Paciente']]

        turnos_filtrados = [t for t in turnos if getattr(t, 'estado', '').lower() != 'disponible']

        for turno in turnos_filtrados:
            # Asumo que fecha_hora_inicio es un objeto datetime o se puede convertir.
            fecha_hora_str = ""
            if isinstance(turno.fecha_hora_inicio, (datetime, date)):
                fecha_hora_str = turno.fecha_hora_inicio.strftime("%Y-%m-%d %H:%M")
            elif isinstance(turno.fecha_hora_inicio, str):
                fecha_hora_str = turno.fecha_hora_inicio # Si ya viene como string
                
            data.append([
                turno.id_turno,
                fecha_hora_str,
                turno.motivo if turno.motivo else "",
                turno.observaciones if turno.observaciones else "",
                turno.estado,
                turno.dni_paciente if turno.dni_paciente else "N/A"
            ])
            
        # Tabla y Estilo
        col_widths = [0.5 * inch, 1.5 * inch, 1.5 * inch, 2.0 * inch, 1.0 * inch, 1.0 * inch]
        table = Table(data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'), # Centrar encabezados
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        # 4. Construir el informe
        try:
            doc.build(elements)
            print(f"[OK] Reporte PDF generado exitosamente: {nombre_archivo}")
            return nombre_archivo
        except Exception as e:
            print(f"[ERROR PDF] Fallo al construir el documento PDF: {e}")
            raise RuntimeError("Fallo interno al generar el archivo PDF.")
    
    def reporte_cantidad_turnos_por_especialidad(self):
        """
        Genera un reporte PDF histórico con gráficos de torta
        mostrando la cantidad de turnos atendidos por especialidad médica
        y la distribución de estados de turnos para cada especialidad.
        """
        #Creo que en graficos falta agregar 
        try:
            dic_data = self.turno_service.obtener_cantidad_turnos_por_especialidades_y_estado()
        except Exception as e:
            print(f"[ERROR] Fallo al obtener datos para el reporte de turnos por especialidad: {e}")
            raise RuntimeError("Ocurrió un error técnico al obtener los datos para el reporte.")
        
        nombre_archivo = "reporte_cantidad_turnos_por_especialidad.pdf"
        ruta_salida = self._output_path(nombre_archivo)
        doc = SimpleDocTemplate(ruta_salida, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        title = "Reporte de Cantidad de Turnos por Especialidad Médica"
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Paragraph("<br/>", styles['Normal']))
        elements.append(Spacer(1, 12))

        text_1 = ("Este reporte muestra: la distribución historica de turnos atendidos por especialidad médica y la distribución de estados de turnos para cada especialidad.")
        elements.append(Paragraph(text_1, styles['Normal']))
        elements.append(Spacer(1, 12))

        data_1 = []
        labels_1 = []
        
        # 1. Preparación de datos para el Gráfico General (solo 'atendido')
        total_atendidos = sum(estados.get("atendido", 0) for estados in dic_data.values())

        if total_atendidos > 0:
            for especialidad, estados in dic_data.items():
                cantidad_atendida = estados.get("atendido", 0)
                if cantidad_atendida > 0:
                    data_1.append(cantidad_atendida)
                    labels_1.append(f"{especialidad} ({cantidad_atendida})")
            
            # Gráfico general de distribución de Turnos ATENDIDOS
            plt.figure(figsize=(8, 8))
            plt.pie(data_1, labels=labels_1, autopct='%1.1f%%', startangle=140)
            plt.title("Distribución de Turnos Atendidos por Especialidad Médica")
            plt.axis('equal')  # Igualar aspecto para que sea un círculo

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            img = Image(img_buffer, 6*inch, 6*inch)
            elements.append(img)
            elements.append(Spacer(1, 24))
            plt.clf()  # Limpiar la figura para el siguiente gráfico
        else:
             elements.append(Paragraph("<b>No hay turnos con estado 'atendido' para generar el gráfico general.</b>", styles['Normal']))
             elements.append(Spacer(1, 24))


        # 2. Gráficos por especialidad (Distribución de ESTADOS)
        for especialidad, estados in dic_data.items():
            
            # Solo graficar si hay datos
            if any(cantidad > 0 for cantidad in estados.values()):
                labels = [
                    f"{label} ({value})" 
                    for label, value in estados.items() if value > 0
                ]
                data = [value for value in estados.values() if value > 0]

                plt.figure(figsize=(8, 8))
                plt.pie(data, labels=labels, autopct='%1.1f%%', startangle=140)
                plt.title(f"Distribución de Estados de Turnos para {especialidad}")
                plt.axis('equal')

                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png')
                img_buffer.seek(0)
                img = Image(img_buffer, 6*inch, 6*inch)
                elements.append(img)
                elements.append(Spacer(1, 24))
                plt.clf()  # Limpiar la figura para el siguiente gráfico
            else:
                elements.append(Paragraph(f"<b>No hay datos de turnos para la especialidad: {especialidad}</b>", styles['Normal']))
                elements.append(Spacer(1, 12))


        # 3. Construir el informe
        try:
            doc.build(elements)
            print(f"[OK] Reporte PDF generado exitosamente: {ruta_salida}")
            return ruta_salida
        except Exception as e:
            print(f"[ERROR PDF] Fallo al construir el documento PDF: {e}")
            raise RuntimeError("Fallo interno al generar el archivo PDF.")
        

    def reporte_pacientes_atendidos_en_un_periodo(self, fecha_inicio, fecha_fin):
        """
        Genera un reporte PDF con la lista de pacientes atendidos en un período determinado,
        no incluye detalles del médico y del turno, ya que puede haber varios turnos por paciente
        y aquí solo se detalla un única vez.
        """

        try:
            pacientes = self.turno_service.obtener_pacientes_atendidos_por_periodo(fecha_inicio, fecha_fin)
        except Exception as e:
            print(f"[ERROR] Fallo al generar el listado de pacientes en un periodo: {e}")
            raise RuntimeError("Ocurrió un error técnico al generar el listado de pacientes en un período.")

        fecha_inicio_str = self._format_date_for_filename(fecha_inicio)
        fecha_fin_str = self._format_date_for_filename(fecha_fin)
        
        # Nombre del archivo
        nombre_archivo = f"pacientes_atendidos_{fecha_inicio_str}_al_{fecha_fin_str}.pdf"
        ruta_salida = self._output_path(nombre_archivo)
        doc = SimpleDocTemplate(ruta_salida, pagesize=A4)
        
        # Crear estilos y elementos
        styles = getSampleStyleSheet()
        elements = []
        
        # Encabezado
        title = "Listado de Pacientes Atendidos en un Período"
        elements.append(Paragraph(title, styles['Title']))
        
        text = (f"Listado de pacientes atendidos "
                f"desde: {fecha_inicio_str} hasta: {fecha_fin_str}.")
        elements.append(Paragraph(text, styles['Normal']))
        elements.append(Paragraph("<br/>", styles['Normal'])) # Espacio
        
        # Datos de la tabla
        data = [['DNI', 'Nombre', 'Apellido', 'Fecha de Nacimiento', 'Email', 'Dirección']]
        
        for paciente in pacientes:
            # Asumo que fecha_hora_inicio es un objeto datetime o se puede convertir.
            fecha_nacimiento_str = self._format_date_for_filename(paciente.fecha_nacimiento) 

            data.append([
                paciente.dni,
                paciente.nombre,
                paciente.apellido,
                fecha_nacimiento_str,
                paciente.email,
                paciente.direccion if paciente.direccion else "N/A"
            ])
            
        # Tabla y Estilo
        col_widths = [1.0 * inch, 1.25 * inch, 1.25 * inch, 1.0 * inch, 1.5 * inch, 1.5 * inch]
        table = Table(data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'), # Centrar encabezados
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        # 4. Construir el informe
        try:
            doc.build(elements)
            print(f"[OK] Reporte PDF generado exitosamente: {ruta_salida}")
            return ruta_salida
        except Exception as e:
            print(f"[ERROR PDF] Fallo al construir el documento PDF: {e}")
            raise RuntimeError("Fallo interno al generar el archivo PDF.")
        
    def asistencias_vs_inasistencias_de_pacientes(self, fecha_inicio, fecha_fin):
        """
        Genera un gráfico comparando asistencias (turnos atendidos) versus
        inasistencias (ausentes + cancelados) en el período indicado.
        """
        if not (fecha_inicio and fecha_fin):
            raise ValueError("Debe indicar fecha de inicio y fin para este reporte.")

        try:
            resumen = self.turno_service.obtener_resumen_asistencias(fecha_inicio, fecha_fin)
        except Exception as e:
            print(f"[ERROR] Fallo al obtener el resumen de asistencias: {e}")
            raise RuntimeError("Ocurrió un error técnico al obtener los datos del reporte.")

        asistencias = resumen.get('atendido', 0)
        inasistencias = resumen.get('ausente', 0) + resumen.get('cancelado', 0)

        if asistencias == 0 and inasistencias == 0:
            raise ValueError("No hay turnos registrados en el periodo seleccionado.")

        fecha_inicio_str = self._format_date_for_filename(fecha_inicio)
        fecha_fin_str = self._format_date_for_filename(fecha_fin)
        nombre_archivo = f"asistencias_vs_inasistencias_{fecha_inicio_str}_al_{fecha_fin_str}.pdf"

        doc = SimpleDocTemplate(nombre_archivo, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        title = "Asistencias vs Inasistencias de Pacientes"
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 12))
        resumen_text = (
            f"Período analizado: {fecha_inicio_str} a {fecha_fin_str}. "
            "Se consideran asistencias los turnos en estado 'atendido' y "
            "inasistencias los turnos en estado 'ausente' o 'cancelado'."
        )
        elements.append(Paragraph(resumen_text, styles['Normal']))
        elements.append(Spacer(1, 12))

        data = [
            ['Categoría', 'Cantidad'],
            ['Asistencias', asistencias],
            ['Inasistencias', inasistencias]
        ]
        table = Table(data, colWidths=[2 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 24))

        # Gráfico
        labels = ['Asistencias', 'Inasistencias']
        valores = [asistencias, inasistencias]
        colores = ['#4CAF50', '#F44336']

        plt.figure(figsize=(5, 5))
        plt.pie(valores, labels=labels, autopct='%1.1f%%', colors=colores, startangle=90)
        plt.title('Distribución de asistencias e inasistencias')
        plt.axis('equal')
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        elements.append(Image(img_buffer, 4.5 * inch, 4.5 * inch))
        plt.clf()

        try:
            doc.build(elements)
            print(f"[OK] Reporte PDF generado exitosamente: {ruta_salida}")
            return ruta_salida
        except Exception as e:
            print(f"[ERROR PDF] Fallo al construir el documento PDF: {e}")
            raise RuntimeError("Fallo interno al generar el archivo PDF.")

