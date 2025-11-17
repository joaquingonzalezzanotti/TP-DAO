from datetime import datetime, date

from persistencia.dao.turno_dao import TurnoDAO
from persistencia.dao.paciente_dao import PacienteDAO
from persistencia.persistencia_errores import IntegridadError, DatabaseError
from modelos.paciente import Paciente


class PacienteService:
    """
    Servicio que encapsula la lógica de negocio relacionada con los pacientes.
    Provee operaciones CRUD y consultas de conveniencia sobre pacientes.
    """

    def __init__(self):
        self.turno_dao = TurnoDAO()
        self.paciente_dao = PacienteDAO()

    def agregar_paciente(self, dni, nombre, apellido, fecha_nacimiento, email=None, direccion=None):
        """
        Registra un nuevo paciente en el sistema.
        Valida existencia previa y delega en el DAO.
        """
        try:
            # Verificar si ya existe
            try:
                existente = self.paciente_dao.obtener_por_id(dni)
            except Exception as e:
                raise RuntimeError(f"Fallo técnico al verificar paciente existente: {e}")

            if existente:
                raise ValueError(f"Ya existe un paciente con DNI {dni}.")

            paciente = Paciente(dni, nombre, apellido, fecha_nacimiento, email, direccion)
            self.paciente_dao.crear(paciente)
            return paciente

        except IntegridadError as e:
            print(f"[ERROR BIZ] Fallo de integridad al agregar paciente: {e}")
            raise ValueError("Fallo en la base de datos al registrar el paciente.")
        except DatabaseError as e:
            print(f"[ERROR DB] Fallo general de base de datos: {e}")
            raise RuntimeError("Ocurrió un error técnico en la base de datos. Intente más tarde.")
        except (ValueError, RuntimeError) as err:
            print(f"[ERROR VALIDACIÓN/RUNTIME] {err}")
            raise

    def obtener_pacientes(self):
        """Obtiene todos los pacientes activos."""
        try:
            return self.paciente_dao.obtener_todos()
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener pacientes: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la lista de pacientes.")

    def obtener_pacientes_inactivos(self):
        """Obtiene pacientes inactivos."""
        try:
            return self.paciente_dao.obtener_todos_inactivos()
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener pacientes inactivos: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la lista de pacientes inactivos.")

    def obtener_paciente_por_dni(self, dni):
        """Obtiene un paciente por su DNI."""
        try:
            return self.paciente_dao.obtener_por_id(dni)
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener paciente: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar el paciente por DNI.")

    def obtener_pacientes_por_apellido(self, apellido: str):
        """
        Obtiene pacientes cuyo apellido coincida parcialmente.
        Si el DAO no ofrece un método específico, realiza el filtrado en memoria.
        """
        try:
            # Intentar llamar al DAO si implementa método específico
            if hasattr(self.paciente_dao, 'obtener_por_apellido'):
                return self.paciente_dao.obtener_por_apellido(apellido)
            # Sino, filtrar localmente
            todos = self.paciente_dao.obtener_todos()
            return [p for p in todos if apellido.lower() in p.apellido.lower()]
        except Exception as e:
            print(f"[ERROR DB] Fallo al obtener pacientes por apellido: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar pacientes por apellido.")

    def actualizar_paciente(self, dni, nombre=None, apellido=None, fecha_nacimiento=None, email=None, direccion=None):
        """
        Actualiza los datos de un paciente existente.
        """
        try:
            paciente = self.paciente_dao.obtener_por_id(dni)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar paciente para actualizar: {e}")

        if not paciente or getattr(paciente, 'activo', 1) == 0:
            raise ValueError(f"No existe un paciente activo con DNI {dni}.")

        if nombre is not None:
            paciente.nombre = nombre
        if apellido is not None:
            paciente.apellido = apellido
        if fecha_nacimiento is not None:
            paciente.fecha_nacimiento = fecha_nacimiento
        if email is not None:
            paciente.email = email
        if direccion is not None:
            paciente.direccion = direccion

        try:
            # Validación a nivel de modelo si existe
            if hasattr(paciente, '_validar'):
                paciente._validar()
            actualizado = self.paciente_dao.actualizar(paciente)
            if actualizado:
                print(f"[OK] Paciente con DNI {dni} actualizado correctamente.")
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

    def eliminar_paciente(self, dni):
        """Baja lógica del paciente (activo = 0)."""
        try:
            paciente = self.paciente_dao.obtener_por_id(dni)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar paciente para baja: {e}")

        if not paciente:
            raise ValueError(f"No existe un paciente con DNI {dni}.")
        if getattr(paciente, 'activo', 1) == 0:
            raise ValueError(f"El paciente con DNI {dni} ya está inactivo.")

        try:
            self.paciente_dao.eliminar(dni)
            print(f"[OK] Paciente con DNI {dni} desactivado correctamente.")
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}")
            raise ValueError("No se puede desactivar el paciente. Podría tener referencias activas.")
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al desactivar el paciente. Intente más tarde.")

    def activar_paciente(self, dni):
        """Reactivar un paciente inactivo (activo = 1)."""
        try:
            paciente = self.paciente_dao.obtener_por_id(dni)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar paciente para activación: {e}")

        if not paciente:
            raise ValueError(f"No existe un paciente con DNI {dni}.")

        if getattr(paciente, 'activo', 1) == 1:
            raise ValueError(f"El paciente con DNI {dni} ya está activo.")

        try:
            self.paciente_dao.activar(dni)
            print(f"[OK] Paciente con DNI {dni} reactivado correctamente.")
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}")
            raise ValueError("No se puede activar el paciente.")
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al activar el paciente. Intente más tarde.")

    def obtener_turnos_por_paciente_en_un_periodo(self, dni, fecha_inicio, fecha_fin):
        """
        Obtiene listado de turnos asignados a un paciente dentro de un período determinado.
        Valida que el paciente exista y delega la consulta al DAO de turnos si el método está disponible.
        """
        try:
            paciente = self.paciente_dao.obtener_por_id(dni)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al verificar el paciente {dni}: {e}")

        if not paciente or getattr(paciente, 'activo', 1) == 0:
            raise ValueError(f"No existe un paciente activo con DNI {dni}.")

        # Validación básica de fechas (acepta string YYYY-MM-DD o date)
        def _parse_date(d):
            if isinstance(d, str):
                try:
                    return datetime.strptime(d, '%Y-%m-%d').date()
                except Exception:
                    raise ValueError('La fecha tiene un formato inválido (usar YYYY-MM-DD)')
            if isinstance(d, datetime):
                return d.date()
            if isinstance(d, date):
                return d
            raise ValueError("La fecha debe ser 'YYYY-MM-DD' o un objeto date/datetime.")

        fecha_inicio = _parse_date(fecha_inicio)
        fecha_fin = _parse_date(fecha_fin)

        if fecha_inicio > fecha_fin:
            raise ValueError('La fecha de inicio no puede ser posterior a la fecha de fin.')
        if (fecha_fin - fecha_inicio).days > 90:
            raise ValueError('El período entre las fechas no puede ser mayor a 90 días.')

        try:
            if hasattr(self.turno_dao, 'obtener_turnos_por_paciente_en_un_periodo'):
                return self.turno_dao.obtener_turnos_por_paciente_en_un_periodo(dni, fecha_inicio, fecha_fin)
            # Si el DAO no implementa el método, intentar delegar a TurnoService no disponible aquí
            raise RuntimeError('El DAO de turnos no implementa la consulta requerida.')
        except DatabaseError as e:
            print(f"[ERROR DB] Fallo al obtener turnos por paciente y periodo: {e}")
            raise RuntimeError('Ocurrió un error técnico al consultar los turnos por paciente y periodo.')
        except Exception as e:
            print(f"[ERROR RUNTIME] Error inesperado en PacienteService: {e}")
            raise
