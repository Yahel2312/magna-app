"""
Tests de la lógica de asistencia y gamificación.

Cubre los escenarios críticos del servicio registrar_asistencia:
- Primera asistencia, asistencia consecutiva (racha), ruptura de racha,
  doble registro, y actualización correcta de racha_maxima.
"""
import pytest
from datetime import datetime
import app.models as models


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post_asistencia(client, joven_id: int, evento_id: int):
    return client.post(f"/asistencia?joven_id={joven_id}&evento_id={evento_id}")


def _get_joven(db, joven_id: int) -> models.Joven:
    return db.query(models.Joven).filter(models.Joven.id == joven_id).first()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPrimeraAsistencia:
    def test_devuelve_200(self, client, joven, evento):
        res = _post_asistencia(client, joven.id, evento.id)
        assert res.status_code == 200

    def test_racha_es_uno(self, client, db, joven, evento):
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        assert joven.racha_actual == 1

    def test_puntos_totales_suman_diez(self, client, db, joven, evento):
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        assert joven.puntos_totales == 10

    def test_racha_maxima_se_inicializa(self, client, db, joven, evento):
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        assert joven.racha_maxima == 1

    def test_respuesta_contiene_campos_correctos(self, client, joven, evento):
        res = _post_asistencia(client, joven.id, evento.id)
        data = res.json()
        assert "racha_actual" in data
        assert "racha_maxima" in data
        assert "puntos_totales" in data
        assert "es_nueva_racha_max" in data
        assert data["ya_registrado"] is False


class TestAsistenciaConsecutiva:
    def test_racha_incrementa(self, client, db, joven, evento_anterior, evento):
        # Asiste al evento anterior
        _post_asistencia(client, joven.id, evento_anterior.id)
        # Asiste al evento actual
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        assert joven.racha_actual == 2

    def test_puntos_totales_acumulan(self, client, db, joven, evento_anterior, evento):
        _post_asistencia(client, joven.id, evento_anterior.id)
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        assert joven.puntos_totales == 20

    def test_racha_maxima_se_actualiza(self, client, db, joven, evento_anterior, evento):
        """racha_maxima debe igualar a racha_actual cuando la supera."""
        _post_asistencia(client, joven.id, evento_anterior.id)
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        assert joven.racha_maxima == 2

    def test_es_nueva_racha_max_es_true(self, client, joven, evento_anterior, evento):
        _post_asistencia(client, joven.id, evento_anterior.id)
        res = _post_asistencia(client, joven.id, evento.id)
        assert res.json()["es_nueva_racha_max"] is True


class TestRupturaDeRacha:
    def test_racha_vuelve_a_uno(self, client, db, joven, evento_anterior, evento):
        """Si no asistió al evento anterior, la racha se reinicia a 1."""
        # Solo asiste al evento actual (sin haber asistido al anterior)
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        assert joven.racha_actual == 1

    def test_racha_maxima_se_conserva_al_romper(self, client, db, joven, evento_anterior, evento):
        """La racha_maxima no debe bajar cuando se rompe la racha."""
        # Construir racha de 2
        _post_asistencia(client, joven.id, evento_anterior.id)
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        racha_max_previa = joven.racha_maxima  # debe ser 2

        # Simular un evento que el joven NO asiste (semana saltada).
        # El servicio busca el evento con el ID más alto < nuevo_evento.id,
        # así que este evento intermedio será el "anterior" al siguiente.
        evento_saltado = models.Evento(fecha=datetime.now(), activo=True)
        db.add(evento_saltado)
        db.commit()
        # ← NO registramos al joven en evento_saltado

        # Crear el siguiente evento y registrar al joven
        nuevo_evento = models.Evento(fecha=datetime.now(), activo=True)
        db.add(nuevo_evento)
        db.commit()
        db.refresh(nuevo_evento)

        _post_asistencia(client, joven.id, nuevo_evento.id)
        db.refresh(joven)
        assert joven.racha_actual == 1          # racha se reinició
        assert joven.racha_maxima == racha_max_previa  # conserva 2


class TestDobleRegistro:
    def test_no_duplica_asistencia(self, client, db, joven, evento):
        _post_asistencia(client, joven.id, evento.id)
        _post_asistencia(client, joven.id, evento.id)
        total = db.query(models.Asistencia).filter(
            models.Asistencia.joven_id == joven.id,
            models.Asistencia.evento_id == evento.id,
        ).count()
        assert total == 1

    def test_ya_registrado_flag(self, client, joven, evento):
        _post_asistencia(client, joven.id, evento.id)
        res = _post_asistencia(client, joven.id, evento.id)
        assert res.json()["ya_registrado"] is True

    def test_puntos_no_duplican(self, client, db, joven, evento):
        _post_asistencia(client, joven.id, evento.id)
        _post_asistencia(client, joven.id, evento.id)
        db.refresh(joven)
        assert joven.puntos_totales == 10  # solo 1 vez


class TestJovenInexistente:
    def test_devuelve_404(self, client, evento):
        res = _post_asistencia(client, 9999, evento.id)
        assert res.status_code == 404

    def test_mensaje_de_error(self, client, evento):
        res = _post_asistencia(client, 9999, evento.id)
        assert "no encontrado" in res.json()["detail"].lower()
