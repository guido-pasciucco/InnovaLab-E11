"""Rutas de la API de consultas (contrato camelCase para el frontend)."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from conco.consultation.domain import (
    ConsultationRequest,
    ConsultationResponse,
    FollowUpRequest,
    FollowUpResponse,
)
from conco.consultation.service import (
    AddressGeocoder,
    GeorefAddressGeocoder,
    build_consultation,
    build_follow_up,
)

# Reutiliza el mismo directorio compartido y pool que el resto de la API.
from conco.guidance.api import (
    get_activity_directory as get_activity_directory_for_consultation,
    get_procedure_catalog as get_procedure_catalog_for_consultation,
)
from conco.guidance.domain import ActivityDirectory, ActivityDirectoryError, ProcedureCatalog

router = APIRouter(prefix="/consultations", tags=["Consultas"])

UNAVAILABLE_DETAIL = "El servicio de consultas no está disponible. Intentá de nuevo más tarde."


def get_address_geocoder() -> AddressGeocoder:
    """Los tests lo reemplazan por un geocoder falso."""
    return GeorefAddressGeocoder()


@router.post("", response_model=ConsultationResponse, status_code=status.HTTP_200_OK)
async def submit_consultation(
    payload: ConsultationRequest,
    directory: Annotated[ActivityDirectory, Depends(get_activity_directory_for_consultation)],
    catalog: Annotated[ProcedureCatalog, Depends(get_procedure_catalog_for_consultation)],
    geocoder: Annotated[AddressGeocoder, Depends(get_address_geocoder)],
) -> ConsultationResponse:
    """Orientación general a partir de la actividad y la dirección declaradas."""
    try:
        return await build_consultation(payload, directory, catalog, geocoder)
    except ActivityDirectoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=UNAVAILABLE_DETAIL,
        ) from exc


@router.post("/{consultation_id}/follow-up", response_model=FollowUpResponse)
async def follow_up(
    consultation_id: str,
    payload: FollowUpRequest,
    directory: Annotated[ActivityDirectory, Depends(get_activity_directory_for_consultation)],
    catalog: Annotated[ProcedureCatalog, Depends(get_procedure_catalog_for_consultation)],
) -> FollowUpResponse:
    """Respuesta acotada: sin IA, apegada al catálogo curado y a las fuentes oficiales."""
    try:
        return await build_follow_up(consultation_id, payload.question, directory, catalog)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de consulta inválido.",
        ) from exc
    except ActivityDirectoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=UNAVAILABLE_DETAIL,
        ) from exc
