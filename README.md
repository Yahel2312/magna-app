# ⚡ Magna App — Asistencia Juvenil

Sistema de registro de asistencia gamificado para el grupo juvenil **Magna**. Permite registrar asistencia semanal, calcular rachas de asistencias consecutivas, y visualizar estadísticas en tiempo real.

---

## 🗂️ Grupos

| Grupo | Descripción |
|---|---|
| 🎒 Secundarios | Jóvenes de secundaria |
| 📚 Prepos | Jóvenes de preparatoria |
| 🎓 Universitarios | Estudiantes universitarios |
| 💼 Profesionistas | Adultos jóvenes con carrera |

---

## 🚀 Instalación y ejecución

### Requisitos previos

- Python 3.11+
- `pip`

### 1. Clonar e instalar dependencias

```bash
git clone <url-del-repo>
cd magna-app
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
# Copia la plantilla
copy .env.example .env

# Edita .env con tus valores
# ADMIN_USER=tu_usuario
# ADMIN_PASSWORD=tu_contrasena_segura
# SECRET_KEY=una-clave-larga-y-aleatoria
```

### 3. Preparar el archivo de jóvenes

Coloca `Chicos.xlsx` en la raíz del proyecto con la estructura:

| A — Secundarios | B — Prepos | C — Universitarios | D — Profesionistas |
|---|---|---|---|
| Juan Pérez | María García | Carlos López | Ana Martínez |
| ... | ... | ... | ... |

*(La primera fila se ignora como encabezado)*

### 4. Ejecutar el servidor

```bash
uvicorn app.main:app --reload
```

Al iniciar, la app:
- Crea las tablas en `asistencia.db` automáticamente
- Importa los jóvenes desde `Chicos.xlsx`
- Crea el admin por defecto (definido en `.env`) si no existe ninguno

### 5. Abrir en el navegador

| Ruta | Descripción |
|---|---|
| `http://localhost:8000` | Pantalla de registro para los jóvenes |
| `http://localhost:8000/admin-panel` | Panel de administración |
| `http://localhost:8000/docs` | Documentación interactiva de la API (Swagger) |

---

## 🎮 Gamificación

Cada vez que un joven registra asistencia:

| Acción | Efecto |
|---|---|
| Asistencia simple | `+10 puntos_totales` |
| Asistencia consecutiva al evento anterior | `racha_actual++`, `+10 puntos_racha` |
| Sin asistencia en el evento anterior | `racha_actual = 1` |
| Superar su racha máxima | `racha_maxima` se actualiza automáticamente |

La pantalla principal muestra mensajes como:
- `🔥 Juan Pérez — 5 semanas en racha`
- `🏆 Ana García — ¡Nueva racha máxima! 8 semanas seguidas`

---

## 🛡️ Administración

El panel de administración (`/admin-panel`) requiere login con usuario y contraseña.

### Funcionalidades del panel

- **Tarjetas de hoy**: conteo de asistentes totales y por grupo
- **Top-10 rachas**: tabla con los jóvenes con mayor racha activa
- **Historial semanal**: gráfica y tabla de los últimos 8 eventos
- **Exportar Excel**: descarga el reporte del día en formato `.xlsx`
- **Gestión de admins**: crea y desactiva cuentas de administrador directamente desde el panel

### Gestión de administradores

#### Desde el panel (recomendado)

1. Inicia sesión en `/admin-panel`.
2. Desplázate hasta la sección **🛡️ Administradores** al final del panel.
3. Haz clic en **＋ Nuevo admin** y completa el formulario (nombre, usuario, contraseña).
4. Para desactivar un admin existente, haz clic en **Desactivar** en su fila.

> **Nota:** no puedes desactivar tu propia cuenta desde el panel.

#### Desde la API (alternativa)

Puedes usar `POST /auth/login` para obtener un token y luego llamar a los endpoints:

```bash
# 1. Obtener token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "magna2024"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Crear un nuevo admin
curl -X POST http://localhost:8000/admin/admins \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "nuevo", "password": "pass1234", "nombre": "Nuevo Admin"}'

# 3. Listar todos los admins
curl http://localhost:8000/admin/admins \
  -H "Authorization: Bearer $TOKEN"

# 4. Desactivar un admin (sustituye {id} por el ID correspondiente)
curl -X DELETE http://localhost:8000/admin/admins/{id} \
  -H "Authorization: Bearer $TOKEN"
```

También puedes usar la documentación interactiva en `http://localhost:8000/docs` (Swagger UI), que permite ejecutar todos los endpoints desde el navegador sin necesidad de curl.

---

## 🔌 API — Endpoints principales

### Públicos (sin autenticación)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/evento/activo` | Evento del día actual |
| `GET` | `/buscar?nombre=X` | Buscar jóvenes por nombre |
| `POST` | `/asistencia?joven_id=X&evento_id=Y` | Registrar asistencia |
| `GET` | `/joven/{id}` | Perfil de un joven |
| `GET` | `/evento/{id}/conteo` | Asistentes en un evento |

### Autenticación

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auth/login` | Login → devuelve JWT |

### Admin (requieren Bearer token)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/admin/dashboard` | Stats del evento activo |
| `GET` | `/admin/dashboard/historial?semanas=8` | Historial de semanas |
| `GET` | `/admin/jovenes` | Todos los jóvenes con stats |
| `GET` | `/admin/excel/activo` | Excel del evento de hoy |
| `GET` | `/admin/excel/evento/{id}` | Excel de evento específico |
| `GET` | `/admin/admins` | Listar admins |
| `POST` | `/admin/admins` | Crear admin |
| `DELETE` | `/admin/admins/{id}` | Desactivar admin |

---

## 🧪 Tests

```bash
# Correr todos los tests
pytest tests/ -v

# Solo tests de asistencia
pytest tests/test_asistencia.py -v

# Solo tests de autenticación
pytest tests/test_auth.py -v

# Con reporte de cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

Los tests usan una base de datos SQLite temporal (`test_magna_temp.db`) que se crea y elimina automáticamente en cada función de test.

---

## 🗄️ Estructura del proyecto

```
magna-app/
├── app/
│   ├── main.py          # Inicio de la app, lifespan, rutas HTML
│   ├── config.py        # Variables de entorno
│   ├── database.py      # Engine SQLAlchemy
│   ├── models.py        # Modelos ORM (Joven, Evento, Asistencia, Admin)
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # JWT y dependencia get_current_admin
│   ├── services/
│   │   ├── asistencia.py  # Lógica de registro y gamificación
│   │   ├── jovenes.py     # Búsqueda, estadísticas, historial, importación
│   │   └── excel.py       # Generación de reportes Excel
│   └── routers/
│       ├── auth.py        # POST /auth/login
│       ├── asistencia.py  # POST /asistencia, GET /evento/*
│       ├── jovenes.py     # GET /buscar, /joven/{id}, /conteo
│       └── admin.py       # GET|POST|DELETE /admin/* (protegidos)
├── frontend/
│   ├── index.html         # Pantalla principal
│   └── admin.html         # Panel de administración
├── static/
│   ├── css/
│   │   ├── main.css       # Estilos pantalla principal
│   │   └── admin.css      # Estilos panel admin (glassmorphism)
│   ├── js/
│   │   ├── main.js        # Lógica pantalla principal
│   │   └── admin.js       # Lógica panel admin (Chart.js, login, Excel)
│   ├── portada_horizontal.png
│   └── portada_vertical.png
├── tests/
│   ├── conftest.py        # Fixtures: DB de test, admin, evento, joven
│   ├── test_asistencia.py # Tests de gamificación y registro
│   ├── test_jovenes.py    # Tests de búsqueda y perfiles
│   └── test_auth.py       # Tests de login y protección de rutas
├── Chicos.xlsx            # Lista de jóvenes por grupo
├── asistencia.db          # Base de datos SQLite (se genera automáticamente)
├── .env                   # Variables de entorno (NO subir a git)
├── .env.example           # Plantilla de .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔒 Seguridad

- Las contraseñas de admins se almacenan con hash **bcrypt**
- El acceso al panel admin se controla con **JWT** (expiración: 8 horas)
- Los endpoints `/admin/*` requieren token válido; devuelven `401` sin él
- Las variables sensibles (contraseñas, `SECRET_KEY`) viven en `.env` (excluido de git)

---

## 🛠️ Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) + [SQLAlchemy](https://www.sqlalchemy.org/) |
| Base de datos | SQLite (prod: PostgreSQL opcional) |
| Autenticación | [python-jose](https://github.com/mpdavis/python-jose) (JWT) + [passlib](https://passlib.readthedocs.io/) (bcrypt) |
| Frontend | HTML5 + CSS3 (Glassmorphism) + JavaScript vanilla |
| Gráficas | [Chart.js](https://www.chartjs.org/) |
| Reportes | [openpyxl](https://openpyxl.readthedocs.io/) |
| Tests | [pytest](https://pytest.org/) + [httpx](https://www.python-httpx.org/) |
