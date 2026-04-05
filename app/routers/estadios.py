from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_postgres_session
from app.repositories import postgres_repo
from app.schemas.responses import EstadioOut

router = APIRouter(prefix="/estadios", tags=["Estádios"])


@router.get("/", response_model=List[EstadioOut], summary="Lista todos os estádios")
def listar_estadios(session: Session = Depends(get_postgres_session)):
    return postgres_repo.get_all_estadios(session)


@router.get("/{estadio_id}", response_model=EstadioOut, summary="Busca estádio por ID")
def get_estadio(estadio_id: int, session: Session = Depends(get_postgres_session)):
    estadio = postgres_repo.get_estadio_by_id(session, estadio_id)
    if not estadio:
        raise HTTPException(status_code=404, detail="Estádio não encontrado")
    return estadio