from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AsistenciaResponse, EventoOut
from app.services.asistencia import registrar_asistencia, obtener_o_crear_evento
import app.models as models

router = APIRouter(tags=["Asistencia"])


@router.post("/asistencia", response_model=AsistenciaResponse, summary="Registrar asistencia")
def registrar(joven_id: int, evento_id: int, db: Session = Depends(get_db)):
    """
    Registra la asistencia de un joven a un evento.
    Calcula automáticamente puntos y rachas (incluyendo racha_maxima).
    """
    return registrar_asistencia(joven_id, evento_id, db)


@router.get("/evento/activo", response_model=EventoOut, summary="Obtener evento del día")
def evento_activo(db: Session = Depends(get_db)):
    """Busca o crea el evento del día actual y devuelve su ID y conteo de asistentes."""
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


@router.get("/evento/{evento_id}/conteo", summary="Conteo de asistentes en un evento")
def conteo_evento(evento_id: int, db: Session = Depends(get_db)):
    total = (
        db.query(models.Asistencia)
        .filter(models.Asistencia.evento_id == evento_id)
        .count()
    )
    return {"asistentes": total}
