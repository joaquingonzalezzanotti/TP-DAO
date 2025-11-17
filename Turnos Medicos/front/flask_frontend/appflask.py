import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

# Ajustar rutas para importar el backend
# appflask.py está en: front/flask_frontend/appflask.py
# Necesitamos llegar a: back/servicios
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # front/flask_frontend
FRONT_DIR = os.path.dirname(BASE_DIR)  # front
TURNOS_DIR = os.path.dirname(FRONT_DIR)  # Turnos Medicos
BACK_DIR = os.path.join(TURNOS_DIR, 'back')
SERVICIOS_DIR = os.path.join(BACK_DIR, 'servicios')

if BACK_DIR not in sys.path:
    sys.path.insert(0, BACK_DIR)
if SERVICIOS_DIR not in sys.path:
    sys.path.insert(0, SERVICIOS_DIR)

try:
    from medico_service import MedicoService
    from turno_service import TurnoService
    from paciente_service import PacienteService
    from especialidad_service import EspecialidadService
    from reporte_service import ReporteService
except Exception as e:
    # Guardar el error para mostrar en la UI si es necesario
    IMPORT_ERROR = e
else:
    IMPORT_ERROR = None

app = Flask(__name__, template_folder='templates')
app.secret_key = 'dev-key'

# Instancias de servicios (se inicializan en runtime)
medico_svc = None
turno_svc = None
paciente_svc = None
especialidad_svc = None
reporte_svc = None


def init_services():
    global medico_svc, turno_svc, paciente_svc, especialidad_svc, reporte_svc
    if IMPORT_ERROR:
        raise IMPORT_ERROR
    medico_svc = MedicoService()
    turno_svc = TurnoService()
    paciente_svc = PacienteService()
    especialidad_svc = EspecialidadService()
    reporte_svc = ReporteService()


@app.route('/')
def index():
    err = IMPORT_ERROR
    return render_template('index.html', import_error=err)


@app.route('/turnos', methods=['GET', 'POST'])
def turnos():
    try:
        if medico_svc is None:
            init_services()
    except Exception as e:
        flash(f'Error inicializando servicios: {e}', 'danger')
        return render_template('turnos.html', medicos=[], created=None)

    medicos = medico_svc.obtener_medicos()
    created = None
    if request.method == 'POST':
        nro = request.form.get('medico')
        mes = request.form.get('mes')
        anio = request.form.get('anio')
        try:
            nro = int(nro)
            mes = int(mes); anio = int(anio)
            creados = medico_svc.generar_turnos_de_medico(nro, mes, anio)
            created = len(creados)
            flash(f'Se generaron {created} turnos.', 'success')
        except Exception as e:
            flash(str(e), 'danger')

    return render_template('turnos.html', medicos=medicos, created=created)


@app.route('/abc/<entidad>', methods=['GET', 'POST'])
def abc(entidad):
    try:
        if paciente_svc is None:
            init_services()
    except Exception as e:
        flash(f'Error inicializando servicios: {e}', 'danger')
        return render_template('abc.html', entidad=entidad, items=[])

    entidad = entidad.lower()
    items = []
    try:
        if entidad == 'pacientes':
            items = paciente_svc.obtener_pacientes()
        elif entidad == 'medicos':
            items = medico_svc.obtener_medicos()
        elif entidad == 'especialidades':
            items = especialidad_svc.obtener_especialidades()
    except Exception as e:
        flash(f'Error al obtener {entidad}: {e}', 'danger')

    # Manejo simple de creación/edición/eliminación vía query params
    action = request.args.get('action')
    if action == 'delete' and request.method == 'POST':
        pk = request.form.get('pk')
        try:
            if entidad == 'pacientes':
                paciente_svc.eliminar_paciente(pk)
            elif entidad == 'medicos':
                medico_svc.eliminar_medico(int(pk))
            elif entidad == 'especialidades':
                especialidad_svc.eliminar(int(pk))
            flash('Eliminación realizada', 'success')
            return redirect(url_for('abc', entidad=entidad))
        except Exception as e:
            flash(str(e), 'danger')

    return render_template('abc.html', entidad=entidad, items=items)


@app.route('/reportes', methods=['GET', 'POST'])
def reportes():
    try:
        if reporte_svc is None:
            init_services()
    except Exception as e:
        flash(f'Error iniciando servicios: {e}', 'danger')
        return render_template('reportes.html', generated=None, medicos=[])

    generated = None
    medicos = []
    try:
        medicos = medico_svc.obtener_medicos() if medico_svc else []
    except Exception as e:
        flash(f'Error al obtener médicos: {e}', 'danger')

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        try:
            if tipo == 'cantidad_especialidad':
                archivo = reporte_svc.reporte_cantidad_turnos_por_especialidad()
            elif tipo == 'pacientes_periodo':
                fi = request.form.get('fi'); ff = request.form.get('ff')
                archivo = reporte_svc.reporte_pacientes_atendidos_en_un_periodo(fi, ff)
            else:
                # listado por medico
                nro = int(request.form.get('medico'))
                fi = request.form.get('fi'); ff = request.form.get('ff')
                archivo = reporte_svc.listado_turnos_por_medico_en_un_periodo(nro, fi, ff)

            generated = archivo
            flash(f'Reporte generado: {archivo}', 'success')
        except Exception as e:
            flash(str(e), 'danger')

    return render_template('reportes.html', medicos=medicos, generated=generated)


@app.route('/reports/<filename>')
def reports_files(filename):
    # Servir archivos generados en el working directory
    cwd = os.getcwd()
    return send_from_directory(cwd, filename)


if __name__ == '__main__':
    app.run(debug=True)
