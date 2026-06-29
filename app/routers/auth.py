from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import verify_password, crear_token, hash_password, get_current_admin
from app.database import get_db
from app.schemas import LoginRequest, TokenResponse, AdminCreate, AdminOut
import app.models as models

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión como admin")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Valida credenciales y devuelve un JWT de sesión."""
    admin = db.query(models.Admin).filter(
        models.Admin.username == request.username,
        models.Admin.activo == True,
    ).first()

    if not admin or not verify_password(request.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    token = crear_token({"sub": admin.username})
    return TokenResponse(access_token=token, admin_nombre=admin.nombre)
