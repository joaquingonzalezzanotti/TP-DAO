import os
from datetime import date, datetime
from textwrap import wrap

from persistencia.dao.receta_dao import RecetaDAO
from persistencia.dao.consulta_dao import ConsultaDAO
from persistencia.dao.paciente_dao import PacienteDAO
from persistencia.dao.medico_dao import MedicoDAO
from persistencia.dao.especialidad_dao import EspecialidadDAO
from persistencia.dao.historial_clinico_dao import HistorialClinicoDAO
from persistencia.persistencia_errores import IntegridadError, DatabaseError
from modelos.receta import Receta
from modelos.historial_clinico import HistorialClinico

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


class RecetaService:
    """Registra recetas y genera el PDF electrónico."""

    INFO_CLINICA = {
        "nombre": "Clínica UTN",
        "direccion": "Maestro M. Lopez esq. Cruz Roja, Córdoba",
        "telefono": "+54 (351) 468-1234",
        "sitio_web": "www.clinica-utn.edu.ar",
    }

    def __init__(self):
        self.receta_dao = RecetaDAO()
        self.consulta_dao = ConsultaDAO()
        self.paciente_dao = PacienteDAO()
        self.medico_dao = MedicoDAO()
        self.especialidad_dao = EspecialidadDAO()
        self.historial_dao = HistorialClinicoDAO()

        self._project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self._default_output = os.path.join(self._project_root, "salidas", "recetas")
        self.logo_path = os.path.join(self._project_root, "assets", "logo_utn.png")

    def registrar_receta(self, fecha_emision, medicamentos, detalle, id_consulta, output_dir=None):
        """Crea la receta (si no existe) y emite un PDF con la información estructurada."""
        try:
            consulta = self.consulta_dao.obtener_por_id(id_consulta)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al obtener la consulta {id_consulta}: {e}")

        if not consulta:
            raise ValueError(f"No existe la consulta #{id_consulta}.")

        try:
            existente = self.receta_dao.obtener_por_consulta(id_consulta)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al verificar recetas existentes: {e}")

        if existente:
            raise ValueError("La consulta seleccionada ya tiene una receta registrada.")

        receta = Receta(
            fecha_emision=fecha_emision,
            medicamentos=medicamentos,
            detalle=detalle,
            id_consulta=id_consulta
        )

        try:
            self.receta_dao.crear(receta)
        except IntegridadError as e:
            raise ValueError(str(e))
        except DatabaseError as e:
            raise RuntimeError(str(e))

        self._ensure_historial(consulta.dni_paciente)

        payload = self._build_payload(receta, consulta)
        output_dir = output_dir or self._default_output
        os.makedirs(output_dir, exist_ok=True)

        filename = f"receta_consulta_{id_consulta}_receta_{receta.id_receta}.pdf"
        destino = os.path.join(output_dir, filename)

        self._emit_pdf(payload, destino)

        return receta, destino

    def _ensure_historial(self, dni):
        try:
            if not self.historial_dao.obtener_por_id(dni):
                self.historial_dao.crear(HistorialClinico(dni))
        except Exception:
            pass

    def _build_payload(self, receta, consulta):
        paciente = self._obtener_paciente(consulta.dni_paciente)
        medico, especialidad = self._obtener_medico_y_especialidad(consulta.nro_matricula_medico)

        medicamentos_list = self._parse_medicamentos(receta.medicamentos)

        return {
            "info_clinica": self.INFO_CLINICA,
            "info_medico": {
                "nombre_completo": f"{medico.nombre} {medico.apellido}",
                "nro_matricula": medico.nro_matricula,
                "especialidad": especialidad or "No registrada",
            },
            "info_paciente": {
                "nombre_completo": f"{paciente.nombre} {paciente.apellido}",
                "dni": paciente.dni,
            },
            "receta": {
                "id_consulta": consulta.id_consulta,
                "fecha_emision": receta.fecha_emision.strftime("%Y-%m-%d")
                if isinstance(receta.fecha_emision, (datetime, date))
                else str(receta.fecha_emision),
                "diagnostico_principal": consulta.diagnostico,
                "medicamentos": medicamentos_list,
                "validez_dias": 30,
                "observaciones_adicionales": receta.detalle or "Sin observaciones adicionales.",
            },
        }

    def _obtener_paciente(self, dni):
        try:
            paciente = self.paciente_dao.obtener_por_id(dni)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al obtener paciente {dni}: {e}")
        if not paciente:
            raise ValueError(f"No existe el paciente con DNI {dni}.")
        return paciente

    def _obtener_medico_y_especialidad(self, matricula):
        try:
            medico = self.medico_dao.obtener_por_id(matricula)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al obtener médico {matricula}: {e}")
        if not medico:
            raise ValueError(f"No existe el médico con matrícula {matricula}.")
        especialidad_nombre = ""
        try:
            especialidad = self.especialidad_dao.obtener_por_id(medico.id_especialidad)
            if especialidad:
                especialidad_nombre = especialidad.nombre
        except Exception:
            especialidad_nombre = ""
        return medico, especialidad_nombre

    def _parse_medicamentos(self, texto):
        meds = []
        if texto:
            lines = [line.strip("•- ").strip() for line in texto.splitlines() if line.strip()]
            for line in lines:
                meds.append({
                    "nombre_generico": line,
                    "nombre_comercial": "",
                    "presentacion": "",
                    "cantidad": "",
                    "posologia": "",
                })
        if not meds:
            meds.append({
                "nombre_generico": texto or "No informado",
                "nombre_comercial": "",
                "presentacion": "",
                "cantidad": "",
                "posologia": "",
            })
        return meds

    def _emit_pdf(self, payload, destino):
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "No se pudo generar el PDF porque la librería 'reportlab' no está instalada."
            )

        receta = payload["receta"]
        clinica = payload["info_clinica"]
        medico = payload["info_medico"]
        paciente = payload["info_paciente"]

        c = canvas.Canvas(destino, pagesize=A4)
        width, height = A4
        y = height - 40

        if os.path.exists(self.logo_path):
            try:
                c.drawImage(
                    self.logo_path,
                    width - 150,
                    height - 130,
                    width=110,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 15)
        c.drawString(40, y, clinica["nombre"])
        c.setFont("Helvetica", 10)
        y -= 15
        c.drawString(40, y, clinica["direccion"])
        y -= 12
        c.drawString(40, y, f"Tel: {clinica['telefono']} - {clinica['sitio_web']}")

        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Datos del Paciente")
        c.setFont("Helvetica", 10)
        y -= 15
        c.drawString(40, y, f"Nombre: {paciente['nombre_completo']}")
        y -= 12
        c.drawString(40, y, f"DNI: {paciente['dni']}")

        y -= 25
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Profesional")
        c.setFont("Helvetica", 10)
        y -= 15
        c.drawString(40, y, f"{medico['nombre_completo']} - Matrícula {medico['nro_matricula']}")
        y -= 12
        c.drawString(40, y, f"Especialidad: {medico['especialidad']}")

        y -= 25
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Diagnóstico principal")
        c.setFont("Helvetica", 10)
        y -= 15
        y = self._draw_wrapped_text(c, receta["diagnostico_principal"], y, width)

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Medicamentos")
        y -= 15

        c.setFont("Helvetica", 10)
        for idx, med in enumerate(receta["medicamentos"], start=1):
            if y < 100:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica", 10)
            c.drawString(40, y, f"{idx}. {med['nombre_generico']}")
            y -= 12
            for label, value in [
                ("Nombre comercial", med.get("nombre_comercial") or "-"),
                ("Presentación", med.get("presentacion") or "-"),
                ("Cantidad", med.get("cantidad") or "-"),
                ("Posología", med.get("posologia") or "-"),
            ]:
                y = self._draw_wrapped_text(c, f"{label}: {value}", y, width, indent=15)
            y -= 5

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Observaciones")
        c.setFont("Helvetica", 10)
        y -= 15
        y = self._draw_wrapped_text(c, receta["observaciones_adicionales"], y, width)

        y -= 25
        c.drawString(
            40, y, f"Validez: {receta['validez_dias']} días - Emitida el {receta['fecha_emision']}"
        )

        c.setFont("Helvetica", 9)
        c.drawRightString(width - 40, 30, "Documento generado automáticamente por Clínica UTN")
        c.save()

    def _draw_wrapped_text(self, canvas_obj, text, y, width, indent=0):
        max_chars = 95
        for line in wrap(text or "", width=max_chars):
            canvas_obj.drawString(40 + indent, y, line)
            y -= 12
        return y
