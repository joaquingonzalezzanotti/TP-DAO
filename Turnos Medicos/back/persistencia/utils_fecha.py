# persistencia/utils_fecha.py
from datetime import datetime, date

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"
DATE_FMT = "%Y-%m-%d"

def format_date_for_db(value):
    """
    Acepta date o str('YYYY-MM-DD') -> retorna 'YYYY-MM-DD' (string).
    Lanza ValueError si no es válido.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.strftime(DATE_FMT)
    if isinstance(value, str):
        # validar formato aceptado
        try:
            _ = datetime.strptime(value, DATE_FMT).date()
            return value
        except ValueError:
            raise ValueError("La fecha debe tener formato 'YYYY-MM-DD'.")
    raise ValueError("La fecha debe ser datetime.date o string 'YYYY-MM-DD'.")

def format_datetime_for_db(value):
    """
    Acepta datetime o str('YYYY-MM-DD HH:MM' o 'YYYY-MM-DD HH:MM:SS') -> retorna 'YYYY-MM-DD HH:MM:SS'
    Lanza ValueError si no es válido.
    """
    if isinstance(value, datetime):
        return value.strftime(DATETIME_FMT)
    if isinstance(value, str):
        # intentar dos formatos comunes
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                dt = datetime.strptime(value, fmt)
                return dt.strftime(DATETIME_FMT)
            except ValueError:
                continue
        raise ValueError("El datetime debe tener formato 'YYYY-MM-DD HH:MM[:SS]'.")
    raise ValueError("El valor debe ser datetime.datetime o string 'YYYY-MM-DD HH:MM[:SS]'.")