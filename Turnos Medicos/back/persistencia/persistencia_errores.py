# persistencia/persistencia_errores.py

class PersistenciaError(Exception):
    """Clase base para errores en la capa de persistencia."""
    pass

class DatabaseError(PersistenciaError):
    """Error general de la base de datos (Ej: Conexión o SQL genérico)."""
    pass

class IntegridadError(PersistenciaError):
    """Error de integridad de datos (Ej: Clave duplicada, FK rota)."""
    pass

class NotFoundError(PersistenciaError):
    """Objeto no encontrado durante una consulta (Ej: obtener_por_id)."""
    pass