"""
Tests de los cuatro fallos corregidos: SSRF en read_boe_pdf, la búsqueda que
devolvía normas equivocadas, las tablas auxiliares vacías y los enlaces a PDF rotos.

Todos son offline: las respuestas de la API van mockeadas con las formas reales
verificadas contra www.boe.es.
"""

import json
from unittest.mock import AsyncMock

import pytest

from mcp_boe.tools.documents import DocumentTools, _host_allowed
from mcp_boe.tools.summaries import _pdf_link
from mcp_boe.utils.http_client import BOEHTTPClient


# ---------------------------------------------------------------------------
# 1. SSRF — read_boe_pdf solo puede descargar de boe.es
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "https://www.boe.es/boe/dias/2018/12/06/pdfs/BOE-A-2018-16673.pdf",
    "https://boe.es/borme/dias/2026/08/14/pdfs/BORME-A-2026-156.pdf",
])
def test_host_permitido(url):
    assert _host_allowed(url) is True


@pytest.mark.parametrize("url", [
    "http://169.254.169.254/latest/meta-data/",       # metadatos del cloud
    "https://httpbin.org/get",                        # host cualquiera
    "https://boe.es.evil.com/x.pdf",                  # sufijo que imita el dominio
    "https://evilboe.es/x.pdf",                       # prefijo que lo imita
    "http://www.boe.es/x.pdf",                        # host bueno pero sin TLS
    "file:///etc/passwd",
    "https://localhost:8000/mcp",
])
def test_host_rechazado(url):
    assert _host_allowed(url) is False


@pytest.mark.asyncio
async def test_resolve_url_rechaza_host_ajeno():
    """Una URL de otro host no se convierte en descarga: se descarta."""
    assert await DocumentTools()._resolve_url("https://httpbin.org/get") is None


@pytest.mark.asyncio
async def test_download_pdf_rechaza_host_ajeno():
    with pytest.raises(ValueError, match="Host no permitido"):
        await DocumentTools()._download_pdf("http://169.254.169.254/latest/meta-data/")


@pytest.mark.asyncio
async def test_download_pdf_bloquea_redireccion_fuera_de_boe(monkeypatch):
    """Un 302 desde boe.es hacia otro host tiene que cortarse ANTES de seguirlo."""
    import httpx

    pedidas = []

    class FakeResponse:
        is_redirect = True
        headers = {"location": "https://attacker.example/x"}

    class FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url):
            pedidas.append(url)
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: FakeClient())

    with pytest.raises(ValueError, match="Redirección fuera de boe.es"):
        await DocumentTools()._download_pdf(
            "https://www.boe.es/boe/dias/2018/12/06/pdfs/BOE-A-2018-16673.pdf"
        )
    # Solo se llegó a pedir la URL buena; la del atacante nunca se pidió.
    assert pedidas == ["https://www.boe.es/boe/dias/2018/12/06/pdfs/BOE-A-2018-16673.pdf"]


# ---------------------------------------------------------------------------
# 2. Búsqueda — la frase va entre comillas y por título
# ---------------------------------------------------------------------------

def _query_string(client, **kwargs):
    return json.loads(client.build_search_query(**kwargs))["query"]["query_string"]["query"]


def test_busqueda_por_defecto_es_frase_exacta_en_titulo():
    """Sin comillas el BOE trocea la frase: «protección de datos» acababa
    devolviendo la Ley General de Subvenciones por matchear «datos»."""
    q = _query_string(BOEHTTPClient(), text="protección de datos")
    assert q == 'titulo:"protección de datos"'
    assert "texto:" not in q


def test_busqueda_title_words_exige_todas_las_palabras():
    q = _query_string(BOEHTTPClient(), text="gases licuados petróleo", text_mode="title_words")
    assert q == "titulo:(gases AND licuados AND petróleo)"


def test_busqueda_fulltext_entrecomilla_las_dos_ramas():
    q = _query_string(BOEHTTPClient(), text="protección de datos", text_mode="fulltext")
    assert q == '(titulo:"protección de datos" OR texto:"protección de datos")'


def test_busqueda_combina_con_los_filtros_por_codigo():
    q = _query_string(BOEHTTPClient(), text="protección de datos", legal_range="1300")
    assert q == 'titulo:"protección de datos" AND rango@codigo:1300'


# ---------------------------------------------------------------------------
# 3. Tablas auxiliares — el diccionario plano viene envuelto en "data"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tabla_auxiliar_envuelta_en_data_se_normaliza():
    """Forma real de la API: {"status": …, "data": {codigo: nombre}}.
    Antes solo se normalizaba el diccionario SIN envoltorio, así que por esta
    rama `entradas` quedaba vacío y las tools decían "No se encontraron…"."""
    client = BOEHTTPClient()
    client.get = AsyncMock(return_value={
        "status": {"code": "200", "text": "ok"},
        "data": {"7723": "Jefatura del Estado", "1430": "Ministerio de Justicia"},
    })

    data = (await client.get_auxiliary_table("departamentos"))["data"]

    assert data["total_entradas"] == 2
    assert {e["codigo"] for e in data["entradas"]} == {"7723", "1430"}
    assert data["entradas"][0]["descripcion"] == "Jefatura del Estado"


@pytest.mark.asyncio
async def test_tabla_auxiliar_sin_envoltorio_sigue_funcionando():
    """No se rompe la forma que ya se soportaba."""
    client = BOEHTTPClient()
    client.get = AsyncMock(return_value={"7723": "Jefatura del Estado"})
    data = (await client.get_auxiliary_table("departamentos"))["data"]
    assert data["total_entradas"] == 1


# ---------------------------------------------------------------------------
# 4. url_pdf es un objeto, no una cadena
# ---------------------------------------------------------------------------

def test_pdf_link_desde_objeto():
    url, size = _pdf_link({
        "szBytes": "317144", "szKBytes": "310",
        "texto": "https://www.boe.es/boe/dias/2026/08/14/pdfs/BOE-S-2026-199.pdf",
    })
    assert url == "https://www.boe.es/boe/dias/2026/08/14/pdfs/BOE-S-2026-199.pdf"
    assert size == "310"


def test_pdf_link_desde_cadena():
    url, size = _pdf_link("https://www.boe.es/x.pdf", fallback_size="42")
    assert (url, size) == ("https://www.boe.es/x.pdf", "42")


def test_pdf_link_ausente():
    assert _pdf_link(None) == (None, "N/A")
    assert _pdf_link("") == (None, "N/A")
