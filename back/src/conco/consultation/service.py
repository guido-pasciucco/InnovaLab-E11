"""Lógica de la consulta: orientación basada en el catálogo curado, sin IA.

Requisito de producto: no hay modelo de lenguaje en este endpoint. La respuesta
se compone con las mismas piezas curadas que usa el resto de la API (actividades,
trámites oficiales de la Ciudad, Georef para direcciones) y que la persona puede
verificar en las fuentes citadas.
"""

import base64
import json
import re
from datetime import date
from typing import Protocol

from conco.consultation.domain import (
    ConsultationRequest,
    ConsultationResponse,
    FollowUpResponse,
    GeoPoint,
    GuidanceStep,
    SourceReference,
)
from conco.guidance.domain import (
    ActivityDirectory,
    ActivityProcedures,
    ContextAnswers,
    ProcedureCatalog,
    apply_context,
)
from conco.integrations.georef.client import GeorefError, search_addresses, normalize_address

SLUG_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*")


class AddressGeocoder(Protocol):
    """Puerto: normaliza/geocodifica una dirección; None si no se pudo verificar."""

    async def geocode(self, address: str) -> tuple[str, GeoPoint | None] | None:
        ...


class GeorefAddressGeocoder:
    """Implementación por defecto: Georef (apis.datos.gob.ar, datos abiertos)."""

    async def geocode(self, address: str) -> tuple[str, GeoPoint | None] | None:
        try:
            result = await search_addresses(normalize_address(address), max_results=1)
        except GeorefError:
            return None
        for address_model in result.addresses:
            location = address_model.location
            point = GeoPoint(lat=location.lat, lng=location.lon) if location else None
            return (address_model.nomenclature, point)
        return None


def encode_consultation_id(slug: str | None) -> str:
    """Identificador opaco e idempotente; codifica solo el slug de la actividad."""
    payload = json.dumps({"s": slug or ""}, separators=(",", ":")).encode()
    return "c_" + base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_consultation_id(consultation_id: str) -> str | None:
    """Extrae el slug del identificador; lanza ValueError si es inválido o está manipulado."""
    if not consultation_id.startswith("c_"):
        raise ValueError("prefijo inválido")
    body = consultation_id[2:]
    try:
        raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        data = json.loads(raw)
    except Exception as exc:
        raise ValueError("no decodifica") from exc
    slug = data.get("s") if isinstance(data, dict) else None
    if not isinstance(slug, str):
        raise ValueError("formato inválido")
    if slug and not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("slug inválido")
    return slug or None


def _caba_source(catalog: ProcedureCatalog) -> SourceReference:
    source = catalog.source
    return SourceReference(
        id="caba-tramites",
        title=source.name,
        publisher="Gobierno de la Ciudad de Buenos Aires",
        url=source.url,
        note=source.license,
        retrievedAt=date.today().isoformat(),
    )


def _georef_source() -> SourceReference:
    return SourceReference(
        id="georef",
        title="Georef — normalización y geocodificación de direcciones",
        publisher="Gobierno de la Nación",
        url="https://apis.datos.gob.ar/georef/api",
        note="Datos abiertos",
        retrievedAt=date.today().isoformat(),
    )


BASE_LIMITATIONS = [
    "La interpretación de la actividad es automática y puede no ser correcta; revisala "
    "contra el nomenclador oficial de CABA.",
    "Los trámites surgen del catálogo curado de CONCO (borrador) y de las fuentes "
    "oficiales citadas; podés necesitar requisitos adicionales según tu caso.",
    "No constituye asesoramiento jurídico ni contable.",
    "La capa del mapa es ilustrativa; no valida zonificación ni habilitación del inmueble.",
]


async def _resolve_activity(
    payload: ConsultationRequest,
    directory: ActivityDirectory,
) -> tuple[ActivityProcedures | None, list[str]]:
    """Resuelve la actividad curada; devuelve los procedimientos y notas de limitación extra."""
    notes: list[str] = []
    slug = payload.activity_slug
    if slug:
        curated = await directory.procedures_for(slug)
        if curated is None:
            notes.append(
                f"No encontramos una actividad curada para «{slug}»; "
                "la orientación de esta consulta es genérica."
            )
        return curated, notes
    suggestions = await directory.suggest(payload.activity, 1)
    if not suggestions:
        notes.append(
            "La actividad no coincide con el catálogo curado; la orientación es genérica. "
            "Revisá la clasificación en la fuente oficial."
        )
        return None, notes
    curated = await directory.procedures_for(suggestions[0].slug)
    return curated, notes


async def build_consultation(
    payload: ConsultationRequest,
    directory: ActivityDirectory,
    catalog: ProcedureCatalog,
    geocoder: AddressGeocoder,
) -> ConsultationResponse:
    normalized_address = normalize_address(payload.address)
    limitations = list(BASE_LIMITATIONS)
    sources = [_caba_source(catalog)]
    source_ids = ["caba-tramites"]

    point = payload.point
    if point is None:
        try:
            geocoded = await geocoder.geocode(normalized_address)
        except Exception:
            geocoded = None
        if geocoded is not None:
            normalized_address, geo_point = geocoded
            point = GeoPoint.model_validate(geo_point) if geo_point else None
            sources.append(_georef_source())
            source_ids.append("georef")
        else:
            limitations.append(
                "No pudimos confirmar la dirección contra Georef; "
                "usá la que escribiste como referencia."
            )

    curated, extra_notes = await _resolve_activity(payload, directory)
    limitations.extend(extra_notes)

    interpreted = curated.activity.name if curated else payload.activity.strip()
    context = apply_context(curated, ContextAnswers()) if curated else None

    steps = [
        GuidanceStep(
            id="step-1",
            title="Confirmá la clasificación de la actividad",
            description=(
                f"«{interpreted}»: revisá cómo se encuadra la actividad y qué régimen "
                "de habilitación corresponde en CABA."
            ),
            documents=["Descripción precisa de la actividad"],
            sourceIds=source_ids,
        ),
        GuidanceStep(
            id="step-2",
            title="Validá las condiciones del domicilio",
            description=(
                f"Dirección declarada: {normalized_address}. Comprobá las condiciones "
                "territoriales y del inmueble aplicables antes de invertir en el local."
            ),
            documents=["Dirección completa"],
            sourceIds=source_ids,
        ),
    ]
    if context is not None and context.procedures:
        titles = "; ".join(procedure.procedure.title for procedure in context.procedures[:5])
        if len(context.procedures) > 5:
            titles += "…"
        steps.append(
            GuidanceStep(
                id="step-3",
                title="Reuní la documentación exigida",
                description=(
                    f"Revisá los requisitos de cada trámite oficial que suele aplicar: "
                    f"{titles}. La lista definitiva depende de tu caso y del régimen aplicable."
                ),
                documents=["Documentación personal y del inmueble, según trámite"],
                sourceIds=["caba-tramites"],
            )
        )
        steps.append(
            GuidanceStep(
                id="step-4",
                title="Presentá la solicitud ante el organismo oficial",
                description=(
                    "Algunos trámites dependen de tus respuestas de contexto (por ejemplo, "
                    "si vas a contratar personal). El orden sugerido está en Orientación."
                ),
                documents=[],
                sourceIds=["caba-tramites"],
            )
        )
    else:
        steps.append(
            GuidanceStep(
                id="step-3",
                title="Consultá la Guía de trámites oficial",
                description=(
                    "No hay una actividad curada que coincida con lo que describiste; "
                    "buscá el trámite por la descripción de la actividad en la fuente oficial."
                ),
                documents=[],
                sourceIds=["caba-tramites"],
            )
        )

    summary = f"Orientación general para «{interpreted}» en {normalized_address}."
    consultation_id = encode_consultation_id(
        curated.activity.slug if curated else None
    )
    return ConsultationResponse(
        consultationId=consultation_id,
        interpretedActivity=interpreted,
        normalizedAddress=normalized_address,
        point=point,
        summary=summary,
        steps=steps,
        territorialFeatures=[],
        sources=sources,
        limitations=limitations,
    )


async def build_follow_up(
    consultation_id: str,
    question: str,
    directory: ActivityDirectory,
    catalog: ProcedureCatalog,
) -> FollowUpResponse:
    slug = decode_consultation_id(consultation_id)
    lines: list[str] = []
    name: str | None = None
    if slug:
        curated = await directory.procedures_for(slug)
        if curated is not None:
            name = curated.activity.name
            context = apply_context(curated, ContextAnswers())
            for item in context.procedures:
                lines.append(f"• {item.procedure.title} — {item.procedure.official_url}")

    answer = (
        f"Tu pregunta «{question}» no tiene una respuesta generada por IA en esta versión: "
        f"no incorporamos IA al endpoint. "
    )
    if name and lines:
        answer += (
            f"Lo que el catálogo curado de CONCO dice para «{name}»:\n" + "\n".join(lines) + "\n"
        )
    else:
        answer += (
            "No hay una actividad curada asociada a esta consulta; "
            "buscá el trámite por la descripción de la actividad en la fuente oficial.\n"
        )
    answer += (
        "Para lo específico de tu caso, consultá un profesional matriculado y verificá "
        "siempre en la fuente oficial antes de avanzar."
    )
    return FollowUpResponse(
        answer=answer,
        sourceIds=["caba-tramites"],
        limitations=[
            "Respuesta automática sin modelo de IA: no genera conclusiones nuevas.",
            "No constituye asesoramiento jurídico ni contable.",
        ],
    )
