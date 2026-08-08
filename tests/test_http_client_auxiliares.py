"""
Tests de normalización de las respuestas de las tablas auxiliares (/datos-auxiliares).
"""

import httpx
import pytest
from unittest.mock import AsyncMock

from mcp_boe.utils.http_client import BOEHTTPClient


# ---------------------------------------------------------------------------
# Muestras de respuestas reales
# ---------------------------------------------------------------------------

AUX_JSON_RESPONSE = {
    "7723": "Jefatura del Estado",
    "1430": "Ministerio de Justicia",
    "1470": "Ministerio del Interior"
}

AUX_XML_RESPONSE = """<?xml version="1.0" encoding="utf-8"?>
<response>
  <status><code>200</code><text>ok</text></status>
  <data>
    <item>
      <codigo>7723</codigo>
      <descripcion>Jefatura del Estado</descripcion>
    </item>
    <item>
      <codigo>1430</codigo>
      <descripcion>Ministerio de Justicia</descripcion>
    </item>
  </data>
</response>
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_normalizacion_json_plano():
    """El JSON plano {codigo: descripcion} debe convertirse al formato con 'entradas'."""
    client = BOEHTTPClient()
    
    async def _fake_request(*args, **kwargs):
        return httpx.Response(200, json=AUX_JSON_RESPONSE)
        
    client._make_request = AsyncMock(side_effect=_fake_request)
    
    res = await client.get_auxiliary_table("departamentos")
    
    assert "data" in res
    data = res["data"]
    assert data["nombre"] == "departamentos"
    assert data["total_entradas"] == 3
    assert len(data["entradas"]) == 3
    
    # Comprobar contenido
    entradas = {e["codigo"]: e["descripcion"] for e in data["entradas"]}
    assert entradas["7723"] == "Jefatura del Estado"
    assert entradas["1430"] == "Ministerio de Justicia"
    assert entradas["1470"] == "Ministerio del Interior"


@pytest.mark.asyncio
async def test_normalizacion_xml_con_item():
    """El XML parseado con clave 'item' debe mapear a 'entradas'."""
    client = BOEHTTPClient()
    
    async def _fake_request(*args, **kwargs):
        return httpx.Response(200, text=AUX_XML_RESPONSE)
        
    client._make_request = AsyncMock(side_effect=_fake_request)
    
    # Forzar que el cliente pida XML
    client.get = AsyncMock(return_value={
        "status": {"code": "200", "text": "ok"},
        "data": {
            "item": [
                {"codigo": "7723", "descripcion": "Jefatura del Estado"},
                {"codigo": "1430", "descripcion": "Ministerio de Justicia"}
            ]
        }
    })
    
    res = await client.get_auxiliary_table("departamentos")
    
    assert "data" in res
    data = res["data"]
    assert data["total_entradas"] == 2
    assert "entradas" in data
    
    entradas = {e["codigo"]: e["descripcion"] for e in data["entradas"]}
    assert entradas["7723"] == "Jefatura del Estado"
    assert entradas["1430"] == "Ministerio de Justicia"
