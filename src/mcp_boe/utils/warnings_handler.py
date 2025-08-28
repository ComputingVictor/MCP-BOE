"""
Sistema de advertencias y mensajes informativos para el usuario.

Este módulo proporciona mensajes claros sobre las limitaciones de la API
y sugiere alternativas cuando sea necesario.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime


class BOEWarnings:
    """Gestiona advertencias y mensajes informativos sobre la API del BOE."""
    
    # IDs de leyes importantes para sugerir
    IMPORTANT_LAWS = {
        "Constitución Española": "BOE-A-1978-31229",
        "LOPDGDD (Protección de Datos)": "BOE-A-2018-16673",
        "Ley 39/2015 (Procedimiento Administrativo)": "BOE-A-2015-10565",
        "Ley 40/2015 (Régimen Jurídico)": "BOE-A-2015-10566",
        "Código Civil": "BOE-A-1889-4763",
        "Código Penal": "BOE-A-1995-25444",
        "Estatuto de los Trabajadores": "BOE-A-2015-11430",
        "Ley de Contratos del Sector Público": "BOE-A-2017-12902",
    }
    
    @staticmethod
    def search_warning(search_text: Optional[str] = None) -> str:
        """
        Genera una advertencia sobre las limitaciones de búsqueda.
        
        Args:
            search_text: Texto que se intentó buscar
            
        Returns:
            Mensaje de advertencia formateado
        """
        warning = []
        warning.append("")
        warning.append("⚠️ **IMPORTANTE: Limitaciones de la búsqueda**")
        warning.append("")
        warning.append("La API del BOE tiene problemas conocidos con la búsqueda por texto:")
        warning.append("- Los resultados pueden NO corresponder a su búsqueda")
        
        if search_text:
            warning.append(f"- Buscó '{search_text}' pero los resultados pueden ser incorrectos")
        
        warning.append("")
        warning.append("### 💡 Alternativas recomendadas:")
        warning.append("")
        warning.append("**1. Use IDs directos para leyes conocidas:**")
        for law_name, law_id in BOEWarnings.IMPORTANT_LAWS.items():
            warning.append(f"   - {law_name}: `{law_id}`")
        
        warning.append("")
        warning.append("**2. Use filtros en lugar de búsqueda por texto:**")
        warning.append("   - Por fecha: `from_date`, `to_date`")
        warning.append("   - Por departamento: `department_code`")
        warning.append("   - Por rango legal: `legal_range_code`")
        
        warning.append("")
        warning.append("**3. Para publicaciones recientes:**")
        warning.append("   - Use `search_recent_boe` o `get_boe_summary`")
        warning.append("   - La búsqueda en sumarios SÍ funciona correctamente")
        
        warning.append("")
        warning.append("📚 [Más información sobre limitaciones](https://github.com/ComputingVictor/MCP-BOE/blob/main/docs/API_LIMITATIONS.md)")
        
        return "\n".join(warning)
    
    @staticmethod
    def invalid_parameter_warning(param_name: str, param_value: Any, expected_format: str) -> str:
        """
        Genera una advertencia sobre parámetros inválidos.
        
        Args:
            param_name: Nombre del parámetro
            param_value: Valor proporcionado
            expected_format: Formato esperado
            
        Returns:
            Mensaje de advertencia
        """
        return (
            f"❌ **Parámetro inválido: {param_name}**\n"
            f"   - Valor proporcionado: `{param_value}`\n"
            f"   - Formato esperado: {expected_format}\n"
            f"   - Ejemplo correcto: {BOEWarnings._get_example_for_param(param_name)}"
        )
    
    @staticmethod
    def _get_example_for_param(param_name: str) -> str:
        """Proporciona un ejemplo para un parámetro específico."""
        examples = {
            "law_id": "`BOE-A-2015-10565`",
            "date": "`20240529` (formato AAAAMMDD)",
            "from_date": "`20240101` (formato AAAAMMDD)",
            "to_date": "`20241231` (formato AAAAMMDD)",
            "department_code": "`7723` (Jefatura del Estado)",
            "legal_range_code": "`1300` (Ley)",
            "limit": "`20` (número entre 1-100)",
            "offset": "`0` (número >= 0)",
        }
        return examples.get(param_name, "Ver documentación")
    
    @staticmethod
    def api_error_message(error_code: int, details: str = "") -> str:
        """
        Genera un mensaje amigable para errores de la API.
        
        Args:
            error_code: Código HTTP del error
            details: Detalles adicionales
            
        Returns:
            Mensaje de error formateado
        """
        messages = {
            404: {
                "title": "Recurso no encontrado",
                "message": "El recurso solicitado no existe en la API del BOE",
                "suggestion": "Verifique el ID o la fecha proporcionada"
            },
            500: {
                "title": "Error del servidor",
                "message": "La API del BOE está experimentando problemas",
                "suggestion": "Intente nuevamente en unos minutos"
            },
            503: {
                "title": "Servicio no disponible",
                "message": "La API del BOE está temporalmente fuera de servicio",
                "suggestion": "Intente más tarde o consulte el estado en boe.es"
            },
            429: {
                "title": "Demasiadas peticiones",
                "message": "Se ha excedido el límite de peticiones a la API",
                "suggestion": "Espere unos segundos antes de intentar nuevamente"
            },
        }
        
        error_info = messages.get(error_code, {
            "title": f"Error HTTP {error_code}",
            "message": "Error al comunicarse con la API del BOE",
            "suggestion": "Consulte la documentación o intente nuevamente"
        })
        
        output = []
        output.append(f"❌ **{error_info['title']}**")
        output.append(f"   {error_info['message']}")
        
        if details:
            output.append(f"   Detalles: {details}")
        
        output.append(f"   💡 {error_info['suggestion']}")
        
        return "\n".join(output)
    
    @staticmethod
    def no_results_message(search_params: Dict[str, Any]) -> str:
        """
        Mensaje cuando no se encuentran resultados.
        
        Args:
            search_params: Parámetros de búsqueda utilizados
            
        Returns:
            Mensaje informativo
        """
        output = []
        output.append("📭 **No se encontraron resultados**")
        output.append("")
        
        if search_params.get('query'):
            output.append("⚠️ Recuerde que la búsqueda por texto puede no funcionar correctamente.")
            output.append("")
        
        output.append("Sugerencias:")
        output.append("- Amplíe el rango de fechas")
        output.append("- Use términos de búsqueda más generales")
        output.append("- Pruebe con un ID específico si lo conoce")
        output.append("- Use los sumarios del BOE para publicaciones recientes")
        
        return "\n".join(output)
    
    @staticmethod
    def deprecation_notice(old_method: str, new_method: str) -> str:
        """
        Aviso de deprecación para métodos antiguos.
        
        Args:
            old_method: Método deprecado
            new_method: Método recomendado
            
        Returns:
            Mensaje de deprecación
        """
        return (
            f"⚠️ **Método deprecado**\n"
            f"   El método `{old_method}` está deprecado.\n"
            f"   Use `{new_method}` en su lugar."
        )


class SearchResultValidator:
    """Valida si los resultados de búsqueda corresponden a la consulta."""
    
    @staticmethod
    def validate_search_results(
        search_text: str,
        results: List[Dict[str, Any]],
        log_mismatches: bool = True
    ) -> Dict[str, Any]:
        """
        Valida si los resultados corresponden a la búsqueda.
        
        Args:
            search_text: Texto buscado
            results: Resultados obtenidos
            log_mismatches: Si debe registrar discrepancias
            
        Returns:
            Diccionario con información de validación
        """
        validation = {
            "search_text": search_text,
            "total_results": len(results),
            "matching_results": 0,
            "confidence": 0.0,
            "likely_incorrect": False,
            "mismatched_titles": []
        }
        
        if not results:
            return validation
        
        # Normalizar texto de búsqueda
        search_lower = search_text.lower()
        search_terms = search_lower.split()
        
        # Verificar cada resultado
        for result in results:
            title = result.get('titulo', '').lower()
            identifier = result.get('identificador', '').lower()
            
            # Verificar si algún término de búsqueda aparece en el resultado
            match_found = False
            for term in search_terms:
                if term in title or term in identifier:
                    match_found = True
                    break
            
            if match_found:
                validation["matching_results"] += 1
            else:
                validation["mismatched_titles"].append(result.get('titulo', 'Sin título'))
        
        # Calcular confianza
        if validation["total_results"] > 0:
            validation["confidence"] = validation["matching_results"] / validation["total_results"]
        
        # Determinar si probablemente es incorrecto
        validation["likely_incorrect"] = validation["confidence"] < 0.3
        
        if log_mismatches and validation["likely_incorrect"]:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Búsqueda de '{search_text}' devolvió resultados no relacionados. "
                f"Confianza: {validation['confidence']:.1%}"
            )
        
        return validation


def format_search_validation_warning(validation: Dict[str, Any]) -> str:
    """
    Formatea una advertencia basada en la validación de resultados.
    
    Args:
        validation: Resultado de SearchResultValidator.validate_search_results
        
    Returns:
        Mensaje de advertencia formateado
    """
    if not validation["likely_incorrect"]:
        return ""
    
    output = []
    output.append("")
    output.append("🔍 **Análisis de resultados**")
    output.append(f"   - Búsqueda: '{validation['search_text']}'")
    output.append(f"   - Resultados que NO coinciden: {len(validation['mismatched_titles'])}/{validation['total_results']}")
    output.append(f"   - Confianza: {validation['confidence']:.0%}")
    output.append("")
    output.append("⚠️ **Los resultados probablemente NO corresponden a su búsqueda**")
    
    if validation["mismatched_titles"]:
        output.append("")
        output.append("Ejemplos de resultados incorrectos:")
        for i, title in enumerate(validation["mismatched_titles"][:3], 1):
            output.append(f"   {i}. {title[:80]}...")
    
    return "\n".join(output)