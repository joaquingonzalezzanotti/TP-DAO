import os
import sys
import re
import calendar
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import date, datetime

# Ajustar rutas para poder importar módulos del backend
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACK_DIR = os.path.join(BASE_DIR, 'back')
SERVICIOS_DIR = os.path.join(BACK_DIR, 'servicios')
if BACK_DIR not in sys.path:
    sys.path.insert(0, BACK_DIR)
if SERVICIOS_DIR not in sys.path:
    sys.path.insert(0, SERVICIOS_DIR)

try:
    # Importar servicios y DAOs que usaremos
    from medico_service import MedicoService
    from turno_service import TurnoService
    from reporte_service import ReporteService
    from consulta_service import ConsultaService
    from receta_service import RecetaService
    from persistencia.dao.paciente_dao import PacienteDAO
    from persistencia.dao.medico_dao import MedicoDAO
    from persistencia.dao.especialidad_dao import EspecialidadDAO
    from persistencia.dao.receta_dao import RecetaDAO
    from persistencia.dao.historial_clinico_dao import HistorialClinicoDAO
    from modelos.historial_clinico import HistorialClinico
except Exception as e:
    # Si falla la importación, mostraremos un diálogo más tarde.
    IMPORT_ERROR = e
else:
    IMPORT_ERROR = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Gestión Clínica - Frontend')
        self.geometry('1000x600')

        # Estilo general (tema y ajustes visuales)
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), foreground='#0b5f8a')
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('Treeview', font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))

        if IMPORT_ERROR:
            messagebox.showerror('Error de importación', f'No se pudieron cargar módulos del backend:\n{IMPORT_ERROR}')

        # Instancias de servicios/DAOs
        try:
            self.medico_service = MedicoService()
            self.turno_service = TurnoService()
            self.reporte_service = ReporteService()
            self.consulta_service = ConsultaService()
            self.receta_service = RecetaService()
            self.paciente_dao = PacienteDAO()
            self.medico_dao = MedicoDAO()
            self.especialidad_dao = EspecialidadDAO()
            self.receta_dao = RecetaDAO()
            self.historial_dao = HistorialClinicoDAO()
        except Exception:
            # tolerar inicialización fallida; manejaremos con mensajes en botones
            self.medico_service = None
            self.turno_service = None
            self.reporte_service = None
            self.consulta_service = None
            self.receta_service = None
            self.paciente_dao = None
            self.medico_dao = None
            self.especialidad_dao = None
            self.receta_dao = None
            self.historial_dao = None

        self._create_widgets()

    def _create_widgets(self):
        # Cabecera
        header = ttk.Label(self, text='Sistema de Turnos - Clínica', style='Header.TLabel')
        header.pack(fill='x', pady=(8, 4))

        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True)

        # Pestaña Turnos
        frame_turnos = ttk.Frame(nb)
        nb.add(frame_turnos, text='Turnos')
        self._build_turnos_tab(frame_turnos)

        # Pestaña ABC
        frame_abc = ttk.Frame(nb)
        nb.add(frame_abc, text='ABC (Pacientes / Médicos / Especialidades)')
        self._build_abc_tab(frame_abc)

        # Pestaña Historial
        frame_historial = ttk.Frame(nb)
        nb.add(frame_historial, text='Consultas / Recetas / Historial')
        self._build_historial_tab(frame_historial)

        # Pestaña Reportes
        frame_reportes = ttk.Frame(nb)
        nb.add(frame_reportes, text='Reportes')
        self._build_reportes_tab(frame_reportes)

    # ---------- Turnos Tab ----------
    def _build_turnos_tab(self, parent):
        pad = {'padx': 8, 'pady': 8}

        top = ttk.Frame(parent)
        top.pack(fill='x', **pad)

        ttk.Label(top, text='Médico:').grid(row=0, column=0, sticky='w')
        self.combo_medicos = ttk.Combobox(top, state='readonly')
        self.combo_medicos.grid(row=0, column=1, sticky='w')

        ttk.Label(top, text='Mes (1-12):').grid(row=0, column=2, sticky='w')
        self.entry_mes = ttk.Entry(top, width=6)
        self.entry_mes.grid(row=0, column=3, sticky='w')

        ttk.Label(top, text='Año:').grid(row=0, column=4, sticky='w')
        self.entry_anio = ttk.Entry(top, width=8)
        self.entry_anio.grid(row=0, column=5, sticky='w')

        hoy = date.today()
        self.entry_mes.insert(0, str(hoy.month))
        self.entry_anio.insert(0, str(hoy.year))

        btn_generar = ttk.Button(top, text='Generar todos los turnos del mes', command=self._on_generar_turnos)
        btn_generar.grid(row=0, column=6, sticky='w', padx=10)

        btn_listar = ttk.Button(top, text='Listar turnos del período', command=self._load_turnos)
        btn_listar.grid(row=0, column=7, sticky='w', padx=10)

        btn_refrescar = ttk.Button(top, text='Refrescar médicos', command=self._load_medicos)
        btn_refrescar.grid(row=0, column=8, sticky='w')

        # Treeview de resultados
        cols = ('id', 'fecha', 'estado', 'paciente', 'medico')
        self.tree_turnos = ttk.Treeview(parent, columns=cols, show='headings')
        for c in cols:
            self.tree_turnos.heading(c, text=c.capitalize())
            self.tree_turnos.column(c, width=150)
        self.tree_turnos.pack(fill='both', expand=True, padx=8, pady=8)

        form = ttk.LabelFrame(parent, text='Registrar turno (seleccione un horario de la tabla)')
        form.pack(fill='x', padx=8, pady=(0, 8))

        ttk.Label(form, text='DNI paciente:').grid(row=0, column=0, sticky='w', padx=4, pady=4)
        self.entry_turno_dni = ttk.Entry(form, width=14)
        self.entry_turno_dni.grid(row=0, column=1, sticky='w', padx=4, pady=4)

        ttk.Label(form, text='Motivo:').grid(row=0, column=2, sticky='w', padx=4, pady=4)
        self.entry_turno_motivo = ttk.Entry(form, width=35)
        self.entry_turno_motivo.grid(row=0, column=3, sticky='we', padx=4, pady=4)

        ttk.Label(form, text='Observaciones:').grid(row=1, column=0, sticky='w', padx=4, pady=4)
        self.entry_turno_obs = ttk.Entry(form, width=60)
        self.entry_turno_obs.grid(row=1, column=1, columnspan=3, sticky='we', padx=4, pady=4)

        btn_programar = ttk.Button(form, text='Asignar turno al paciente', command=self._on_programar_turno)
        btn_programar.grid(row=0, column=4, rowspan=2, padx=10, pady=4, sticky='nsw')
        # Acciones sobre turnos ya programados
        btn_cancelar = ttk.Button(form, text='Cancelar turno', command=self._on_cancelar_turno)
        btn_cancelar.grid(row=0, column=5, rowspan=1, padx=6, pady=4, sticky='nsw')
        btn_ausente = ttk.Button(form, text='Marcar ausente', command=self._on_marcar_ausente)
        btn_ausente.grid(row=1, column=5, rowspan=1, padx=6, pady=4, sticky='nsw')
        btn_atendido = ttk.Button(form, text='Marcar atendido', command=self._on_marcar_atendido)
        btn_atendido.grid(row=0, column=6, rowspan=2, padx=6, pady=4, sticky='nsw')

        form.columnconfigure(3, weight=1)

        self._load_medicos()

    def _build_historial_tab(self, parent):
        pad = {'padx': 8, 'pady': 8}

        top = ttk.Frame(parent)
        top.pack(fill='x', **pad)

        ttk.Label(top, text='DNI Paciente:').grid(row=0, column=0, sticky='w')
        self.entry_hist_dni = ttk.Entry(top, width=16)
        self.entry_hist_dni.grid(row=0, column=1, sticky='w', padx=(4, 12))

        ttk.Button(top, text='Cargar historial', command=self._load_historial).grid(row=0, column=2, sticky='w')
        ttk.Button(top, text='Registrar consulta', command=self._on_nueva_consulta).grid(row=0, column=3, sticky='w', padx=6)
        ttk.Button(top, text='Registrar receta', command=self._on_nueva_receta).grid(row=0, column=4, sticky='w')

        self.historial_info_var = tk.StringVar(value='Ingrese un DNI y presione "Cargar historial".')
        ttk.Label(parent, textvariable=self.historial_info_var).pack(fill='x', padx=10)

        main = ttk.Frame(parent)
        main.pack(fill='both', expand=True, padx=8, pady=4)

        left = ttk.LabelFrame(main, text='Consultas registradas')
        left.pack(side='left', fill='both', expand=True, padx=(0, 4))

        cols = ('id', 'fecha', 'medico', 'diagnostico')
        self.tree_consultas = ttk.Treeview(left, columns=cols, show='headings', height=12)
        headings = {
            'id': 'ID',
            'fecha': 'Fecha/Hora',
            'medico': 'Médico',
            'diagnostico': 'Diagnóstico'
        }
        widths = {'id': 60, 'fecha': 160, 'medico': 190, 'diagnostico': 260}
        for col in cols:
            self.tree_consultas.heading(col, text=headings[col])
            self.tree_consultas.column(col, width=widths[col], anchor='w')
        self.tree_consultas.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(left, orient='vertical', command=self.tree_consultas.yview)
        sb.pack(side='right', fill='y')
        self.tree_consultas.configure(yscrollcommand=sb.set)
        self.tree_consultas.bind('<<TreeviewSelect>>', self._on_consulta_select)

        right = ttk.LabelFrame(main, text='Receta de la consulta seleccionada')
        right.pack(side='left', fill='both', expand=True, padx=(4, 0))

        self.receta_text = tk.Text(right, height=15, wrap='word')
        self.receta_text.pack(fill='both', expand=True, padx=4, pady=4)
        self.receta_text.configure(state='disabled')
        self._set_receta_text('Seleccione una consulta para ver su receta.')

        self.historial_consultas = {}
        self.selected_consulta_id = None

    def _load_medicos(self):
        try:
            if self.medico_service is None:
                raise RuntimeError('Servicio de médicos no disponible')
            medicos = self.medico_service.obtener_medicos()
            items = []
            for m in medicos:
                label = f"{m.nro_matricula} - {m.apellido}, {m.nombre}"
                items.append(label)
            self.combo_medicos['values'] = items
            if items:
                self.combo_medicos.current(0)
                # Refrescar turnos para el primer médico cargado
                self._load_turnos()
        except Exception as e:
            messagebox.showerror('Error', f'No se pueden cargar médicos: {e}')

    def _load_turnos(self):
        """Llena la grilla con los turnos del médico seleccionado en el mes/año ingresados."""
        if self.turno_service is None or self.medico_dao is None:
            messagebox.showerror('Error', 'Servicios de turnos o médicos no disponibles')
            return

        for item in self.tree_turnos.get_children():
            self.tree_turnos.delete(item)

        sel = self.combo_medicos.get()
        if not sel:
            return

        try:
            nro = int(sel.split('-')[0].strip())
        except Exception:
            messagebox.showerror('Error', 'Formato de médico inválido')
            return

        try:
            medico = self.medico_dao.obtener_por_id(nro)
            if not medico:
                raise ValueError('Médico no encontrado')
            medico_label = f"{medico.apellido}, {medico.nombre} (Mat. {medico.nro_matricula})"
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo obtener el médico: {e}')
            return

        mes = self.entry_mes.get()
        anio = self.entry_anio.get()
        ok, msg = self._validate_month_year(mes, anio)
        if not ok:
            messagebox.showerror('Error', msg)
            return
        mes = int(mes)
        anio = int(anio)

        inicio = date(anio, mes, 1)
        _, dias_mes = calendar.monthrange(anio, mes)
        fin = date(anio, mes, dias_mes)

        try:
            turnos = self.turno_service.obtener_turnos_por_medico_en_un_periodo(
                nro,
                inicio.isoformat(),
                fin.isoformat()
            )
        except Exception as e:
            messagebox.showerror('Error', f'No se pueden cargar turnos: {e}')
            return

        for turno in turnos:
            fecha_val = getattr(turno, 'fecha_hora_inicio', '')
            if isinstance(fecha_val, datetime):
                fecha_val = fecha_val.strftime("%Y-%m-%d %H:%M")

            paciente_val = ''
            dni_paciente = getattr(turno, 'dni_paciente', None)
            if dni_paciente:
                paciente_val = str(dni_paciente)
                if self.paciente_dao is not None:
                    try:
                        paciente = self.paciente_dao.obtener_por_id(dni_paciente)
                        if paciente:
                            paciente_val = f"{dni_paciente} - {paciente.apellido}, {paciente.nombre}"
                    except Exception:
                        paciente_val = str(dni_paciente)

            self.tree_turnos.insert(
                '',
                'end',
                values=(
                    getattr(turno, 'id_turno', ''),
                    fecha_val,
                    getattr(turno, 'estado', ''),
                    paciente_val,
                    medico_label
                )
            )

    def _load_historial(self):
        if self.consulta_service is None:
            messagebox.showerror('Error', 'Servicio de consultas no disponible')
            return

        dni = self.entry_hist_dni.get().strip()
        if not self._is_valid_dni(dni):
            messagebox.showerror('Error', 'Ingrese un DNI válido para consultar el historial.')
            return

        dni_int = int(dni)
        self.selected_consulta_id = None
        self.historial_consultas = {}
        for item in self.tree_consultas.get_children():
            self.tree_consultas.delete(item)

        self._set_receta_text('Seleccione una consulta para ver su receta.')

        try:
            consultas = self.consulta_service.obtener_consultas_por_paciente(dni_int)
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo cargar el historial: {e}')
            return

        label = f'Consultas de DNI {dni_int}'
        if self.paciente_dao is not None:
            try:
                paciente = self.paciente_dao.obtener_por_id(dni_int)
                if paciente:
                    label = f"{paciente.apellido}, {paciente.nombre} (DNI {dni_int})"
            except Exception:
                pass
        self.historial_info_var.set(label)

        if not consultas:
            self._set_receta_text('No hay consultas registradas para este paciente.')
            return

        consultas_ordenadas = sorted(
            consultas,
            key=lambda c: getattr(c, 'fecha_hora', datetime.min)
        )

        for consulta in consultas_ordenadas:
            fecha_obj = getattr(consulta, 'fecha_hora', None)
            fecha_val = fecha_obj.strftime("%Y-%m-%d %H:%M") if isinstance(fecha_obj, datetime) else str(fecha_obj)

            medico_label = str(getattr(consulta, 'nro_matricula_medico', ''))
            if self.medico_dao is not None and getattr(consulta, 'nro_matricula_medico', None):
                try:
                    medico = self.medico_dao.obtener_por_id(consulta.nro_matricula_medico)
                    if medico:
                        medico_label = f"{medico.apellido}, {medico.nombre} (Mat. {medico.nro_matricula})"
                except Exception:
                    medico_label = str(getattr(consulta, 'nro_matricula_medico', ''))

            consulta_id = getattr(consulta, 'id_consulta')
            self.historial_consultas[consulta_id] = consulta
            self.tree_consultas.insert(
                '',
                'end',
                values=(
                    consulta_id,
                    fecha_val,
                    medico_label,
                    getattr(consulta, 'diagnostico', '')
                )
            )

        self._ensure_historial_registrado(dni_int)

    def _ensure_historial_registrado(self, dni_paciente):
        if self.historial_dao is None:
            return
        try:
            if not self.historial_dao.obtener_por_id(dni_paciente):
                self.historial_dao.crear(HistorialClinico(dni_paciente))
        except Exception:
            pass

    def _set_receta_text(self, contenido):
        self.receta_text.configure(state='normal')
        self.receta_text.delete('1.0', tk.END)
        self.receta_text.insert('1.0', contenido)
        self.receta_text.configure(state='disabled')

    def _on_consulta_select(self, _event=None):
        sel = self.tree_consultas.selection()
        if not sel:
            return
        valores = self.tree_consultas.item(sel[0]).get('values', [])
        if not valores:
            return
        try:
            consulta_id = int(valores[0])
        except Exception:
            consulta_id = valores[0]
        self.selected_consulta_id = consulta_id
        self._mostrar_receta_para_consulta(consulta_id)

    def _mostrar_receta_para_consulta(self, consulta_id):
        if self.receta_dao is None:
            self._set_receta_text('Gestión de recetas no disponible.')
            return
        try:
            receta = self.receta_dao.obtener_por_consulta(consulta_id)
        except Exception as e:
            self._set_receta_text(f'No se pudo cargar la receta: {e}')
            return

        if not receta:
            self._set_receta_text('No hay receta registrada para esta consulta.')
            return

        fecha_val = receta.fecha_emision.strftime("%Y-%m-%d") if hasattr(receta.fecha_emision, 'strftime') else str(receta.fecha_emision)
        detalle = receta.detalle or 'Sin detalle adicional.'
        texto = (
            f"ID Receta: {receta.id_receta}\n"
            f"Fecha de emisión: {fecha_val}\n\n"
            f"Medicamentos:\n{receta.medicamentos}\n\n"
            f"Detalle:\n{detalle}"
        )
        self._set_receta_text(texto)

    def _on_nueva_consulta(self):
        if self.consulta_service is None:
            messagebox.showerror('Error', 'Servicio de consultas no disponible')
            return

        dni = self.entry_hist_dni.get().strip()
        if not self._is_valid_dni(dni):
            messagebox.showerror('Error', 'Ingrese un DNI válido antes de registrar la consulta.')
            return
        dni_int = int(dni)

        data = self._open_form_dialog(
            'Registrar consulta',
            [
                ('fecha', 'Fecha y hora (YYYY-MM-DD HH:MM)'),
                ('matricula', 'Matrícula del médico'),
                ('diagnostico', 'Diagnóstico'),
                ('observaciones', 'Observaciones')
            ],
            {
                'fecha': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        )
        if not data:
            return

        fecha = data.get('fecha')
        matricula = data.get('matricula')
        diagnostico = data.get('diagnostico')
        observaciones = data.get('observaciones') or None

        if not fecha or not matricula or not diagnostico:
            messagebox.showerror('Error', 'Fecha, matrícula y diagnóstico son obligatorios.')
            return

        try:
            matricula_int = int(matricula)
        except ValueError:
            messagebox.showerror('Error', 'La matrícula debe ser numérica.')
            return

        try:
            self.consulta_service.agregar_consulta(
                fecha, diagnostico, observaciones, dni_int, matricula_int
            )
            self._ensure_historial_registrado(dni_int)
            messagebox.showinfo('OK', 'Consulta registrada correctamente.')
            self._load_historial()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _on_nueva_receta(self):
        if self.receta_service is None:
            messagebox.showerror('Error', 'Generación de recetas no disponible')
            return

        if not self.selected_consulta_id:
            messagebox.showwarning('Atención', 'Seleccione primero la consulta para la cual desea registrar la receta.')
            return

        consulta_id = self.selected_consulta_id

        data = self._open_form_dialog(
            'Registrar receta',
            [
                ('fecha', 'Fecha de emisión (YYYY-MM-DD)'),
                ('medicamentos', 'Medicamentos'),
                ('detalle', 'Detalle')
            ],
            {
                'fecha': date.today().isoformat()
            }
        )
        if not data:
            return

        fecha = data.get('fecha') or date.today().isoformat()
        medicamentos = data.get('medicamentos')
        detalle = data.get('detalle') or None

        if not medicamentos:
            messagebox.showerror('Error', 'El campo de medicamentos es obligatorio.')
            return

        try:
            receta, pdf_path = self.receta_service.registrar_receta(
                fecha_emision=fecha,
                medicamentos=medicamentos,
                detalle=detalle,
                id_consulta=consulta_id
            )
            mensaje = 'Receta registrada correctamente.'
            if pdf_path:
                mensaje += f"\nPDF generado en:\n{pdf_path}"
            messagebox.showinfo('OK', mensaje)
            self._mostrar_receta_para_consulta(consulta_id)
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _validate_month_year(self, mes, anio):
        # Validaciones básicas: mes 1-12, año >= actual, no permitir meses pasados en el mismo año
        try:
            mes = int(mes)
            anio = int(anio)
        except Exception:
            return False, 'Mes y año deben ser enteros.'
        if not (1 <= mes <= 12):
            return False, 'Mes fuera de rango (1-12).'
        hoy = date.today()
        if anio < hoy.year:
            return False, 'Año no puede ser anterior al actual.'
        if anio == hoy.year and mes < hoy.month:
            return False, 'No puede generar turnos para meses anteriores al actual.'
        return True, ''

    def _is_valid_email(self, email):
        if not email:
            return True
        # Validación simple
        pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _is_valid_date(self, fecha_str):
        try:
            fecha_str = (fecha_str or "").strip()
            # yyyy-mm-dd
            parts = fecha_str.split('-')
            if len(parts) != 3:
                return False
            y, m, d = map(int, parts)
            _ = date(y, m, d)
            return True
        except Exception:
            return False

    def _is_valid_dni(self, dni):
        try:
            dni = str(dni).strip()
            return dni.isdigit() and 5 <= len(dni) <= 10
        except Exception:
            return False

    def _on_generar_turnos(self):
        sel = self.combo_medicos.get()
        if not sel:
            messagebox.showwarning('Atención', 'Seleccione un médico primero')
            return
        try:
            nro = int(sel.split('-')[0].strip())
        except Exception:
            messagebox.showerror('Error', 'Formato de médico inválido')
            return

        try:
            mes = self.entry_mes.get()
            anio = self.entry_anio.get()
            ok, msg = self._validate_month_year(mes, anio)
            if not ok:
                messagebox.showerror('Error', msg)
                return
            mes = int(mes); anio = int(anio)
        except Exception:
            messagebox.showerror('Error', 'Ingrese mes y año válidos')
            return

        try:
            if self.medico_service is None:
                raise RuntimeError('Servicio de médicos no disponible')
            creados = self.medico_service.generar_turnos_de_medico(nro, mes, anio)
            messagebox.showinfo('Ok', f'Se generaron {len(creados)} turnos')
            self._load_turnos()
        except Exception as e:
            messagebox.showerror('Error al generar', str(e))

    def _on_programar_turno(self):
        if self.turno_service is None:
            messagebox.showerror('Error', 'Servicio de turnos no disponible')
            return

        seleccion = self.tree_turnos.selection()
        if not seleccion:
            messagebox.showwarning('Atención', 'Seleccione un turno de la tabla')
            return

        item = self.tree_turnos.item(seleccion[0])
        valores = item.get('values', [])
        if not valores:
            messagebox.showerror('Error', 'No se pudo determinar el turno seleccionado')
            return

        turno_id = valores[0]
        estado_actual = str(valores[2]).lower() if len(valores) > 2 and valores[2] else ''
        if estado_actual and estado_actual != 'disponible':
            messagebox.showerror('Turno no disponible', 'Solo se pueden asignar turnos en estado "disponible".')
            return

        dni = self.entry_turno_dni.get().strip()
        motivo = self.entry_turno_motivo.get().strip()
        observ = self.entry_turno_obs.get().strip()

        if not self._is_valid_dni(dni):
            messagebox.showerror('Error', 'Ingrese un DNI válido (solo números).')
            return
        if not motivo:
            messagebox.showerror('Error', 'El motivo es obligatorio.')
            return

        try:
            turno_id = int(turno_id)
            dni_int = int(dni)
        except Exception:
            messagebox.showerror('Error', 'No se pudo interpretar el turno o el DNI.')
            return

        observ = observ or None

        try:
            self.turno_service.programar_turno(turno_id, dni_int, motivo, observ)
            messagebox.showinfo('OK', 'Turno asignado correctamente.')
            self.entry_turno_motivo.delete(0, tk.END)
            self.entry_turno_obs.delete(0, tk.END)
            self.entry_turno_dni.delete(0, tk.END)
            self._load_turnos()
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    def _on_cancelar_turno(self):
        if self.turno_service is None:
            messagebox.showerror('Error', 'Servicio de turnos no disponible')
            return
        sel = self.tree_turnos.selection()
        if not sel:
            messagebox.showwarning('Atención', 'Seleccione un turno de la tabla')
            return
        item = self.tree_turnos.item(sel[0])
        valores = item.get('values', [])
        if not valores:
            messagebox.showerror('Error', 'No se pudo determinar el turno seleccionado')
            return
        turno_id = valores[0]
        estado_actual = str(valores[2]).lower() if len(valores) > 2 and valores[2] else ''
        if estado_actual != 'programado':
            messagebox.showerror('Error', 'Solo se pueden cancelar turnos en estado "programado".')
            return
        try:
            turno_id = int(turno_id)
            nuevo = self.turno_service.cancelar_turno(turno_id)
            messagebox.showinfo('OK', f'Turno {turno_id} cancelado. Turno disponible creado (ID nuevo: {getattr(nuevo, "id_turno", "n/a")}).')
            self._load_turnos()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _on_marcar_ausente(self):
        if self.turno_service is None:
            messagebox.showerror('Error', 'Servicio de turnos no disponible')
            return
        sel = self.tree_turnos.selection()
        if not sel:
            messagebox.showwarning('Atención', 'Seleccione un turno de la tabla')
            return
        item = self.tree_turnos.item(sel[0])
        valores = item.get('values', [])
        if not valores:
            messagebox.showerror('Error', 'No se pudo determinar el turno seleccionado')
            return
        turno_id = valores[0]
        estado_actual = str(valores[2]).lower() if len(valores) > 2 and valores[2] else ''
        if estado_actual != 'programado':
            messagebox.showerror('Error', 'Solo se pueden marcar ausentes turnos en estado "programado".')
            return
        try:
            turno_id = int(turno_id)
            updated = self.turno_service.marcar_ausente_turno(turno_id)
            messagebox.showinfo('OK', f'Turno {turno_id} marcado como ausente.')
            self._load_turnos()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _on_marcar_atendido(self):
        if self.turno_service is None:
            messagebox.showerror('Error', 'Servicio de turnos no disponible')
            return
        sel = self.tree_turnos.selection()
        if not sel:
            messagebox.showwarning('Atención', 'Seleccione un turno de la tabla')
            return
        item = self.tree_turnos.item(sel[0])
        valores = item.get('values', [])
        if not valores:
            messagebox.showerror('Error', 'No se pudo determinar el turno seleccionado')
            return
        turno_id = valores[0]
        estado_actual = str(valores[2]).lower() if len(valores) > 2 and valores[2] else ''
        if estado_actual != 'programado':
            messagebox.showerror('Error', 'Solo se pueden marcar atendido los turnos en estado "programado".')
            return
        try:
            turno_id = int(turno_id)
            updated = self.turno_service.marcar_atendido_turno(turno_id)
            messagebox.showinfo('OK', f'Turno {turno_id} marcado como atendido.')
            self._load_turnos()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _on_crear_agenda_medico(self):
        # Este método se invoca desde la pestaña ABC cuando se selecciona un médico.
        entidad = self.combo_entidad.get()
        if entidad != 'Médicos':
            messagebox.showwarning('Atención', 'Seleccione la entidad "Médicos" en el panel ABC para crear agenda.')
            return
        sel = self.tree_abc.selection()
        if not sel:
            messagebox.showwarning('Atención', 'Seleccione un médico en la lista antes de crear la agenda.')
            return
        pk = self.tree_abc.item(sel[0])['values'][0]
        try:
            nro = int(pk)
        except Exception:
            messagebox.showerror('Error', 'Matrícula de médico inválida')
            return
        data = self._open_form_dialog('Crear agenda', [('mes', 'Mes (1-12)'), ('anio', 'Año (YYYY)')], {'mes': date.today().month, 'anio': date.today().year})
        if not data:
            return
        mes = data.get('mes')
        anio = data.get('anio')
        try:
            mes_i = int(str(mes).strip())
            anio_i = int(str(anio).strip())
        except Exception:
            messagebox.showerror('Error', 'Mes y año deben ser numéricos')
            return
        try:
            if self.medico_service is None:
                raise RuntimeError('Servicio de médicos no disponible')
            creados = self.medico_service.generar_turnos_de_medico(nro, mes_i, anio_i)
            messagebox.showinfo('OK', f'Se generaron {len(creados)} turnos para el médico {nro} ({mes_i}/{anio_i})')
            # Si estamos en Turnos, refrescar
            self._load_turnos()
        except Exception as e:
            messagebox.showerror('Error', str(e))
    def _open_form_dialog(self, title, fields, initial=None):
        """
        Reusable modal dialog for data entry.
        fields: list of tuples (key, label[, options dict like {'readonly': True}])
        """
        initial = initial or {}

        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        container = ttk.Frame(dlg, padding=10)
        container.pack(fill='both', expand=True)

        entries = {}
        for idx, field in enumerate(fields):
            opts = {}
            if isinstance(field, dict):
                key = field.get('key')
                label = field.get('label', key)
                opts = field
            else:
                if len(field) == 2:
                    key, label = field
                elif len(field) == 3:
                    key, label, opts = field
                else:
                    raise ValueError("Los campos deben definirse como (key, label[, options]).")

            readonly = bool(opts.get('readonly', False))

            ttk.Label(container, text=label).grid(row=idx, column=0, sticky='w', padx=4, pady=4)
            entry = ttk.Entry(container, width=40)
            entry.grid(row=idx, column=1, sticky='we', padx=4, pady=4)
            entry.insert(0, str(initial.get(key, '') or ''))
            if readonly:
                entry.state(['readonly'])
            entries[key] = entry

        btn_frame = ttk.Frame(container)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(12, 0))

        result = {'data': None}

        def accept():
            data = {}
            for key, entry in entries.items():
                data[key] = entry.get().strip()
            result['data'] = data
            dlg.destroy()

        def cancel():
            result['data'] = None
            dlg.destroy()

        ttk.Button(btn_frame, text='Cancelar', command=cancel).pack(side='right', padx=4)
        ttk.Button(btn_frame, text='Aceptar', command=accept).pack(side='right', padx=4)

        dlg.bind('<Return>', lambda event: accept())
        dlg.bind('<Escape>', lambda event: cancel())
        container.columnconfigure(1, weight=1)
        dlg.wait_window()
        return result['data']

    # ---------- ABC Tab ----------
    def _build_abc_tab(self, parent):
        pan = ttk.Panedwindow(parent, orient='horizontal')
        pan.pack(fill='both', expand=True)

        left = ttk.Frame(pan, width=420)
        right = ttk.Frame(pan)
        pan.add(left)
        pan.add(right)

        # Entity selection
        ttk.Label(left, text='Entidad:').pack(anchor='w', padx=8, pady=(8,0))
        self.combo_entidad = ttk.Combobox(left, state='readonly', values=['Pacientes', 'Médicos', 'Especialidades'])
        self.combo_entidad.pack(fill='x', padx=8)
        self.combo_entidad.current(0)
        self.combo_entidad.bind('<<ComboboxSelected>>', lambda e: self._refresh_abc())

        # Treeview (definimos hasta 6 columnas; cada entidad usará las que necesite)
        cols = ('pk', 'col1', 'col2', 'col3', 'col4', 'col5')
        self.tree_abc = ttk.Treeview(left, columns=cols, show='headings')
        for c in cols:
            self.tree_abc.heading(c, text=c.upper())
            self.tree_abc.column(c, width=120)
        self.tree_abc.pack(fill='both', expand=True, padx=8, pady=8)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill='x', padx=8, pady=8)
        ttk.Button(btn_frame, text='Crear', command=self._abc_crear).pack(side='left')
        ttk.Button(btn_frame, text='Editar', command=self._abc_editar).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Eliminar', command=self._abc_eliminar).pack(side='left')
        ttk.Button(btn_frame, text='Crear agenda', command=self._on_crear_agenda_medico).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Refrescar', command=self._refresh_abc).pack(side='left', padx=6)

        # Detail panel (right)
        self.detail_text = tk.Text(right, width=50)
        self.detail_text.pack(fill='both', expand=True, padx=8, pady=8)

        # Bind selection
        self.tree_abc.bind('<<TreeviewSelect>>', self._on_abc_select)

        self._refresh_abc()

    def _refresh_abc(self):
        entidad = self.combo_entidad.get()

        # Actualizar encabezados según la entidad seleccionada.
        # Pacientes: agregar "Fecha de nacimiento" y "Dirección" (total 6 columnas).
        # Médicos: mostrar 4 columnas: Matrícula, Nombre, Apellido, Especialidad (omitimos email aquí).
        # Especialidades: mostrar 3 columnas: ID, Nombre, Descripción (eliminamos la columna vacía intermedia).
        headers_map = {
            'Pacientes': ('DNI', 'Nombre', 'Apellido', 'Email', 'Fecha de nacimiento', 'Dirección'),
            'Médicos': ('Matrícula', 'Nombre', 'Apellido', 'Especialidad'),
            'Especialidades': ('ID', 'Nombre', 'Descripción')
        }
        labels = headers_map.get(entidad, ('PK', 'COL1', 'COL2', 'COL3'))
        cols = ('pk', 'col1', 'col2', 'col3', 'col4', 'col5')
        # Usar la lista completa de columnas y asignar encabezados solo a las posiciones necesarias
        for col, lab in zip(cols, labels):
            self.tree_abc.heading(col, text=lab)
            # ajustar ancho según el label
            self.tree_abc.column(col, width=160 if lab else 80)
        # Para columnas no usadas por la entidad, asegurarse que su encabezado quede vacío
        remaining = cols[len(labels):]
        for col in remaining:
            self.tree_abc.heading(col, text='')
            self.tree_abc.column(col, width=80)

        for i in self.tree_abc.get_children():
            self.tree_abc.delete(i)

        try:
            if entidad == 'Pacientes':
                if self.paciente_dao is None:
                    raise RuntimeError('DAO Paciente no disponible')
                items = self.paciente_dao.obtener_todos()
                for p in items:
                    fecha = getattr(p, 'fecha_nacimiento', '')
                    direccion = getattr(p, 'direccion', '')
                    # Insertar 6 valores (completando con '' si alguna propiedad falta)
                    self.tree_abc.insert('', 'end', values=(p.dni, p.nombre, p.apellido, getattr(p, 'email', ''), fecha or '', direccion or ''))
            elif entidad == 'Médicos':
                if self.medico_dao is None:
                    raise RuntimeError('DAO Medico no disponible')
                items = self.medico_dao.obtener_todos()
                for m in items:
                    esp = ''
                    try:
                        if self.especialidad_dao is not None and getattr(m, 'id_especialidad', None) is not None:
                            e = self.especialidad_dao.obtener_por_id(m.id_especialidad)
                            if e:
                                esp = getattr(e, 'nombre', '')
                    except Exception:
                        esp = ''
                    # Insertar solo las 4 columnas configuradas para médicos (las columnas adicionales quedan vacías)
                    self.tree_abc.insert('', 'end', values=(m.nro_matricula, m.nombre, m.apellido, esp or '', '', ''))
            elif entidad == 'Especialidades':
                if self.especialidad_dao is None:
                    raise RuntimeError('DAO Especialidad no disponible')
                items = self.especialidad_dao.obtener_todos()
                for s in items:
                    # Insertar solo ID, Nombre y Descripción (columnas extra vacías)
                    self.tree_abc.insert('', 'end', values=(s.id_especialidad, s.nombre, getattr(s, 'descripcion', ''), '', '', ''))
        except Exception as e:
            messagebox.showerror('Error', f'No se pueden listar {entidad}: {e}')

    def _on_abc_select(self, event):
        sel = self.tree_abc.selection()
        if not sel:
            return
        vals = self.tree_abc.item(sel[0])['values']
        self.detail_text.delete('1.0', tk.END)
        self.detail_text.insert(tk.END, '\n'.join([str(v) for v in vals]))

    def _abc_crear(self):
        entidad = self.combo_entidad.get()
        if entidad == 'Pacientes':
            self._crear_paciente()
        elif entidad == 'Médicos':
            self._crear_medico()
        elif entidad == 'Especialidades':
            self._crear_especialidad()

    def _abc_editar(self):
        entidad = self.combo_entidad.get()
        sel = self.tree_abc.selection()
        if not sel:
            messagebox.showwarning('Atención', 'Seleccione un registro para editar')
            return
        pk = self.tree_abc.item(sel[0])['values'][0]
        if entidad == 'Pacientes':
            try:
                pk = int(str(pk).strip())
            except Exception:
                messagebox.showerror('Error', 'DNI inválido seleccionado')
                return
            self._editar_paciente(pk)
        elif entidad == 'Médicos':
            self._editar_medico(pk)
        elif entidad == 'Especialidades':
            self._editar_especialidad(pk)

    def _abc_eliminar(self):
        entidad = self.combo_entidad.get()
        sel = self.tree_abc.selection()
        if not sel:
            messagebox.showwarning('Atención', 'Seleccione un registro para eliminar')
            return
        pk = self.tree_abc.item(sel[0])['values'][0]
        if messagebox.askyesno('Confirmar', f'¿Eliminar {entidad} con id {pk}?'):
            try:
                if entidad == 'Pacientes':
                    self.paciente_dao.eliminar(int(str(pk).strip()))
                elif entidad == 'Médicos':
                    self.medico_dao.eliminar(pk)
                elif entidad == 'Especialidades':
                    self.especialidad_dao.eliminar(pk)
                messagebox.showinfo('OK', 'Eliminación realizada')
                self._refresh_abc()
            except Exception as e:
                messagebox.showerror('Error', str(e))

    # ----- Paciente CRUD -----
    def _crear_paciente(self):
        campos = [
            ('dni', 'DNI'),
            ('nombre', 'Nombre'),
            ('apellido', 'Apellido'),
            ('email', 'Email'),
            ('direccion', 'Dirección'),
            ('fecha', 'Fecha de nacimiento (YYYY-MM-DD)')
        ]
        data = self._open_form_dialog('Nuevo paciente', campos)
        if not data:
            return
        dni = data.get('dni')
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        email = data.get('email')
        direccion = data.get('direccion')
        fecha = data.get('fecha')
        try:
            # Validaciones
            if not self._is_valid_dni(dni):
                raise ValueError('DNI inválido. Debe ser numérico y tener 5-10 dígitos.')
            if not nombre or not apellido:
                raise ValueError('Nombre y apellido son obligatorios.')
            if email and not self._is_valid_email(email):
                raise ValueError('Email inválido.')
            if fecha and not self._is_valid_date(fecha):
                raise ValueError('Fecha inválida. Formato YYYY-MM-DD.')

            dni_int = int(str(dni).strip())

            from modelos.paciente import Paciente
            p = Paciente(dni_int, nombre, apellido, fecha, email, direccion)
            self.paciente_dao.crear(p)
            messagebox.showinfo('OK', 'Paciente creado')
            self._refresh_abc()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _editar_paciente(self, dni):
        try:
            dni_int = int(str(dni).strip())
            p = self.paciente_dao.obtener_por_id(dni_int)
            if not p:
                raise ValueError('Paciente no encontrado')
            data = self._open_form_dialog(
                'Editar paciente',
                [
                    ('dni', 'DNI', {'readonly': True}),
                    ('nombre', 'Nombre'),
                    ('apellido', 'Apellido'),
                    ('email', 'Email'),
                    ('direccion', 'Dirección')
                ],
                {
                    'dni': p.dni,
                    'nombre': p.nombre,
                    'apellido': p.apellido,
                    'email': p.email,
                    'direccion': p.direccion
                }
            )
            if not data:
                return
            p.nombre = data.get('nombre')
            p.apellido = data.get('apellido')
            p.email = data.get('email')
            p.direccion = data.get('direccion')
            # Validaciones
            if not p.nombre or not p.apellido:
                raise ValueError('Nombre y apellido son obligatorios.')
            if p.email and not self._is_valid_email(p.email):
                raise ValueError('Email inválido.')
            self.paciente_dao.actualizar(p)
            messagebox.showinfo('OK', 'Paciente actualizado')
            self._refresh_abc()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    # ----- Médico CRUD -----
    def _crear_medico(self):
        try:
            data = self._open_form_dialog(
                'Nuevo médico',
                [
                    ('nro', 'Matrícula'),
                    ('nombre', 'Nombre'),
                    ('apellido', 'Apellido'),
                    ('email', 'Email'),
                    ('id_esp', 'ID Especialidad')
                ]
            )
            if not data:
                return
            nro = data.get('nro')
            nombre = data.get('nombre')
            apellido = data.get('apellido')
            email = data.get('email')
            id_esp = data.get('id_esp')
            # Validaciones
            if not nro or not nro.isdigit():
                raise ValueError('Matrícula es obligatoria y numérica.')
            if not nombre or not apellido:
                raise ValueError('Nombre y apellido son obligatorios.')
            if email and not self._is_valid_email(email):
                raise ValueError('Email inválido.')
            if not id_esp or not id_esp.isdigit():
                raise ValueError('ID de especialidad es obligatorio y numérico.')

            from modelos.medico import Medico
            m = Medico(int(nro), nombre, apellido, email, int(id_esp))
            self.medico_dao.crear(m)
            messagebox.showinfo('OK', 'Médico creado')
            self._refresh_abc()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _editar_medico(self, nro):
        try:
            m = self.medico_dao.obtener_por_id(nro)
            if not m:
                raise ValueError('Médico no encontrado')
            data = self._open_form_dialog(
                'Editar médico',
                [
                    ('nro', 'Matrícula', {'readonly': True}),
                    ('nombre', 'Nombre'),
                    ('apellido', 'Apellido'),
                    ('email', 'Email'),
                    ('id_esp', 'ID Especialidad')
                ],
                {
                    'nro': m.nro_matricula,
                    'nombre': m.nombre,
                    'apellido': m.apellido,
                    'email': m.email,
                    'id_esp': m.id_especialidad
                }
            )
            if not data:
                return
            m.nombre = data.get('nombre')
            m.apellido = data.get('apellido')
            m.email = data.get('email')
            m.id_especialidad = int(data.get('id_esp')) if data.get('id_esp') else None
            # Validaciones
            if not m.nombre or not m.apellido:
                raise ValueError('Nombre y apellido son obligatorios.')
            if m.email and not self._is_valid_email(m.email):
                raise ValueError('Email inválido.')
            if m.id_especialidad is None:
                raise ValueError('ID de especialidad obligatorio.')
            self.medico_dao.actualizar(m)
            messagebox.showinfo('OK', 'Médico actualizado')
            self._refresh_abc()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    # ----- Especialidad CRUD -----
    def _crear_especialidad(self):
        try:
            data = self._open_form_dialog(
                'Nueva especialidad',
                [
                    ('nombre', 'Nombre'),
                    ('descripcion', 'Descripción')
                ]
            )
            if not data:
                return
            nombre = data.get('nombre')
            descripcion = data.get('descripcion')
            if not nombre or not nombre.strip():
                raise ValueError('Nombre de especialidad obligatorio.')
            from modelos.especialidad import Especialidad
            s = Especialidad(None, nombre, descripcion)
            self.especialidad_dao.crear(s)
            messagebox.showinfo('OK', 'Especialidad creada')
            self._refresh_abc()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _editar_especialidad(self, id_esp):
        try:
            s = self.especialidad_dao.obtener_por_id(id_esp)
            if not s:
                raise ValueError('Especialidad no encontrada')
            data = self._open_form_dialog(
                'Editar especialidad',
                [
                    ('nombre', 'Nombre'),
                    ('descripcion', 'Descripción')
                ],
                {
                    'nombre': s.nombre,
                    'descripcion': getattr(s, 'descripcion', '')
                }
            )
            if not data:
                return
            s.nombre = data.get('nombre')
            if hasattr(s, 'descripcion'):
                s.descripcion = data.get('descripcion')
            if not s.nombre or not s.nombre.strip():
                raise ValueError('Nombre de especialidad obligatorio.')
            self.especialidad_dao.actualizar(s)
            messagebox.showinfo('OK', 'Especialidad actualizada')
            self._refresh_abc()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    # ---------- Reportes Tab ----------
    def _build_reportes_tab(self, parent):
        pad = {'padx': 8, 'pady': 8}
        top = ttk.Frame(parent)
        top.pack(fill='x', **pad)

        ttk.Label(top, text='Generar reportes desde el sistema').grid(row=0, column=0, sticky='w')
        btn = ttk.Button(top, text='Generar reportes', command=self._on_generar_reportes)
        btn.grid(row=0, column=1, sticky='w', padx=10)

        self.reportes_log = tk.Text(parent, height=20)
        self.reportes_log.pack(fill='both', expand=True, padx=8, pady=8)

    def _on_generar_reportes(self):
        if self.reporte_service is None:
            messagebox.showerror('Error', 'Servicio de reportes no disponible')
            return

        # Ventana para elegir tipo de reporte
        dlg = tk.Toplevel(self)
        dlg.title('Generar Reporte')
        dlg.geometry('480x220')

        ttk.Label(dlg, text='Tipo de reporte:').pack(anchor='w', padx=8, pady=(8,0))
        combo = ttk.Combobox(dlg, state='readonly', values=[
            'Turnos por médico en período',
            'Cantidad por especialidad',
            'Pacientes atendidos en período',
            'Asistencias vs inasistencias'
        ])
        combo.pack(fill='x', padx=8)
        combo.current(0)

        frm_inputs = ttk.Frame(dlg)
        frm_inputs.pack(fill='x', padx=8, pady=8)

        # Inputs comunes (se mostrarán/ocultarán según selección)
        lbl_m = ttk.Label(frm_inputs, text='Matrícula médico:')
        ent_m = ttk.Entry(frm_inputs)
        lbl_fi = ttk.Label(frm_inputs, text='Fecha inicio (YYYY-MM-DD):')
        ent_fi = ttk.Entry(frm_inputs)
        lbl_ff = ttk.Label(frm_inputs, text='Fecha fin (YYYY-MM-DD):')
        ent_ff = ttk.Entry(frm_inputs)

        def refresh_inputs(event=None):
            for w in frm_inputs.winfo_children():
                w.grid_forget()
            sel = combo.get()
            if sel == 'Turnos por médico en período':
                lbl_m.grid(row=0, column=0, sticky='w')
                ent_m.grid(row=0, column=1, sticky='w')
                lbl_fi.grid(row=1, column=0, sticky='w')
                ent_fi.grid(row=1, column=1, sticky='w')
                lbl_ff.grid(row=2, column=0, sticky='w')
                ent_ff.grid(row=2, column=1, sticky='w')
            elif sel == 'Cantidad por especialidad':
                ttk.Label(frm_inputs, text='(No se requieren parámetros)').grid(row=0, column=0, sticky='w')
            elif sel in ('Pacientes atendidos en período', 'Asistencias vs inasistencias'):
                lbl_fi.grid(row=0, column=0, sticky='w')
                ent_fi.grid(row=0, column=1, sticky='w')
                lbl_ff.grid(row=1, column=0, sticky='w')
                ent_ff.grid(row=1, column=1, sticky='w')

        combo.bind('<<ComboboxSelected>>', refresh_inputs)
        refresh_inputs()

        def ejecutar():
            tipo = combo.get()
            try:
                if tipo == 'Turnos por médico en período':
                    nro = int(ent_m.get().strip())
                    fi = ent_fi.get().strip(); ff = ent_ff.get().strip()
                    if not self._is_valid_date(fi) or not self._is_valid_date(ff):
                        raise ValueError('Fechas inválidas. Formato YYYY-MM-DD')
                    archivo = self.reporte_service.listado_turnos_por_medico_en_un_periodo(nro, fi, ff)
                elif tipo == 'Cantidad por especialidad':
                    archivo = self.reporte_service.reporte_cantidad_turnos_por_especialidad()
                elif tipo == 'Pacientes atendidos en período':
                    fi = ent_fi.get().strip(); ff = ent_ff.get().strip()
                    if not self._is_valid_date(fi) or not self._is_valid_date(ff):
                        raise ValueError('Fechas inválidas. Formato YYYY-MM-DD')
                    archivo = self.reporte_service.reporte_pacientes_atendidos_en_un_periodo(fi, ff)
                elif tipo == 'Asistencias vs inasistencias':
                    fi = ent_fi.get().strip(); ff = ent_ff.get().strip()
                    if not self._is_valid_date(fi) or not self._is_valid_date(ff):
                        raise ValueError('Fechas inválidas. Formato YYYY-MM-DD')
                    archivo = self.reporte_service.asistencias_vs_inasistencias_de_pacientes(fi, ff)
                else:
                    raise ValueError('Tipo de reporte no soportado')

                msg = f'Reporte generado: {archivo}\n'
                self.reportes_log.insert(tk.END, msg)
                messagebox.showinfo('OK', msg)
                dlg.destroy()
            except Exception as e:
                messagebox.showerror('Error al generar reporte', str(e))

        btn_exec = ttk.Button(dlg, text='Generar', command=ejecutar)
        btn_exec.pack(side='right', padx=12, pady=12)
        btn_close = ttk.Button(dlg, text='Cancelar', command=dlg.destroy)
        btn_close.pack(side='right', padx=6, pady=12)


if __name__ == '__main__':
    app = App()
    app.mainloop()
