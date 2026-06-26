"""
Fixtures compartidas para todos los tests de Magna App.

Usa SQLite en memoria con StaticPool para:
- Aislamiento total entre tests (drop/create en cada función)
- Sin archivos temporales (evita PermissionError en Windows)
- Velocidad máxima
"""
import pytest
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.auth import hash_password
import app.models as models

# ── BD de tests: SQLite en memoria compartida ─────────────────────────────────
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,   # una sola conexión compartida → la DB en memoria persiste
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


# ── Fixtures principales ──────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db():
    """Sesión de DB limpia para cada test — crea y destruye tablas en cada ejecución."""
    Base.metadata.create_all(bind=engine_test)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db):
    """TestClient de FastAPI con la BD en memoria inyectada vía dependency_overrides."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── Fixtures de datos ─────────────────────────────────────────────────────────

@pytest.fixture
def admin(db):
    """Admin de prueba con contraseña hasheada."""
    a = models.Admin(
        username="test_admin",
        hashed_password=hash_password("test1234"),
        nombre="Admin Test",
        activo=True,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@pytest.fixture
def auth_headers(client, admin):
    """Headers Authorization con JWT válido del admin de test."""
    res = client.post("/auth/login", json={"username": "test_admin", "password": "test1234"})
    assert res.status_code == 200, f"Login falló: {res.json()}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def evento(db):
    """Evento del día actual."""
    ev = models.Evento(fecha=datetime.now(), activo=True)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


@pytest.fixture
def evento_anterior(db):
    """Evento de 7 días atrás (para simular semana previa en tests de racha)."""
    from datetime import timedelta
    ev = models.Evento(fecha=datetime.now() - timedelta(days=7), activo=True)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


@pytest.fixture
def joven(db):
    """Joven de prueba con todos los contadores en cero."""
    j = models.Joven(
        nombre="Test Joven",
        grupo="Universitarios",
        puntos_totales=0,
        puntos_racha=0,
        racha_actual=0,
        racha_maxima=0,
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j
