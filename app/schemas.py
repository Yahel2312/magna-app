from pydantic import BaseModel
from typing import Optional, List, Dict


# ---------- Jóvenes ----------

class JovenOut(BaseModel):
    id: int
    nombre: str
    grupo: str
    puntos_totales: int
    puntos_racha: int
    racha_actual: int
    racha_maxima: int

    model_config = {"from_attributes": True}


class JovenBusqueda(BaseModel):
    id: int
    nombre: str


# ---------- Asistencia ----------

class AsistenciaResponse(BaseModel):
    mensaje: str
    ya_registrado: bool = False
    puntos_totales: int
    racha_actual: int
    racha_maxima: int
    es_nueva_racha_max: bool


# ---------- Eventos ----------

class EventoOut(BaseModel):
    evento_id: int
    fecha: str
    total_asistentes: int


# ---------- Auth ----------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_nombre: str


# ---------- Admin panel ----------

class TopJoven(BaseModel):
    nombre: str
    grupo: str
    racha_actual: int
    racha_maxima: int
    puntos_totales: int


class DashboardResponse(BaseModel):
    evento_id: int
    fecha: str
    total_asistentes: int
    por_grupo: Dict[str, int]
    top_rachas: List[TopJoven]


class HistorialSemana(BaseModel):
    evento_id: int
    fecha: str
    total: int
    por_grupo: Dict[str, int]


# ---------- Gestión de admins ----------

class AdminCreate(BaseModel):
    username: str
    password: str
    nombre: str


class AdminOut(BaseModel):
    id: int
    username: str
    nombre: str
    activo: bool

    model_config = {"from_attributes": True}
