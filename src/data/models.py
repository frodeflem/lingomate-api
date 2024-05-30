from __future__ import annotations
import datetime
import uuid 
from sqlalchemy import JSON, Boolean, Float, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped
from sqlalchemy import UniqueConstraint


class Base(DeclarativeBase):
	pass


class User(Base):
	__tablename__ = "users"
	id: Mapped[str] = mapped_column(String(255), primary_key=True)
	email_address: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
	password: Mapped[str] = mapped_column(String(255), nullable=True)
	created_at: Mapped[datetime.datetime] = mapped_column(DateTime)
