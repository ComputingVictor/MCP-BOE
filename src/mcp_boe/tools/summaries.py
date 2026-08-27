"""
Herramientas MCP para acceso a los sumarios del BOE y BORME.

Este módulo contiene las herramientas que Claude puede usar para consultar
las publicaciones diarias del BOE y del BORME.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import calendar

from mcp.types import TextContent, Tool

from ..utils.http_client import BOEHTTPClient, APIError
from ..models.boe_models import validate_date_format, format_date_for_api

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# `url_pdf` es un OBJETO, no una cadena
# ---------------------------------------------------------------------------
# La API devuelve {"szBytes": "317144", "szKBytes": "310", "texto": "https://…"}.
# Antes se interpolaba directamente en el markdown, así que el enlace del
# sumario salía como `[N/A KB]({'szBytes': '317144', …})`: ni el usuario puede
# pulsarlo ni el modelo puede pasárselo a `read_boe_pdf`, que es justo lo que su
# descripción le dice que haga con el campo url_pdf.
def _pdf_link(raw: Any, fallback_size: Any = None) -> tuple[str | None, str]:
    """Devuelve (url, tamaño_en_kb) a partir de un `url_pdf` en cualquiera de sus
    dos formas: objeto {texto, szKBytes} (JSON) o cadena suelta (XML)."""
    if isinstance(raw, dict):
        url = raw.get("texto") or raw.get("url") or None
        size = raw.get("szKBytes") or raw.get("size_kbytes") or fallback_size or "N/A"
        return url, str(size)
    if isinstance(raw, str) and raw.strip():
        return raw.strip(), str(fallback_size or "N/A")
    return None, str(fallback_size or "N/A")


class SummaryTools:
    """Herramientas para trabajar con sumarios del BOE y BORME."""
    
    def __init__(self, http_client: BOEHTTPClient):
        self.client = http_client

    def get_tools(self) -> List[Tool]:
        """Retorna la lista de herramientas disponibles."""
        return [
            Tool(
                name="get_boe_summary",
                description="Obtiene el sumario del BOE para una fecha específica",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "pattern": "^\\d{8}$",
                            "description": "Fecha en formato AAAAMMDD (ej: '20240529')"
                        },
                        "section_filter": {
                            "type": "string",
                            "enum": ["all", "1", "2A", "2B", "3", "4", "5"],
                            "default": "all",
                            "description": "Filtrar por sección específica (1=Disposiciones generales, 2A=Autoridades y personal, etc.)"
                        },
                        "department_filter": {
                            "type": "string", 
                            "description": "Filtrar por código de departamento específico (ej: '7723' para Jefatura del Estado)"
                        },
                        "include_pdf_links": {
                            "type": "boolean",
                            "default": True,
                            "description": "Incluir enlaces a documentos PDF"
                        },
                        "max_items": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 50,
                            "description": "Número máximo de documentos a mostrar"
                        }
                    },
                    "required": ["date"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_borme_summary", 
                description="Obtiene el sumario del BORME para una fecha específica",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "pattern": "^\\d{8}$",
                            "description": "Fecha en formato AAAAMMDD (ej: '20240529')"
                        },
                        "province_filter": {
                            "type": "string",
                            "description": "Filtrar por provincia específica (código de 2 cifras)"
                        },
                        "include_pdf_links": {
                            "type": "boolean",
                            "default": True,
                            "description": "Incluir enlaces a documentos PDF"
                        },
                        "max_items": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100, 
                            "default": 50,
                            "description": "Número máximo de documentos a mostrar"
                        }
                    },
                    "required": ["date"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="search_recent_boe",
                description="Busca documentos en el BOE de los últimos días",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days_back": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 30,
                            "default": 7,
                            "description": "Número de días hacia atrás para buscar"
                        },
                        "search_terms": {
                            "type": "string",
                            "description": "Términos de búsqueda en títulos de documentos"
                        },
                        "section_filter": {
                            "type": "string",
                            "enum": ["all", "1", "2A", "2B", "3", "4", "5"],
                            "default": "all",
                            "description": "Filtrar por sección específica"
                        },
                        "department_filter": {
                            "type": "string",
                            "description": "Filtrar por código de departamento específico"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_weekly_summary",
                description="Obtiene un resumen semanal de publicaciones del BOE",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "pattern": "^\\d{8}$",
                            "description": "Fecha de inicio de la semana en formato AAAAMMDD"
                        },
                        "include_statistics": {
                            "type": "boolean",
                            "default": True,
                            "description": "Incluir estadísticas de la semana"
                        }
                    },
                    "required": ["start_date"],
                    "additionalProperties": False
                }
            ),
            # --- Nuevas tools (grupo B) ---
            Tool(
                name="get_boe_summary_range",
                description=(
                    "Obtiene y agrega los sumarios del BOE para un rango de fechas. "
                    "Permite ver todas las publicaciones de un período sin llamar a get_boe_summary "
                    "día por día. Máximo 31 días de rango."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_date": {
                            "type": "string",
                            "description": "Fecha de inicio en formato AAAAMMDD o YYYY-MM-DD"
                        },
                        "to_date": {
                            "type": "string",
                            "description": "Fecha de fin en formato AAAAMMDD o YYYY-MM-DD"
                        },
                        "section": {
                            "type": "string",
                            "description": "Filtrar por sección del BOE (ej: '1', '2A', '3'). Omitir para todas."
                        },
                        "max_items": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 500,
                            "default": 100,
                            "description": "Límite total de documentos a devolver (default: 100)"
                        }
                    },
                    "required": ["from_date", "to_date"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="watch_boe_changes",
                description=(
                    "Busca publicaciones recientes del BOE que coincidan con palabras clave, "
                    "mirando hacia atrás un número de días configurable. "
                    "Útil como 'radar normativo' para monitorizar temas de interés."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days_back": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 90,
                            "description": "Número de días hacia atrás para buscar"
                        },
                        "keywords": {
                            "type": "string",
                            "description": "Palabras clave separadas por espacios. Se busca cada palabra de forma independiente (OR)."
                        },
                        "sections": {
                            "type": "string",
                            "description": "Secciones del BOE a incluir, separadas por comas (ej: '1,3'). Omitir para todas."
                        },
                        "max_items": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 200,
                            "default": 50,
                            "description": "Límite total de resultados (default: 50)"
                        }
                    },
                    "required": ["days_back", "keywords"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="group_summary_by_department",
                description=(
                    "Obtiene el sumario del BOE para un rango de fechas y agrupa las publicaciones "
                    "por departamento emisor, mostrando cuántas y cuáles disposiciones emitió cada uno."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_date": {
                            "type": "string",
                            "description": "Fecha de inicio en formato AAAAMMDD o YYYY-MM-DD"
                        },
                        "to_date": {
                            "type": "string",
                            "description": "Fecha de fin en formato AAAAMMDD o YYYY-MM-DD"
                        },
                        "sections": {
                            "type": "string",
                            "description": "Secciones del BOE a incluir, separadas por comas. Omitir para todas."
                        },
                        "max_items_per_dept": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10,
                            "description": "Máximo de documentos a mostrar por departamento (default: 10)"
                        }
                    },
                    "required": ["from_date", "to_date"],
                    "additionalProperties": False
                }
            ),
        ]

    async def get_boe_summary(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene el sumario del BOE para una fecha específica.
        
        Args:
            arguments: Parámetros de la consulta
            
        Returns:
            Lista de contenido con el sumario del BOE
        """
        try:
            date = arguments['date']
            section_filter = arguments.get('section_filter', 'all')
            department_filter = arguments.get('department_filter')
            include_pdf_links = arguments.get('include_pdf_links', True)
            max_items = arguments.get('max_items', 50)

            # Validar fecha
            if not validate_date_format(date):
                raise ValueError(f"Formato de fecha inválido: {date}")

            logger.info(f"Obteniendo sumario BOE para {date}")

            # Obtener sumario
            response = await self.client.get_boe_summary(date)
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text=f"No se encontró sumario del BOE para la fecha {date}. Verifique que sea una fecha de publicación válida (días laborables)."
                )]

            summary_data = response['data']['sumario']
            formatted_summary = self._format_boe_summary(
                summary_data, 
                date, 
                section_filter,
                department_filter,
                include_pdf_links,
                max_items
            )

            return [TextContent(
                type="text",
                text=formatted_summary
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo sumario BOE {date}: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo al sumario del BOE: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo sumario BOE: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_borme_summary(
        self, 
        summary_data: Dict[str, Any], 
        date: str,
        province_filter: Optional[str],
        include_pdf_links: bool,
        max_items: int
    ) -> str:
        """Formatea el sumario del BORME."""
        output = []
        
        # Formatear fecha para mostrar
        try:
            date_obj = datetime.strptime(date, '%Y%m%d')
            formatted_date = date_obj.strftime('%d de %B de %Y')
            day_name = calendar.day_name[date_obj.weekday()]
        except ValueError:
            formatted_date = date
            day_name = ""

        output.append(f"# 🏢 BORME del {formatted_date}")
        if day_name:
            output.append(f"*{day_name}*")
        output.append("")

        # Información general
        diarios = summary_data.get('diario', [])
        if not isinstance(diarios, list):
            diarios = [diarios]

        total_docs = 0
        for diario in diarios:
            numero_diario = diario.get('numero', 'N/A')
            output.append(f"**Número de diario:** {numero_diario}")
            
            # URL del sumario completo
            sumario_info = diario.get('sumario_diario', {})
            if include_pdf_links and sumario_info.get('url_pdf'):
                pdf_url, size_kb = _pdf_link(sumario_info.get('url_pdf'), sumario_info.get('size_kbytes'))
                if pdf_url:
                    output.append(f"**Sumario completo PDF:** [{size_kb} KB]({pdf_url})")
            
            output.append("")

            # Procesar secciones (provincias en BORME)
            secciones = diario.get('seccion', [])
            if not isinstance(secciones, list):
                secciones = [secciones]

            items_shown = 0
            for seccion in secciones:
                seccion_codigo = seccion.get('codigo', '')
                seccion_nombre = seccion.get('nombre', f'Provincia {seccion_codigo}')
                
                # Aplicar filtro de provincia
                if province_filter and seccion_codigo != province_filter:
                    continue

                section_items = []
                departamentos = seccion.get('departamento', [])
                if not isinstance(departamentos, list):
                    departamentos = [departamentos]

                for departamento in departamentos:
                    dept_codigo = departamento.get('codigo', '')
                    dept_nombre = departamento.get('nombre', f'Registro {dept_codigo}')
                    
                    # Procesar documentos del departamento (registro mercantil)
                    dept_items = self._process_borme_department_items(
                        departamento, 
                        dept_nombre, 
                        include_pdf_links
                    )
                    
                    if dept_items and items_shown < max_items:
                        section_items.extend(dept_items[:max_items - items_shown])
                        items_shown += len(dept_items[:max_items - items_shown])

                if section_items:
                    output.append(f"## {seccion_nombre}")
                    output.append("")
                    output.extend(section_items)
                    output.append("")

                total_docs += len(section_items)

        if total_docs == 0:
            if province_filter:
                output.append(f"No se encontraron documentos de la provincia {province_filter}.")
            else:
                output.append("No se encontraron documentos en este BORME.")
        else:
            output.append("---")
            output.append(f"**Total mostrado:** {min(total_docs, max_items)} documento(s)")
            if total_docs > max_items:
                output.append(f"*(Se omitieron {total_docs - max_items} documentos adicionales)*")

        return "\n".join(output)

    def _process_borme_department_items(
        self, 
        departamento: Dict[str, Any], 
        dept_nombre: str,
        include_pdf_links: bool
    ) -> List[str]:
        """Procesa los documentos de un registro mercantil en BORME."""
        items = []
        
        # Documentos del registro mercantil
        direct_items = departamento.get('item', [])
        if not isinstance(direct_items, list):
            direct_items = [direct_items] if direct_items else []

        if direct_items:
            items.append(f"### {dept_nombre}")
            items.append("")

            for item in direct_items:
                titulo = item.get('titulo', 'Sin título')
                identificador = item.get('identificador', 'N/A')
                
                # El BORME típicamente tiene información de empresas
                items.append(f"- **{titulo}**")
                items.append(f"  - ID: `{identificador}`")
                
                if include_pdf_links:
                    pdf_url, size_kb = _pdf_link(item.get('url_pdf'), item.get('size_kbytes'))
                    if pdf_url:
                        items.append(f"  - PDF: [{size_kb} KB]({pdf_url})")
                
                # Información específica del BORME
                html_url = item.get('url_html')
                if html_url:
                    items.append(f"  - HTML: {html_url}")
                
                items.append("")

        return items

    async def search_recent_boe(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Busca documentos en el BOE de los últimos días.
        
        Args:
            arguments: Parámetros de búsqueda
            
        Returns:
            Lista de contenido con los documentos encontrados
        """
        try:
            days_back = arguments.get('days_back', 7)
            search_terms = arguments.get('search_terms')
            section_filter = arguments.get('section_filter', 'all')
            department_filter = arguments.get('department_filter')

            logger.info(f"Buscando en BOE últimos {days_back} días")

            # Calcular fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            output = []
            output.append(f"# 🔍 Búsqueda en BOE - Últimos {days_back} días")
            output.append(f"**Desde:** {start_date.strftime('%d/%m/%Y')} **hasta:** {end_date.strftime('%d/%m/%Y')}")
            output.append("")

            found_documents = []
            current_date = start_date

            # Buscar día por día (excluyendo domingos que no hay BOE)
            while current_date <= end_date:
                if current_date.weekday() != 6:  # No domingo
                    date_str = current_date.strftime('%Y%m%d')
                    
                    try:
                        response = await self.client.get_boe_summary(date_str)
                        if response.get('data'):
                            day_docs = self._extract_matching_documents(
                                response['data']['sumario'],
                                date_str,
                                search_terms,
                                section_filter,
                                department_filter
                            )
                            found_documents.extend(day_docs)
                    except APIError:
                        # Fecha sin BOE (festivos, etc.)
                        pass
                
                current_date += timedelta(days=1)

            if not found_documents:
                search_desc = f"términos '{search_terms}'" if search_terms else "criterios especificados"
                output.append(f"No se encontraron documentos que coincidan con {search_desc} en los últimos {days_back} días.")
            else:
                output.append(f"**Encontrados {len(found_documents)} documento(s):**")
                output.append("")
                
                # Agrupar por fecha
                docs_by_date = {}
                for doc in found_documents:
                    date_key = doc['fecha']
                    if date_key not in docs_by_date:
                        docs_by_date[date_key] = []
                    docs_by_date[date_key].append(doc)

                # Mostrar por fecha (más reciente primero)
                for date_key in sorted(docs_by_date.keys(), reverse=True):
                    docs = docs_by_date[date_key]
                    try:
                        date_obj = datetime.strptime(date_key, '%Y%m%d')
                        formatted_date = date_obj.strftime('%d de %B de %Y')
                    except ValueError:
                        formatted_date = date_key
                    
                    output.append(f"## {formatted_date}")
                    output.append("")
                    
                    for doc in docs:
                        output.append(f"- **{doc['titulo']}**")
                        output.append(f"  - ID: `{doc['identificador']}`")
                        output.append(f"  - Departamento: {doc['departamento']}")
                        if doc['seccion']:
                            output.append(f"  - Sección: {doc['seccion']}")
                        if doc.get('pdf_url'):
                            output.append(f"  - PDF: {doc['pdf_url']}")
                        output.append("")

            return [TextContent(
                type="text",
                text="\n".join(output)
            )]

        except Exception as e:
            logger.error(f"Error buscando en BOE reciente: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _extract_matching_documents(
        self,
        summary_data: Dict[str, Any],
        date_str: str,
        search_terms: Optional[str],
        section_filter: str,
        department_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Extrae documentos que coinciden con los criterios de búsqueda."""
        matching_docs = []
        
        diarios = summary_data.get('diario', [])
        if not isinstance(diarios, list):
            diarios = [diarios]

        for diario in diarios:
            secciones = diario.get('seccion', [])
            if not isinstance(secciones, list):
                secciones = [secciones]

            for seccion in secciones:
                seccion_codigo = seccion.get('codigo', '')
                seccion_nombre = seccion.get('nombre', '')
                
                # Aplicar filtro de sección
                if section_filter != 'all' and seccion_codigo != section_filter:
                    continue

                departamentos = seccion.get('departamento', [])
                if not isinstance(departamentos, list):
                    departamentos = [departamentos]

                for departamento in departamentos:
                    dept_codigo = departamento.get('codigo', '')
                    dept_nombre = departamento.get('nombre', '')
                    
                    # Aplicar filtro de departamento
                    if department_filter and dept_codigo != department_filter:
                        continue

                    # Procesar documentos
                    all_items = []
                    
                    # Documentos directos
                    direct_items = departamento.get('item', [])
                    if not isinstance(direct_items, list):
                        direct_items = [direct_items] if direct_items else []
                    all_items.extend(direct_items)
                    
                    # Documentos en epígrafes
                    epigrafes = departamento.get('epigrafe', [])
                    if not isinstance(epigrafes, list):
                        epigrafes = [epigrafes] if epigrafes else []
                    
                    for epigrafe in epigrafes:
                        epi_items = epigrafe.get('item', [])
                        if not isinstance(epi_items, list):
                            epi_items = [epi_items] if epi_items else []
                        all_items.extend(epi_items)

                    # Filtrar por términos de búsqueda
                    for item in all_items:
                        titulo = item.get('titulo', '')
                        
                        # Si hay términos de búsqueda, verificar coincidencia
                        if search_terms:
                            search_lower = search_terms.lower()
                            if search_lower not in titulo.lower():
                                continue

                        matching_docs.append({
                            'fecha': date_str,
                            'titulo': titulo,
                            'identificador': item.get('identificador', 'N/A'),
                            'departamento': dept_nombre,
                            'seccion': seccion_nombre,
                            'pdf_url': _pdf_link(item.get('url_pdf'))[0]
                        })

        return matching_docs

    async def get_weekly_summary(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene un resumen semanal de publicaciones del BOE.
        
        Args:
            arguments: Parámetros de la consulta
            
        Returns:
            Lista de contenido con el resumen semanal
        """
        try:
            start_date_str = arguments['start_date']
            include_statistics = arguments.get('include_statistics', True)

            # Validar fecha
            if not validate_date_format(start_date_str):
                raise ValueError(f"Formato de fecha inválido: {start_date_str}")

            start_date = datetime.strptime(start_date_str, '%Y%m%d')
            end_date = start_date + timedelta(days=6)  # Semana completa

            logger.info(f"Obteniendo resumen semanal desde {start_date_str}")

            output = []
            output.append(f"# 📅 Resumen semanal del BOE")
            output.append(f"**Semana del {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}**")
            output.append("")

            # Recopilar datos de toda la semana
            weekly_data = {
                'total_documents': 0,
                'days_with_boe': 0,
                'sections': {},
                'departments': {},
                'documents_by_day': {}
            }

            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() != 6:  # No domingo
                    date_str = current_date.strftime('%Y%m%d')
                    day_name = calendar.day_name[current_date.weekday()]
                    
                    try:
                        response = await self.client.get_boe_summary(date_str)
                        if response.get('data'):
                            day_stats = self._analyze_day_summary(response['data']['sumario'])
                            weekly_data['documents_by_day'][day_name] = day_stats
                            weekly_data['total_documents'] += day_stats['total']
                            weekly_data['days_with_boe'] += 1
                            
                            # Acumular estadísticas
                            for section, count in day_stats['sections'].items():
                                weekly_data['sections'][section] = weekly_data['sections'].get(section, 0) + count
                            
                            for dept, count in day_stats['departments'].items():
                                weekly_data['departments'][dept] = weekly_data['departments'].get(dept, 0) + count
                    except APIError:
                        # Día sin BOE
                        weekly_data['documents_by_day'][day_name] = {'total': 0, 'sections': {}, 'departments': {}}
                
                current_date += timedelta(days=1)

            # Formatear resumen
            if weekly_data['total_documents'] == 0:
                output.append("No se encontraron publicaciones del BOE en esta semana.")
            else:
                # Resumen general
                output.append("## 📊 Resumen general")
                output.append(f"- **Total de documentos:** {weekly_data['total_documents']}")
                output.append(f"- **Días con publicación:** {weekly_data['days_with_boe']}")
                avg_docs = weekly_data['total_documents'] / max(weekly_data['days_with_boe'], 1)
                output.append(f"- **Promedio diario:** {avg_docs:.1f} documentos")
                output.append("")

                # Documentos por día
                output.append("## 📈 Distribución diaria")
                for day_name, day_data in weekly_data['documents_by_day'].items():
                    total = day_data['total']
                    if total > 0:
                        output.append(f"- **{day_name}:** {total} documentos")
                    else:
                        output.append(f"- **{day_name}:** Sin publicación")
                output.append("")

                if include_statistics:
                    # Top secciones
                    if weekly_data['sections']:
                        output.append("## 📋 Secciones más activas")
                        top_sections = sorted(weekly_data['sections'].items(), key=lambda x: x[1], reverse=True)[:5]
                        for section, count in top_sections:
                            output.append(f"- **{section}:** {count} documentos")
                        output.append("")

                    # Top departamentos
                    if weekly_data['departments']:
                        output.append("## 🏛️ Departamentos más activos")
                        top_depts = sorted(weekly_data['departments'].items(), key=lambda x: x[1], reverse=True)[:5]
                        for dept, count in top_depts:
                            # Truncar nombres muy largos
                            dept_name = dept if len(dept) <= 50 else f"{dept[:47]}..."
                            output.append(f"- **{dept_name}:** {count} documentos")
                        output.append("")

            return [TextContent(
                type="text",
                text="\n".join(output)
            )]

        except Exception as e:
            logger.error(f"Error obteniendo resumen semanal: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _analyze_day_summary(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el sumario de un día para extraer estadísticas."""
        stats = {
            'total': 0,
            'sections': {},
            'departments': {}
        }

        diarios = summary_data.get('diario', [])
        if not isinstance(diarios, list):
            diarios = [diarios]

        for diario in diarios:
            secciones = diario.get('seccion', [])
            if not isinstance(secciones, list):
                secciones = [secciones]

            for seccion in secciones:
                seccion_nombre = seccion.get('nombre', 'Sin nombre')
                section_docs = 0

                departamentos = seccion.get('departamento', [])
                if not isinstance(departamentos, list):
                    departamentos = [departamentos]

                for departamento in departamentos:
                    dept_nombre = departamento.get('nombre', 'Sin nombre')
                    dept_docs = 0

                    # Contar documentos directos
                    direct_items = departamento.get('item', [])
                    if not isinstance(direct_items, list):
                        direct_items = [direct_items] if direct_items else []
                    dept_docs += len(direct_items)

                    # Contar documentos en epígrafes
                    epigrafes = departamento.get('epigrafe', [])
                    if not isinstance(epigrafes, list):
                        epigrafes = [epigrafes] if epigrafes else []
                    
                    for epigrafe in epigrafes:
                        epi_items = epigrafe.get('item', [])
                        if not isinstance(epi_items, list):
                            epi_items = [epi_items] if epi_items else []
                        dept_docs += len(epi_items)

                    section_docs += dept_docs
                    if dept_docs > 0:
                        stats['departments'][dept_nombre] = stats['departments'].get(dept_nombre, 0) + dept_docs

                if section_docs > 0:
                    stats['sections'][seccion_nombre] = stats['sections'].get(seccion_nombre, 0) + section_docs

                stats['total'] += section_docs

        return stats

    def _handle_summary_error(self, e: Exception) -> List[TextContent]:
        """Maneja errores al obtener el sumario del BOE."""
        logger.error(f"Error inesperado obteniendo sumario BOE: {e}")
        return [TextContent(
            type="text",
            text=f"Error interno: {str(e)}"
        )]

    def _format_boe_summary(
        self, 
        summary_data: Dict[str, Any], 
        date: str,
        section_filter: str,
        department_filter: Optional[str],
        include_pdf_links: bool,
        max_items: int
    ) -> str:
        """Formatea el sumario del BOE."""
        output = []
        
        # Formatear fecha para mostrar
        try:
            date_obj = datetime.strptime(date, '%Y%m%d')
            formatted_date = date_obj.strftime('%d de %B de %Y')
            day_name = calendar.day_name[date_obj.weekday()]
        except ValueError:
            formatted_date = date
            day_name = ""

        output.append(f"# 📰 BOE del {formatted_date}")
        if day_name:
            output.append(f"*{day_name}*")
        output.append("")

        # Información general
        diarios = summary_data.get('diario', [])
        if not isinstance(diarios, list):
            diarios = [diarios]

        total_docs = 0
        for diario in diarios:
            numero_diario = diario.get('numero', 'N/A')
            output.append(f"**Número de diario:** {numero_diario}")
            
            # URL del sumario completo
            sumario_info = diario.get('sumario_diario', {})
            if include_pdf_links and sumario_info.get('url_pdf'):
                pdf_url, size_kb = _pdf_link(sumario_info.get('url_pdf'), sumario_info.get('size_kbytes'))
                if pdf_url:
                    output.append(f"**Sumario completo PDF:** [{size_kb} KB]({pdf_url})")
            
            output.append("")

            # Procesar secciones
            secciones = diario.get('seccion', [])
            if not isinstance(secciones, list):
                secciones = [secciones]

            items_shown = 0
            for seccion in secciones:
                seccion_codigo = seccion.get('codigo', '')
                seccion_nombre = seccion.get('nombre', f'Sección {seccion_codigo}')
                
                # Aplicar filtro de sección
                if section_filter != 'all' and seccion_codigo != section_filter:
                    continue

                section_items = []
                departamentos = seccion.get('departamento', [])
                if not isinstance(departamentos, list):
                    departamentos = [departamentos]

                for departamento in departamentos:
                    dept_codigo = departamento.get('codigo', '')
                    dept_nombre = departamento.get('nombre', f'Departamento {dept_codigo}')
                    
                    # Aplicar filtro de departamento
                    if department_filter and dept_codigo != department_filter:
                        continue

                    # Procesar documentos del departamento
                    dept_items = self._process_department_items(
                        departamento, 
                        dept_nombre, 
                        include_pdf_links
                    )
                    
                    if dept_items and items_shown < max_items:
                        section_items.extend(dept_items[:max_items - items_shown])
                        items_shown += len(dept_items[:max_items - items_shown])

                if section_items:
                    output.append(f"## {seccion_nombre}")
                    output.append("")
                    output.extend(section_items)
                    output.append("")

                total_docs += len(section_items)

        if total_docs == 0:
            if section_filter != 'all':
                output.append(f"No se encontraron documentos en la sección {section_filter}.")
            elif department_filter:
                output.append(f"No se encontraron documentos del departamento {department_filter}.")
            else:
                output.append("No se encontraron documentos en este BOE.")
        else:
            output.append("---")
            output.append(f"**Total mostrado:** {min(total_docs, max_items)} documento(s)")
            if total_docs > max_items:
                output.append(f"*(Se omitieron {total_docs - max_items} documentos adicionales)*")

        return "\n".join(output)

    def _process_department_items(
        self, 
        departamento: Dict[str, Any], 
        dept_nombre: str,
        include_pdf_links: bool
    ) -> List[str]:
        """Procesa los documentos de un departamento."""
        items = []
        
        # Documentos directos del departamento
        direct_items = departamento.get('item', [])
        if not isinstance(direct_items, list):
            direct_items = [direct_items] if direct_items else []

        # Documentos en epígrafes
        epigrafe_items = []
        epigrafes = departamento.get('epigrafe', [])
        if not isinstance(epigrafes, list):
            epigrafes = [epigrafes] if epigrafes else []

        for epigrafe in epigrafes:
            epigrafe_nombre = epigrafe.get('nombre', 'Sin nombre')
            epi_items = epigrafe.get('item', [])
            if not isinstance(epi_items, list):
                epi_items = [epi_items] if epi_items else []
            
            for item in epi_items:
                item['_epigrafe'] = epigrafe_nombre
                epigrafe_items.append(item)

        all_items = direct_items + epigrafe_items

        if all_items:
            items.append(f"### {dept_nombre}")
            items.append("")

            for item in all_items:
                titulo = item.get('titulo', 'Sin título')
                identificador = item.get('identificador', 'N/A')
                epigrafe_name = item.get('_epigrafe')
                
                items.append(f"- **{titulo}**")
                items.append(f"  - ID: `{identificador}`")
                
                if epigrafe_name:
                    items.append(f"  - Epígrafe: {epigrafe_name}")
                
                if include_pdf_links:
                    pdf_url, size_kb = _pdf_link(item.get('url_pdf'), item.get('size_kbytes'))
                    if pdf_url:
                        paginas = ""
                        pag_ini = item.get('pagina_inicial')
                        pag_fin = item.get('pagina_final')
                        if pag_ini and pag_fin:
                            paginas = f" (págs. {pag_ini}-{pag_fin})"
                        items.append(f"  - PDF: [{size_kb} KB{paginas}]({pdf_url})")
                
                items.append("")

        return items

    async def get_borme_summary(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene el sumario del BORME para una fecha específica.
        
        Args:
            arguments: Parámetros de la consulta
            
        Returns:
            Lista de contenido con el sumario del BORME
        """
        try:
            date = arguments['date']
            province_filter = arguments.get('province_filter')
            include_pdf_links = arguments.get('include_pdf_links', True)
            max_items = arguments.get('max_items', 50)

            # Validar fecha
            if not validate_date_format(date):
                raise ValueError(f"Formato de fecha inválido: {date}")

            logger.info(f"Obteniendo sumario BORME para {date}")

            # Obtener sumario
            response = await self.client.get_borme_summary(date)
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text=f"No se encontró sumario del BORME para la fecha {date}. Verifique que sea una fecha de publicación válida."
                )]

            summary_data = response['data']['sumario']
            formatted_summary = self._format_borme_summary(
                summary_data, 
                date, 
                province_filter,
                include_pdf_links,
                max_items
            )

            return [TextContent(
                type="text",
                text=formatted_summary
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo sumario BORME {date}: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo al sumario del BORME: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo sumario BORME: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    # =========================================================================
    # get_boe_summary_range
    # =========================================================================

    async def get_boe_summary_range(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Obtiene y agrega los sumarios del BOE para un rango de fechas.

        Itera sobre cada día del rango (excluyendo domingos), recoge los documentos
        y aplica filtros opcionales de sección y límite total.

        Args:
            arguments: Diccionario con from_date, to_date, section y max_items.

        Returns:
            TextContent con los documentos del rango agrupados por fecha.
        """
        try:
            from_date_raw = arguments['from_date']
            to_date_raw = arguments['to_date']
            section = arguments.get('section')
            max_items = arguments.get('max_items', 100)

            from_date = format_date_for_api(from_date_raw)
            to_date = format_date_for_api(to_date_raw)

            if from_date > to_date:
                raise ValueError("from_date debe ser anterior o igual a to_date.")

            start_dt = datetime.strptime(from_date, '%Y%m%d')
            end_dt = datetime.strptime(to_date, '%Y%m%d')
            delta_days = (end_dt - start_dt).days

            if delta_days > 31:
                raise ValueError(
                    f"El rango máximo es de 31 días. Se solicitaron {delta_days} días. "
                    "Usa rangos más cortos o itera manualmente."
                )

            logger.info(f"Obteniendo sumario BOE rango {from_date}–{to_date}, sección={section}")

            all_docs: List[Dict[str, Any]] = []
            current_dt = start_dt
            truncated = False

            while current_dt <= end_dt:
                if current_dt.weekday() == 6:  # domingo sin BOE
                    current_dt += timedelta(days=1)
                    continue

                date_str = current_dt.strftime('%Y%m%d')
                try:
                    response = await self.client.get_boe_summary(date_str)
                    if response.get('data'):
                        day_docs = self._extract_matching_documents(
                            response['data']['sumario'],
                            date_str,
                            search_terms=None,
                            section_filter=section or 'all',
                            department_filter=None
                        )
                        all_docs.extend(day_docs)
                        if len(all_docs) >= max_items:
                            all_docs = all_docs[:max_items]
                            truncated = True
                            break
                except APIError:
                    pass  # Día sin BOE (festivo, etc.)

                current_dt += timedelta(days=1)

            formatted = self._format_range_summary(all_docs, from_date_raw, to_date_raw, truncated, max_items)
            return [TextContent(type="text", text=formatted)]

        except ValueError as e:
            return [TextContent(type="text", text=f"Parámetros inválidos: {str(e)}")]
        except Exception as e:
            logger.error(f"Error obteniendo sumario por rango: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _format_range_summary(
        self,
        docs: List[Dict[str, Any]],
        from_date: str,
        to_date: str,
        truncated: bool,
        max_items: int
    ) -> str:
        """Formatea el sumario de un rango de fechas."""
        output = [
            f"# 📰 Sumario BOE del {from_date} al {to_date}",
            "",
        ]

        if not docs:
            output.append("No se encontraron documentos en el rango especificado.")
            return "\n".join(output)

        output.append(f"**{len(docs)} documento(s) encontrado(s)**{'  *(resultado truncado)*' if truncated else ''}")
        output.append("")

        # Agrupar por fecha
        by_date: Dict[str, List[Dict]] = {}
        for doc in docs:
            by_date.setdefault(doc['fecha'], []).append(doc)

        for date_key in sorted(by_date.keys()):
            try:
                date_obj = datetime.strptime(date_key, '%Y%m%d')
                formatted_date = date_obj.strftime('%d/%m/%Y')
            except ValueError:
                formatted_date = date_key

            output.append(f"## {formatted_date} ({len(by_date[date_key])} docs)")
            output.append("")
            for doc in by_date[date_key]:
                output.append(f"- **{doc['titulo']}**")
                output.append(f"  - ID: `{doc['identificador']}` · {doc['departamento']}")
                if doc.get('pdf_url'):
                    output.append(f"  - PDF: {doc['pdf_url']}")
                output.append("")

        if truncated:
            output.append(f"⚠️ Se alcanzó el límite de {max_items} documentos. Reduce el rango o aumenta max_items.")

        return "\n".join(output)

    # =========================================================================
    # watch_boe_changes
    # =========================================================================

    async def watch_boe_changes(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Busca publicaciones recientes del BOE que coincidan con palabras clave.

        Args:
            arguments: Diccionario con days_back, keywords, sections y max_items.

        Returns:
            TextContent con las publicaciones relevantes encontradas.
        """
        try:
            days_back = arguments['days_back']
            keywords_raw = arguments['keywords']
            sections_raw = arguments.get('sections', '')
            max_items = arguments.get('max_items', 50)

            # Parsear keywords
            keywords = [k.strip() for k in keywords_raw.replace(',', ' ').split() if k.strip()]
            if not keywords:
                raise ValueError("Debes proporcionar al menos una palabra clave.")

            # Parsear secciones
            section_set: Optional[set] = None
            if sections_raw:
                section_set = {s.strip() for s in sections_raw.split(',') if s.strip()}

            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days_back)

            logger.info(f"watch_boe_changes: {days_back} días, keywords={keywords}, sections={section_set}")

            found_docs: List[Dict[str, Any]] = []
            current_dt = start_dt

            while current_dt <= end_dt and len(found_docs) < max_items:
                if current_dt.weekday() == 6:
                    current_dt += timedelta(days=1)
                    continue

                date_str = current_dt.strftime('%Y%m%d')
                try:
                    response = await self.client.get_boe_summary(date_str)
                    if response.get('data'):
                        for kw in keywords:
                            day_docs = self._extract_matching_documents(
                                response['data']['sumario'],
                                date_str,
                                search_terms=kw,
                                section_filter='all',
                                department_filter=None
                            )
                            # Filtrar secciones si se indicaron
                            if section_set:
                                day_docs = [
                                    d for d in day_docs
                                    if any(sec in d.get('seccion', '') for sec in section_set)
                                ]
                            for d in day_docs:
                                # Evitar duplicados por identificador
                                if not any(
                                    existing['identificador'] == d['identificador']
                                    for existing in found_docs
                                ):
                                    d['matched_keyword'] = kw
                                    found_docs.append(d)
                                    if len(found_docs) >= max_items:
                                        break
                            if len(found_docs) >= max_items:
                                break
                except APIError:
                    pass

                current_dt += timedelta(days=1)

            formatted = self._format_watch_results(
                found_docs, days_back, keywords,
                max_items, len(found_docs) >= max_items
            )
            return [TextContent(type="text", text=formatted)]

        except ValueError as e:
            return [TextContent(type="text", text=f"Parámetros inválidos: {str(e)}")]
        except Exception as e:
            logger.error(f"Error en watch_boe_changes: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _format_watch_results(
        self,
        docs: List[Dict[str, Any]],
        days_back: int,
        keywords: List[str],
        max_items: int,
        truncated: bool
    ) -> str:
        """Formatea los resultados del radar normativo."""
        kw_str = ', '.join(f'«{k}»' for k in keywords)
        output = [
            f"# 📡 Radar normativo — últimos {days_back} días",
            f"**Palabras clave:** {kw_str}",
            "",
        ]

        if not docs:
            output.append(
                f"No se encontraron publicaciones del BOE relacionadas con {kw_str} "
                f"en los últimos {days_back} días."
            )
            return "\n".join(output)

        output.append(
            f"**{len(docs)} resultado(s)**{'  *(truncado a ' + str(max_items) + ')*' if truncated else ''}"
        )
        output.append("")

        # Agrupar por fecha (más reciente primero)
        by_date: Dict[str, List[Dict]] = {}
        for doc in docs:
            by_date.setdefault(doc['fecha'], []).append(doc)

        for date_key in sorted(by_date.keys(), reverse=True):
            try:
                date_obj = datetime.strptime(date_key, '%Y%m%d')
                formatted_date = date_obj.strftime('%d/%m/%Y')
            except ValueError:
                formatted_date = date_key

            output.append(f"## {formatted_date}")
            for doc in by_date[date_key]:
                kw_match = doc.get('matched_keyword', '')
                output.append(f"- **{doc['titulo']}**")
                output.append(f"  - ID: `{doc['identificador']}` · {doc['departamento']}")
                if kw_match:
                    output.append(f"  - *Coincidencia: «{kw_match}»*")
                if doc.get('pdf_url'):
                    output.append(f"  - PDF: {doc['pdf_url']}")
                output.append("")

        return "\n".join(output)

    # =========================================================================
    # group_summary_by_department
    # =========================================================================

    async def group_summary_by_department(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Obtiene el sumario de un rango de fechas y agrupa por departamento emisor.

        Args:
            arguments: Diccionario con from_date, to_date, sections y max_items_per_dept.

        Returns:
            TextContent con los departamentos ordenados por número de publicaciones.
        """
        try:
            from_date_raw = arguments['from_date']
            to_date_raw = arguments['to_date']
            sections_raw = arguments.get('sections', '')
            max_items_per_dept = arguments.get('max_items_per_dept', 10)

            from_date = format_date_for_api(from_date_raw)
            to_date = format_date_for_api(to_date_raw)

            if from_date > to_date:
                raise ValueError("from_date debe ser anterior o igual a to_date.")

            start_dt = datetime.strptime(from_date, '%Y%m%d')
            end_dt = datetime.strptime(to_date, '%Y%m%d')
            delta_days = (end_dt - start_dt).days

            if delta_days > 31:
                raise ValueError(f"El rango máximo es de 31 días (se solicitaron {delta_days}).")

            section_set: Optional[set] = None
            if sections_raw:
                section_set = {s.strip() for s in sections_raw.split(',') if s.strip()}

            logger.info(f"group_summary_by_department: {from_date}–{to_date}, sections={section_set}")

            # Recoger todos los documentos del rango
            all_docs: List[Dict[str, Any]] = []
            current_dt = start_dt

            while current_dt <= end_dt:
                if current_dt.weekday() == 6:
                    current_dt += timedelta(days=1)
                    continue

                date_str = current_dt.strftime('%Y%m%d')
                try:
                    response = await self.client.get_boe_summary(date_str)
                    if response.get('data'):
                        day_docs = self._extract_matching_documents(
                            response['data']['sumario'],
                            date_str,
                            search_terms=None,
                            section_filter='all',
                            department_filter=None
                        )
                        if section_set:
                            day_docs = [
                                d for d in day_docs
                                if any(sec in d.get('seccion', '') for sec in section_set)
                            ]
                        all_docs.extend(day_docs)
                except APIError:
                    pass

                current_dt += timedelta(days=1)

            formatted = self._format_grouped_by_department(
                all_docs, from_date_raw, to_date_raw, max_items_per_dept
            )
            return [TextContent(type="text", text=formatted)]

        except ValueError as e:
            return [TextContent(type="text", text=f"Parámetros inválidos: {str(e)}")]
        except Exception as e:
            logger.error(f"Error en group_summary_by_department: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _format_grouped_by_department(
        self,
        docs: List[Dict[str, Any]],
        from_date: str,
        to_date: str,
        max_items_per_dept: int
    ) -> str:
        """Formatea los documentos agrupados por departamento."""
        output = [
            f"# 🏛️ Publicaciones BOE por departamento ({from_date} – {to_date})",
            "",
        ]

        if not docs:
            output.append("No se encontraron publicaciones en el rango especificado.")
            return "\n".join(output)

        # Agrupar por departamento
        by_dept: Dict[str, List[Dict]] = {}
        for doc in docs:
            dept = doc.get('departamento', 'Sin departamento')
            by_dept.setdefault(dept, []).append(doc)

        # Ordenar departamentos por número de documentos (descendente)
        sorted_depts = sorted(by_dept.items(), key=lambda x: len(x[1]), reverse=True)

        output.append(
            f"**{len(docs)} documentos · {len(sorted_depts)} departamentos**"
        )
        output.append("")

        for dept_name, dept_docs in sorted_depts:
            output.append(f"## {dept_name} ({len(dept_docs)} docs)")
            output.append("")

            for doc in dept_docs[:max_items_per_dept]:
                output.append(f"- **{doc['titulo']}**")
                output.append(f"  - ID: `{doc['identificador']}` · {doc['fecha']}")
                if doc.get('pdf_url'):
                    output.append(f"  - PDF: {doc['pdf_url']}")
                output.append("")

            if len(dept_docs) > max_items_per_dept:
                output.append(
                    f"  *(y {len(dept_docs) - max_items_per_dept} más — "
                    "aumenta max_items_per_dept para ver todos)*"
                )
                output.append("")

        return "\n".join(output)