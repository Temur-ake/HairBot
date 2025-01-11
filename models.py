from datetime import datetime
from sqlalchemy import create_engine, Integer, String, ForeignKey, DateTime, BIGINT, VARCHAR, Time, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base, Session

# Database connection setup
engine = create_engine(f'postgresql+psycopg2://postgres:1@localhost:5449/hair_bot')
session = Session(bind=engine)

# Base class definition
Base = declarative_base()


# User Model
class User(Base):
    __tablename__ = 'users'

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    username: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    appointments: Mapped[list['Appointment']] = relationship("Appointment", back_populates="user")


# Salon Model
class Salon(Base):
    __tablename__ = 'salons'

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    latitude: Mapped[float]
    longtitude: Mapped[float]

    # Relationships
    barbers: Mapped[list['Barber']] = relationship("Barber", back_populates="salon")
    services: Mapped[list['Service']] = relationship("Service", back_populates="salon")
    appointments: Mapped[list['Appointment']] = relationship("Appointment", back_populates="salon")


# Service Model
class Service(Base):
    __tablename__ = 'services'

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    salon_id: Mapped[int] = mapped_column(Integer, ForeignKey('salons.id'), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[Float] = mapped_column(Float, nullable=False)

    # Relationships
    salon: Mapped['Salon'] = relationship("Salon", back_populates="services")


# Barber Model
class Barber(Base):
    __tablename__ = 'barbers'

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    salon_id: Mapped[int] = mapped_column(Integer, ForeignKey('salons.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(BIGINT, nullable=False)

    salon: Mapped['Salon'] = relationship("Salon", back_populates="barbers")
    appointments: Mapped[list['Appointment']] = relationship("Appointment", back_populates="barber")
    availabilities: Mapped[list['BarberAvailability']] = relationship("BarberAvailability", back_populates="barber")
    services: Mapped[list['BarberService']] = relationship("BarberService", back_populates="barber")


class BarberAvailability(Base):
    __tablename__ = 'barber_availabilities'

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    barber_id: Mapped[int] = mapped_column(Integer, ForeignKey('barbers.id'), nullable=False)
    available_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # Date and time of availability
    free_time: Mapped[Time] = mapped_column(Time, nullable=False)

    # Relationships
    barber: Mapped['Barber'] = relationship("Barber", back_populates="availabilities")


# BarberService Model (linking services to barbers)
class BarberService(Base):
    __tablename__ = 'barber_services'

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    barber_id: Mapped[int] = mapped_column(Integer, ForeignKey('barbers.id'), nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey('services.id'), nullable=False)

    # Relationships
    barber: Mapped['Barber'] = relationship("Barber", back_populates="services")
    service: Mapped['Service'] = relationship("Service")


# Appointment Model (Order)
class Appointment(Base):
    __tablename__ = 'appointments'

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    salon_id: Mapped[int] = mapped_column(Integer, ForeignKey('salons.id'), nullable=False)
    barber_id: Mapped[int] = mapped_column(Integer, ForeignKey('barbers.id'), nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey('services.id'),
                                            nullable=False)

    # Relationships
    user: Mapped['User'] = relationship("User", back_populates="appointments")
    salon: Mapped['Salon'] = relationship("Salon", back_populates="appointments")
    barber: Mapped['Barber'] = relationship("Barber", back_populates="appointments")
    service: Mapped['Service'] = relationship("Service")  # The service selected for the appointment


# Create all tables in the database
Base.metadata.create_all(engine)
