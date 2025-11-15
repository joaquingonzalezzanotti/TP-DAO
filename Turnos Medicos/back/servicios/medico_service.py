from datetime import datetime, timedelta
import calendar

from persistencia.dao.agenda_dao import AgendaDAO
from persistencia.dao.turno_dao import TurnoDAO
from persistencia.dao.medico_dao import MedicoDAO
from persistencia.dao.especialidad_dao import EspecialidadDAO
from modelos.turno import Turno
from modelos.medico import Medico
class MedicoService:
    """
    Servicio que encapsula la lógica de negocio relacionada con los médicos.
    Coordina acceso a DAO y aplica reglas (baja cohesión, bajo acoplamiento).
    """

    def __init__(self):
        self.agenda_dao = AgendaDAO()
        self.turno_dao = TurnoDAO()
        self.medico_dao = MedicoDAO()
        self.especialidad_dao = EspecialidadDAO()

    def agregar_medico(self, nro_matricula, nombre, apellido, email, id_especialidad):
        
        # Validación usando la DB (preexistencia, FK)
        especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
        if especialidad is None:
            raise ValueError(f"La especialidad con ID {id_especialidad} no existe.")

        existente = self.medico_dao.obtener_por_matricula(nro_matricula)
        if existente:
            raise ValueError(f"Ya existe un médico con matrícula {nro_matricula}.")

        # Crear el objeto de dominio (valida formato, reglas internas)
        medico = Medico(
            nro_matricula=nro_matricula,
            nombre=nombre,
            apellido=apellido,
            email=email,
            id_especialidad=id_especialidad
        )

        # Persistir en la DB
        self.medico_dao.crear(medico)

        return medico
    
    def eliminar_medico(self, nro_matricula: int):
        """
        Realiza la baja lógica de un médico (activo = 0).

        Parámetros:
            nro_matricula: int → número de matrícula del médico a eliminar
        """

        medico = self.medico_dao.obtener_por_id(nro_matricula)
        if not medico:
            raise ValueError(f"No existe un médico con matrícula {nro_matricula}.")

        self.medico_dao.eliminar(nro_matricula)
        print(f"[OK] Médico con matrícula {nro_matricula} desactivado correctamente.")
    
    def activar_medico(self, nro_matricula: int):
        """
        Reactiva un médico inactivo (activo = 1).

        Parámetros:
            nro_matricula: int → número de matrícula del médico a reactivar
        """

        medico = self.medico_dao.obtener_por_id(nro_matricula)
        if not medico:
            raise ValueError(f"No existe un médico con matrícula {nro_matricula}.")

        if medico.activo == 1:
            raise ValueError(f"El médico con matrícula {nro_matricula} ya está activo.")

        self.medico_dao.activar(nro_matricula)
        print(f"[OK] Médico con matrícula {nro_matricula} reactivado correctamente.")
    
    def obtener_medicos(self):
        """
        Obtiene todos los médicos activos.

        Retorna:
            lista de Medico
        """
        return self.medico_dao.obtener_todos()
    
    def obtener_medicos_inactivos(self):
        """
        Obtiene todos los médicos inactivos.

        Retorna:
            lista de Medico
        """
        return self.medico_dao.obtener_todos_inactivos()
    
    def obtener_medico_por_matricula(self, nro_matricula: int):
        """
        Obtiene un médico por su número de matrícula.

        Parámetros:
            nro_matricula: int → número de matrícula del médico

        Retorna:
            Medico o None si no existe
        """
        return self.medico_dao.obtener_por_id(nro_matricula)
    
    def obtener_medicos_por_especialidad(self, id_especialidad: int):
        """
        Obtiene todos los médicos activos de una especialidad específica.

        Parámetros:
            id_especialidad: int → ID de la especialidad

        Retorna:
            lista de Medico
        """
        if not self.especialidad_dao.obtener_por_id(id_especialidad):
            raise ValueError(f"La especialidad con ID {id_especialidad} no existe.")
        return self.medico_dao.obtener_por_especialidad(id_especialidad)
    
    def obtener_medicos_por_apellido(self, apellido: str):
        """
        Obtiene todos los médicos activos cuyo apellido coincida parcialmente.

        Parámetros:
            apellido: str → apellido o parte del apellido a buscar

        Retorna:
            lista de Medico
        """
        return self.medico_dao.obtener_por_apellido(apellido)
    
    def actualizar_medico(self, nro_matricula:int, nombre:str =None, apellido:str =None, email:str =None, id_especialidad:int =None):

        """
        Actualiza los datos de un médico existente.

        Parámetros:
            nro_matricula: int → número de matrícula del médico a actualizar
            nombre: str → nuevo nombre (opcional)
            apellido: str → nuevo apellido (opcional)
            email: str → nuevo email (opcional)
            id_especialidad: int → nuevo ID de especialidad (opcional)

        Retorna:
            Medico actualizado o None si no se pudo actualizar
        """

        medico = self.medico_dao.obtener_por_id(nro_matricula)
        if not medico:
            raise ValueError(f"No existe un médico con matrícula {nro_matricula}.")

        # Actualizar solo los campos proporcionados
        if nombre is not None:
            medico.nombre = nombre
        if apellido is not None:
            medico.apellido = apellido
        if email is not None:
            medico.email = email
        if id_especialidad is not None:
            especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
            if especialidad is None:
                raise ValueError(f"La especialidad con ID {id_especialidad} no existe.")
            medico.id_especialidad = id_especialidad

        # Validar y persistir cambios
        try:
            medico._validar()
        except ValueError as ve:
            print(f"[VALIDACIÓN] {ve}")
            return None

        actualizado = self.medico_dao.actualizar(medico)
        if actualizado:
            print(f"[OK] Médico con matrícula {nro_matricula} actualizado correctamente.")
        return actualizado

    def generar_turnos_de_medico(self, nro_matricula_medico: int, mes: int, anio: int):
        """
        Genera los turnos de un médico para el mes especificado.
        Se basa en su agenda (días, horario y duración).

        Parámetros:
            nro_matricula_medico: int → ID del médico
            mes: int → número de mes (1-12)

        Retorna:
            lista de Turno creados
        """

        try:
            # Validaciones básicas
            if not (1 <= mes <= 12):
                raise ValueError("El mes debe estar entre 1 y 12.")
            if anio < datetime.now().year:
                raise ValueError("No se pueden generar turnos en años anteriores.")

            # Validar existencia del médico
            if not self.medico_dao.obtener_por_id(nro_matricula_medico):
                raise ValueError(f"No existe un médico con matrícula {nro_matricula_medico}.")

            # Obtener agenda
            agenda = self.agenda_dao.obtener_por_medico_y_mes(nro_matricula_medico, mes)
            if not agenda:
                raise ValueError(
                    f"No existe agenda para el médico {nro_matricula_medico} en el mes {mes}"
                )
            # Verificar si ya existen turnos generados para ese médico en ese mes
            if self.turno_dao.existen_turnos_generados(nro_matricula_medico, mes, anio):
                raise ValueError("Ya existen turnos generados para ese mes.")

            # Diccionario de traducción (inglés → español)
            dias_en = {
                "monday": "lunes",
                "tuesday": "martes",
                "wednesday": "miércoles",
                "thursday": "jueves",
                "friday": "viernes",
                "saturday": "sábado",
                "sunday": "domingo",
            }

            dias_semana = [d.strip().lower() for d in agenda.dias_semana.split(",")]
            turnos_creados = []
            _, dias_mes = calendar.monthrange(anio, mes)

            # Recorrer todos los días del mes
            for dia in range(1, dias_mes + 1):
                fecha = datetime(anio, mes, dia)

                # Verificar si el día actual está en los días de la agenda
                dia_es = dias_en[fecha.strftime("%A").lower()]

                if dia_es in dias_semana:
                    hora_inicio = datetime.strptime(agenda.hora_inicio, "%H:%M").time()
                    hora_fin = datetime.strptime(agenda.hora_fin, "%H:%M").time()
                    actual = datetime.combine(fecha.date(), hora_inicio)

                    while actual.time() < hora_fin:
                        # Crear el objeto Turno mientras esté dentro del horario
                        turno = Turno(
                            fecha_hora_inicio=actual.strftime("%Y-%m-%d %H:%M:%S"),
                            estado="disponible",
                            nro_matricula_medico=nro_matricula_medico
                        )
                        # Insertar en DB mediante DAO
                        self.turno_dao.crear(turno)
                        turnos_creados.append(turno)
                        actual += timedelta(minutes=agenda.duracion_minutos)

            print(f"[OK] Se generaron {len(turnos_creados)} turnos para el médico {nro_matricula_medico} (mes {mes}).")
            return turnos_creados

        except ValueError as ve:
            print(f"[VALIDACIÓN] {ve}")
        except Exception as e:
            print(f"[ERROR] No se pudieron generar los turnos: {e}")

        
