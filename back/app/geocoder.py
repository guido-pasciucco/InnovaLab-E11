La geocodificación debe añadirse cuando se elija un proveedor y se definan
sus condiciones de uso, límites, manejo de errores y protección de datos.
La ubicación del mapa será aproximada y no determinará zonificación,
habilitaciones ni permisos oficiales.
"""


def normalize_address(address: str) -> str:
    """Normaliza espacios en una dirección antes de enviarla a un proveedor."""
    return " ".join(address.strip().split())
