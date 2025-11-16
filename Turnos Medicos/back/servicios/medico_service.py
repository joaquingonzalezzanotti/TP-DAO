from datetime import datetime, timedelta
import calendar

from persistencia.dao.agenda_dao import AgendaDAO
from persistencia.dao.turno_dao import TurnoDAO
from persistencia.dao.medico_dao import MedicoDAO
from persistencia.dao.especialidad_dao import EspecialidadDAO
from persistencia.persistencia_errores import IntegridadError, DatabaseError, NotFoundError
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
        try:
            # Validación usando la DB (preexistencia, FK)
            # Manejo de error técnico en la consulta de especialidad
            try:
                especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar especialidad: {e}")

            if especialidad is None:
                raise ValueError(f"La especialidad con ID {id_especialidad} no existe.")

            # Manejo de error técnico en la consulta de existencia
            try:
                existente = self.medico_dao.obtener_por_matricula(nro_matricula)
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar médico existente: {e}")
                
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
        # Si el DAO lanza un error de integridad (ej. si dos procesos intentan crear la misma matrícula)
        except IntegridadError as e:
            print(f"[ERROR BIZ] Fallo de integridad al agregar médico: {e}")
            raise ValueError("Fallo en la base de datos al registrar el médico (verificar DNI o FK).")      
        # Si el DAO lanza cualquier otro error de DB (ej. conexión)
        except DatabaseError as e:
            print(f"[ERROR DB] Fallo general de base de datos: {e}")
            raise RuntimeError("Ocurrió un error técnico en la base de datos. Intente más tarde.") 
        # Para capturar las excepciones de tipo ValueError o RuntimeError (propia del service)
        except (ValueError, RuntimeError) as err:
            print(f"[ERROR VALIDACIÓN/RUNTIME] {err}")
            raise # Relanza el error para que la interfaz de usuario lo maneje.
            
    def obtener_medicos(self):
        """
        Obtiene todos los médicos activos.
        Retorna:
            lista de Medico
        """
        try:
            return self.medico_dao.obtener_todos()
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener médicos: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la lista de médicos.")
    
    def obtener_medicos_inactivos(self):
        """
        Obtiene todos los médicos inactivos.
        Retorna:
            lista de Medico
        """
        try:
            return self.medico_dao.obtener_todos_inactivos()
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener médicos inactivos: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la lista de médicos inactivos.")
    
    def obtener_medico_por_matricula(self, nro_matricula: int):
        """
        Obtiene un médico por su número de matrícula.
        Retorna:
            Medico o None si no existe
        """
        try:
            return self.medico_dao.obtener_por_id(nro_matricula)
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener médico: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar el médico por matrícula.")
    
    def obtener_medicos_por_especialidad(self, id_especialidad: int):
        """
        Obtiene todos los médicos activos de una especialidad específica.
        Retorna:
            lista de Medico
        """
        try:
            if not self.especialidad_dao.obtener_por_id(id_especialidad):
                raise ValueError(f"La especialidad con ID {id_especialidad} no existe.")
            return self.medico_dao.obtener_por_especialidad(id_especialidad)
        except Exception as e:
            if isinstance(e, ValueError): # Si ya es un error de negocio, relanzarlo
                raise
            print(f"[ERROR DB] Fallo general de base de datos al obtener médicos por especialidad: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar médicos por especialidad.")
    
    def obtener_medicos_por_apellido(self, apellido: str):
        """
        Obtiene todos los médicos activos cuyo apellido coincida parcialmente.
        Retorna:
            lista de Medico
        """
        try:
            return self.medico_dao.obtener_por_apellido(apellido)
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener médicos por apellido: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar médicos por apellido.")
    
    def actualizar_medico(self, nro_matricula:int, nombre:str =None, apellido:str =None, email:str =None, id_especialidad:int =None):

        """
        Actualiza los datos de un médico existente.
        Retorna:
            Medico actualizado o None si no se pudo actualizar
        """
        # Manejo de errores de obtención
        try:
            medico = self.medico_dao.obtener_por_id(nro_matricula)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar médico para actualizar: {e}")

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
            # Manejo de errores de obtención de especialidad
            try:
                especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar nueva especialidad: {e}")
                
            if especialidad is None:
                raise ValueError(f"La especialidad con ID {id_especialidad} no existe.")
            medico.id_especialidad = id_especialidad

        try:
            # Validar y persistir cambios
            medico._validar()
            actualizado = self.medico_dao.actualizar(medico)
            if actualizado:
                print(f"[OK] Médico con matrícula {nro_matricula} actualizado correctamente.")
            return actualizado
        
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            raise ValueError("Error de datos. Los datos proporcionados (Ej: nueva especialidad) no son válidos.") 
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al actualizar la base de datos. Intente más tarde.")
        except ValueError as ve:
            # Captura errores de validación del modelo (medico._validar())
            print(f"[VALIDACIÓN] {ve}")
            raise
    
    def eliminar_medico(self, nro_matricula: int):
        """
        Realiza la baja lógica de un médico (activo = 0).
        """
        # Manejo de errores de obtención
        try:
            medico = self.medico_dao.obtener_por_id(nro_matricula)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar médico para baja: {e}")
            
        if not medico:
            raise ValueError(f"No existe un médico con matrícula {nro_matricula}.")
        if medico.activo == 0:
            raise ValueError(f"El médico con matrícula {nro_matricula} ya está inactivo.")
        
        try:
            self.medico_dao.eliminar(nro_matricula)
            print(f"[OK] Médico con matrícula {nro_matricula} desactivado correctamente.")
        
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            # El error aquí sería más probable si hubiera un 'hard-delete' en cascada.
            raise ValueError("No se puede desactivar el médico. Podría tener referencias activas.")  
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al desactivar el médico. Intente más tarde.")
    
    def activar_medico(self, nro_matricula: int):
        """
        Reactiva un médico inactivo (activo = 1).
        """
        # Manejo de errores de obtención
        try:
            medico = self.medico_dao.obtener_por_id(nro_matricula)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar médico para activación: {e}")

        if not medico:
            raise ValueError(f"No existe un médico con matrícula {nro_matricula}.")

        if medico.activo == 1:
            raise ValueError(f"El médico con matrícula {nro_matricula} ya está activo.")

        try:
            self.medico_dao.activar(nro_matricula)
            print(f"[OK] Médico con matrícula {nro_matricula} reactivado correctamente.")

        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            raise ValueError("No se puede activar el médico.")  
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al activar el médico. Intente más tarde.")

    def generar_turnos_de_medico(self, nro_matricula_medico: int, mes: int, anio: int):
        """
        Genera los turnos de un médico para el mes especificado.
        """
        try:
            # Validaciones básicas
            if not (1 <= mes <= 12):
                raise ValueError("El mes debe estar entre 1 y 12.")
            if anio < datetime.now().year:
                raise ValueError("No se pueden generar turnos en años anteriores.")
            if mes <= datetime.now().month and anio == datetime.now().year:
                raise ValueError("Solo se pueen generar turnos para meses posteriores al actual.")

            # Validar existencia del médico (Manejo de error de obtención)
            try:
                if not self.medico_dao.obtener_por_id(nro_matricula_medico):
                    raise ValueError(f"No existe un médico con matrícula {nro_matricula_medico}.")
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar existencia del médico: {e}")

            # Obtener agenda (Manejo de error de obtención)
            try:
                agenda = self.agenda_dao.obtener_por_medico_y_mes(nro_matricula_medico, mes)
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al consultar la agenda del médico: {e}")
                
            if not agenda:
                raise ValueError(
                    f"No existe agenda para el médico {nro_matricula_medico} en el mes {mes}"
                )
            
            # Verificar si ya existen turnos generados (Manejo de error de obtención)
            try:
                if self.turno_dao.existen_turnos_generados(nro_matricula_medico, mes, anio):
                    raise ValueError("Ya existen turnos generados para ese mes.")
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar turnos existentes: {e}")


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
                    # Usar directamente los objetos time() del modelo Agenda (como se corrigió)
                    hora_inicio = agenda.hora_inicio 
                    hora_fin = agenda.hora_fin
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

        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] Fallo al generar turnos: {e}")
            raise ValueError("No se pudieron generar los turnos debido a un error de integridad de datos.")
        except DatabaseError as e:
            print(f"[ERROR DB] Fallo al generar turnos: {e}")
            raise RuntimeError("Ocurrió un error técnico de base de datos durante la generación de turnos.") 
        except ValueError as ve: 
            print(f"[VALIDACIÓN] {ve}")
            raise
        except RuntimeError as re:
            # Captura fallos técnicos de obtención/existencia dentro del método
            print(f"[RUNTIME] {re}")
            raise