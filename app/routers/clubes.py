from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_postgres_session
from app.repositories import postgres_repo
from app.schemas.responses import ClubeOut
from app.schemas.inputs import ClubeCreate, ClubeUpdate

router = APIRouter(prefix="/clubes", tags=["Clubes"])


@router.get(
    "/",
    response_model=List[ClubeOut],
    summary="Lista todos os clubes",
)
def listar_clubes(session: Session = Depends(get_postgres_session)):
    """Retorna todos os clubes cadastrados, ordenados por nome."""
    return postgres_repo.get_all_clubes(session)


@router.get(
    "/{clube_id}",
    response_model=ClubeOut,
    summary="Busca clube por ID",
)
def get_clube(clube_id: int, session: Session = Depends(get_postgres_session)):
    clube = postgres_repo.get_clube_by_id(session, clube_id)
    if not clube:
        raise HTTPException(status_code=404, detail="Clube não encontrado")
    return clube


@router.post(
    "/",
    response_model=ClubeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo clube",
)
def criar_clube(
    dados: ClubeCreate,
    session: Session = Depends(get_postgres_session),
):
    """
    Cria um clube com nome oficial único.
    Retorna 409 se já existir um clube com o mesmo nome.
    """
    try:
        return postgres_repo.create_clube(session, dados)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/{clube_id}",
    response_model=ClubeOut,
    summary="Atualiza um clube",
)
def atualizar_clube(
    clube_id: int,
    dados: ClubeUpdate,
    session: Session = Depends(get_postgres_session),
):
    """
    Atualiza os campos informados de um clube (campos ausentes mantêm valor atual).
    Equivalente a PATCH semântico via PUT.
    """
    clube = postgres_repo.update_clube(session, clube_id, dados)
    if not clube:
        raise HTTPException(status_code=404, detail="Clube não encontrado")
    return clube


@router.delete(
    "/{clube_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um clube",
)
def deletar_clube(
    clube_id: int,
    session: Session = Depends(get_postgres_session),
):
    """
    Remove um clube. Retorna 409 se o clube tiver partidas vinculadas.
    Para remover um clube com partidas, delete as partidas primeiro.
    """
    try:
        encontrado = postgres_repo.delete_clube(session, clube_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not encontrado:
        raise HTTPException(status_code=404, detail="Clube não encontrado")