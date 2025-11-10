import sqlite3
import os

class DBConnection:
    _instance = None

    def __new__(cls, db_path="turnos_medicos.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(db_path)
        return cls._instance

    def _initialize(self, db_path):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._create_schema()

    @property
    def conn(self):
        return self._connection
    
    def _create_schema(self):
        cur = self.conn.cursor()

        # Paciente
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Paciente (
            dni INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            fecha_nacimiento DATE NOT NULL,
            email TEXT NOT NULL,
            direccion TEXT
            activo INTEGER DEFAULT 1
        )
        ''')

        # Especialidad
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Especialidad (
            id_especialidad INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre UNIQUE TEXT NOT NULL,
            descripcion TEXT
            activo INTEGER DEFAULT 1
        )
        ''')

        # Medico
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Medico (
            nro_matricula INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            email TEXT,
            id_especialidad INTEGER NOT NULL,
            activo INTEGER DEFAULT 1
            FOREIGN KEY(id_especialidad) REFERENCES Especialidad(id_especialidad)
        )
        ''')

        # Agenda
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Agenda (
            nro_matricula_medico INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            dias_semana TEXT NOT NULL,  -- SET simulado con texto
            hora_inicio TIME NOT NULL,
            hora_fin TIME NOT NULL,
            duracion_minutos INTEGER NOT NULL,
            PRIMARY KEY (nro_matricula_medico, mes),
            FOREIGN KEY (nro_matricula_medico) REFERENCES Medico(nro_matricula)
        )
        ''')

        # Turno
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Turno (
            id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora_inicio DATETIME NOT NULL,
            motivo TEXT,
            observaciones TEXT,
            estado TEXT CHECK(estado IN ('disponible', 'programado', 'atendido', 'cancelado', 'ausente')),
            dni_paciente INTEGER,
            nro_matricula_medico INTEGER,
            FOREIGN KEY(dni_paciente) REFERENCES Paciente(dni),
            FOREIGN KEY(nro_matricula_medico) REFERENCES Medico(nro_matricula)
        )
        ''')

        # Historial Clínico
        cur.execute('''
        CREATE TABLE IF NOT EXISTS HistorialClinico (
            dni_paciente INTEGER PRIMARY KEY,
            FOREIGN KEY(dni_paciente) REFERENCES Paciente(dni)
        )
        ''')

        # Consulta
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Consulta (
            id_consulta INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora DATETIME NOT NULL,
            diagnostico TEXT,
            observaciones TEXT,
            id_historial_clinico INTEGER NOT NULL,
            nro_matricula_medico INTEGER NOT NULL,
            FOREIGN KEY(id_historial_clinico) REFERENCES HistorialClinico(dni_paciente),
            FOREIGN KEY(nro_matricula_medico) REFERENCES Medico(nro_matricula)
        )
        ''')

        # Receta
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Receta (
            id_receta INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_emision DATE NOT NULL,
            medicamentos TEXT,
            detalle TEXT,
            id_consulta INTEGER NOT NULL,
            FOREIGN KEY(id_consulta) REFERENCES Consulta(id_consulta)
        )
        ''')

        """Persistencia de datos iniciales, por ahora no hay datos iniciales.

        # Datos iniciales
        cur.executemany('''
        INSERT OR IGNORE INTO Especialidad (id_especialidad, nombre, descripcion)
        VALUES (?, ?, ?)
        ''', [
            (1, 'Clínica Médica', 'Medicina general'),
            (2, 'Pediatría', 'Atención a niños'),
            (3, 'Cardiología', 'Enfermedades del corazón')
        ])
        """
        self.conn.commit()
