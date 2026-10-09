from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import JovenOut
from app.services.jovenes import buscar_jovenes
import app.models as models
from app.services.asistencia import obtener_o_crear_evento
router = APIRouter(tags=["Jóvenes"])


@router.get("/buscar", summary="Buscar jóvenes por nombre")
def buscar(nombre: str, db: Session = Depends(get_db)):
    """
    Busca jóvenes ignorando acentos y mayúsculas.
    No muestra como disponibles a quienes ya registraron
    asistencia en el evento actual.
    """

    if len(nombre.strip()) < 2:
        return {
            "resultados": [],
            "ya_registrado": False,
        }

    # Buscar coincidencias conservando la búsqueda existente.
    jovenes = buscar_jovenes(nombre, db)

    if not jovenes:
        return {
            "resultados": [],
            "ya_registrado": False,
        }

    # Obtener el evento actual.
    evento = obtener_o_crear_evento(db)

    ids_jovenes = [j.id for j in jovenes]

    # Consultar cuáles ya registraron asistencia en ese evento.
    asistencias_existentes = (
        db.query(models.Asistencia.joven_id)
        .filter(
            models.Asistencia.evento_id == evento.id,
            models.Asistencia.joven_id.in_(ids_jovenes),
        )
        .all()
    )

    ids_registrados = {
        joven_id for (joven_id,) in asistencias_existentes
    }

    disponibles = [
        j for j in jovenes
        if j.id not in ids_registrados
    ]

    return {
        "resultados": [
            {"id": j.id, "nombre": j.nombre}
            for j in disponibles
        ],
        "ya_registrado": (
            not disponibles
            and any(j.id in ids_registrados for j in jovenes)
        ),
    }


@router.get("/joven/{joven_id}", response_model=JovenOut, summary="Perfil de un joven")
def ver_joven(joven_id: int, db: Session = Depends(get_db)):
    joven = db.query(models.Joven).filter(models.Joven.id == joven_id).first()
    if not joven:
        raise HTTPException(status_code=404, detail="Joven no encontrado")
    return joven


@router.get("/conteo", summary="Total de jóvenes registrados")
def conteo_jovenes(db: Session = Depends(get_db)):
    return {"total_jovenes": db.query(models.Joven).count()}
