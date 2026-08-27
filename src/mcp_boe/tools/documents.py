"""
Herramienta MCP para leer y resumir documentos PDF del BOE.

Descarga el PDF directamente desde boe.es, extrae el texto con pypdf
y lo devuelve listo para que el LLM lo analice.
"""

import io
import logging
from urllib.parse import urljoin, urlparse
from typing import Any, Dict, List

import httpx
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)

# Tamaño máximo de PDF que procesamos (10 MB)
MAX_PDF_BYTES = 10 * 1024 * 1024

# Caracteres máximos que devolvemos al LLM (~100 k tokens aprox.)
MAX_TEXT_CHARS = 80_000

# ---------------------------------------------------------------------------
# Allowlist estricta de host (SSRF)
# ---------------------------------------------------------------------------
# Antes bastaba con `source.startswith("http")` para aceptar la URL, que luego se
# descargaba con follow_redirects=True devolviendo el cuerpo al modelo. Eso hace de
# `read_boe_pdf` un lector de URLs arbitrarias con la identidad de red del proceso:
# el endpoint de metadatos del proveedor cloud, servicios internos accesibles solo
# desde esa red, o exfiltración (el modelo acaba pegando el contenido en el chat).
# Una denylist no basta — hay que fijar los hosts permitidos, y revalidar en CADA
# salto de redirección, porque si no un 302 desde boe.es esquiva el filtro.
ALLOWED_PDF_HOSTS = frozenset({"boe.es", "www.boe.es"})
MAX_REDIRECTS = 5


def _host_allowed(url: str) -> bool:
    """True solo para https://(www.)boe.es/... — todo lo demás se rechaza."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in ALLOWED_PDF_HOSTS


class DocumentTools:
    """Herramienta para leer PDFs del BOE."""

    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="read_boe_pdf",
                description=(
                    "Descarga y extrae el texto COMPLETO de cualquier documento del BOE "
                    "(leyes, decretos, órdenes ministeriales, ceses, nombramientos, "
                    "anuncios, resoluciones, etc.) para leerlo y explicarlo en detalle. "
                    "Úsala SIEMPRE que el usuario pida 'más detalles', 'el contenido', "
                    "'qué dice exactamente' o 'léeme' un documento del BOE. "
                    "Acepta la URL directa del PDF (campo url_pdf de los sumarios) "
                    "o el identificador BOE (ej: BOE-A-2025-6192), del que se construye "
                    "la URL automáticamente. Es la única herramienta que puede leer el "
                    "contenido íntegro de documentos NO consolidados (sección II, III, etc.)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": (
                                "URL completa del PDF (https://www.boe.es/boe/dias/…/BOE-A-…pdf) "
                                "o identificador BOE (ej: BOE-A-2025-6192 o BOE-A-2025-6192.pdf)"
                            ),
                        },
                        "max_pages": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 30,
                            "description": "Número máximo de páginas a leer (por defecto 30)",
                        },
                    },
                    "required": ["source"],
                    "additionalProperties": False,
                },
            )
        ]

    async def read_boe_pdf(self, arguments: Dict[str, Any]) -> List[TextContent]:
        source: str = arguments["source"].strip()
        max_pages: int = arguments.get("max_pages", 30)

        url = await self._resolve_url(source)
        if url is None:
            return [TextContent(type="text", text=f"No se pudo construir una URL válida a partir de: {source}")]

        logger.info(f"Descargando PDF: {url}")

        try:
            pdf_bytes = await self._download_pdf(url)
        except Exception as e:
            return [TextContent(type="text", text=f"Error descargando el PDF ({url}): {e}")]

        try:
            text, total_pages, pages_read = self._extract_text(pdf_bytes, max_pages)
        except Exception as e:
            return [TextContent(type="text", text=f"Error extrayendo texto del PDF: {e}")]

        if not text.strip():
            return [TextContent(
                type="text",
                text=(
                    f"El PDF ({url}) no contiene texto extraíble. "
                    "Es posible que esté escaneado como imagen."
                ),
            )]

        truncated = len(text) > MAX_TEXT_CHARS
        if truncated:
            text = text[:MAX_TEXT_CHARS]

        header = (
            f"## 📄 Contenido del PDF\n"
            f"**Fuente:** {url}\n"
            f"**Páginas leídas:** {pages_read} de {total_pages}"
        )
        if truncated:
            header += f" *(texto truncado a {MAX_TEXT_CHARS:,} caracteres)*"
        header += "\n\n---\n\n"

        return [TextContent(type="text", text=header + text)]

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _resolve_url(self, source: str) -> str | None:
        """Convierte un identificador BOE o URL parcial en URL completa de PDF."""
        if source.startswith("http"):
            # solo boe.es. Ver ALLOWED_PDF_HOSTS.
            return source if _host_allowed(source) else None

        # Normalizar: quitar extensión si la trae
        boe_id = source.removesuffix(".pdf").strip()

        # Formato esperado: BOE-A-YYYY-NNNNN  o  BORME-A-YYYY-NNNNN
        parts = boe_id.split("-")
        if len(parts) < 4:
            return None

        diario = parts[0].lower()   # "boe" o "borme"

        # Intento 1: API de legislación consolidada (devuelve fecha en YYYYMMDD o YYYY-MM-DD)
        try:
            api_url = f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{boe_id}/metadatos"
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                r = await client.get(api_url, headers={"Accept": "application/json"})
                if r.status_code == 200:
                    payload = r.json()
                    data = payload.get("data") or {}
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    fecha = self._normalize_fecha(data.get("fecha_publicacion", ""))
                    if fecha:
                        yyyy, mm, dd = fecha[:4], fecha[4:6], fecha[6:]
                        return f"https://www.boe.es/{diario}/dias/{yyyy}/{mm}/{dd}/pdfs/{boe_id}.pdf"
        except Exception:
            pass

        # Intento 2: página HTML del BOE, que existe para CUALQUIER documento publicado
        try:
            import re
            html_url = f"https://www.boe.es/diario_boe/txt.php?id={boe_id}"
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                r = await client.get(html_url, headers={"Accept": "text/html"})
                if r.status_code == 200:
                    match = re.search(
                        r'/(?:boe|borme)/dias/(\d{4}/\d{2}/\d{2})/pdfs/',
                        r.text,
                    )
                    if match:
                        date_path = match.group(1)   # "2026/04/29"
                        return f"https://www.boe.es/{diario}/dias/{date_path}/pdfs/{boe_id}.pdf"
        except Exception:
            pass

        return None

    @staticmethod
    def _normalize_fecha(fecha: str) -> str | None:
        """Normaliza fecha a formato YYYYMMDD; acepta YYYYMMDD y YYYY-MM-DD."""
        if not fecha:
            return None
        if len(fecha) == 8 and fecha.isdigit():
            return fecha
        if len(fecha) == 10 and fecha[4] == "-" and fecha[7] == "-":
            return fecha.replace("-", "")
        return None

    async def _download_pdf(self, url: str) -> bytes:
        # follow_redirects=False + bucle manual, para poder
        # rechazar un 302 que salga de boe.es (con follow_redirects=True la
        # petición al host ajeno ya se habría hecho).
        if not _host_allowed(url):
            raise ValueError(f"Host no permitido: solo se descargan PDFs de boe.es ({url})")

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            follow_redirects=False,
            headers={"User-Agent": "MCP-BOE/0.1.0 (https://github.com/ComputingVictor/MCP-BOE)"},
        ) as client:
            for _ in range(MAX_REDIRECTS):
                response = await client.get(url)
                if not response.is_redirect:
                    break
                url = urljoin(url, response.headers.get("location", ""))
                if not _host_allowed(url):
                    raise ValueError(
                        f"Redirección fuera de boe.es bloqueada: {url}"
                    )
            else:
                raise ValueError("Demasiadas redirecciones")

            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "pdf" not in content_type and not url.endswith(".pdf"):
                raise ValueError(f"La respuesta no es un PDF (Content-Type: {content_type})")

            if len(response.content) > MAX_PDF_BYTES:
                raise ValueError(
                    f"El PDF es demasiado grande ({len(response.content) / 1024 / 1024:.1f} MB). "
                    f"Límite: {MAX_PDF_BYTES // 1024 // 1024} MB."
                )

            return response.content

    def _extract_text(self, pdf_bytes: bytes, max_pages: int) -> tuple[str, int, int]:
        """Extrae texto del PDF. Devuelve (texto, total_páginas, páginas_leídas)."""
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        pages_to_read = min(max_pages, total_pages)

        parts = []
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text() or ""
            if page_text.strip():
                parts.append(page_text)

        return "\n\n".join(parts), total_pages, pages_to_read
