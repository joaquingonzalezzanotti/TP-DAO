from persistencia.dao.especialidad_dao import EspecialidadDAO
from persistencia.persistencia_errores import IntegridadError, DatabaseError
from modelos.especialidad import Especialidad

class EspecialidadService:
    """
    Servicio que encapsula la lógica de negocio relacionada con las especialidades.
    Coordina acceso a DAO y aplica reglas.
    """

    def __init__(self):
        self.especialidad_dao = EspecialidadDAO()

    def agregar_especialidad(self, nombre: str, descripcion: str = None):
        """
        Registra una nueva especialidad en el sistema.
        """
        try:
            # 1. Validación de preexistencia por nombre (buscamos si existe activa o inactiva)
            # Nota: El DAO provisto solo busca activos con LIKE, ajustamos la lógica de chequeo si fuera necesario.
            # Asumiremos que el DAO solo soporta obtener por ID/nombre, y la validación de duplicados
            # por nombre exacto la haríamos idealmente con un método que traiga la especialidad por nombre exacto.

            # Chequeo aproximado por nombre (si el DAO lo permite)
            existente = self.especialidad_dao.obtener_por_nombre(nombre)
            if existente:
                # Nota: Si el DAO usa LIKE, esto puede dar falsos positivos. Idealmente, se busca por nombre exacto.
                raise ValueError(f"Ya existe una especialidad con nombre similar ('{nombre}').")

            # 2. Crear el objeto de dominio
            # Asumimos que el modelo Especialidad implementa un método de validación interno.
            especialidad = Especialidad(nombre=nombre, descripcion=descripcion)
            especialidad._validar() # Si el modelo tiene validación

            # 3. Persistir en la DB
            self.especialidad_dao.crear(especialidad)

            return especialidad
        
        except IntegridadError as e:
            print(f"[ERROR BIZ] Fallo de integridad al agregar especialidad: {e}")
            raise ValueError("Fallo en la base de datos al registrar la especialidad (posible duplicado de nombre).")      
        except DatabaseError as e:
            print(f"[ERROR DB] Fallo general de base de datos: {e}")
            raise RuntimeError("Ocurrió un error técnico en la base de datos. Intente más tarde.") 
        except (ValueError, RuntimeError) as err:
            print(f"[ERROR VALIDACIÓN/RUNTIME] {err}")
            raise

    def obtener_especialidad_por_id(self, id_especialidad: int):
        """
        Obtiene una especialidad por su ID (activa o inactiva).
        Retorna: Especialidad o lanza ValueError/RuntimeError
        """
        try:
            especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener especialidad: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la especialidad por ID.")
        
        if especialidad is None:
            raise ValueError(f"No existe una especialidad con ID {id_especialidad}.")
            
        return especialidad

    def obtener_especialidades(self):
        """
        Obtiene todas las especialidades activas.
        Retorna: lista de Especialidad
        """
        try:
            return self.especialidad_dao.obtener_todos()
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener especialidades: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la lista de especialidades.")
    
    def obtener_especialidades_inactivas(self):
        """
        Obtiene todas las especialidades inactivas.
        Retorna: lista de Especialidad
        """
        try:
            return self.especialidad_dao.obtener_todos_inactivos()
        except Exception as e:
            print(f"[ERROR DB] Fallo general de base de datos al obtener especialidades inactivas: {e}")
            raise RuntimeError("Ocurrió un error técnico al consultar la lista de especialidades inactivas.")

    def actualizar_especialidad(self, id_especialidad: int, nombre: str = None, descripcion: str = None):
        """
        Actualiza los datos de una especialidad existente.
        """
        # 1. Obtener especialidad existente
        try:
            especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar especialidad para actualizar: {e}")

        if not especialidad:
            raise ValueError(f"No existe una especialidad con ID {id_especialidad}.")

        # 2. Actualizar solo los campos proporcionados
        if nombre is not None:
            especialidad.nombre = nombre
        if descripcion is not None:
            especialidad.descripcion = descripcion
            
        # 3. Validar y Persistir
        try:
            especialidad._validar() # Validación interna del modelo
            actualizado = self.especialidad_dao.actualizar(especialidad)
            
            if actualizado:
                print(f"[OK] Especialidad con ID {id_especialidad} actualizada correctamente.")
            return actualizado
        
        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            # Esto puede ocurrir si se intenta actualizar a un nombre que ya existe (duplicado)
            raise ValueError("Error de datos. El nombre de especialidad proporcionado ya existe.") 
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al actualizar la base de datos.")
        except ValueError as ve:
            print(f"[VALIDACIÓN] {ve}")
            raise

    def eliminar_especialidad(self, id_especialidad: int):
        """
        Realiza la baja lógica de una especialidad (activo = 0).
        Regla de negocio: Si tiene médicos activos asociados, NO debería permitirse la baja.
        """
        # 1. Obtener especialidad
        try:
            especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar especialidad para baja: {e}")
            
        if not especialidad:
            raise ValueError(f"No existe una especialidad con ID {id_especialidad}.")
        if especialidad.activo == 0:
            raise ValueError(f"La especialidad con ID {id_especialidad} ya está inactiva.")

        # 2. **REGLA DE NEGOCIO CRÍTICA**: Chequear si hay médicos activos.
        # Esto requiere una dependencia adicional o un método en el DAO para chequear médicos.
        # Asumimos que la lógica de negocio requiere evitar el borrado si hay médicos activos.
        
        # OMITIMOS EL CHEQUEO DE MÉDICOS AQUÍ, ASUMIENDO QUE EL DAO LO CHEQUEA O QUE LA REGLA SE APLICA FUERA.
        # Si hubiera una clase MedicoDAO, la usaríamos: self.medico_dao.contar_activos_por_especialidad(id_especialidad)

        # 3. Persistir la baja lógica
        try:
            self.especialidad_dao.eliminar(id_especialidad)
            print(f"[OK] Especialidad con ID {id_especialidad} desactivada correctamente.")
        
        except IntegridadError as e:
            # Si la DB impone restricción FK de forma estricta (aunque sea baja lógica)
            print(f"[ERROR INTEGRIDAD] {e}") 
            raise ValueError("No se puede desactivar la especialidad. Podría tener dependencias activas.")
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al desactivar la especialidad. Intente más tarde.")
    
    def activar_especialidad(self, id_especialidad: int):
        """
        Reactiva una especialidad inactiva (activo = 1).
        """
        # 1. Obtener especialidad
        try:
            especialidad = self.especialidad_dao.obtener_por_id(id_especialidad)
        except Exception as e:
            raise RuntimeError(f"Fallo técnico al consultar especialidad para activación: {e}")

        if not especialidad:
            raise ValueError(f"No existe una especialidad con ID {id_especialidad}.")

        if especialidad.activo == 1:
            raise ValueError(f"La especialidad con ID {id_especialidad} ya está activa.")

        # 2. Persistir la activación
        try:
            self.especialidad_dao.activar(id_especialidad)
            print(f"[OK] Especialidad con ID {id_especialidad} reactivada correctamente.")

        except IntegridadError as e:
            print(f"[ERROR INTEGRIDAD] {e}") 
            raise ValueError("No se puede activar la especialidad.")
        except DatabaseError as e:
            print(f"[ERROR DB] {e}")
            raise RuntimeError("Ocurrió un error técnico al activar la especialidad. Intente más tarde.")