import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Voice(Base):
    __tablename__ = "voices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    preset_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    elevenlabs_voice_id: Mapped[str] = mapped_column(String, nullable=False)
    language_code: Mapped[str | None] = mapped_column(String, ForeignKey("languages.code"), nullable=True)
    similarity: Mapped[float] = mapped_column(Numeric(3, 2), default=0.75)
    stability: Mapped[float] = mapped_column(Numeric(3, 2), default=0.50)
    style: Mapped[float] = mapped_column(Numeric(3, 2), default=0.00)
    speed: Mapped[float] = mapped_column(Numeric(3, 2), default=1.00)
    sample_audio_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
