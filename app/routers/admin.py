import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_admin, hash_password
from app.database import get_db
from app.schemas import (
    AdminCreate, AdminOut,
    DashboardResponse, TopJoven,
    JovenOut,
)
from app.services.asistencia import obtener_o_crear_evento
from app.services.jovenes import (
    obtener_estadisticas_por_grupo,
    obtener_historial,
    obtener_top_rachas,
)
from app.services.excel import generar_excel_evento
import app.models as models

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/admin", tags=["Administración"])


# ─────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardResponse, summary="Resumen del día")
def dashboard(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    """Retorna las estadísticas del evento activo + top-10 rachas."""
    evento = obtener_o_crear_evento(db)
    por_grupo = obtener_estadisticas_por_grupo(evento.id, db)
    total = sum(por_grupo.values())
    top = obtener_top_rachas(db, limit=10)

    return DashboardResponse(
        evento_id=evento.id,
        fecha=evento.fecha.strftime("%d/%m/%Y"),
        total_asistentes=total,
        por_grupo=por_grupo,
        top_rachas=[
            TopJoven(
                nombre=j.nombre,
                grupo=j.grupo,
                racha_actual=j.racha_actual,
                racha_maxima=j.racha_maxima,
                puntos_totales=j.puntos_totales,
            )
            for j in top
        ],
    )


@router.get("/dashboard/historial", summary="Historial de asistencia por semanas")
def historial(
    semanas: int = 8,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    """Retorna el historial de los últimos N eventos con conteo por grupo."""
    return obtener_historial(db, semanas=semanas)


# ─────────────────────────────────────────────
#  Jóvenes
# ─────────────────────────────────────────────

@router.get("/jovenes", response_model=List[JovenOut], summary="Listado de todos los jóvenes")
def ver_todos(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    return db.query(models.Joven).order_by(models.Joven.grupo, models.Joven.nombre).all()


# ─────────────────────────────────────────────
#  Eventos
# ─────────────────────────────────────────────

@router.post("/eventos", summary="Crear evento manualmente")
def crear_evento(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    nuevo = models.Evento(fecha=datetime.now(), activo=True)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Evento creado", "evento_id": nuevo.id}


# ─────────────────────────────────────────────
#  Exportar Excel
# ─────────────────────────────────────────────

@router.get("/excel/activo", summary="Exportar Excel del evento de hoy")
def excel_activo(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    evento = obtener_o_crear_evento(db)
    return generar_excel_evento(evento.id, db, BASE_DIR)


@router.get("/excel/evento/{evento_id}", summary="Exportar Excel de un evento específico")
def excel_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    return generar_excel_evento(evento_id, db, BASE_DIR)


# ─────────────────────────────────────────────
#  Gestión de admins
# ─────────────────────────────────────────────

@router.get("/admins", response_model=List[AdminOut], summary="Listar administradores")
def listar_admins(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    return db.query(models.Admin).order_by(models.Admin.nombre).all()


@router.post(
    "/admins",
    response_model=AdminOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo administrador",
)
def crear_admin(
    data: AdminCreate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    if db.query(models.Admin).filter(models.Admin.username == data.username).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    nuevo = models.Admin(
        username=data.username,
        hashed_password=hash_password(data.password),
        nombre=data.nombre,
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.delete("/admins/{admin_id}", summary="Desactivar un administrador")
def desactivar_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
):
    if admin.id == admin_id:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")

    target = db.query(models.Admin).filter(models.Admin.id == admin_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Admin no encontrado")

    target.activo = False
    db.commit()
    return {"mensaje": f"Admin '{target.username}' desactivado"}
