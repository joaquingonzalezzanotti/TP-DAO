Trabajo práctico DAO - Sistema de Turnos Médicos
## 🗂️ Estructura del repositorio
```
TP-DAO-G9/
├── Documentacion/                 # Consignas y diagramas de referencia
├── Turnos Medicos/
│   ├── assets/                    # Recursos estáticos (logo, imágenes)
│   ├── back/                      # Lógica de negocio y persistencia
│   │   ├── modelos/               # Clases de dominio (Turno, Paciente, Médicos, etc.)
│   │   ├── persistencia/          # DAOs, conexión y base SQLite local
│   │   │   └── dao/               # Implementaciones DAO por entidad
│   │   └── servicios/             # Servicios que orquestan DAOs y reglas
│   └── front/                     # Interfaz de usuario
│       ├── app.py                 # Aplicación principal en Tkinter (usar esta)
│       └── flask_frontend/        # Prototipo web no utilizado
├── README.md
```