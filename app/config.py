from dotenv import load_dotenv
import os

load_dotenv()

# Base de datos
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./asistencia.db")

# JWT
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-key-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS: int = 8

# Admin por defecto (se crea al iniciar si no existe ningún admin)
ADMIN_USER_DEFAULT: str = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD_DEFAULT: str = os.getenv("ADMIN_PASSWORD", "magna2024")
ADMIN_NOMBRE_DEFAULT: str = os.getenv("ADMIN_NOMBRE", "Administrador")
