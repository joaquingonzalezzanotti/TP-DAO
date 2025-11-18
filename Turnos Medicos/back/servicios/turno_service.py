from persistencia.dao.turno_dao import TurnoDAO
from persistencia.dao.paciente_dao import PacienteDAO
from persistencia.dao.medico_dao import MedicoDAO
from persistencia.dao.especialidad_dao import EspecialidadDAO
from persistencia.persistencia_errores import IntegridadError, DatabaseError, NotFoundError
from modelos.turno import Turno
from especialidad_service import EspecialidadService
from mail_service import MailService
import os
from datetime import datetime, date, timedelta
class TurnoService:
    """
    Servicio que encapsula la lógica de negocio relacionada con los médicos.
    Coordina acceso a DAO y aplica reglas (baja cohesión, bajo acoplamiento).
    """

    def __init__(self):
        self.turno_dao = TurnoDAO()
        self.paciente_dao = PacienteDAO()
        self.medico_dao = MedicoDAO()
        self.especialidad_dao = EspecialidadDAO()
        self.especialidad_service = EspecialidadService()

    
    def programar_turno(self, id_turno, dni_paciente, motivo, observaciones=None):
        """
        Asigna un turno a un paciente.
        """
        try:
            turno = self.turno_dao.obtener_por_id(id_turno)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar el turno {id_turno}: {e}")

        if not turno:
            raise ValueError(f"No existe un turno con ID {id_turno}.")
        
        if turno.fecha_hora_inicio < datetime.now():
            raise ValueError(f"El turno con ID {id_turno} es pasado ({turno.fecha_hora_inicio}) y no puede ser programado.")
        
        try:
            paciente = self.paciente_dao.obtener_por_id(dni_paciente)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar el paciente {dni_paciente}: {e}")
        
        if not paciente or paciente.activo == 0:
            raise ValueError(f"No existe un paciente activo con DNI {dni_paciente}.")

        if turno.estado != 'disponible':
            raise ValueError(f"El turno con ID {id_turno} no está disponible para asignación.")

        # Asignar el paciente al turno y cambiar estado
        turno.dni_paciente = dni_paciente
        turno.estado = 'programado'
        turno.motivo = motivo
        if observaciones:
            turno.observaciones = observaciones

        # Validar y persistir cambios
        try:
            turno._validar()
            actualizado = self.turno_dao.actualizar(turno)
            if actualizado:
                print(f"[OK] Turno {id_turno} asignado correctamente.")

                # Intentar enviar notificación por mail al paciente. No revertimos la operación
                # si el envío falla: solo registramos el resultado en consola.
                try:
                    email = getattr(paciente, 'email', None)
                    if email:
                        # Construir mail_config aquí si tu servicio/DB lo provee.
                        # Actualmente usamos variables de entorno como ejemplo,
                        # pero puedes reemplazar esto por campos del médico/clinica.
                        mail_config = {
                            'SMTP_HOST': os.environ.get('SMTP_HOST'),
                            'SMTP_PORT': os.environ.get('SMTP_PORT'),
                            'SMTP_USER': os.environ.get('SMTP_USER'),
                            'SMTP_PASS': os.environ.get('SMTP_PASS'),
                            'FROM_EMAIL': os.environ.get('FROM_EMAIL'),
                            'SENDGRID_API_KEY': os.environ.get('SENDGRID_API_KEY'),
                            'ALLOW_SENDGRID_UNSUPPRESS': os.environ.get('ALLOW_SENDGRID_UNSUPPRESS'),
                        }
                        enviado = MailService.enviar_turno(email, turno, mail_config)
                        if enviado:
                            print(f"[OK] Notificación por mail enviada a {email} para turno {id_turno}.")
                        else:
                            print(f"[WARN] No se pudo enviar la notificación por mail a {email}.")
                    else:
                        print(f"[WARN] El paciente {dni_paciente} no tiene email registrado; no se envió notificación.")
                except Exception as e:
                    print(f"[ERROR Mail] Ocurrió un error al intentar enviar el mail: {e}")

            return actualizado
        
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            raise ValueError("Error de datos. Los datos proporcionados no son válidos.")    
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al actualizar la base de datos. Intente más tarde.")
        except ValueError as ve:
            print(f"[VALIDACIÓN] {ve}")
            raise
        except RuntimeError as re:
            # Captura errores de obtención/chequeo de existencia
            raise

    def cancelar_turno(self, id_turno, observaciones=None):
        """
        Cancela un turno programado y lo devuelve a estado 'disponible' para
        que vuelva a ofrecerse en la agenda.
        """
        # Obtener y validar turno
        try:
            turno = self.turno_dao.obtener_por_id(id_turno)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar el turno {id_turno}: {e}")

        if not turno:
            raise ValueError(f"No existe un turno con ID {id_turno}.")
        
        if turno.fecha_hora_inicio < datetime.now():
            raise ValueError(f"El turno con ID {id_turno} es pasado ({turno.fecha_hora_inicio}) y no puede ser cancelado.")

        if turno.estado not in ['programado']:
            raise ValueError(f"El turno {id_turno} no puede ser cancelado. Estado actual: {turno.estado}.")

        # Reestablecer el turno como disponible para que pueda reasignarse
        turno.estado = 'disponible'
        turno.dni_paciente = None
        turno.motivo = None
        turno.observaciones = observaciones or None

        try:
            turno._validar()
            actualizado = self.turno_dao.actualizar(turno)
            print(f"[OK] Turno {id_turno} marcado nuevamente como 'disponible'.")
            return actualizado

        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            raise ValueError("Fallo de integridad al cancelar el turno.")     
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico en la base de datos durante la cancelación.")
        except ValueError as ve:
            # Captura errores de validación si el modelo Turno._validar() falla
            print(f"[VALIDACIÓN] {ve}")
            raise
        except RuntimeError as re:
            # Captura errores de obtención/chequeo de existencia
            raise

    def marcar_atendido_turno(self, id_turno):
        """
        Marca un turno como 'atendido'. Aplica solo si el estado es 'programado'.
        """
        # Obtener y validar turno
        try:
            turno = self.turno_dao.obtener_por_id(id_turno)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar el turno {id_turno}: {e}")

        if not turno:
            raise ValueError(f"No existe un turno con ID {id_turno}.")

        ahora = datetime.now()
        if turno.fecha_hora_inicio.date() != ahora.date():
            raise ValueError(
                f"El turno {id_turno} no puede marcarse como atendido. "
                "Solo se permiten turnos del día en curso."
            )
        if ahora < turno.fecha_hora_inicio:
            raise ValueError(
                f"El turno {id_turno} no puede marcarse como atendido antes de la hora programada "
                f"({turno.fecha_hora_inicio.strftime('%H:%M')})."
            )
            
        if turno.estado != 'programado':
            raise ValueError(f"El turno {id_turno} solo se puede marcar como atendido si está 'programado'. Estado actual: {turno.estado}")

        # Modificar el estado y persistir
        turno.estado = 'atendido'

        try:
            turno._validar()
            self.turno_dao.actualizar(turno)
            print(f"[OK] Turno {id_turno} marcado como atendido.")
            return turno
        
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            raise ValueError("Fallo de integridad al actualizar el turno.")     
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al actualizar la base de datos.")
        except ValueError as ve:
            print(f"[VALIDACIÓN] {ve}")
            raise
        except RuntimeError as re:
            raise

    def marcar_ausente_turno(self, id_turno):
        """
        Marca un turno como 'ausente' si el paciente no se presentó.
        """
        # Obtener y validar turno
        try:
            turno = self.turno_dao.obtener_por_id(id_turno)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar el turno {id_turno}: {e}")

        if not turno:
            raise ValueError(f"No existe un turno con ID {id_turno}.")
        
        # VALIDACIÓN DE LA HORA DEL TURNO   
        # Regla: El turno debe haber pasado para poder marcarlo como ausente.
        if turno.fecha_hora_inicio > datetime.now():
            raise ValueError(
                f"El turno {id_turno} es futuro ({turno.fecha_hora_inicio.strftime('%Y-%m-%d %H:%M')}) "
                f"y aún no puede ser marcado como ausente."
            )
        
        if turno.estado != 'programado':
            raise ValueError(f"El turno {id_turno} solo se puede marcar como ausente si está 'programado'. Estado actual: {turno.estado}")

        # Modificar el estado y persistir
        turno.estado = 'ausente'

        try:
            turno._validar()
            self.turno_dao.actualizar(turno)
            print(f"[OK] Turno {id_turno} marcado como ausente.")
            return turno
        
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            raise ValueError("Fallo de integridad al actualizar el turno.")     
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al actualizar la base de datos.")
        except ValueError as ve:
            print(f"[VALIDACIÓN] {ve}")
            raise
        except RuntimeError as re:
            raise

    def obtener_turnos_disponibles_por_medico_y_fecha(self, nro_matricula_medico, fecha):
        """
        Obtiene los turnos disponibles para un médico en una fecha específica.
        """
        try:
            medico = self.medico_dao.obtener_por_id(nro_matricula_medico)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al verificar el médico {nro_matricula_medico}: {e}")
        
        if not medico or medico.activo == 0:
            raise ValueError(f"No existe un médico activo con matrícula {nro_matricula_medico}.")
        
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("La fecha tiene un formato inválido (usar YYYY-MM-DD)")
        if isinstance(fecha, (datetime, date)):
            fecha = fecha.date() if isinstance(fecha, datetime) else fecha
        else:
            raise ValueError("La fecha debe ser un string 'YYYY-MM-DD' o un objeto date/datetime.")
        
        if fecha < date.today():
            raise ValueError("La fecha no puede ser anterior a hoy")

        try:
            return self.turno_dao.obtener_turnos_disponibles_por_medico_y_fecha(nro_matricula_medico, fecha)
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener turnos disponibles por médico/fecha: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar los turnos disponibles.")
    
    def obtener_turnos_disponibles_por_medico_y_mes(self, nro_matricula_medico):
        """
        Obtiene los turnos disponibles para un médico en el mes actual.
        """
        try:
            medico = self.medico_dao.obtener_por_id(nro_matricula_medico)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al verificar el médico {nro_matricula_medico}: {e}")
        
        if not medico or medico.activo == 0:
            raise ValueError(f"No existe un médico activo con matrícula {nro_matricula_medico}.")

        hoy = date.today()
        mes_actual = hoy.month
        anio_actual = hoy.year

        try:
            return self.turno_dao.obtener_turnos_disponibles_por_medico_y_mes(nro_matricula_medico, mes_actual, anio_actual)
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener turnos disponibles por médico/mes: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar los turnos disponibles.")
    
    def obtener_turnos_disponibles_por_especialidad_y_fecha(self, especialidad, fecha):
        """
        Obtiene los turnos disponibles para el nombre de una especialidad en una fecha específica.
        """
        try:
            especialidad_obj = self.especialidad_dao.obtener_por_nombre(especialidad)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar la especialidad '{especialidad}': {e}")
        
        if not especialidad_obj:
            raise ValueError(f"No existe una especialidad activa con nombre '{especialidad}'.")
        else:
            id_especialidad = especialidad_obj.id_especialidad

        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("La fecha tiene un formato inválido (usar YYYY-MM-DD)")
        if isinstance(fecha, (datetime, date)):
            fecha = fecha.date() if isinstance(fecha, datetime) else fecha
        else:
            raise ValueError("La fecha debe ser un string 'YYYY-MM-DD' o un objeto date/datetime.")
        
        if fecha < date.today():
            raise ValueError("La fecha no puede ser anterior a hoy")

        try:
            return self.turno_dao.obtener_turnos_disponibles_por_especialidad_y_fecha(id_especialidad, fecha)
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener turnos por especialidad/fecha: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar los turnos por especialidad.")
        
    def obtener_turnos_disponibles_por_especialidad_y_mes(self, especialidad):
        """
        Obtiene los turnos disponibles para una el nombre de especialidad en el mes actual.
        """
        try:
            especialidad_obj = self.especialidad_dao.obtener_por_nombre(especialidad)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar la especialidad '{especialidad}': {e}")

        if not especialidad_obj:
            raise ValueError(f"No existe una especialidad activa con nombre '{especialidad}'.")
        
        id_especialidad = especialidad_obj.id_especialidad

        hoy = date.today()
        mes_actual = hoy.month
        anio_actual = hoy.year

        try:
            return self.turno_dao.obtener_turnos_disponibles_por_especialidad_y_mes(id_especialidad, mes_actual, anio_actual)
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener turnos por especialidad/mes: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar los turnos por especialidad.")

    def obtener_turnos_por_medico_en_un_periodo(self, nro_matricula_medico, fecha_inicio, fecha_fin):
        """Obtiene listado de turnos para un médico específico dentro de un período determinado."""

        # Verificar que el médico existe y está activo
        try:
            medico = self.medico_dao.obtener_por_id(nro_matricula_medico)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al verificar el médico {nro_matricula_medico}: {e}")
        
        if not medico or medico.activo == 0:
            raise ValueError(f"No existe un médico activo con matrícula {nro_matricula_medico}.")        
        
        # Validar el rango de fechas
        if isinstance(fecha_inicio, str):
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("La fecha tiene un formato inválido (usar YYYY-MM-DD)")
        if isinstance(fecha_inicio, (datetime, date)):
            fecha_inicio = fecha_inicio.date() if isinstance(fecha_inicio, datetime) else fecha_inicio
        else:
            raise ValueError("La fecha debe ser un string 'YYYY-MM-DD' o un objeto date/datetime.")    
        

        if isinstance(fecha_fin, str):
            try:
                fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("La fecha tiene un formato inválido (usar YYYY-MM-DD)")
        if isinstance(fecha_fin, (datetime, date)):
            fecha_fin = fecha_fin.date() if isinstance(fecha_fin, datetime) else fecha_fin
        else:
            raise ValueError("La fecha debe ser un string 'YYYY-MM-DD' o un objeto date/datetime.")

        if fecha_inicio > fecha_fin:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        
        if (fecha_fin - fecha_inicio).days > 30:
            raise ValueError("El período entre las fechas no puede ser mayor a 30 días.")
        
        # Obtener los turnos del médico en el período especificado
        try:
            return self.turno_dao.obtener_turnos_por_medico_en_un_periodo(nro_matricula_medico, fecha_inicio, fecha_fin)
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener turnos por medico y periodo: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar los turnos medico y periodo.")

    def obtener_turnos_por_especialidad_en_un_periodo(self, id_especialidad, fecha_inicio, fecha_fin):
        """Obtiene turnos de todos los médicos de una especialidad en un rango de fechas."""
        try:
            id_especialidad = int(id_especialidad)
        except Exception:
            raise ValueError("El identificador de la especialidad es inválido.")

        try:
            especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar la especialidad {id_especialidad}: {e}")

        if not especialidad or getattr(especialidad, "activo", 0) == 0:
            raise ValueError(f"No existe una especialidad activa con ID {id_especialidad}.")

        if isinstance(fecha_inicio, str):
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("La fecha tiene un formato inválido (usar YYYY-MM-DD)")
        if isinstance(fecha_inicio, datetime):
            fecha_inicio = fecha_inicio.date()
        if not isinstance(fecha_inicio, date):
            raise ValueError("La fecha debe ser un string 'YYYY-MM-DD' o un objeto date/datetime.")

        if isinstance(fecha_fin, str):
            try:
                fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("La fecha tiene un formato inválido (usar YYYY-MM-DD)")
        if isinstance(fecha_fin, datetime):
            fecha_fin = fecha_fin.date()
        if not isinstance(fecha_fin, date):
            raise ValueError("La fecha debe ser un string 'YYYY-MM-DD' o un objeto date/datetime.")

        if fecha_inicio > fecha_fin:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")

        if (fecha_fin - fecha_inicio).days > 30:
            raise ValueError("El período entre las fechas no puede ser mayor a 30 días.")

        try:
            return self.turno_dao.obtener_turnos_por_especialidad_en_un_periodo(
                id_especialidad, fecha_inicio, fecha_fin
            )
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener turnos por especialidad y periodo: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar los turnos por especialidad.")

    def obtener_resumen_asistencias(self, fecha_inicio=None, fecha_fin=None):
        """
        Retorna el conteo de turnos agrupados por estado dentro de un periodo opcional.
        """
        try:
            return self.turno_dao.contar_turnos_por_estado(fecha_inicio, fecha_fin)
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener resumen de asistencias: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar el resumen de asistencias.")

    def obtener_cantidad_turnos_por_estado_y_especialidad(self, id_especialidad):
        """
        Obtiene la cantidad de turnos por estado para una especialidad médica específica.
        Retorna un diccionario con estados como claves y cantidades como valores.
        """
        try:
            especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar la especialidad {id_especialidad}: {e}")
        
        if not especialidad or especialidad.activo == 0:
            raise ValueError(f"No existe una especialidad activa con ID {id_especialidad}.")

        try:
            return self.turno_dao.obtener_cantidad_turnos_por_estado_y_especialidad(id_especialidad)
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener cantidad de turnos por estado y especialidad: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la cantidad de turnos por estado y especialidad.")

    def obtener_cantidad_turnos_por_especialidades_y_estado(self):
        """Retorna un diccionario anidado con la cantidad de turnos por especialidad y estado. {especialidad: {estado: cantidad}}"""
        try:
            especialidades = self.especialidad_service.obtener_especialidades()
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar las especialidades: {e}")
        
        if especialidades is None or len(especialidades) == 0:
            raise ValueError("No existen especialidades registradas en el sistema.")

        resultado = {}
        for especialidad in especialidades:
            try:
                cantidades = self.obtener_cantidad_turnos_por_estado_y_especialidad(especialidad.id_especialidad)
                resultado[especialidad.nombre] = cantidades
            except Exception as e:
                print(f"[ERROR] Fallo al obtener cantidades para especialidad {especialidad.nombre}: {e}")
                resultado[especialidad.nombre] = {}
        return resultado

    def obtener_pacientes_atendidos_por_periodo(self, fecha_inicio, fecha_fin):
        """
        Obtiene la lista de objetos Paciente que fueron atendidos 
        (turno en estado 'atendido') dentro del rango de fechas.
        
        Retorna: lista de objetos Paciente.
        """
        # 1. Validación de fechas (formato y lógica)
        try:
            # Validar el rango de fechas
            if isinstance(fecha_inicio, str):
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError("La fecha tiene un formato inválido (usar YYYY-MM-DD)")
            if isinstance(fecha_inicio, (datetime, date)):
                fecha_inicio = fecha_inicio.date() if isinstance(fecha_inicio, datetime) else fecha_inicio
            else:
                raise ValueError("La fecha debe ser un string 'YYYY-MM-DD' o un objeto date/datetime.")    
            

            if isinstance(fecha_fin, str):
                try:
                    fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError("La fecha tiene un formato inválido (usar YYYY-MM-DD)")
            if isinstance(fecha_fin, (datetime, date)):
                fecha_fin = fecha_fin.date() if isinstance(fecha_fin, datetime) else fecha_fin
            else:
                raise ValueError("La fecha debe ser un string 'YYYY-MM-DD' o un objeto date/datetime.")

            if fecha_inicio > fecha_fin:
                raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")
            
            if (fecha_fin - fecha_inicio).days > 30:
                raise ValueError("El período entre las fechas no puede ser mayor a 30 días.")
            
            
        except ValueError as e:
            # Captura errores de formato o lógica de fechas
            print(f"[ERROR VALIDACIÓN] Error en el formato o lógica de fechas: {e}")
            raise ValueError("Formato de fecha inválido (use YYYY-MM-DD) o rango incorrecto.")
        
        # 2. Llamada al DAO
        try:
            # La llamada al DAO usa las fechas validadas
            pacientes = self.turno_dao.obtener_pacientes_atendidos_por_periodo(fecha_inicio, fecha_fin)
            return pacientes
            
        except DatabaseError as e:
            print(f"[ERROR DB] Fallo al obtener pacientes atendidos: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la base de datos.")
        except Exception as e:
            print(f"[ERROR RUNTIME] Error inesperado en TurnoService: {e}")
            raise RuntimeError("Ocurrió un error interno del sistema.")



    ################# VER SI ESTA BIEN IMPLEMENTADO Y SI VAN ############################
    def procesar_ausentes_dia_anterior(self):
        #Ya seria mucho implementar esto? 
        """
        Método diseñado para ser llamado por un proceso automático (cron job).
        Marca como 'ausente' todos los turnos 'programado' de ayer.
        """
        ayer = (datetime.now() - timedelta(days=1)).date()
        
        try:
            # Esta lógica debería estar implementada en el DAO con una única consulta UPDATE
            conteo_actualizado = self.turno_dao.marcar_ausentes_por_fecha(ayer)
            print(f"[JOB OK] {conteo_actualizado} turnos de la fecha {ayer} marcados como ausentes.")
            return conteo_actualizado
        
        except DatabaseError as e:
            print(f"[ERROR DB AUTOMÁTICO] Fallo al procesar ausentes de ayer: {e}")
            raise RuntimeError("Fallo en el proceso automático de marcado de ausentes.")
        
    def obtener_todos_los_turnos(self):
        """
        Obtiene todos los turnos registrados en el sistema.
        """
        try:
            return self.turno_dao.obtener_todos()
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener todos los turnos: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar todos los turnos.")
    
    def obtener_turno_por_id(self, id_turno):
        """
        Obtiene un turno por su ID.
        """
        try:
            turno = self.turno_dao.obtener_por_id(id_turno)
            if not turno:
                raise NotFoundError(f"No existe un turno con ID {id_turno}.")
            return turno
        except NotFoundError as nfe:
            raise nfe
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener el turno {id_turno}: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar el turno.")                                           
    
