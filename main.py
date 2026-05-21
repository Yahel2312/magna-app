from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from pydantic import BaseModel
from datetime import datetime
from datetime import timedelta
from openpyxl import Workbook

# Crear las tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Asistencia Juvenil Gamificada")

# ---------------------------
# MODELO PARA ENTRADA DE DATOS
# ---------------------------
class JovenCreate(BaseModel):
    nombre: str

# ---------------------------
# DEPENDENCIA PARA LA DB
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generar_excel(db):
    print("GENERANDO EXCEL 🔥")

    asistencias = db.query(models.Asistencia).all()

    wb = Workbook()
    ws = wb.active

    ws.append(["Nombre", "Fecha"])

    for a in asistencias:
        joven = db.query(models.Joven).filter_by(id=a.joven_id).first()
        ws.append([joven.nombre, str(a.fecha_hora)])

    ruta = os.path.join(BASE_DIR, "asistencia.xlsx")
    wb.save(ruta)


@app.get("/conteo")
def conteo(db: Session = Depends(get_db)):
    total = db.query(models.Joven).count()
    return {"total_jovenes": total}
# ---------------------------
# ENDPOINT REGISTRAR JOVEN
# ---------------------------
@app.post("/jovenes")
def crear_joven(joven: JovenCreate, db: Session = Depends(get_db)):
    nuevo_joven = models.Joven(
    nombre=joven.nombre,
    puntos_totales=0,
    puntos_racha=0,
    racha_actual=0,
    racha_maxima=0
)
    db.add(nuevo_joven)
    db.commit()
    db.refresh(nuevo_joven)
    return {
        "mensaje": "Joven registrado",
        "id": nuevo_joven.id,
        "nombre": nuevo_joven.nombre
    }

@app.post("/eventos")
def crear_evento(db: Session = Depends(get_db)):
    nuevo_evento = models.Evento(
        fecha=datetime.now(),
        activo=True
    )
    db.add(nuevo_evento)
    db.commit()
    db.refresh(nuevo_evento)
    return {
        "mensaje": "Evento creado",
        "evento_id": nuevo_evento.id
    }


@app.post("/asistencia")
def registrar_asistencia(joven_id: int, evento_id: int, db: Session = Depends(get_db)):

    joven = db.query(models.Joven).filter(models.Joven.id == joven_id).first()
    if not joven:
        return {"error": "Joven no encontrado"}

    evento = db.query(models.Evento).filter(models.Evento.id == evento_id).first()
    if not evento:
        return {"error": "Evento no encontrado"}

    # evitar doble registro
    existe = db.query(models.Asistencia).filter(
        models.Asistencia.joven_id == joven_id,
        models.Asistencia.evento_id == evento_id
    ).first()

    if existe:
        return {"mensaje": "Asistencia ya registrada"}

    # buscar evento anterior
    evento_anterior = db.query(models.Evento)\
        .filter(models.Evento.id < evento_id)\
        .order_by(models.Evento.id.desc())\
        .first()

    # verificar si asistió al evento anterior
    asistio_anterior = False

    if evento_anterior:
        asistencia_anterior = db.query(models.Asistencia).filter(
            models.Asistencia.joven_id == joven_id,
            models.Asistencia.evento_id == evento_anterior.id
        ).first()

        if asistencia_anterior:
            asistio_anterior = True

    # registrar asistencia
    nueva = models.Asistencia(
        joven_id=joven_id,
        evento_id=evento_id
    )
    db.add(nueva)

    # ---- GAMIFICACIÓN ----
    if asistio_anterior:
       joven.racha_actual += 1
       joven.puntos_racha += 10
    else:
       joven.racha_actual = 1
       joven.puntos_racha = 10

# SIEMPRE suma puntos totales
    joven.puntos_totales += 10

    db.commit()

    return {
        "mensaje": "Asistencia registrada",
        "puntos": joven.puntos_totales,
        "racha": joven.racha_actual
    }
    
    
@app.get("/joven/{joven_id}")
def ver_joven(joven_id: int, db: Session = Depends(get_db)):
        joven = db.query(models.Joven).filter(models.Joven.id == joven_id).first()
    
        if not joven:
            return {"error": "No existe"}
    
        return {
            "nombre": joven.nombre,
            "puntos_totales": joven.puntos_totales,
            "puntos_racha": joven.puntos_racha,
            "racha_actual": joven.racha_actual,
            "racha_maxima": joven.racha_maxima
        }

@app.get("/admin/jovenes")
def ver_todos(db: Session = Depends(get_db)):
    jovenes = db.query(models.Joven).all()

    resultado = []

    for j in jovenes:
        resultado.append({
            "id": j.id,
            "nombre": j.nombre,
            "puntos_totales": j.puntos_totales,
            "puntos_racha": j.puntos_racha,
            "racha_actual": j.racha_actual,
            "racha_maxima": j.racha_maxima
        })

    return resultado
@app.get("/buscar")
def buscar(nombre: str, db: Session = Depends(get_db)):
    resultados = db.query(models.Joven).filter(
        models.Joven.nombre.ilike(f"%{nombre}%")
    ).all()

    return [
        {"id": j.id, "nombre": j.nombre}
        for j in resultados
    ]
@app.post("/asistencia_manual")
def asistencia_manual(joven_id: int, evento_id: int, db: Session = Depends(get_db)):

    joven = db.query(models.Joven).filter(models.Joven.id == joven_id).first()
    if not joven:
        return {"error": "No encontrado"}

    evento = db.query(models.Evento).filter(models.Evento.id == evento_id).first()
    if not evento:
        return {"error": "Evento no encontrado"}

    existe = db.query(models.Asistencia).filter(
        models.Asistencia.joven_id == joven_id,
        models.Asistencia.evento_id == evento_id
    ).first()

    if not existe:
        nueva = models.Asistencia(joven_id=joven_id, evento_id=evento_id)
        db.add(nueva)

        joven.puntos_totales += 10
        db.commit()

    # 🔥 SIEMPRE GENERA EXCEL (clave)
    generar_excel(db)

    return {"mensaje": "Asistencia registrada"}



@app.get("/evento/{evento_id}/conteo")
def conteo_evento(evento_id: int, db: Session = Depends(get_db)):
    total = db.query(models.Asistencia).filter(
        models.Asistencia.evento_id == evento_id
    ).count()

    return {"asistentes": total}

@app.get("/evento/activo")
def evento_activo(db: Session = Depends(get_db)):
    evento = db.query(models.Evento)\
        .order_by(models.Evento.id.desc())\
        .first()

    if not evento:
        return {"error": "No hay eventos"}

    return {"evento_id": evento.id}


@app.get("/api/exportar/{evento_id}")
def exportar(evento_id: int, db: Session = Depends(get_db)):

    asistencias = db.query(models.Asistencia).filter(
        models.Asistencia.evento_id == evento_id
    ).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    # encabezados
    ws.append(["Nombre", "Fecha"])

    for a in asistencias:
        joven = db.query(models.Joven).filter(
            models.Joven.id == a.joven_id
        ).first()

        ws.append([
            joven.nombre,
            str(a.fecha_hora)
        ])

    archivo = "asistencia.xlsx"
    wb.save(archivo)

    return FileResponse(archivo, filename=archivo)
from fastapi.responses import FileResponse
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "main.html"))


@app.get("/admin/excel")
def ver_excel():
    ruta = os.path.join(BASE_DIR, "asistencia.xlsx")

    if not os.path.exists(ruta):
        return {"error": "Excel no existe aún"}

    return FileResponse(ruta, filename="asistencia.xlsx")

@app.get("/test/excel")
def test_excel(db: Session = Depends(get_db)):
    generar_excel(db)
    return {"mensaje": "Excel generado"}

    return {"mensaje": "VERSION NUEVA "}


