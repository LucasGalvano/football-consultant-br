from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_postgres_session
from app.repositories import postgres_repo
from app.schemas.responses import EstadioOut
from app.schemas.inputs import EstadioCreate, EstadioUpdate

router = APIRouter(prefix="/estadios", tags=["Estádios"])


@router.get(
    "/",
    response_model=List[EstadioOut],
    summary="Lista todos os estádios",
)
def listar_estadios(session: Session = Depends(get_postgres_session)):
    return postgres_repo.get_all_estadios(session)


@router.get(
    "/{estadio_id}",
    response_model=EstadioOut,
    summary="Busca estádio por ID",
)
def get_estadio(estadio_id: int, session: Session = Depends(get_postgres_session)):
    estadio = postgres_repo.get_estadio_by_id(session, estadio_id)
    if not estadio:
        raise HTTPException(status_code=404, detail="Estádio não encontrado")
    return estadio


@router.post(
    "/",
    response_model=EstadioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo estádio",
)
def criar_estadio(
    dados: EstadioCreate,
    session: Session = Depends(get_postgres_session),
):
    """Retorna 409 se já existir estádio com o mesmo nome."""
    try:
        return postgres_repo.create_estadio(session, dados)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/{estadio_id}",
    response_model=EstadioOut,
    summary="Atualiza um estádio",
)
def atualizar_estadio(
    estadio_id: int,
    dados: EstadioUpdate,
    session: Session = Depends(get_postgres_session),
):
    estadio = postgres_repo.update_estadio(session, estadio_id, dados)
    if not estadio:
        raise HTTPException(status_code=404, detail="Estádio não encontrado")
    return estadio


@router.delete(
    "/{estadio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um estádio",
)
def deletar_estadio(
    estadio_id: int,
    session: Session = Depends(get_postgres_session),
):
    """Retorna 409 se o estádio tiver partidas vinculadas."""
    try:
        encontrado = postgres_repo.delete_estadio(session, estadio_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not encontrado:
        raise HTTPException(status_code=404, detail="Estádio não encontrado")