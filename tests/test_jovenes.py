"""Tests del endpoint de búsqueda de jóvenes."""
import pytest
import app.models as models


@pytest.fixture
def jovenes_db(db):
    """Crea 3 jóvenes de prueba en distintos grupos."""
    data = [
        ("Ana García", "Secundarios"),
        ("Andrea López", "Prepos"),
        ("Carlos Martínez", "Universitarios"),
    ]
    result = []
    for nombre, grupo in data:
        j = models.Joven(nombre=nombre, grupo=grupo, puntos_totales=0,
                         puntos_racha=0, racha_actual=0, racha_maxima=0)
        db.add(j)
        result.append(j)
    db.commit()
    for j in result:
        db.refresh(j)
    return result


class TestBusqueda:
    def test_busqueda_por_nombre_parcial(self, client, jovenes_db):
        res = client.get("/buscar?nombre=ana")
        assert res.status_code == 200
        nombres = [j["nombre"] for j in res.json()]
        assert "Ana García" in nombres

    def test_busqueda_case_insensitive(self, client, jovenes_db):
        res = client.get("/buscar?nombre=ANA")
        assert res.status_code == 200
        assert len(res.json()) >= 1

    def test_busqueda_coincidencias_multiples(self, client, jovenes_db):
        # "an" debería coincidir con Ana y Andrea
        res = client.get("/buscar?nombre=an")
        assert res.status_code == 200
        assert len(res.json()) >= 2

    def test_busqueda_sin_resultados(self, client, jovenes_db):
        res = client.get("/buscar?nombre=zzznoresult")
        assert res.status_code == 200
        assert res.json() == []

    def test_busqueda_muy_corta_devuelve_vacio(self, client, jovenes_db):
        res = client.get("/buscar?nombre=a")
        assert res.status_code == 200
        assert res.json() == []

    def test_respuesta_incluye_id_y_nombre(self, client, jovenes_db):
        res = client.get("/buscar?nombre=Carlos")
        assert res.status_code == 200
        item = res.json()[0]
        assert "id" in item
        assert "nombre" in item


class TestPerfilJoven:
    def test_obtener_joven_existente(self, client, joven):
        res = client.get(f"/joven/{joven.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["nombre"] == joven.nombre
        assert data["grupo"] == joven.grupo

    def test_obtener_joven_inexistente_devuelve_404(self, client):
        res = client.get("/joven/9999")
        assert res.status_code == 404

    def test_perfil_incluye_campos_gamificacion(self, client, joven):
        res = client.get(f"/joven/{joven.id}")
        data = res.json()
        for campo in ["puntos_totales", "racha_actual", "racha_maxima", "puntos_racha"]:
            assert campo in data


class TestConteoJovenes:
    def test_conteo_total(self, client, jovenes_db):
        res = client.get("/conteo")
        assert res.status_code == 200
        assert res.json()["total_jovenes"] == len(jovenes_db)

    def test_conteo_vacio(self, client):
        res = client.get("/conteo")
        assert res.status_code == 200
        assert res.json()["total_jovenes"] == 0
