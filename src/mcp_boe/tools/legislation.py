"""
Herramientas MCP para acceso a la legislación consolidada del BOE.

Este módulo contiene las herramientas que Claude puede usar para buscar
y obtener información sobre legislación española consolidada.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from mcp.types import TextContent, ImageContent, EmbeddedResource, Tool

from ..utils.http_client import BOEHTTPClient, APIError
from ..models.boe_models import (
    ConsolidatedLawSearchResult,
    ConsolidatedLaw,
    SearchParameters,
    validate_boe_identifier,
    validate_date_format,
    format_date_for_api
)

logger = logging.getLogger(__name__)


class LegislationTools:
    """Herramientas para trabajar con legislación consolidada."""
    
    def __init__(self, http_client: BOEHTTPClient):
        self.client = http_client

    def get_tools(self) -> List[Tool]:
        """Retorna la lista de herramientas disponibles."""
        return [
            Tool(
                name="search_consolidated_legislation",
                description="Busca normas en la legislación consolidada del BOE",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Términos de búsqueda (ej: 'Ley 40/2015', 'crisis sanitaria', 'procedimiento administrativo')"
                        },
                        "title": {
                            "type": "string", 
                            "description": "Búsqueda específica en el título de la norma"
                        },
                        "department_code": {
                            "type": "string",
                            "description": "Código del departamento emisor (ej: '7723' para Jefatura del Estado)"
                        },
                        "legal_range_code": {
                            "type": "string", 
                            "description": "Código del rango normativo (ej: '1300' para Ley, '1200' para Real Decreto)"
                        },
                        "matter_code": {
                            "type": "string",
                            "description": "Código de materia según vocabulario controlado del BOE"
                        },
                        "from_date": {
                            "type": "string",
                            "pattern": "^\\d{8}$",
                            "description": "Fecha de inicio de búsqueda en formato AAAAMMDD (ej: '20200101')"
                        },
                        "to_date": {
                            "type": "string", 
                            "pattern": "^\\d{8}$",
                            "description": "Fecha de fin de búsqueda en formato AAAAMMDD (ej: '20201231')"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20,
                            "description": "Número máximo de resultados a devolver"
                        },
                        "offset": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "Número de resultados a saltar (para paginación)"
                        },
                        "include_derogated": {
                            "type": "boolean",
                            "default": False,
                            "description": "Incluir normas derogadas en los resultados"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_consolidated_law",
                description="Obtiene el texto completo y metadatos de una norma consolidada específica",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "law_id": {
                            "type": "string",
                            "pattern": "^BOE-[A-Z]-\\d{4}-\\d{1,5}$",
                            "description": "Identificador único de la norma (ej: 'BOE-A-2015-10566')"
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "default": True,
                            "description": "Incluir metadatos de la norma"
                        },
                        "include_analysis": {
                            "type": "boolean", 
                            "default": True,
                            "description": "Incluir análisis jurídico (materias, referencias, notas)"
                        },
                        "include_full_text": {
                            "type": "boolean",
                            "default": False,
                            "description": "Incluir texto consolidado completo (puede ser muy extenso)"
                        },
                        "include_eli_metadata": {
                            "type": "boolean",
                            "default": False,
                            "description": "Incluir metadatos ELI (European Legislation Identifier)"
                        }
                    },
                    "required": ["law_id"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_law_text_block",
                description="Obtiene un bloque específico del texto de una norma (artículo, disposición, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "law_id": {
                            "type": "string",
                            "pattern": "^BOE-[A-Z]-\\d{4}-\\d{1,5}$", 
                            "description": "Identificador único de la norma"
                        },
                        "block_id": {
                            "type": "string",
                            "description": "ID del bloque de texto (ej: 'a1' para artículo 1, 'dd' para disposición derogatoria)"
                        }
                    },
                    "required": ["law_id", "block_id"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_law_structure",
                description="Obtiene el índice/estructura de una norma (títulos de artículos, disposiciones, etc.)",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "law_id": {
                            "type": "string",
                            "pattern": "^BOE-[A-Z]-\\d{4}-\\d{1,5}$",
                            "description": "Identificador único de la norma"
                        }
                    },
                    "required": ["law_id"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="find_related_laws",
                description="Encuentra leyes relacionadas (que modifican, derogan o son modificadas por una norma)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "law_id": {
                            "type": "string",
                            "pattern": "^BOE-[A-Z]-\\d{4}-\\d{1,5}$",
                            "description": "Identificador único de la norma base"
                        },
                        "relation_type": {
                            "type": "string",
                            "enum": ["all", "modifies", "modified_by", "derogates", "derogated_by"],
                            "default": "all",
                            "description": "Tipo de relación a buscar"
                        }
                    },
                    "required": ["law_id"],
                    "additionalProperties": False
                }
            )
        ]

    async def search_consolidated_legislation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Busca normas en la legislación consolidada.
        
        Args:
            arguments: Parámetros de búsqueda
            
        Returns:
            Lista de contenido de texto con los resultados
        """
        try:
            # Extraer y validar parámetros
            query = arguments.get('query')
            title = arguments.get('title')
            department_code = arguments.get('department_code')
            legal_range_code = arguments.get('legal_range_code')
            matter_code = arguments.get('matter_code')
            from_date = arguments.get('from_date')
            to_date = arguments.get('to_date')
            limit = arguments.get('limit', 20)
            offset = arguments.get('offset', 0)
            include_derogated = arguments.get('include_derogated', False)

            # Validar fechas si se proporcionan
            if from_date and not validate_date_format(from_date):
                raise ValueError(f"Formato de fecha inválido: {from_date}")
            if to_date and not validate_date_format(to_date):
                raise ValueError(f"Formato de fecha inválido: {to_date}")

            # Construir query estructurada
            search_query = self.client.build_search_query(
                text=query,
                title=title,
                department=department_code,
                legal_range=legal_range_code,
                matter=matter_code,
                date_from=from_date,
                date_to=to_date
            )

            # Realizar búsqueda
            logger.info(f"Buscando legislación: query='{query}', limit={limit}")
            
            response = await self.client.search_legislation(
                query=search_query if any([query, title, department_code, legal_range_code, matter_code]) else None,
                from_date=from_date,
                to_date=to_date,
                offset=offset,
                limit=limit
            )

            # Procesar resultados
            results = self._extract_results(response)

            # Filtrar normas derogadas si no se solicitan
            if not include_derogated:
                results = [r for r in results if r.get('vigencia_agotada') != 'S' and r.get('estatus_derogacion') != 'S']

            fallback_note = ""

            # — Reintento automático —————————————————————————————————————
            # Si no hay resultados y el usuario buscó por query (texto libre),
            # volvemos a intentar con cada palabra suelta en lugar de la frase
            # completa. Así "gases licuados del petróleo" también encuentra
            # documentos que solo contienen "petróleo" o "gases licuados".
            if not results and query and not title:
                words = [w for w in query.split() if len(w) > 3]
                if words:
                    fallback_query = self.client.build_search_query(
                        text=" OR ".join(words),
                        department=department_code,
                        legal_range=legal_range_code,
                        matter=matter_code,
                        date_from=from_date,
                        date_to=to_date
                    )
                    logger.info(f"Sin resultados exactos, reintentando con términos sueltos: {words}")
                    fb_response = await self.client.search_legislation(
                        query=fallback_query,
                        from_date=from_date,
                        to_date=to_date,
                        offset=offset,
                        limit=limit
                    )
                    results = self._extract_results(fb_response)
                    if not include_derogated:
                        results = [r for r in results if r.get('vigencia_agotada') != 'S' and r.get('estatus_derogacion') != 'S']
                    if results:
                        fallback_note = (
                            f"> ⚠️ **No se encontraron resultados exactos para «{query}».**\n"
                            f"> La búsqueda se amplió usando los términos sueltos: "
                            f"{', '.join(f'`{w}`' for w in words)}.\n"
                            f"> Si los resultados no son los esperados, prueba con la denominación "
                            f"técnica oficial (p. ej. «gases licuados del petróleo» en vez de «gasolina»).\n\n"
                        )

            if not results:
                # Construir sugerencias útiles basadas en lo que se buscó
                sugerencias = []
                if query:
                    palabras = [w for w in query.split() if len(w) > 3]
                    if len(palabras) > 1:
                        sugerencias.append(f"- Prueba con una sola palabra clave: `{palabras[0]}`")
                    sugerencias.append("- Usa la denominación técnica oficial en lugar de sinónimos comunes")
                    sugerencias.append("- Busca por título exacto con el parámetro `title`")
                if not include_derogated:
                    sugerencias.append("- Activa `include_derogated: true` para incluir normas derogadas")
                sugerencias.append("- Consulta `get_matters_table` o `get_legal_ranges_table` para encontrar los códigos de filtro correctos")

                msg = f"No se encontraron normas para «{query or title}»."
                if sugerencias:
                    msg += "\n\n**Sugerencias:**\n" + "\n".join(sugerencias)
                return [TextContent(type="text", text=msg)]

            formatted_results = self._format_search_results(results, limit)

            return [TextContent(
                type="text",
                text=fallback_note + formatted_results
            )]

        except APIError as e:
            logger.error(f"Error de API buscando legislación: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a la API del BOE: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado buscando legislación: {e}")
            return [TextContent(
                type="text", 
                text=f"Error interno: {str(e)}"
            )]

    def _extract_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae la lista de resultados de una respuesta de la API."""
        if not response.get('data'):
            return []
        results = response['data']
        if not isinstance(results, list):
            results = [results]
        return results

    def _format_search_results(self, results: List[Dict[str, Any]], limit: int) -> str:
        """Formatea los resultados de búsqueda para mostrar al usuario."""
        output = []
        
        output.append(f"## 📋 Resultados de búsqueda de legislación consolidada")
        output.append(f"**Encontradas {len(results)} normas** (mostrando hasta {limit})")
        output.append("")

        for i, result in enumerate(results, 1):
            # Información básica
            identifier = result.get('identificador', 'N/A')
            title = result.get('titulo', 'Sin título')
            
            # Metadatos importantes
            publication_date = result.get('fecha_publicacion', '')
            if publication_date and len(publication_date) == 8:
                try:
                    date_obj = datetime.strptime(publication_date, '%Y%m%d')
                    publication_date = date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    pass
            
            # Información del departamento y rango
            department = ""
            if isinstance(result.get('departamento'), dict):
                department = result['departamento'].get('texto', '')
            elif isinstance(result.get('departamento'), str):
                department = result['departamento']
                
            legal_range = ""
            if isinstance(result.get('rango'), dict):
                legal_range = result['rango'].get('texto', '')
            elif isinstance(result.get('rango'), str):
                legal_range = result['rango']

            # Estado de la norma
            status_indicators = []
            if result.get('vigencia_agotada') == 'S':
                status_indicators.append("❌ Vigencia agotada")
            if result.get('estatus_derogacion') == 'S':
                status_indicators.append("🚫 Derogada")
            if result.get('estado_consolidacion', {}).get('texto') == 'Desactualizado':
                status_indicators.append("⚠️ Desactualizada")

            # Construir entrada
            output.append(f"### {i}. {legal_range}")
            output.append(f"**{title}**")
            output.append(f"- **ID:** `{identifier}`")
            output.append(f"- **Publicado:** {publication_date}")
            output.append(f"- **Departamento:** {department}")
            
            if status_indicators:
                output.append(f"- **Estado:** {' | '.join(status_indicators)}")
            
            # URL para consulta
            url = result.get('url_html_consolidada')
            if url:
                output.append(f"- **Ver en BOE:** {url}")
            
            output.append("")

        output.append("---")
        output.append("💡 **Sugerencia:** Usa `get_consolidated_law` con el ID de la norma para obtener el texto completo.")
        
        return "\n".join(output)

    async def get_consolidated_law(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene una norma consolidada específica.
        
        Args:
            arguments: Parámetros de la consulta
            
        Returns:
            Lista de contenido con la información de la norma
        """
        try:
            law_id = arguments['law_id']
            include_metadata = arguments.get('include_metadata', True)
            include_analysis = arguments.get('include_analysis', True) 
            include_full_text = arguments.get('include_full_text', False)
            include_eli_metadata = arguments.get('include_eli_metadata', False)

            # Validar ID
            if not validate_boe_identifier(law_id):
                raise ValueError(f"Identificador de norma inválido: {law_id}")

            logger.info(f"Obteniendo norma consolidada: {law_id}")

            # Obtener información base
            content_parts = []
            
            if include_metadata:
                metadata_response = await self.client.get_law_by_id(law_id, 'metadatos')
                if metadata_response.get('data'):
                    content_parts.append(self._format_law_metadata(metadata_response['data']))

            if include_analysis:
                try:
                    analysis_response = await self.client.get_law_by_id(law_id, 'analisis')
                    if analysis_response.get('data'):
                        content_parts.append(self._format_law_analysis(analysis_response['data']))
                except APIError:
                    # El análisis es opcional
                    pass

            if include_eli_metadata:
                try:
                    eli_response = await self.client.get_law_by_id(law_id, 'metadata-eli')
                    if eli_response.get('data'):
                        content_parts.append(self._format_eli_metadata(eli_response['data']))
                except APIError:
                    # ELI es opcional
                    pass

            if include_full_text:
                try:
                    text_response = await self.client.get_law_by_id(law_id, 'texto')
                    if text_response.get('data'):
                        content_parts.append(self._format_law_text(text_response['data'], full_text=True))
                except APIError as e:
                    content_parts.append(f"⚠️ No se pudo obtener el texto completo: {e.mensaje}")

            if not content_parts:
                return [TextContent(
                    type="text",
                    text=f"No se encontró información para la norma {law_id}"
                )]

            return [TextContent(
                type="text",
                text="\n\n".join(content_parts)
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo norma {law_id}: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a la norma {law_id}: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo norma {law_id}: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_law_metadata(self, metadata: Dict[str, Any]) -> str:
        """Formatea los metadatos de una norma."""
        output = []
        output.append(f"# 📜 {metadata.get('titulo', 'Norma sin título')}")
        output.append("")
        
        # Información básica
        output.append("## Información básica")
        output.append(f"- **Identificador BOE:** `{metadata.get('identificador')}`")
        
        # Fechas importantes
        pub_date = metadata.get('fecha_publicacion', '')
        if pub_date and len(pub_date) == 8:
            try:
                date_obj = datetime.strptime(pub_date, '%Y%m%d')
                pub_date = date_obj.strftime('%d de %B de %Y')
            except ValueError:
                pass
        output.append(f"- **Fecha de publicación:** {pub_date}")
        
        vigor_date = metadata.get('fecha_vigencia', '')
        if vigor_date and len(vigor_date) == 8:
            try:
                date_obj = datetime.strptime(vigor_date, '%Y%m%d')
                vigor_date = date_obj.strftime('%d de %B de %Y')
            except ValueError:
                pass
            output.append(f"- **Entrada en vigor:** {vigor_date}")

        # Información del emisor
        department = metadata.get('departamento', {})
        if isinstance(department, dict):
            dept_name = department.get('texto', 'Desconocido')
        else:
            dept_name = str(department)
        output.append(f"- **Departamento:** {dept_name}")
        
        legal_range = metadata.get('rango', {})
        if isinstance(legal_range, dict):
            range_name = legal_range.get('texto', 'Desconocido')
        else:
            range_name = str(legal_range)
        output.append(f"- **Rango normativo:** {range_name}")

        # Estado actual
        output.append("")
        output.append("## Estado actual")
        
        status_items = []
        if metadata.get('vigencia_agotada') == 'S':
            status_items.append("❌ **Vigencia agotada**")
        elif metadata.get('estatus_derogacion') == 'S':
            status_items.append("🚫 **Derogada**")
            deroga_date = metadata.get('fecha_derogacion', '')
            if deroga_date and len(deroga_date) == 8:
                try:
                    date_obj = datetime.strptime(deroga_date, '%Y%m%d')
                    deroga_date = date_obj.strftime('%d/%m/%Y')
                    status_items.append(f"  - Fecha de derogación: {deroga_date}")
                except ValueError:
                    pass
        else:
            status_items.append("✅ **Vigente**")
        
        consolidation_status = metadata.get('estado_consolidacion', {})
        if isinstance(consolidation_status, dict):
            cons_status = consolidation_status.get('texto', '')
            if cons_status == 'Desactualizado':
                status_items.append("⚠️ **Consolidación desactualizada**")
            elif cons_status == 'Finalizado':
                status_items.append("✅ **Consolidación actualizada**")

        output.extend(status_items)

        # Enlaces
        output.append("")
        output.append("## Enlaces")
        html_url = metadata.get('url_html_consolidada')
        if html_url:
            output.append(f"- **Texto consolidado:** {html_url}")
        
        eli_url = metadata.get('url_eli')
        if eli_url:
            output.append(f"- **ELI (European Legislation Identifier):** {eli_url}")

        return "\n".join(output)

    def _format_law_analysis(self, analysis: Dict[str, Any]) -> str:
        """Formatea el análisis jurídico de una norma."""
        output = []
        output.append("## 🔍 Análisis jurídico")
        
        # Materias
        materias = analysis.get('materias', [])
        if materias:
            output.append("")
            output.append("### Materias")
            for materia in materias:
                if isinstance(materia, dict):
                    output.append(f"- {materia.get('texto', 'Sin descripción')} (código: {materia.get('codigo', 'N/A')})")
                else:
                    output.append(f"- {materia}")

        # Referencias anteriores
        anteriores = analysis.get('referencias', {}).get('anteriores', [])
        if anteriores:
            output.append("")
            output.append("### 📖 Referencias a normas anteriores")
            for ref in anteriores:
                rel_text = ref.get('relacion', {}).get('texto', 'Relacionada con') if isinstance(ref.get('relacion'), dict) else str(ref.get('relacion', ''))
                output.append(f"- **{rel_text}:** {ref.get('texto', 'Sin descripción')}")
                if ref.get('id_norma'):
                    output.append(f"  - ID: `{ref.get('id_norma')}`")

        # Referencias posteriores  
        posteriores = analysis.get('referencias', {}).get('posteriores', [])
        if posteriores:
            output.append("")
            output.append("### 📝 Referencias a normas posteriores")
            for ref in posteriores:
                rel_text = ref.get('relacion', {}).get('texto', 'Relacionada con') if isinstance(ref.get('relacion'), dict) else str(ref.get('relacion', ''))
                output.append(f"- **{rel_text}:** {ref.get('texto', 'Sin descripción')}")
                if ref.get('id_norma'):
                    output.append(f"  - ID: `{ref.get('id_norma')}`")

        # Notas
        notas = analysis.get('notas', [])
        if notas:
            output.append("")
            output.append("### 📌 Notas")
            for i, nota in enumerate(notas, 1):
                nota_text = nota.get('texto') if isinstance(nota, dict) else str(nota)
                output.append(f"{i}. {nota_text}")

        return "\n".join(output)

    def _format_law_text(self, text_data: Dict[str, Any], full_text: bool = False) -> str:
        """Formatea el texto de una norma."""
        output = []
        output.append("## 📄 Texto consolidado")

        bloques = text_data.get('texto', [])
        if not isinstance(bloques, list):
            bloques = [bloques] if bloques else []

        if not bloques:
            return "## 📄 Texto consolidado\n\nNo hay contenido de texto disponible."

        max_bloques = len(bloques) if full_text else min(5, len(bloques))
        for bloque in bloques[:max_bloques]:
            titulo = bloque.get('titulo', '')
            contenido = bloque.get('contenido_html', bloque.get('texto', ''))
            if titulo:
                output.append(f"\n### {titulo}")
            if contenido:
                output.append(self._clean_html_content(str(contenido)))

        if not full_text and len(bloques) > max_bloques:
            output.append(f"\n*... ({len(bloques) - max_bloques} bloques adicionales. Use `get_law_structure` + `get_law_text_block` para acceder a secciones concretas.)*")

        return "\n".join(output)

    def _format_law_structure(self, text_data: Dict[str, Any]) -> str:
        """Formatea la estructura de una norma."""
        output = []
        output.append("## 📑 Estructura de la norma")
        
        texto_blocks = text_data.get('texto', [])
        if not texto_blocks:
            return "No hay información de estructura disponible."
        
        for block in texto_blocks:
            block_id = block.get('id', 'N/A')
            titulo = block.get('titulo', 'Sin título')
            tipo = block.get('tipo', 'desconocido')
            
            # Formatear según el tipo
            if tipo == 'precepto':
                output.append(f"- **{titulo}** (`{block_id}`)")
            elif tipo == 'preambulo':
                output.append(f"- 📝 **{titulo}** (`{block_id}`)")
            elif tipo == 'parte_dispositiva':
                output.append(f"- ⚖️ **{titulo}** (`{block_id}`)")
            else:
                output.append(f"- **{titulo}** (`{block_id}`)")
        
        output.append("")
        output.append("💡 Use `get_law_text_block` con el ID entre paréntesis para obtener el contenido específico.")
        
        return "\n".join(output)

    def _format_eli_metadata(self, eli_data: Dict[str, Any]) -> str:
        """Formatea los metadatos ELI."""
        output = []
        output.append("## 🇪🇺 Metadatos ELI (European Legislation Identifier)")
        output.append("")
        output.append("Los metadatos ELI proporcionan identificación estándar europea para legislación.")
        output.append("")
        # Aquí se podría expandir según el formato específico de los metadatos ELI
        output.append(f"```json\n{json.dumps(eli_data, indent=2, ensure_ascii=False)}\n```")
        
        return "\n".join(output)

    async def get_law_text_block(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene un bloque específico del texto de una norma.
        
        Args:
            arguments: Parámetros con law_id y block_id
            
        Returns:
            Lista de contenido con el bloque de texto
        """
        try:
            law_id = arguments['law_id']
            block_id = arguments['block_id']

            if not validate_boe_identifier(law_id):
                raise ValueError(f"Identificador de norma inválido: {law_id}")

            logger.info(f"Obteniendo bloque {block_id} de norma {law_id}")

            # Obtener el bloque específico
            response = await self.client.get_law_by_id(law_id, f'texto/bloque/{block_id}')
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text=f"No se encontró el bloque '{block_id}' en la norma {law_id}"
                )]

            block_data = response['data']
            formatted_block = self._format_text_block(block_data, law_id, block_id)

            return [TextContent(
                type="text",
                text=formatted_block
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo bloque {block_id} de {law_id}: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo al bloque: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo bloque: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_text_block(self, block_data: Dict[str, Any], law_id: str, block_id: str) -> str:
        """Formatea un bloque de texto de una norma."""
        output = []
        
        # Información del bloque
        block_info = block_data.get('bloque', block_data)
        titulo = block_info.get('titulo', f'Bloque {block_id}')
        tipo = block_info.get('tipo', 'desconocido')
        
        output.append(f"# 📄 {titulo}")
        output.append(f"**Norma:** `{law_id}` | **Bloque:** `{block_id}` | **Tipo:** {tipo}")
        output.append("")

        # Versiones del bloque
        versiones = block_info.get('version', [])
        if not isinstance(versiones, list):
            versiones = [versiones]

        if not versiones:
            return "No se encontró contenido para este bloque."

        # Mostrar la versión más reciente
        version_actual = versiones[0]
        fecha_pub = version_actual.get('fecha_publicacion', '')
        if fecha_pub and len(fecha_pub) == 8:
            try:
                date_obj = datetime.strptime(fecha_pub, '%Y%m%d')
                fecha_pub = date_obj.strftime('%d/%m/%Y')
            except ValueError:
                pass

        output.append(f"**Versión actual** (desde {fecha_pub}):")
        output.append("")

        # Contenido HTML del bloque
        contenido_html = version_actual.get('contenido_html', '')
        if not contenido_html:
            # Buscar en elementos hijos del XML
            for key, value in version_actual.items():
                if isinstance(value, str) and len(value) > 50:
                    contenido_html = value
                    break

        if contenido_html:
            # Limpiar HTML básico para mostrar texto legible
            clean_text = self._clean_html_content(contenido_html)
            output.append(clean_text)
        else:
            output.append("*No se pudo extraer el contenido del bloque.*")

        # Si hay múltiples versiones, mostrar historial
        if len(versiones) > 1:
            output.append("")
            output.append("## 📅 Historial de versiones")
            for i, version in enumerate(versiones):
                fecha = version.get('fecha_publicacion', 'N/A')
                if fecha and len(fecha) == 8:
                    try:
                        date_obj = datetime.strptime(fecha, '%Y%m%d')
                        fecha = date_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        pass
                
                id_norma = version.get('id_norma', 'N/A')
                output.append(f"{i + 1}. **{fecha}** - Norma modificadora: `{id_norma}`")

        return "\n".join(output)

    def _clean_html_content(self, html_content: str) -> str:
        """Limpia contenido HTML para mostrar texto legible."""
        import re
        
        # Remover tags HTML básicos pero mantener estructura
        text = html_content
        
        # Convertir párrafos en saltos de línea
        text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', text)
        text = re.sub(r'<p[^>]*>', '', text)
        text = re.sub(r'</p>', '', text)
        
        # Convertir listas
        text = re.sub(r'<li[^>]*>', '\n• ', text)
        text = re.sub(r'</li>', '', text)
        text = re.sub(r'</?[uo]l[^>]*>', '', text)
        
        # Mantener énfasis
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text)
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text)
        
        # Limpiar otros tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Limpiar espacios extra
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text

    async def get_law_structure(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene la estructura/índice de una norma.
        
        Args:
            arguments: Parámetros con law_id
            
        Returns:
            Lista de contenido con la estructura de la norma
        """
        try:
            law_id = arguments['law_id']

            if not validate_boe_identifier(law_id):
                raise ValueError(f"Identificador de norma inválido: {law_id}")

            logger.info(f"Obteniendo estructura de norma {law_id}")

            # Obtener índice de la norma
            response = await self.client.get_law_by_id(law_id, 'texto/indice')
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text=f"No se encontró estructura para la norma {law_id}"
                )]

            structure_data = response['data']
            formatted_structure = self._format_detailed_structure(structure_data, law_id)

            return [TextContent(
                type="text",
                text=formatted_structure
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo estructura de {law_id}: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a la estructura: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo estructura: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_detailed_structure(self, structure_data: Dict[str, Any], law_id: str) -> str:
        """Formatea la estructura detallada de una norma."""
        output = []
        output.append(f"# 📑 Estructura de la norma `{law_id}`")
        output.append("")

        # Procesar bloques del índice
        bloques = structure_data.get('bloque', [])
        if not isinstance(bloques, list):
            bloques = [bloques]

        if not bloques:
            return "No se encontró información de estructura."

        # Agrupar por tipo de bloque
        tipos_bloques = {}
        for bloque in bloques:
            block_id = bloque.get('id', 'N/A')
            titulo = bloque.get('titulo', 'Sin título')
            fecha_act = bloque.get('fecha_actualizacion', '')
            
            # Determinar tipo de contenido
            if block_id.startswith('a'):
                tipo = "📄 Articulado"
            elif block_id.startswith('d') and 'd' in block_id[1:]:
                tipo = "📋 Disposiciones Derogatorias"
            elif block_id.startswith('d') and 'f' in block_id:
                tipo = "📝 Disposiciones Finales"
            elif block_id.startswith('d') and 'a' in block_id:
                tipo = "➕ Disposiciones Adicionales"
            elif block_id.startswith('d') and 't' in block_id:
                tipo = "🔄 Disposiciones Transitorias"
            elif 'preambulo' in titulo.lower() or block_id == 'pr':
                tipo = "📖 Preámbulo"
            elif 'anexo' in titulo.lower():
                tipo = "📎 Anexos"
            else:
                tipo = "📄 Otras disposiciones"

            if tipo not in tipos_bloques:
                tipos_bloques[tipo] = []
            
            tipos_bloques[tipo].append({
                'id': block_id,
                'titulo': titulo,
                'fecha_actualizacion': fecha_act
            })

        # Ordenar tipos para mostrar en orden lógico
        orden_tipos = [
            "📖 Preámbulo",
            "📄 Articulado", 
            "➕ Disposiciones Adicionales",
            "🔄 Disposiciones Transitorias",
            "📋 Disposiciones Derogatorias",
            "📝 Disposiciones Finales",
            "📎 Anexos",
            "📄 Otras disposiciones"
        ]

        for tipo in orden_tipos:
            if tipo in tipos_bloques:
                output.append(f"## {tipo}")
                output.append("")
                
                for bloque in tipos_bloques[tipo]:
                    fecha_act = bloque['fecha_actualizacion']
                    if fecha_act and len(fecha_act) == 8:
                        try:
                            date_obj = datetime.strptime(fecha_act, '%Y%m%d')
                            fecha_act = date_obj.strftime('%d/%m/%Y')
                        except ValueError:
                            pass
                    
                    output.append(f"- **{bloque['titulo']}** (`{bloque['id']}`)")
                    if fecha_act:
                        output.append(f"  - *Última actualización: {fecha_act}*")
                
                output.append("")

        output.append("---")
        output.append("💡 **Instrucciones:**")
        output.append("- Use `get_law_text_block` con el ID entre paréntesis para obtener el contenido específico")
        output.append("- Los IDs más comunes: `a1` (artículo 1), `dd` (disposición derogatoria), `df` (disposición final)")
        
        return "\n".join(output)

    async def find_related_laws(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Encuentra leyes relacionadas con una norma específica.
        
        Args:
            arguments: Parámetros con law_id y relation_type
            
        Returns:
            Lista de contenido con las normas relacionadas
        """
        try:
            law_id = arguments['law_id']
            relation_type = arguments.get('relation_type', 'all')

            if not validate_boe_identifier(law_id):
                raise ValueError(f"Identificador de norma inválido: {law_id}")

            logger.info(f"Buscando normas relacionadas con {law_id}, tipo: {relation_type}")

            # Obtener análisis de la norma para encontrar referencias
            response = await self.client.get_law_by_id(law_id, 'analisis')
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text=f"No se encontraron relaciones para la norma {law_id}"
                )]

            analysis_data = response['data']
            formatted_relations = self._format_law_relations(analysis_data, law_id, relation_type)

            return [TextContent(
                type="text",
                text=formatted_relations
            )]

        except APIError as e:
            logger.error(f"Error de API buscando relaciones de {law_id}: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a las relaciones: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado buscando relaciones: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_law_relations(self, analysis_data: Dict[str, Any], law_id: str, relation_type: str) -> str:
        """Formatea las relaciones de una norma."""
        output = []
        output.append(f"# 🔗 Normas relacionadas con `{law_id}`")
        output.append("")

        referencias = analysis_data.get('referencias', {})
        anteriores = referencias.get('anteriores', [])
        posteriores = referencias.get('posteriores', [])

        if not anteriores and not posteriores:
            return f"No se encontraron normas relacionadas con `{law_id}`."

        # Referencias anteriores (normas que esta norma afecta)
        if relation_type in ['all', 'modifies', 'derogates'] and anteriores:
            output.append("## 📖 Normas anteriores afectadas por esta norma")
            output.append("")
            
            for ref in anteriores:
                id_norma = ref.get('id_norma', 'N/A')
                relacion = ref.get('relacion', {})
                rel_text = relacion.get('texto', 'Relacionada') if isinstance(relacion, dict) else str(relacion)
                descripcion = ref.get('texto', 'Sin descripción')
                
                # Filtrar por tipo de relación si se especifica
                if relation_type == 'modifies' and 'MODIFICA' not in rel_text.upper():
                    continue
                if relation_type == 'derogates' and 'DEROGA' not in rel_text.upper():
                    continue
                
                output.append(f"- **{rel_text}:** `{id_norma}`")
                output.append(f"  - {descripcion}")
                output.append("")

        # Referencias posteriores (normas que afectan a esta norma)  
        if relation_type in ['all', 'modified_by', 'derogated_by'] and posteriores:
            output.append("## 📝 Normas posteriores que afectan a esta norma")
            output.append("")
            
            for ref in posteriores:
                id_norma = ref.get('id_norma', 'N/A')
                relacion = ref.get('relacion', {})
                rel_text = relacion.get('texto', 'Relacionada') if isinstance(relacion, dict) else str(relacion)
                descripcion = ref.get('texto', 'Sin descripción')
                
                # Filtrar por tipo de relación si se especifica
                if relation_type == 'modified_by' and 'MODIFICA' not in rel_text.upper():
                    continue
                if relation_type == 'derogated_by' and 'DEROGA' not in rel_text.upper():
                    continue
                
                output.append(f"- **{rel_text}:** `{id_norma}`")
                output.append(f"  - {descripcion}")
                output.append("")

        if len(output) <= 2:  # Solo el título
            return f"No se encontraron normas del tipo '{relation_type}' relacionadas con `{law_id}`."

        output.append("---")
        output.append("💡 Use `get_consolidated_law` con cualquiera de los IDs mostrados para obtener más información sobre esas normas.")
        
        return "\n".join(output)