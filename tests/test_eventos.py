"""
Tests de los endpoints de eventos: /evento/activo y /evento/{id}/conteo.

Estos endpoints son críticos para el frontend principal:
- GET /evento/activo   → el JS lo llama al cargar para obtener EVENTO_ID
- GET /evento/{id}/conteo → el JS lo usa para el contador de asistentes
- POST /admin/eventos  → creación manual de evento desde el panel admin
"""
import pytest
from datetime import datetime, timedelta
import app.models as models


# ── Helpers ───────────────────────────────────────────────────────────────────

def _registrar(client, joven_id: int, evento_id: int):
    return client.post(f"/asistencia?joven_id={joven_id}&evento_id={evento_id}")


# ── GET /evento/activo ─────────────────────────────────────────────────────────

class TestEventoActivo:
    def test_devuelve_200(self, client):
        """El endpoint siempre devuelve 200 (crea el evento si no existe)."""
        res = client.get("/evento/activo")
        assert res.status_code == 200

    def test_respuesta_tiene_campos_requeridos(self, client):
        """El frontend necesita evento_id, fecha y total_asistentes."""
        res = client.get("/evento/activo")
        data = res.json()
        assert "evento_id" in data
        assert "fecha" in data
        assert "total_asistentes" in data

    def test_evento_id_es_entero_positivo(self, client):
        res = client.get("/evento/activo")
        assert isinstance(res.json()["evento_id"], int)
        assert res.json()["evento_id"] > 0

    def test_crea_evento_si_no_existe(self, client, db):
        """Sin ningún evento previo debe crear uno al vuelo."""
        assert db.query(models.Evento).count() == 0
        res = client.get("/evento/activo")
        assert res.status_code == 200
        assert db.query(models.Evento).count() == 1

    def test_no_duplica_evento_del_mismo_dia(self, client, db):
        """Llamar dos veces no debe crear dos eventos para hoy."""
        client.get("/evento/activo")
        client.get("/evento/activo")
        assert db.query(models.Evento).count() == 1

    def test_reutiliza_evento_del_dia(self, client, db):
        """Si ya existe un evento de hoy, devuelve ese mismo ID."""
        ev = models.Evento(fecha=datetime.now(), activo=True)
        db.add(ev)
        db.commit()
        db.refresh(ev)

        res = client.get("/evento/activo")
        assert res.json()["evento_id"] == ev.id

    def test_total_asistentes_es_cero_al_inicio(self, client):
        res = client.get("/evento/activo")
        assert res.json()["total_asistentes"] == 0

    def test_total_asistentes_refleja_registros(self, client, db, joven, evento):
        """Tras registrar asistencia, total_asistentes debe incrementar."""
        _registrar(client, joven.id, evento.id)

        # Crear un segundo joven y registrarlo también
        joven2 = models.Joven(
            nombre="Joven Dos", grupo="Prepos",
            puntos_totales=0, puntos_racha=0, racha_actual=0, racha_maxima=0,
        )
        db.add(joven2)
        db.commit()
        db.refresh(joven2)
        _registrar(client, joven2.id, evento.id)

        res = client.get("/evento/activo")
        assert res.json()["total_asistentes"] == 2

    def test_ignora_evento_de_dia_anterior(self, client, db):
        """Un evento de ayer no se reutiliza — se crea uno nuevo para hoy."""
        ayer = datetime.now() - timedelta(days=1)
        ev_ayer = models.Evento(fecha=ayer, activo=True)
        db.add(ev_ayer)
        db.commit()
        db.refresh(ev_ayer)

        res = client.get("/evento/activo")
        assert res.status_code == 200
        # Debe ser un evento diferente (creado hoy)
        assert res.json()["evento_id"] != ev_ayer.id


# ── GET /evento/{evento_id}/conteo ─────────────────────────────────────────────

class TestConteoEvento:
    def test_conteo_vacio(self, client, evento):
        res = client.get(f"/evento/{evento.id}/conteo")
        assert res.status_code == 200
        assert res.json()["asistentes"] == 0

    def test_conteo_aumenta_tras_registro(self, client, db, joven, evento):
        _registrar(client, joven.id, evento.id)
        res = client.get(f"/evento/{evento.id}/conteo")
        assert res.json()["asistentes"] == 1

    def test_conteo_no_duplica_mismo_joven(self, client, db, joven, evento):
        """El doble registro no debe inflar el conteo."""
        _registrar(client, joven.id, evento.id)
        _registrar(client, joven.id, evento.id)
        res = client.get(f"/evento/{evento.id}/conteo")
        assert res.json()["asistentes"] == 1

    def test_conteo_evento_inexistente_devuelve_cero(self, client):
        """Evento que no existe → conteo de 0 (no errores)."""
        res = client.get("/evento/9999/conteo")
        assert res.status_code == 200
        assert res.json()["asistentes"] == 0

    def test_conteos_de_eventos_son_independientes(self, client, db, joven):
        """El conteo de un evento no se mezcla con el de otro."""
        ev1 = models.Evento(fecha=datetime.now() - timedelta(days=7), activo=True)
        ev2 = models.Evento(fecha=datetime.now(), activo=True)
        db.add_all([ev1, ev2])
        db.commit()
        db.refresh(ev1)
        db.refresh(ev2)

        _registrar(client, joven.id, ev1.id)

        assert client.get(f"/evento/{ev1.id}/conteo").json()["asistentes"] == 1
        assert client.get(f"/evento/{ev2.id}/conteo").json()["asistentes"] == 0


# ── POST /admin/eventos ────────────────────────────────────────────────────────

class TestCrearEventoManual:
    def test_crear_evento_requiere_token(self, client):
        res = client.post("/admin/eventos")
        assert res.status_code == 401

    def test_crear_evento_con_token(self, client, auth_headers):
        res = client.post("/admin/eventos", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "evento_id" in data
        assert isinstance(data["evento_id"], int)

    def test_crear_evento_persiste_en_db(self, client, db, auth_headers):
        antes = db.query(models.Evento).count()
        client.post("/admin/eventos", headers=auth_headers)
        assert db.query(models.Evento).count() == antes + 1
