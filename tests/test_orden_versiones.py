"""
Tests de la normalización del XML de /texto.

Dos defectos que se manifiestan sobre datos reales del BOE y que el fixture
SAMPLE_LAW_TEXTO de conftest no reproduce (allí las versiones ya vienen de
más reciente a más antigua y el título es un campo del dict):

  1. El BOE emite las <version> de MÁS ANTIGUA a MÁS RECIENTE, y
     search_law_articles lee versiones[0]: buscaba sobre el texto derogado.
  2. El título del bloque es un ATRIBUTO del XML, no un elemento hijo.
"""

import httpx
import pytest
from unittest.mock import AsyncMock

from mcp_boe.tools.legislation import LegislationTools
from mcp_boe.utils.http_client import BOEHTTPClient


# ---------------------------------------------------------------------------
# XML de ejemplo: /texto de la LGSS recortado al artículo 194.
# Orden de versiones y título como atributo, tal y como los sirve el BOE.
# La Ley 2/2025 sustituyó "gran invalidez" por "gran incapacidad".
# ---------------------------------------------------------------------------

TEXTO_XML = """<?xml version="1.0" encoding="utf-8"?>
<response>
  <status><code>200</code><text>ok</text></status>
  <data>
    <texto>
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
    </texto>
  </data>
</response>
"""


@pytest.fixture
def client_con_texto():
    """Cliente real con _make_request simulado, sirviendo el XML de /texto."""
    client = BOEHTTPClient()

    async def _fake_request(method, url, params=None, headers=None, **kwargs):
        return httpx.Response(200, text=TEXTO_XML)

    client._make_request = AsyncMock(side_effect=_fake_request)
    return client


# ---------------------------------------------------------------------------
# Normalización del XML
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_versiones_de_mas_reciente_a_mas_antigua(client_con_texto):
    """versiones[0] debe ser la vigente, no la redacción original."""
    respuesta = await client_con_texto.get_law_by_id("BOE-A-2015-11724", "texto")

    versiones = respuesta["data"]["texto"][0]["versiones"]
    assert [v["fecha_vigencia"] for v in versiones] == ["20250501", "20160102"]


@pytest.mark.asyncio
async def test_titulo_del_bloque_se_lee_del_atributo(client_con_texto):
    """El título es un atributo del <bloque>, no un elemento hijo."""
    respuesta = await client_con_texto.get_law_by_id("BOE-A-2015-11724", "texto")

    assert respuesta["data"]["texto"][0]["titulo"] == "Artículo 194"


# ---------------------------------------------------------------------------
# search_law_articles
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_busqueda_encuentra_el_texto_vigente(client_con_texto):
    """Buscar un término introducido por una reforma debe encontrarlo."""
    tools = LegislationTools(client_con_texto)

    resultado = await tools.search_law_articles({
        "law_id": "BOE-A-2015-11724",
        "query": "gran incapacidad",
    })

    texto = resultado[0].text
    assert "No se encontraron" not in texto
    assert "a194" in texto


@pytest.mark.asyncio
async def test_busqueda_no_devuelve_redaccion_derogada(client_con_texto):
    """Un término que solo existe en la versión derogada no es texto vigente."""
    tools = LegislationTools(client_con_texto)

    resultado = await tools.search_law_articles({
        "law_id": "BOE-A-2015-11724",
        "query": "gran invalidez",
    })

    assert "No se encontraron" in resultado[0].text


@pytest.mark.asyncio
async def test_resultados_de_busqueda_llevan_titulo(client_con_texto):
    """El artículo encontrado se identifica por su título, no solo por su id."""
    tools = LegislationTools(client_con_texto)

    resultado = await tools.search_law_articles({
        "law_id": "BOE-A-2015-11724",
        "query": "gran incapacidad",
    })

    assert "Artículo 194" in resultado[0].text


# ---------------------------------------------------------------------------
# No regresión: compare_law_versions elige versión por fecha
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_comparacion_sigue_detectando_la_modificacion(client_con_texto):
    """compare_law_versions usa _get_active_version, que ordena por su cuenta."""
    tools = LegislationTools(client_con_texto)

    resultado = await tools.compare_law_versions({
        "law_id": "BOE-A-2015-11724",
        "from_date": "20200101",
        "to_date": "20260101",
    })

    assert "modificad" in resultado[0].text.lower()
