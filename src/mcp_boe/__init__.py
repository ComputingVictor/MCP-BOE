"""
MCP BOE - Model Context Protocol para el Boletín Oficial del Estado español.

Este paquete proporciona un servidor MCP que permite a Claude acceder
a la API oficial del BOE para consultar legislación consolidada,
sumarios diarios y tablas auxiliares.
"""

__version__ = "0.1.0"
__author__ = "Víctor Viloria"
__email__ = "vvictor.97@gmail.com"
__description__ = "MCP para acceso a la API del Boletín Oficial del Estado español"

# Imports principales
from .server import BOEMCPServer, BOEMCPConfig, main
from .utils.http_client import BOEHTTPClient

# Imports de modelos
from .models.boe_models import (
    ConsolidatedLaw,
    ConsolidatedLawMetadata,
    ConsolidatedLawSearchResult,
    Summary,
    AuxiliaryTable,
    APIError,
    validate_boe_identifier,
    validate_date_format,
    format_date_for_api,
)

__all__ = [
    # Versión y metadatos
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
    
    # Clases principales
    "BOEMCPServer",
    "BOEMCPConfig",
    "BOEHTTPClient",
    
    # Modelos de datos
    "ConsolidatedLaw",
    "ConsolidatedLawMetadata", 
    "ConsolidatedLawSearchResult",
    "Summary",
    "AuxiliaryTable",
    "APIError",
    
    # Utilidades
    "validate_boe_identifier",
    "validate_date_format",
    "format_date_for_api",
    
    # Función principal
    "main",
]

# Información del paquete
PACKAGE_INFO = {
    "name": "mcp-boe",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "email": __email__,
    "url": "https://github.com/tuusuario/mcp-boe",
    "license": "MIT",
    "python_requires": ">=3.8",
}