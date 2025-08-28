"""
Herramienta MCP para acceso rápido a leyes españolas comunes.

Este módulo proporciona acceso directo a las normas más importantes
sin necesidad de búsquedas en la API.
"""

import logging
from typing import Dict, Any, List
from mcp.types import TextContent, Tool

from ..data.common_laws import (
    COMMON_LAWS,
    LAW_CATEGORIES,
    get_laws_by_category,
    search_laws_by_keyword,
    get_recent_laws
)

logger = logging.getLogger(__name__)


class CommonLawsTools:
    """Herramientas para acceso rápido a leyes comunes."""
    
    def __init__(self):
        pass
    
    def get_tools(self) -> List[Tool]:
        """Retorna la lista de herramientas disponibles."""
        return [
            Tool(
                name="list_common_laws",
                description="Lista las leyes españolas más importantes y frecuentemente consultadas",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["all"] + list(LAW_CATEGORIES.keys()),
                            "default": "all",
                            "description": "Categoría de leyes a listar (fundamental, organica, civil, laboral, etc.)"
                        },
                        "show_descriptions": {
                            "type": "boolean",
                            "default": True,
                            "description": "Mostrar descripciones de las leyes"
                        }
                    },
                    "additionalProperties": False
                }
            ),
            Tool(
                name="search_common_laws",
                description="Busca en el diccionario de leyes comunes por palabra clave",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Palabra clave para buscar en títulos y descripciones"
                        }
                    },
                    "required": ["keyword"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_recent_important_laws",
                description="Obtiene las leyes importantes más recientes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "years_back": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 20,
                            "default": 5,
                            "description": "Número de años hacia atrás desde hoy"
                        }
                    },
                    "additionalProperties": False
                }
            )
        ]
    
    async def list_common_laws(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Lista las leyes comunes por categoría.
        
        Args:
            arguments: Parámetros de filtrado
            
        Returns:
            Lista de contenido con las leyes
        """
        try:
            category = arguments.get('category', 'all')
            show_descriptions = arguments.get('show_descriptions', True)
            
            output = []
            output.append("# 📚 Leyes Españolas Importantes")
            output.append("")
            output.append("Identificadores BOE de las normas más consultadas del ordenamiento jurídico español.")
            output.append("")
            
            if category == 'all':
                # Mostrar todas las leyes organizadas por categoría
                for cat_key, cat_name in LAW_CATEGORIES.items():
                    laws = get_laws_by_category(cat_key)
                    if laws:
                        output.append(f"## {cat_name}")
                        output.append("")
                        
                        for law_id, law_info in laws:
                            output.append(f"### {law_info['titulo']}")
                            output.append(f"- **ID BOE:** `{law_id}`")
                            output.append(f"- **Fecha:** {law_info['fecha']}")
                            if show_descriptions:
                                output.append(f"- **Descripción:** {law_info['descripcion']}")
                            output.append("")
            else:
                # Mostrar solo la categoría solicitada
                cat_name = LAW_CATEGORIES.get(category, "Categoría desconocida")
                laws = get_laws_by_category(category)
                
                if not laws:
                    return [TextContent(
                        type="text",
                        text=f"No se encontraron leyes en la categoría '{category}'"
                    )]
                
                output.append(f"## {cat_name}")
                output.append("")
                
                for law_id, law_info in laws:
                    output.append(f"### {law_info['titulo']}")
                    output.append(f"- **ID BOE:** `{law_id}`")
                    output.append(f"- **Fecha:** {law_info['fecha']}")
                    if show_descriptions:
                        output.append(f"- **Descripción:** {law_info['descripcion']}")
                    output.append("")
            
            output.append("---")
            output.append("💡 **Tip:** Use estos IDs con `get_consolidated_law` para obtener el texto completo de la norma.")
            
            return [TextContent(
                type="text",
                text="\n".join(output)
            )]
            
        except Exception as e:
            logger.error(f"Error listando leyes comunes: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]
    
    async def search_common_laws(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Busca leyes comunes por palabra clave.
        
        Args:
            arguments: Parámetros de búsqueda
            
        Returns:
            Lista de contenido con los resultados
        """
        try:
            keyword = arguments['keyword']
            
            results = search_laws_by_keyword(keyword)
            
            if not results:
                return [TextContent(
                    type="text",
                    text=f"No se encontraron leyes que contengan '{keyword}' en el diccionario de leyes comunes.\n\n" +
                         "💡 Pruebe con términos como: constitución, civil, penal, laboral, datos, transparencia, etc."
                )]
            
            output = []
            output.append(f"# 🔍 Resultados de búsqueda: '{keyword}'")
            output.append(f"**Encontradas {len(results)} leyes**")
            output.append("")
            
            for law_id, law_info in results:
                output.append(f"## {law_info['titulo']}")
                output.append(f"- **ID BOE:** `{law_id}`")
                output.append(f"- **Fecha:** {law_info['fecha']}")
                output.append(f"- **Categoría:** {LAW_CATEGORIES.get(law_info['categoria'], 'Otra')}")
                output.append(f"- **Descripción:** {law_info['descripcion']}")
                output.append("")
            
            output.append("---")
            output.append("💡 **Tip:** Use `get_consolidated_law` con cualquiera de estos IDs para obtener el texto completo.")
            
            return [TextContent(
                type="text",
                text="\n".join(output)
            )]
            
        except Exception as e:
            logger.error(f"Error buscando en leyes comunes: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]
    
    async def get_recent_important_laws(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene las leyes importantes más recientes.
        
        Args:
            arguments: Parámetros de búsqueda
            
        Returns:
            Lista de contenido con las leyes recientes
        """
        try:
            years_back = arguments.get('years_back', 5)
            
            results = get_recent_laws(years_back)
            
            if not results:
                return [TextContent(
                    type="text",
                    text=f"No se encontraron leyes importantes en los últimos {years_back} años en el diccionario."
                )]
            
            output = []
            output.append(f"# 📅 Leyes Importantes de los Últimos {years_back} Años")
            output.append(f"**Encontradas {len(results)} leyes**")
            output.append("")
            
            for law_id, law_info in results:
                output.append(f"## {law_info['titulo']}")
                output.append(f"- **ID BOE:** `{law_id}`")
                output.append(f"- **Fecha:** {law_info['fecha']}")
                output.append(f"- **Categoría:** {LAW_CATEGORIES.get(law_info['categoria'], 'Otra')}")
                output.append(f"- **Descripción:** {law_info['descripcion']}")
                output.append("")
            
            output.append("---")
            output.append("💡 **Nota:** Esta lista incluye solo las leyes más importantes del diccionario.")
            output.append("Para una búsqueda completa, use `search_consolidated_legislation` con filtros de fecha.")
            
            return [TextContent(
                type="text",
                text="\n".join(output)
            )]
            
        except Exception as e:
            logger.error(f"Error obteniendo leyes recientes: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]