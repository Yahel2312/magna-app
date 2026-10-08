from datetime import datetime, timedelta, time 
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from zoneinfo import ZoneInfo
import app.models as models
from app.schemas import AsistenciaResponse

ZONA_HORARIA = ZoneInfo("America/Mexico_City")

HORA_INICIO = time(18, 0)
HORA_FIN = time(19, 30)

def obtener_o_crear_evento(db):
    ahora = datetime.now(ZONA_HORARIA)
    hoy = ahora.date()

    # ==========================================================
    # DOMINGO = EVENTO REAL
    # ==========================================================
    if hoy.weekday() == 6:
        inicio_dia = datetime.combine(
            hoy,
            time.min,
            tzinfo=ZONA_HORARIA
        )
        fin_dia = datetime.combine(
            hoy,
            time.max,
            tzinfo=ZONA_HORARIA
        )

        evento = (
            db.query(models.Evento)
            .filter(
                models.Evento.fecha >= inicio_dia.replace(tzinfo=None),
                models.Evento.fecha <= fin_dia.replace(tzinfo=None),
                models.Evento.activo == True
            )
            .first()
        )

        if evento:
            return evento

        nuevo_evento = models.Evento(
            fecha=ahora.replace(tzinfo=None),
            activo=True
        )

        db.add(nuevo_evento)
        db.commit()
        db.refresh(nuevo_evento)

        return nuevo_evento

    # ==========================================================
    # LUNES-SÁBADO = EVENTO DE PRUEBA
    # ==========================================================
    inicio_dia = datetime.combine(
        hoy,
        time.min
    )
    fin_dia = datetime.combine(
        hoy,
        time.max
    )

    evento_prueba = (
        db.query(models.Evento)
        .filter(
            models.Evento.fecha >= inicio_dia,
            models.Evento.fecha <= fin_dia
        )
        .first()
    )

    if evento_prueba:
        return evento_prueba

    # Evento de prueba:
# usamos una fecha fija de referencia para distinguirlo
# de los eventos reales de domingo.
    fecha_prueba = datetime.combine(
    hoy,
    time.min
    )

    nuevo_evento_prueba = models.Evento(
    fecha=fecha_prueba,
    activo=False
    )

    db.add(nuevo_evento_prueba)
    db.commit()
    db.refresh(nuevo_evento_prueba)

    return nuevo_evento_prueba


def registrar_asistencia(
    joven_id: int,
    evento_id: int,
    db: Session
) -> AsistenciaResponse:
    """
    Registra la asistencia de un joven.

    Eventos reales:
    - Suman puntos.
    - Actualizan la racha.
    - Actualizan la racha máxima.

    Eventos de prueba:
    - Registran la asistencia.
    - NO modifican puntos.
    - NO modifican rachas.
    - NO afectan las estadísticas reales.
    """

    joven = (
        db.query(models.Joven)
        .filter(models.Joven.id == joven_id)
        .first()
    )

    if not joven:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Joven no encontrado"
        )

    evento = (
        db.query(models.Evento)
        .filter(models.Evento.id == evento_id)
        .first()
    )

    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
        # ==========================================================
    # HORARIO DEL EVENTO REAL
    # ==========================================================

    if evento.activo:
        ahora = datetime.now(ZONA_HORARIA)

        if ahora.weekday() != 6:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El registro de asistencia solo está disponible los domingos."
            )

        hora_actual = ahora.time()

        if not (HORA_INICIO <= hora_actual < HORA_FIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El registro de asistencia está disponible de 6:00 PM a 7:30 PM."
            )

    # ==========================================================
    # VERIFICAR DUPLICADO
    # ==========================================================

    ya_existe = (
        db.query(models.Asistencia)
        .filter(
            models.Asistencia.joven_id == joven_id,
            models.Asistencia.evento_id == evento_id,
        )
        .first()
    )

    if ya_existe:
        return AsistenciaResponse(
            mensaje="Asistencia ya registrada anteriormente",
            ya_registrado=True,
            puntos_totales=joven.puntos_totales,
            racha_actual=joven.racha_actual,
            racha_maxima=joven.racha_maxima,
            es_nueva_racha_max=False,
        )

    # ==========================================================
    # REGISTRAR ASISTENCIA
    # ==========================================================

    nueva = models.Asistencia(
        joven_id=joven_id,
        evento_id=evento_id
    )

    db.add(nueva)

    print("=" * 50)
    print("GUARDANDO ASISTENCIA")
    print("Joven:", joven.nombre)
    print("Evento:", evento.id)
    print("Evento activo:", evento.activo)
    print("=" * 50)

    # ==========================================================
    # EVENTO DE PRUEBA
    # ==========================================================

    if not evento.activo:
        db.commit()

        print("ASISTENCIA DE PRUEBA")
        print("No se modificaron puntos ni rachas")
        print("=" * 50)

        return AsistenciaResponse(
            mensaje="Asistencia de prueba registrada",
            ya_registrado=False,
            puntos_totales=joven.puntos_totales,
            racha_actual=joven.racha_actual,
            racha_maxima=joven.racha_maxima,
            es_nueva_racha_max=False,
        )

    # ==========================================================
    # EVENTO REAL
    # ==========================================================

    # Buscar el evento real anterior.
    # Los eventos de prueba quedan excluidos.
    evento_anterior = (
        db.query(models.Evento)
        .filter(
            models.Evento.id < evento_id,
            models.Evento.activo == True
        )
        .order_by(models.Evento.id.desc())
        .first()
    )

    asistio_anterior = False

    if evento_anterior:
        asistio_anterior = (
            db.query(models.Asistencia)
            .filter(
                models.Asistencia.joven_id == joven_id,
                models.Asistencia.evento_id == evento_anterior.id,
            )
            .first()
            is not None
        )

    # ==========================================================
    # GAMIFICACIÓN
    # ==========================================================

    if asistio_anterior:
        joven.racha_actual += 1
        joven.puntos_racha += 10
    else:
        joven.racha_actual = 1
        joven.puntos_racha = 10

    joven.puntos_totales += 10

    # Actualizar racha máxima
    es_nueva_racha_max = (
        joven.racha_actual > joven.racha_maxima
    )

    joven.racha_maxima = max(
        joven.racha_maxima,
        joven.racha_actual
    )

    db.commit()

    print("Asistencia real guardada correctamente")
    print("Puntos totales:", joven.puntos_totales)
    print("Racha actual:", joven.racha_actual)
    print("Racha máxima:", joven.racha_maxima)
    print("=" * 50)

    return AsistenciaResponse(
        mensaje="Asistencia registrada",
        ya_registrado=False,
        puntos_totales=joven.puntos_totales,
        racha_actual=joven.racha_actual,
        racha_maxima=joven.racha_maxima,
        es_nueva_racha_max=es_nueva_racha_max,
    )
