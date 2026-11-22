"""Errores propios de la API: cada uno tiene un código, un mensaje en español y un estado HTTP.

Un único manejador en `conco.main` los convierte al cuerpo
`{"code": ..., "request_id": ..., "detail": <mensaje>}`. El campo `detail` se mantiene
porque el frontend y QA ya lo leen.
"""

from fastapi import status


class ConcoError(Exception):
    """Error esperado de la API, con el mensaje que se le muestra a la persona."""

    code: str = "INTERNAL_ERROR"
    message: str = "Ocurrió un error inesperado. Intentá de nuevo más tarde."
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class ProcedureNotFound(ConcoError):
    code = "PROCEDURE_NOT_FOUND"
    message = "No encontramos ese trámite."
    status_code = status.HTTP_404_NOT_FOUND


class ProceduresUnavailable(ConcoError):
    code = "PROCEDURES_UNAVAILABLE"
    message = "No pudimos consultar los trámites. Intentá de nuevo."
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ProceduresLoading(ConcoError):
    code = "PROCEDURES_LOADING"
    message = "Estamos cargando los trámites, volvé a intentar."
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ActivityNotFound(ConcoError):
    code = "ACTIVITY_NOT_FOUND"
    message = "No se encontró la actividad solicitada."
    status_code = status.HTTP_404_NOT_FOUND


class ActivitiesUnavailable(ConcoError):
    code = "ACTIVITIES_UNAVAILABLE"
    message = "La búsqueda de actividades no está disponible. Intentá de nuevo más tarde."
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class AddressesUnavailable(ConcoError):
    # Se mantiene 502: el frontend distingue este estado.
    code = "ADDRESSES_UNAVAILABLE"
    message = "El servicio de direcciones no está disponible. Intentá de nuevo más tarde."
    status_code = status.HTTP_502_BAD_GATEWAY


class ConsultationsUnavailable(ConcoError):
    code = "CONSULTATIONS_UNAVAILABLE"
    message = "El servicio de consultas no está disponible. Intentá de nuevo más tarde."
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class InvalidConsultationId(ConcoError):
    code = "INVALID_CONSULTATION_ID"
    message = "Identificador de consulta inválido."
    status_code = status.HTTP_400_BAD_REQUEST


class InternalError(ConcoError):
    """Error no previsto: el detalle técnico queda solo en los logs."""
