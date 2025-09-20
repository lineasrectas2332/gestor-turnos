# backend/main.py
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, List
import uuid
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

DATABASE_URL = "sqlite:///./reservas.db"  # para PostgreSQL cambia la URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

class Reservation(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    clientName: str
    phone: str
    date: str       # ISO date string (YYYY-MM-DD)
    time: str       # "HH:MM"
    reservationDate: str  # ISO datetime string
    status: Optional[str] = "confirmed"

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI(title="API Reservas - Lodeltirry")

# CORS: ajusta orígenes según donde alojes el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # en producción pon tu dominio (ej. https://tudominio.com)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/api/reservations", response_model=List[Reservation])
def list_reservations():
    with Session(engine) as session:
        statement = select(Reservation)
        results = session.exec(statement).all()
        return results

@app.post("/api/reservations", response_model=Reservation, status_code=201)
def create_reservation(reservation: Reservation):
    # asignar id y reservationDate si no vienen
    if not reservation.id:
        reservation.id = str(uuid.uuid4())
    if not reservation.reservationDate:
        reservation.reservationDate = datetime.utcnow().isoformat()
    with Session(engine) as session:
        session.add(reservation)
        session.commit()
        session.refresh(reservation)
        return reservation

@app.delete("/api/reservations/{reservation_id}", status_code=204)
def delete_reservation(reservation_id: str):
    with Session(engine) as session:
        res = session.get(Reservation, reservation_id)
        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        session.delete(res)
        session.commit()
        return None
