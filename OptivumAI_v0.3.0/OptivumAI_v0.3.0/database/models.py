from __future__ import annotations
from typing import Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.database import Base

class Teacher(Base):
    __tablename__ = "teachers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="teacher", cascade="all, delete-orphan")

class SchoolClass(Base):
    __tablename__ = "school_classes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="school_class")

class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="room")

class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), index=True)
    school_class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("school_classes.id"), nullable=True, index=True)
    room_id: Mapped[Optional[int]] = mapped_column(ForeignKey("rooms.id"), nullable=True, index=True)
    day_name: Mapped[str] = mapped_column(String(30))
    day_index: Mapped[int] = mapped_column()
    lesson_number: Mapped[int] = mapped_column()
    time_range: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    group_name: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    subject: Mapped[str] = mapped_column(String(200))
    teacher: Mapped["Teacher"] = relationship(back_populates="lessons")
    school_class: Mapped[Optional["SchoolClass"]] = relationship(back_populates="lessons")
    room: Mapped[Optional["Room"]] = relationship(back_populates="lessons")
