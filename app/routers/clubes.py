from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_postgres_session
from app.repositories import postgres_repo
from app.schemas.responses import ClubeOut

router = APIRouter(prefix="/clubes", tags=["Clubes"])


@router.get("/", response_model=List[ClubeOut], summary="Lista todos os clubes")
def listar_clubes(session: Session = Depends(get_postgres_session)):
    """Retorna todos os clubes que já participaram do Brasileirão no período analisado."""
    return postgres_repo.get_all_clubes(session)


@router.get("/{clube_id}", response_model=ClubeOut, summary="Busca clube por ID")
def get_clube(clube_id: int, session: Session = Depends(get_postgres_session)):
    clube = postgres_repo.get_clube_by_id(session, clube_id)
    if not clube:
        raise HTTPException(status_code=404, detail="Clube não encontrado")
    return clube