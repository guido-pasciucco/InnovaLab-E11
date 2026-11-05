import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Corre los tests asíncronos solo con asyncio."""
    return "asyncio"
