from datetime import datetime, timedelta, time 
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

import app.models as models
from app.schemas import AsistenciaResponse


def obtener_o_crear_evento(db: Session) -> models.Evento:
    """
    Busca el evento semanal correspondiente al domingo.
    Si no existe, crea uno nuevo.

    Así se evita crear un evento diferente cada día.
    """

    hoy = datetime.now().date()

    # weekday():
    # lunes = 0
    # domingo = 6
    dias_hasta_domingo = (6 - hoy.weekday()) % 7
    domingo = hoy + timedelta(days=dias_hasta_domingo)

    inicio_domingo = datetime.combine(domingo, time.min)
    fin_domingo = datetime.combine(domingo, time.max)

    evento = (
        db.query(models.Evento)
        .filter(
            models.Evento.fecha >= inicio_domingo,
            models.Evento.fecha <= fin_domingo,
        )
        .first()
    )

    if evento:
        return evento

    nuevo = models.Evento(
        fecha=datetime.combine(domingo, time(hour=12)),
        activo=True,
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo


def registrar_asistencia(joven_id: int, evento_id: int, db: Session) -> AsistenciaResponse:
    """
    Registra la asistencia de un joven a un evento con gamificación completa:
    - Suma puntos_totales siempre (+10)
    - Incrementa racha_actual si asistió al evento anterior
    - Reinicia racha_actual a 1 si no asistió
    - Actualiza racha_maxima si la racha actual la supera
    - Evita duplicados silenciosamente
    """
    joven = db.query(models.Joven).filter(models.Joven.id == joven_id).first()
    if not joven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Joven no encontrado")

    evento = db.query(models.Evento).filter(models.Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")

    # Verificar duplicado
    ya_existe = db.query(models.Asistencia).filter(
        models.Asistencia.joven_id == joven_id,
        models.Asistencia.evento_id == evento_id,
    ).first()

    if ya_existe:
        return AsistenciaResponse(
            mensaje="Asistencia ya registrada anteriormente",
            ya_registrado=True,
            puntos_totales=joven.puntos_totales,
            racha_actual=joven.racha_actual,
            racha_maxima=joven.racha_maxima,
            es_nueva_racha_max=False,
        )

    # Verificar si asistió al evento inmediatamente anterior
    evento_anterior = (
        db.query(models.Evento)
        .filter(models.Evento.id < evento_id)
        .order_by(models.Evento.id.desc())
        .first()
    )

    asistio_anterior = False
    if evento_anterior:
        asistio_anterior = db.query(models.Asistencia).filter(
            models.Asistencia.joven_id == joven_id,
            models.Asistencia.evento_id == evento_anterior.id,
        ).first() is not None

    # Registrar asistencia
    nueva = models.Asistencia(joven_id=joven_id, evento_id=evento_id)
    db.add(nueva)

    # Gamificación
    if asistio_anterior:
        joven.racha_actual += 1
        joven.puntos_racha += 10
    else:
        joven.racha_actual = 1
        joven.puntos_racha = 10

    joven.puntos_totales += 10

    # Actualizar racha máxima (bug corregido: ahora siempre se actualiza)
    es_nueva_racha_max = joven.racha_actual > joven.racha_maxima
    joven.racha_maxima = max(joven.racha_maxima, joven.racha_actual)

    db.commit()

    return AsistenciaResponse(
        mensaje="Asistencia registrada",
        ya_registrado=False,
        puntos_totales=joven.puntos_totales,
        racha_actual=joven.racha_actual,
        racha_maxima=joven.racha_maxima,
        es_nueva_racha_max=es_nueva_racha_max,
    )
