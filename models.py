from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Joven(Base):
    __tablename__ = "jovenes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    grupo = Column(String, default="Sin grupo")
    puntos_totales = Column(Integer, default=0)
    puntos_racha = Column(Integer, default=0)
    racha_actual = Column(Integer, default=0)
    racha_maxima = Column(Integer, default=0)
    


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)

    asistencias = relationship("Asistencia", back_populates="evento")


class Asistencia(Base):
    __tablename__ = "asistencias"

    id = Column(Integer, primary_key=True, index=True)
    joven_id = Column(Integer, ForeignKey("jovenes.id"))
    evento_id = Column(Integer, ForeignKey("eventos.id"))
    fecha_hora = Column(DateTime, default=datetime.utcnow)

    joven = relationship("Joven", back_populates="asistencias")
    evento = relationship("Evento", back_populates="asistencias")
