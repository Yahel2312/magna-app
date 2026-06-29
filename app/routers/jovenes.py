from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import JovenOut
from app.services.jovenes import buscar_jovenes
import app.models as models

router = APIRouter(tags=["Jóvenes"])


@router.get("/buscar", summary="Buscar jóvenes por nombre")
def buscar(nombre: str, db: Session = Depends(get_db)):
    """
    Búsqueda case-insensitive de jóvenes por nombre parcial.
    Requiere mínimo 2 caracteres para evitar carga innecesaria.
    """
    if len(nombre.strip()) < 2:
        return []
    jovenes = buscar_jovenes(nombre, db)
    return [{"id": j.id, "nombre": j.nombre} for j in jovenes]


@router.get("/joven/{joven_id}", response_model=JovenOut, summary="Perfil de un joven")
def ver_joven(joven_id: int, db: Session = Depends(get_db)):
    joven = db.query(models.Joven).filter(models.Joven.id == joven_id).first()
    if not joven:
        raise HTTPException(status_code=404, detail="Joven no encontrado")
    return joven


@router.get("/conteo", summary="Total de jóvenes registrados")
def conteo_jovenes(db: Session = Depends(get_db)):
    return {"total_jovenes": db.query(models.Joven).count()}
