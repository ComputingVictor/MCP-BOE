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
            )
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
            logger.error(f"Error inesperado obteniendo sumario BORME: {e}")
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
                size_kb = sumario_info.get('size_kbytes', 'N/A')
                output.append(f"**Sumario completo PDF:** [{size_kb} KB]({sumario_info['url_pdf']})")
            
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
                    pdf_url = item.get('url_pdf')
                    if pdf_url:
                        size_kb = item.get('size_kbytes', 'N/A')
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
                            'pdf_url': item.get('url_pdf')
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
                size_kb = sumario_info.get('size_kbytes', 'N/A')
                output.append(f"**Sumario completo PDF:** [{size_kb} KB]({sumario_info['url_pdf']})")
            
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
                    pdf_url = item.get('url_pdf')
                    if pdf_url:
                        size_kb = item.get('size_kbytes', 'N/A')
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
            logger