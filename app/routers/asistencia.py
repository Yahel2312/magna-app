from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AsistenciaResponse, EventoOut
from app.services.asistencia import registrar_asistencia, obtener_o_crear_evento
import app.models as models

router = APIRouter(tags=["Asistencia"])

@router.post("/asistencia", response_model=AsistenciaResponse, summary="Registrar asistencia")
def registrar(
    joven_id: int,
    db: Session = Depends(get_db),
):
    """
    Registra la asistencia en el evento activo del día.
    El evento se obtiene automáticamente para evitar IDs incorrectos.
    """
    evento = obtener_o_crear_evento(db)

    return registrar_asistencia(
        joven_id=joven_id,
        evento_id=evento.id,
        db=db,
    )


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
@router.post("/asistencia")
def registrar(
    joven_id: int,
    evento_id: int,
    db: Session = Depends(get_db),
):
    print(
        f"REGISTRO RECIBIDO: joven_id={joven_id}, "
        f"evento_id={evento_id}"
    )

    return registrar_asistencia(
        joven_id=joven_id,
        evento_id=evento_id,
        db=db,
    )
