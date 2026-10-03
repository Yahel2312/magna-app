from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AsistenciaResponse, EventoOut
from app.services.asistencia import (
    registrar_asistencia,
    obtener_o_crear_evento,
)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import app.models as models

ZONA_HORARIA = ZoneInfo("America/Mexico_City")


def obtener_proximo_domingo():
    ahora = datetime.now(ZONA_HORARIA)
    dias_hasta_domingo = (6 - ahora.weekday()) % 7

    if dias_hasta_domingo == 0:
        return ahora.date()

    return (ahora + timedelta(days=dias_hasta_domingo)).date()
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
    summary="Obtener evento actual o próximo",
)
def evento_activo(db: Session = Depends(get_db)):
    ahora = datetime.now(ZONA_HORARIA)
    hoy = ahora.date()

    # ==========================================================
    # DOMINGO = EVENTO REAL
    # ==========================================================
    if hoy.weekday() == 6:
        evento = obtener_o_crear_evento(db)

        total = (
            db.query(models.Asistencia)
            .filter(
                models.Asistencia.evento_id == evento.id
            )
            .count()
        )

        return EventoOut(
            evento_id=evento.id,
            fecha=str(hoy),
            total_asistentes=total,
        )

    # ==========================================================
    # LUNES-SÁBADO = PRÓXIMO DOMINGO
    # ==========================================================
    proximo_domingo = obtener_proximo_domingo()

    return EventoOut(
        evento_id=0,
        fecha=str(proximo_domingo),
        total_asistentes=0,
    )

    # ==========================================================
    # LUNES-SÁBADO = PRÓXIMO DOMINGO
    # ==========================================================
    proximo_domingo = obtener_proximo_domingo()

    return EventoOut(
        evento_id=0,
        fecha=str(proximo_domingo),
        total_asistentes=0,
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