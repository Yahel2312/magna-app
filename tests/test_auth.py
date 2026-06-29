"""
Tests de autenticación y protección de rutas admin.

Cubre: login correcto/incorrecto, expiración implícita, protección de
todos los endpoints /admin/*, y gestión de admins.
"""
import pytest


class TestLogin:
    def test_login_correcto_devuelve_token(self, client, admin):
        res = client.post("/auth/login", json={"username": "test_admin", "password": "test1234"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "admin_nombre" in data

    def test_login_contrasena_incorrecta_devuelve_401(self, client, admin):
        res = client.post("/auth/login", json={"username": "test_admin", "password": "wrong"})
        assert res.status_code == 401

    def test_login_usuario_inexistente_devuelve_401(self, client):
        res = client.post("/auth/login", json={"username": "nobody", "password": "pass"})
        assert res.status_code == 401

    def test_login_admin_inactivo_devuelve_401(self, client, db, admin):
        admin.activo = False
        db.commit()
        res = client.post("/auth/login", json={"username": "test_admin", "password": "test1234"})
        assert res.status_code == 401


class TestProteccionRutas:
    """Todos los endpoints /admin/* deben devolver 401 sin token."""

    def test_dashboard_sin_token(self, client):
        res = client.get("/admin/dashboard")
        assert res.status_code == 401

    def test_historial_sin_token(self, client):
        res = client.get("/admin/dashboard/historial")
        assert res.status_code == 401

    def test_jovenes_sin_token(self, client):
        res = client.get("/admin/jovenes")
        assert res.status_code == 401

    def test_excel_sin_token(self, client):
        res = client.get("/admin/excel/activo")
        assert res.status_code == 401

    def test_admins_sin_token(self, client):
        res = client.get("/admin/admins")
        assert res.status_code == 401

    def test_token_invalido_devuelve_401(self, client):
        headers = {"Authorization": "Bearer token.invalido.aqui"}
        res = client.get("/admin/dashboard", headers=headers)
        assert res.status_code == 401


class TestDashboardConToken:
    def test_dashboard_con_token_valido_devuelve_200(self, client, auth_headers, evento):
        res = client.get("/admin/dashboard", headers=auth_headers)
        assert res.status_code == 200

    def test_dashboard_incluye_campos_esperados(self, client, auth_headers, evento):
        res = client.get("/admin/dashboard", headers=auth_headers)
        data = res.json()
        for campo in ["evento_id", "fecha", "total_asistentes", "por_grupo", "top_rachas"]:
            assert campo in data

    def test_historial_con_token_devuelve_lista(self, client, auth_headers):
        res = client.get("/admin/dashboard/historial", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)


class TestGestionAdmins:
    def test_listar_admins(self, client, auth_headers, admin):
        res = client.get("/admin/admins", headers=auth_headers)
        assert res.status_code == 200
        nombres = [a["username"] for a in res.json()]
        assert "test_admin" in nombres

    def test_crear_admin_nuevo(self, client, auth_headers):
        payload = {"username": "nuevo_admin", "password": "pass1234", "nombre": "Nuevo Admin"}
        res = client.post("/admin/admins", json=payload, headers=auth_headers)
        assert res.status_code == 201
        assert res.json()["username"] == "nuevo_admin"

    def test_crear_admin_username_duplicado_devuelve_400(self, client, auth_headers, admin):
        payload = {"username": "test_admin", "password": "otro", "nombre": "Dup"}
        res = client.post("/admin/admins", json=payload, headers=auth_headers)
        assert res.status_code == 400

    def test_desactivar_admin_ajeno(self, client, db, auth_headers):
        from app.auth import hash_password
        import app.models as models
        otro = models.Admin(username="otro", hashed_password=hash_password("x"), nombre="Otro", activo=True)
        db.add(otro)
        db.commit()
        db.refresh(otro)

        res = client.delete(f"/admin/admins/{otro.id}", headers=auth_headers)
        assert res.status_code == 200
        db.refresh(otro)
        assert otro.activo is False

    def test_no_puede_desactivarse_a_si_mismo(self, client, db, auth_headers, admin):
        res = client.delete(f"/admin/admins/{admin.id}", headers=auth_headers)
        assert res.status_code == 400
