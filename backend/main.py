# backend/main.py
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, List
import uuid
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

DATABASE_URL = "sqlite:///./reservas.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Reservation(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    clientName: str
    phone: str
    date: str       # ISO date string (YYYY-MM-DD)
    time: str       # "HH:MM"
    reservationDate: str  # ISO datetime string
    status: Optional[str] = "confirmed"


class Config(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    price: int = 2500


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Insertar config inicial si no existe
    with Session(engine) as session:
        cfg = session.get(Config, 1)
        if not cfg:
            session.add(Config(id=1, price=2500))
            session.commit()


app = FastAPI(title="API Reservas - Lodeltirry")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ en producción restringir a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}


# ---------------- RESERVAS ----------------
@app.get("/api/reservations", response_model=List[Reservation])
def list_reservations():
    with Session(engine) as session:
        statement = select(Reservation)
        results = session.exec(statement).all()
        return results


@app.post("/api/reservations", response_model=Reservation, status_code=201)
def create_reservation(reservation: Reservation):
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


# ---------------- CONFIGURACIÓN ----------------
@app.get("/api/config", response_model=Config)
def get_config():
    with Session(engine) as session:
        cfg = session.get(Config, 1)
        if not cfg:
            raise HTTPException(status_code=404, detail="Config no encontrada")
        return cfg


@app.put("/api/config", response_model=Config)
def update_config(price: int):
    with Session(engine) as session:
        cfg = session.get(Config, 1)
        if not cfg:
            cfg = Config(id=1, price=price)
            session.add(cfg)
        else:
            cfg.price = price
        session.commit()
        session.refresh(cfg)
        return cfg
