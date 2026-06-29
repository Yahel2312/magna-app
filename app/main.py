import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import inspect, text

from app.database import engine, SessionLocal
import app.models as models
from app.auth import hash_password
from app.config import ADMIN_USER_DEFAULT, ADMIN_PASSWORD_DEFAULT, ADMIN_NOMBRE_DEFAULT
from app.services.jovenes import importar_desde_excel
from app.routers.auth import router as auth_router
from app.routers.asistencia import router as asistencia_router
from app.routers.jovenes import router as jovenes_router
from app.routers.admin import router as admin_router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _migrar_columna_grupo() -> None:
    """Agrega la columna 'grupo' a la tabla jovenes si no existe (migración segura)."""
    with engine.connect() as conn:
        inspector = inspect(engine)
        columnas = [c["name"] for c in inspector.get_columns("jovenes")]
        if "grupo" not in columnas:
            conn.execute(text("ALTER TABLE jovenes ADD COLUMN grupo VARCHAR DEFAULT 'Sin grupo'"))
            conn.commit()


def _crear_admin_por_defecto(db) -> None:
    """Crea el admin inicial desde .env si aún no existe ningún admin."""
    if db.query(models.Admin).count() == 0:
        db.add(
            models.Admin(
                username=ADMIN_USER_DEFAULT,
                hashed_password=hash_password(ADMIN_PASSWORD_DEFAULT),
                nombre=ADMIN_NOMBRE_DEFAULT,
                activo=True,
            )
        )
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────
    models.Base.metadata.create_all(bind=engine)
    _migrar_columna_grupo()

    db = SessionLocal()
    try:
        importar_desde_excel(db, BASE_DIR)
        _crear_admin_por_defecto(db)
    finally:
        db.close()

    yield  # La aplicación corre aquí

    # ── Shutdown ──────────────────────────────────────────
    # (espacio para tareas de limpieza si se requieren en el futuro)


app = FastAPI(
    title="Magna App — Asistencia Juvenil",
    version="2.0.0",
    lifespan=lifespan,
)

# Archivos estáticos (CSS, JS, imágenes)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

# Routers
app.include_router(auth_router)
app.include_router(asistencia_router)
app.include_router(jovenes_router)
app.include_router(admin_router)


# ─── Páginas HTML ───────────────────────────────────────

@app.get("/", include_in_schema=False)
def home():
    """Pantalla principal de registro de asistencia."""
    return FileResponse(os.path.join(BASE_DIR, "frontend", "index.html"))


@app.get("/admin-panel", include_in_schema=False)
def admin_page():
    """Panel de administración (requiere login desde el propio panel)."""
    return FileResponse(os.path.join(BASE_DIR, "frontend", "admin.html"))
