"""
Script rápido para crear datos de prueba y programar un turno para
`maurisalum@gmail.com`. Usalo desde la raíz del repo en la misma sesión
con tus variables de entorno (SENDGRID_API_KEY, FROM_EMAIL) activas.

Ejecución:
. .\.venv\Scripts\Activate.ps1
python .\tests\programar_turno_maurisalum.py

El script:
- crea (si falta) una Especialidad 'PruebaMail'
- crea (si falta) un Médico con matrícula 900010
- crea (si falta) el Paciente con DNI 77777777 y email `maurisalum@gmail.com`
- crea un turno disponible 24h en el futuro y lo programa -> debe disparar MailService
"""

import os
import sys
from datetime import datetime, timedelta, date

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Turnos Medicos', 'back'))
SERVICES_PATH = os.path.join(BASE, 'servicios')
PERSISTENCE_PATH = os.path.join(BASE, 'persistencia')
MODELS_PATH = os.path.join(BASE, 'modelos')
for p in (SERVICES_PATH, PERSISTENCE_PATH, MODELS_PATH, BASE):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from servicios.turno_service import TurnoService
    from persistencia.dao.especialidad_dao import EspecialidadDAO
    from persistencia.dao.medico_dao import MedicoDAO
    from persistencia.dao.paciente_dao import PacienteDAO
    from persistencia.dao.turno_dao import TurnoDAO
    from modelos.especialidad import Especialidad
    from modelos.medico import Medico
    from modelos.paciente import Paciente
    from modelos.turno import Turno
except Exception as e:
    print('Error al importar módulos del backend:', e)
    sys.exit(1)


def safe_create_especialidad(nombre='PruebaMail', descripcion='Especialidad de prueba para mail'):
    edao = EspecialidadDAO()
    try:
        existente = edao.obtener_por_nombre(nombre)
        if existente:
            print(f'Especialidad existente encontrada: id={existente.id_especialidad} nombre={existente.nombre}')
            return existente
    except Exception:
        pass
    esp = Especialidad(nombre=nombre, descripcion=descripcion)
    edao.crear(esp)
    print(f'Especialidad creada: id={esp.id_especialidad} nombre={esp.nombre}')
    return esp


def safe_create_medico(nro_matricula=900010, nombre='Dr Mail', apellido='Tester', email=None, id_especialidad=None):
    mdao = MedicoDAO()
    existente = mdao.obtener_por_id(nro_matricula)
    if existente:
        print(f'Médico existente: matrícula={existente.nro_matricula}')
        return existente
    med = Medico(nro_matricula=nro_matricula, nombre=nombre, apellido=apellido, email=email or 'medico_mail@example.com', id_especialidad=id_especialidad)
    mdao.crear(med)
    print(f'Médico creado: matrícula={med.nro_matricula}')
    return med


def safe_create_paciente(dni=77777777, nombre='Mauricio', apellido='Prueba', fecha_nac=None, email='maurisalum@gmail.com', direccion='Calle Test 1'):
    pdao = PacienteDAO()
    existente = pdao.obtener_por_id(dni)
    if existente:
        print(f'Paciente existente: DNI={existente.dni} email={existente.email}')
        return existente
    if fecha_nac is None:
        fecha_nac = (date.today().replace(year=date.today().year - 30)).isoformat()
    pac = Paciente(dni=dni, nombre=nombre, apellido=apellido, fecha_nacimiento=fecha_nac, email=email, direccion=direccion)
    pdao.crear(pac)
    print(f'Paciente creado: DNI={pac.dni} email={pac.email}')
    return pac


def create_turno_disponible(nro_matricula_medico, minutes_from_now=60*24):
    fecha = datetime.now() + timedelta(minutes=minutes_from_now)
    fecha_str = fecha.strftime('%Y-%m-%d %H:%M')
    turno = Turno(fecha_hora_inicio=fecha_str, motivo='', observaciones='', estado='disponible', dni_paciente=None, nro_matricula_medico=nro_matricula_medico)
    tdao = TurnoDAO()
    tdao.crear(turno)
    print(f'Turno disponible creado: id={turno.id_turno} fecha={turno.fecha_hora_inicio} medico={turno.nro_matricula_medico}')
    return turno


def main():
    print('Variables de entorno (SENDGRID_API_KEY present):', bool(os.environ.get('SENDGRID_API_KEY')))
    print('FROM_EMAIL:', os.environ.get('FROM_EMAIL'))

    esp = safe_create_especialidad()
    med = safe_create_medico(id_especialidad=esp.id_especialidad, email=os.environ.get('FROM_EMAIL') or 'medico_mail@example.com')
    pac = safe_create_paciente()

    turno = create_turno_disponible(nro_matricula_medico=med.nro_matricula, minutes_from_now=60*24)

    ts = TurnoService()
    print('\nProgramando el turno (esto debería disparar MailService)...')
    try:
        resultado = ts.programar_turno(turno.id_turno, pac.dni, motivo='Prueba automatizada', observaciones='Generado por script')
        print('\nResultado de programar_turno:', bool(resultado))
    except Exception as e:
        print('programar_turno lanzó excepción:')
        print(e)
        sys.exit(1)

    print('\nRevisá las salidas:')
    print('- Consola (mensajes de MailService)')
    print("- Archivo: Turnos Medicos/front/salidas/emails/mail_success.log o mail_errors.log")
    print('- Bandeja de ingreso del destinatario (maurisalum@gmail.com)')


if __name__ == '__main__':
    main()
