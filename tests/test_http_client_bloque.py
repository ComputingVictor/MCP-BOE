"""
Tests del acceso a un bloque suelto de una norma (/texto/bloque/<id>).

Ese endpoint del BOE, igual que /texto, rechaza application/json. Como
get_law_by_id solo enrutaba a XML la sección exacta 'texto', cualquier
llamada a get_law_text_block terminaba en HTTP 400.
"""

import httpx
import pytest
from unittest.mock import AsyncMock
from mcp.types import TextContent

from mcp_boe.tools.legislation import LegislationTools
from mcp_boe.utils.http_client import BOEHTTPClient


# ---------------------------------------------------------------------------
# XML de ejemplo: respuesta real de /texto/bloque/a194 de la LGSS.
# El BOE emite las <version> de MÁS ANTIGUA a MÁS RECIENTE.
# ---------------------------------------------------------------------------

BLOQUE_XML = """<?xml version="1.0" encoding="utf-8"?>
<response>
  <status><code>200</code><text>ok</text></status>
  <data>
    <bloque id="a194" tipo="precepto" titulo="Artículo 194">
      <version id_norma="BOE-A-2015-11724" fecha_publicacion="20151031" fecha_vigencia="20160102">
        <p class="articulo">Artículo 194. Grados de incapacidad permanente.</p>
        <p class="parrafo">d) Gran invalidez.</p>
      </version>
      <version id_norma="BOE-A-2025-8567" fecha_publicacion="20250430" fecha_vigencia="20250501">
        <p class="articulo">Artículo 194. Grados de incapacidad permanente.</p>
        <p class="parrafo">d) Gran incapacidad.</p>
      </version>
    </bloque>
  </data>
</response>
"""


@pytest.fixture
def client_con_bloque():
    """Cliente real con _make_request simulado, para observar los headers."""
    client = BOEHTTPClient()
    peticiones = []

    async def _fake_request(method, url, params=None, headers=None, **kwargs):
        peticiones.append({"url": url, "headers": headers or {}})
        return httpx.Response(200, text=BLOQUE_XML)

    client._make_request = AsyncMock(side_effect=_fake_request)
    return client, peticiones


# ---------------------------------------------------------------------------
# Cliente HTTP
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bloque_se_pide_en_xml(client_con_bloque):
    """El endpoint de bloque rechaza JSON: hay que pedirlo en XML."""
    client, peticiones = client_con_bloque

    await client.get_law_by_id("BOE-A-2015-11724", "texto/bloque/a194")

    assert len(peticiones) == 1
    assert peticiones[0]["headers"].get("Accept") == "application/xml"
    assert peticiones[0]["url"].endswith("/texto/bloque/a194")


@pytest.mark.asyncio
async def test_bloque_normalizado_al_formato_esperado(client_con_bloque):
    """La respuesta se normaliza a data.bloque{titulo, tipo, version[]}."""
    client, _ = client_con_bloque

    respuesta = await client.get_law_by_id("BOE-A-2015-11724", "texto/bloque/a194")

    bloque = respuesta["data"]["bloque"]
    assert bloque["id"] == "a194"
    assert bloque["tipo"] == "precepto"
    assert bloque["titulo"] == "Artículo 194"
    assert len(bloque["version"]) == 2
    assert "contenido_html" in bloque["version"][0]


@pytest.mark.asyncio
async def test_bloque_devuelve_la_version_vigente_primero(client_con_bloque):
    """version[0] es la "versión actual" para el formateador: debe ser la vigente."""
    client, _ = client_con_bloque

    respuesta = await client.get_law_by_id("BOE-A-2015-11724", "texto/bloque/a194")

    versiones = respuesta["data"]["bloque"]["version"]
    assert versiones[0]["fecha_vigencia"] == "20250501"
    assert "Gran incapacidad" in versiones[0]["contenido_html"]


# ---------------------------------------------------------------------------
# Herramienta get_law_text_block
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_law_text_block_devuelve_el_articulo(client_con_bloque):
    """La herramienta devuelve el texto del artículo, no un error de acceso."""
    client, _ = client_con_bloque
    tools = LegislationTools(client)

    resultado = await tools.get_law_text_block({
        "law_id": "BOE-A-2015-11724",
        "block_id": "a194",
    })

    assert len(resultado) == 1
    assert isinstance(resultado[0], TextContent)
    texto = resultado[0].text
    assert "Error accediendo al bloque" not in texto
    assert "Artículo 194" in texto
    assert "Gran incapacidad" in texto
