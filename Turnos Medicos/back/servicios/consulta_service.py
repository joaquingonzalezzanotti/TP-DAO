from datetime import datetime, date

from persistencia.dao.consulta_dao import ConsultaDAO
from persistencia.dao.paciente_dao import PacienteDAO
from persistencia.dao.medico_dao import MedicoDAO
from persistencia.persistencia_errores import IntegridadError, DatabaseError
from modelos.consulta import Consulta


class ConsultaService:
    """
    Servicio para operaciones sobre Consultas.
    Sigue el patrón de MedicoService/PacienteService en manejo de errores
    y validaciones mínimas.
    """

    def __init__(self):
        self.consulta_dao = ConsultaDAO()
        self.paciente_dao = PacienteDAO()
        self.medico_dao = MedicoDAO()

    def agregar_consulta(self, fecha_hora, diagnostico, observaciones, dni_paciente, nro_matricula_medico):
        """Crea una nueva consulta validando existencia de paciente y médico."""
        try:
            # Validar paciente
            try:
                paciente = self.paciente_dao.obtener_por_id(dni_paciente)
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar paciente: {e}")
            if not paciente or getattr(paciente, 'activo', 1) == 0:
                raise ValueError(f"No existe un paciente activo con DNI {dni_paciente}.")

            # Validar médico
            try:
                medico = self.medico_dao.obtener_por_id(nro_matricula_medico)
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar médico: {e}")
            if not medico or getattr(medico, 'activo', 1) == 0:
                raise ValueError(f"No existe un médico activo con matrícula {nro_matricula_medico}.")

            # Parse fecha_hora si viene como string
            if isinstance(fecha_hora, str):
                try:
                    fecha_hora_parsed = datetime.strptime(fecha_hora, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    try:
                        fecha_hora_parsed = datetime.strptime(fecha_hora, '%Y-%m-%d %H:%M')
                    except Exception:
                        raise ValueError('Formato de fecha_hora inválido. Use YYYY-MM-DD HH:MM[:SS]')
            elif isinstance(fecha_hora, datetime):
                fecha_hora_parsed = fecha_hora
            else:
                raise ValueError('fecha_hora debe ser string o datetime')

            consulta = Consulta(
                fecha_hora=fecha_hora_parsed,
                diagnostico=diagnostico,
                observaciones=observaciones,
                dni_paciente=dni_paciente,
                nro_matricula_medico=nro_matricula_medico
            )

            self.consulta_dao.crear(consulta)
            return consulta

        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}")
            raise ValueError("Error de integridad al crear la consulta.")
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Error técnico en la base de datos. Intente más tarde.")
        except (ValueError, RuntimeError) as err:
            print(f"[ERROR VALIDACIÓN/RUNTIME] {err}")
            raise

    def obtener_consultas(self):
        try:
            return self.consulta_dao.obtener_todos()
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener consultas: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar las consultas.")

    def obtener_consulta_por_id(self, id_consulta):
        try:
            consulta = self.consulta_dao.obtener_por_id(id_consulta)
            if not consulta:
                raise ValueError(f"No existe una consulta con ID {id_consulta}.")
            return consulta
        except ValueError:
            raise
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener la consulta {id_consulta}: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la consulta.")

    def actualizar_consulta(self, id_consulta, diagnostico=None, observaciones=None):
        try:
            consulta = self.consulta_dao.obtener_por_id(id_consulta)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar consulta para actualizar: {e}")

        if not consulta:
            raise ValueError(f"No existe una consulta con ID {id_consulta}.")

        if diagnostico is not None:
            consulta.diagnostico = diagnostico
        if observaciones is not None:
            consulta.observaciones = observaciones

        try:
            actualizado = self.consulta_dao.actualizar(consulta)
            if actualizado:
                print(f"[OK] Consulta {id_consulta} actualizada correctamente.")
            return actualizado
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}")
            raise ValueError("Error de integridad al actualizar la consulta.")
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Error técnico en la base de datos. Intente más tarde.")
        except ValueError as ve:
            print(f"[VALIDACIÓN] {ve}")
            raise

    def eliminar_consulta(self, id_consulta):
        """Elimina físicamente una consulta (operación DELETE)."""
        try:
            # Llamar al DAO. El DAO puede prohibir la operación según reglas.
            self.consulta_dao.eliminar(id_consulta)
            print(f"[OK] Consulta {id_consulta} eliminada físicamente.")
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}")
            raise ValueError("No se puede eliminar la consulta debido a una violación de integridad.")
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Error técnico en la base de datos al eliminar la consulta.")
        except ValueError as ve:
            # El DAO puede lanzar ValueError si la eliminación no está permitida
            print(f"[VALIDACIÓN] {ve}")
            raise
        except Exception as e:
            print(f"[ERROR] Fallo inesperado al eliminar la consulta: {e}")
            raise RuntimeError("Fallo interno al eliminar la consulta.")

    def obtener_consultas_por_paciente(self, dni_paciente):
        try:
            # Validar paciente existe
            try:
                paciente = self.paciente_dao.obtener_por_id(dni_paciente)
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar paciente: {e}")
            if not paciente:
                raise ValueError(f"No existe un paciente con DNI {dni_paciente}.")

            # Si el DAO tiene un método específico, usarlo
            if hasattr(self.consulta_dao, 'obtener_por_paciente'):
                return self.consulta_dao.obtener_por_paciente(dni_paciente)

            # Sino, filtrar en memoria
            todas = self.consulta_dao.obtener_todos()
            return [c for c in todas if getattr(c, 'dni_paciente', None) == dni_paciente]

        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Error técnico al consultar consultas por paciente.")
        except Exception as e:
            print(f"[ERROR RUNTIME] {e}")
            raise
