digi-location-manager/
│
├── src/
│   ├── app.py                # Punto de entrada Flask
│   │
│   ├── config/
│   │   └── settings.py       # Variables de entorno, DB config
│   │
│   ├── domain/
│   │   ├── digi.py           # Dataclass Digi
│   │   ├── execution.py      # Modelo ejecución/audit
│   │   └── router_status.py  # Estados del sistema
│   │
│   ├── services/
│   │   ├── digi_service.py   # Llamadas API Digi RM
│   │   ├── execution_service.py  # Lógica de validación y ejecución
│   │   └── reboot_service.py     # Reboot escalonado
│   │
│   ├── repositories/
│   │   ├── db.py             # Conexión MSSQL
│   │   ├── audit_repository.py
│   │   └── router_repository.py
│   │
│   ├── controllers/
│   │   └── web_controller.py # Endpoints Flask
│   │
│   ├── utils/
│   │   ├── csv_loader.py
│   │   ├── validators.py
│   │   └── timers.py
│   │
│   ├── templates/
│   │   └── index.html        # Tu UI
│   │
│   └── static/
│       ├── css/
│       └── js/
│
├── .env
├── requirements.txt
└── README.md