from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AsistenciaResponse, EventoOut
from app.services.asistencia import (
    registrar_asistencia,
    obtener_o_crear_evento,
)
import app.models as models


router = APIRouter(tags=["Asistencia"])


# ─────────────────────────────────────────────
# Registrar asistencia
# ─────────────────────────────────────────────

@router.post(
    "/asistencia",
    response_model=AsistenciaResponse,
    summary="Registrar asistencia",
)
def registrar(
    joven_id: int,
    db: Session = Depends(get_db),
):
    print("=" * 60)
    print("REGISTRO DE ASISTENCIA")
    print("Joven ID:", joven_id)

    # Obtener automáticamente el evento correspondiente al día
    evento = obtener_o_crear_evento(db)

    print("Evento utilizado:", evento.id)
    print("Fecha del evento:", evento.fecha)

    resultado = registrar_asistencia(
        joven_id=joven_id,
        evento_id=evento.id,
        db=db,
    )

    print("Resultado:", resultado)
    print("=" * 60)

    return resultado


# ─────────────────────────────────────────────
# Evento activo
# ─────────────────────────────────────────────

@router.get(
    "/evento/activo",
    response_model=EventoOut,
    summary="Obtener evento del día",
)
def evento_activo(
    db: Session = Depends(get_db),
):
    """Busca o crea el evento del día actual y devuelve su información."""

    evento = obtener_o_crear_evento(db)

    total = (
        db.query(models.Asistencia)
        .filter(models.Asistencia.evento_id == evento.id)
        .count()
    )

    return EventoOut(
        evento_id=evento.id,
        fecha=str(evento.fecha.date()),
        total_asistentes=total,
    )


# ─────────────────────────────────────────────
# Conteo de asistentes
# ─────────────────────────────────────────────

@router.get(
    "/evento/{evento_id}/conteo",
    summary="Conteo de asistentes en un evento",
)
def conteo_evento(
    evento_id: int,
    db: Session = Depends(get_db),
):
    total = (
        db.query(models.Asistencia)
        .filter(models.Asistencia.evento_id == evento_id)
        .count()
    )

    return {
        "asistentes": total
    }