from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

try:
    from app.database.base import Base
except ModuleNotFoundError:
    from database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

