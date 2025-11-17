import os
import sys
import re
import calendar
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
from datetime import date

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
    from persistencia.dao.paciente_dao import PacienteDAO
    from persistencia.dao.medico_dao import MedicoDAO
    from persistencia.dao.especialidad_dao import EspecialidadDAO
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
            self.paciente_dao = PacienteDAO()
            self.medico_dao = MedicoDAO()
            self.especialidad_dao = EspecialidadDAO()
        except Exception:
            # tolerar inicialización fallida; manejaremos con mensajes en botones
            self.medico_service = None
            self.turno_service = None
            self.reporte_service = None
            self.paciente_dao = None
            self.medico_dao = None
            self.especialidad_dao = None

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

        # Pestaña Otros (placeholders)
        frame_otros = ttk.Frame(nb)
        nb.add(frame_otros, text='Consultas / Recetas / Historial')
        lbl = ttk.Label(frame_otros, text='Secciones de Consultas, Recetas y Historial clínico: en desarrollo.')
        lbl.pack(padx=12, pady=12)

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
        cols = ('id', 'fecha', 'estado', 'medico')
        self.tree_turnos = ttk.Treeview(parent, columns=cols, show='headings')
        for c in cols:
            self.tree_turnos.heading(c, text=c.capitalize())
            self.tree_turnos.column(c, width=150)
        self.tree_turnos.pack(fill='both', expand=True, padx=8, pady=8)

        self._load_medicos()

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
            self.tree_turnos.insert(
                '',
                'end',
                values=(
                    getattr(turno, 'id_turno', ''),
                    getattr(turno, 'fecha_hora_inicio', ''),
                    getattr(turno, 'estado', ''),
                    medico_label
                )
            )

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

        # Treeview
        cols = ('pk', 'col1', 'col2', 'col3')
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
        ttk.Button(btn_frame, text='Refrescar', command=self._refresh_abc).pack(side='left', padx=6)

        # Detail panel (right)
        self.detail_text = tk.Text(right, width=50)
        self.detail_text.pack(fill='both', expand=True, padx=8, pady=8)

        # Bind selection
        self.tree_abc.bind('<<TreeviewSelect>>', self._on_abc_select)

        self._refresh_abc()

    def _refresh_abc(self):
        entidad = self.combo_entidad.get()

        # Actualizar encabezados según la entidad seleccionada
        headers_map = {
            'Pacientes': ('DNI', 'Nombre', 'Apellido', 'Email'),
            'Médicos': ('Matrícula', 'Nombre', 'Apellido', 'Email'),
            'Especialidades': ('ID', 'Nombre', '-', 'Descripción')
        }
        labels = headers_map.get(entidad, ('PK', 'COL1', 'COL2', 'COL3'))
        cols = ('pk', 'col1', 'col2', 'col3')
        for col, lab in zip(cols, labels):
            self.tree_abc.heading(col, text=lab)
            # ajustar ancho si el label está vacío o corto
            self.tree_abc.column(col, width=140 if lab else 80)

        for i in self.tree_abc.get_children():
            self.tree_abc.delete(i)

        try:
            if entidad == 'Pacientes':
                if self.paciente_dao is None:
                    raise RuntimeError('DAO Paciente no disponible')
                items = self.paciente_dao.obtener_todos()
                for p in items:
                    self.tree_abc.insert('', 'end', values=(p.dni, p.nombre, p.apellido, p.email))
            elif entidad == 'Médicos':
                if self.medico_dao is None:
                    raise RuntimeError('DAO Medico no disponible')
                items = self.medico_dao.obtener_todos()
                for m in items:
                    self.tree_abc.insert('', 'end', values=(m.nro_matricula, m.nombre, m.apellido, m.email))
            elif entidad == 'Especialidades':
                if self.especialidad_dao is None:
                    raise RuntimeError('DAO Especialidad no disponible')
                items = self.especialidad_dao.obtener_todos()
                for s in items:
                    self.tree_abc.insert('', 'end', values=(s.id_especialidad, s.nombre, '', getattr(s, 'descripcion', '')))
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
        dni = simpledialog.askstring('Nuevo paciente', 'DNI:')
        if not dni:
            return
        nombre = simpledialog.askstring('Nuevo paciente', 'Nombre:')
        apellido = simpledialog.askstring('Nuevo paciente', 'Apellido:')
        email = simpledialog.askstring('Nuevo paciente', 'Email:')
        direccion = simpledialog.askstring('Nuevo paciente', 'Dirección:')
        fecha = simpledialog.askstring('Nuevo paciente', 'Fecha de nacimiento (YYYY-MM-DD):')
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
            nombre = simpledialog.askstring('Editar paciente', 'Nombre:', initialvalue=p.nombre)
            apellido = simpledialog.askstring('Editar paciente', 'Apellido:', initialvalue=p.apellido)
            email = simpledialog.askstring('Editar paciente', 'Email:', initialvalue=p.email)
            direccion = simpledialog.askstring('Editar paciente', 'Dirección:', initialvalue=p.direccion)
            p.nombre = nombre
            p.apellido = apellido
            p.email = email
            p.direccion = direccion
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
            nro = simpledialog.askinteger('Nuevo médico', 'Matrícula:')
            nombre = simpledialog.askstring('Nuevo médico', 'Nombre:')
            apellido = simpledialog.askstring('Nuevo médico', 'Apellido:')
            email = simpledialog.askstring('Nuevo médico', 'Email:')
            id_esp = simpledialog.askinteger('Nuevo médico', 'ID Especialidad:')
            # Validaciones
            if nro is None:
                raise ValueError('Matrícula es obligatoria y numérica.')
            if not nombre or not apellido:
                raise ValueError('Nombre y apellido son obligatorios.')
            if email and not self._is_valid_email(email):
                raise ValueError('Email inválido.')
            if id_esp is None:
                raise ValueError('ID de especialidad es obligatorio y numérico.')

            from modelos.medico import Medico
            m = Medico(nro, nombre, apellido, email, id_esp)
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
            nombre = simpledialog.askstring('Editar médico', 'Nombre:', initialvalue=m.nombre)
            apellido = simpledialog.askstring('Editar médico', 'Apellido:', initialvalue=m.apellido)
            email = simpledialog.askstring('Editar médico', 'Email:', initialvalue=m.email)
            id_esp = simpledialog.askinteger('Editar médico', 'ID Especialidad:', initialvalue=m.id_especialidad)
            m.nombre = nombre
            m.apellido = apellido
            m.email = email
            m.id_especialidad = id_esp
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
            nombre = simpledialog.askstring('Nueva especialidad', 'Nombre:')
            descripcion = simpledialog.askstring('Nueva especialidad', 'Descripción:')
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
            nombre = simpledialog.askstring('Editar especialidad', 'Nombre:', initialvalue=s.nombre)
            descripcion = simpledialog.askstring('Editar especialidad', 'Descripción:', initialvalue=getattr(s, 'descripcion', ''))
            s.nombre = nombre
            if hasattr(s, 'descripcion'):
                s.descripcion = descripcion
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
            'Pacientes atendidos en período'
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
            elif sel == 'Pacientes atendidos en período':
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
                    nro = int(ent_m.get())
                    fi = ent_fi.get(); ff = ent_ff.get()
                    if not self._is_valid_date(fi) or not self._is_valid_date(ff):
                        raise ValueError('Fechas inválidas. Formato YYYY-MM-DD')
                    archivo = self.reporte_service.listado_turnos_por_medico_en_un_periodo(nro, fi, ff)
                elif tipo == 'Cantidad por especialidad':
                    archivo = self.reporte_service.reporte_cantidad_turnos_por_especialidad()
                elif tipo == 'Pacientes atendidos en período':
                    fi = ent_fi.get(); ff = ent_ff.get()
                    if not self._is_valid_date(fi) or not self._is_valid_date(ff):
                        raise ValueError('Fechas inválidas. Formato YYYY-MM-DD')
                    archivo = self.reporte_service.reporte_pacientes_atendidos_en_un_periodo(fi, ff)
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
