"""
Servidor principal del MCP para el BOE.

Este módulo implementa el servidor MCP que coordina todas las herramientas
y maneja la comunicación con Claude.
"""

import asyncio
import logging
import sys
from typing import Any, Sequence

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from .utils.http_client import BOEHTTPClient
from .tools.legislation import LegislationTools
from .tools.summaries import SummaryTools
from .tools.auxiliary import AuxiliaryTools
from .tools.documents import DocumentTools

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BOEMCPServer:
    """Servidor MCP principal para el BOE."""
    
    def __init__(self):
        """Inicializa el servidor MCP."""
        self.server = Server("mcp-boe")
        self.http_client = None
        self.legislation_tools = None
        self.summary_tools = None
        self.auxiliary_tools = None
        self.document_tools = DocumentTools()
        self._setup_handlers()

    def _setup_handlers(self):
        """Configura los handlers del servidor MCP."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Lista todas las herramientas disponibles."""
            tools = []
            
            if self.legislation_tools:
                tools.extend(self.legislation_tools.get_tools())
            
            if self.summary_tools:
                tools.extend(self.summary_tools.get_tools())
            
            if self.auxiliary_tools:
                tools.extend(self.auxiliary_tools.get_tools())

            tools.extend(self.document_tools.get_tools())

            logger.info(f"Listando {len(tools)} herramientas disponibles")
            return tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Maneja la llamada a una herramienta específica."""
            if arguments is None:
                arguments = {}

            logger.info(f"Llamando herramienta: {name} con argumentos: {arguments}")

            # Tabla de despacho: evita una cadena larga de if/elif
            dispatch: dict[str, Any] = {
                # Legislación
                "search_consolidated_legislation": lambda a: self.legislation_tools.search_consolidated_legislation(a),
                "get_consolidated_law":            lambda a: self.legislation_tools.get_consolidated_law(a),
                "get_law_text_block":              lambda a: self.legislation_tools.get_law_text_block(a),
                "get_law_structure":               lambda a: self.legislation_tools.get_law_structure(a),
                "find_related_laws":               lambda a: self.legislation_tools.find_related_laws(a),
                # Sumarios
                "get_boe_summary":                 lambda a: self.summary_tools.get_boe_summary(a),
                "get_borme_summary":               lambda a: self.summary_tools.get_borme_summary(a),
                "search_recent_boe":               lambda a: self.summary_tools.search_recent_boe(a),
                "get_weekly_summary":              lambda a: self.summary_tools.get_weekly_summary(a),
                # Tablas auxiliares
                "get_departments_table":           lambda a: self.auxiliary_tools.get_departments_table(a),
                "get_legal_ranges_table":          lambda a: self.auxiliary_tools.get_legal_ranges_table(a),
                "get_matters_table":               lambda a: self.auxiliary_tools.get_matters_table(a),
                "get_scopes_table":                lambda a: self.auxiliary_tools.get_scopes_table(a),
                "get_consolidation_states_table":  lambda a: self.auxiliary_tools.get_consolidation_states_table(a),
                "search_auxiliary_data":           lambda a: self.auxiliary_tools.search_auxiliary_data(a),
                "get_code_description":            lambda a: self.auxiliary_tools.get_code_description(a),
                # Documentos PDF
                "read_boe_pdf":                    lambda a: self.document_tools.read_boe_pdf(a),
            }

            handler = dispatch.get(name)
            if handler is None:
                raise ValueError(f"Herramienta desconocida: {name}")

            try:
                return await handler(arguments)
            except Exception as e:
                logger.error(f"Error ejecutando herramienta {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error ejecutando {name}: {str(e)}"
                    )
                ]

        @self.server.list_prompts()
        async def handle_list_prompts() -> list[types.Prompt]:
            """Lista los prompts disponibles."""
            return [
                types.Prompt(
                    name="buscar_legislacion",
                    description="Busca y resume una norma o conjunto de normas del BOE",
                    arguments=[
                        types.PromptArgument(name="tema", description="Tema o nombre de la norma a buscar", required=True),
                        types.PromptArgument(name="departamento", description="Ministerio u organismo emisor (opcional)", required=False),
                    ],
                ),
                types.Prompt(
                    name="analizar_norma",
                    description="Analiza en profundidad una norma específica: metadatos, estado, referencias y estructura",
                    arguments=[
                        types.PromptArgument(name="id_norma", description="Identificador BOE (ej: BOE-A-2015-10566)", required=True),
                    ],
                ),
                types.Prompt(
                    name="resumen_boe_dia",
                    description="Obtiene y resume las publicaciones más relevantes del BOE de una fecha concreta",
                    arguments=[
                        types.PromptArgument(name="fecha", description="Fecha en formato AAAAMMDD (ej: 20240529)", required=True),
                        types.PromptArgument(name="seccion", description="Sección del BOE (1, 2A, 2B, 3, 4, 5) — opcional", required=False),
                    ],
                ),
                types.Prompt(
                    name="comparar_normas",
                    description="Compara dos normas: busca relaciones de modificación o derogación entre ellas",
                    arguments=[
                        types.PromptArgument(name="id_norma_1", description="Identificador de la primera norma", required=True),
                        types.PromptArgument(name="id_norma_2", description="Identificador de la segunda norma", required=True),
                    ],
                ),
            ]

        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
            """Devuelve el contenido de un prompt específico."""
            args = arguments or {}

            if name == "buscar_legislacion":
                tema = args.get("tema", "")
                departamento = args.get("departamento", "")
                dept_hint = f" emitida por {departamento}" if departamento else ""
                return types.GetPromptResult(
                    description=f"Buscar legislación sobre: {tema}",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=(
                                    f"Busca en la legislación consolidada del BOE información sobre '{tema}'{dept_hint}.\n\n"
                                    "Por favor:\n"
                                    "1. Usa `search_consolidated_legislation` para encontrar las normas relevantes.\n"
                                    "2. Para las 2-3 más relevantes, usa `get_consolidated_law` para obtener sus metadatos y análisis.\n"
                                    "3. Presenta un resumen claro con: título, fecha de publicación, estado de vigencia y enlace al BOE.\n"
                                    "4. Indica si alguna norma ha sido modificada o derogada recientemente."
                                ),
                            ),
                        )
                    ],
                )

            elif name == "analizar_norma":
                id_norma = args.get("id_norma", "")
                return types.GetPromptResult(
                    description=f"Análisis completo de {id_norma}",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=(
                                    f"Analiza en profundidad la norma `{id_norma}` del BOE.\n\n"
                                    "Sigue estos pasos:\n"
                                    "1. Usa `get_consolidated_law` con `include_metadata=true` e `include_analysis=true`.\n"
                                    "2. Usa `get_law_structure` para mostrar el índice de la norma.\n"
                                    "3. Usa `find_related_laws` para identificar normas que la modifican o derogan.\n"
                                    "4. Presenta un informe estructurado con: datos básicos, estado actual, "
                                    "materias que regula, historial de modificaciones y estructura.\n"
                                    "5. Señala si la consolidación está actualizada o si hay cambios pendientes."
                                ),
                            ),
                        )
                    ],
                )

            elif name == "resumen_boe_dia":
                fecha = args.get("fecha", "")
                seccion = args.get("seccion", "")
                seccion_hint = f" de la sección {seccion}" if seccion else ""
                return types.GetPromptResult(
                    description=f"Resumen del BOE del {fecha}",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=(
                                    f"Obtén y resume las publicaciones del BOE del día {fecha}{seccion_hint}.\n\n"
                                    "Por favor:\n"
                                    "1. Usa `get_boe_summary` para obtener el sumario completo.\n"
                                    "2. Identifica las disposiciones más relevantes (especialmente de la Sección I).\n"
                                    "3. Agrupa los documentos por departamento emisor.\n"
                                    "4. Destaca leyes, reales decretos y resoluciones de especial importancia.\n"
                                    "5. Proporciona los enlaces PDF de los documentos más destacados."
                                ),
                            ),
                        )
                    ],
                )

            elif name == "comparar_normas":
                id1 = args.get("id_norma_1", "")
                id2 = args.get("id_norma_2", "")
                return types.GetPromptResult(
                    description=f"Comparar {id1} y {id2}",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=(
                                    f"Compara las normas `{id1}` y `{id2}` del BOE.\n\n"
                                    "Sigue estos pasos:\n"
                                    f"1. Usa `get_consolidated_law` para obtener los metadatos de `{id1}`.\n"
                                    f"2. Usa `get_consolidated_law` para obtener los metadatos de `{id2}`.\n"
                                    f"3. Usa `find_related_laws` en cada una para ver si existe relación directa entre ellas.\n"
                                    "4. Elabora una tabla comparativa con: rango normativo, fecha, departamento, estado de vigencia.\n"
                                    "5. Explica si una modifica, complementa o deroga a la otra, y en qué aspectos."
                                ),
                            ),
                        )
                    ],
                )

            else:
                raise ValueError(f"Prompt desconocido: {name}")

        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """Lista los recursos disponibles."""
            return [
                types.Resource(
                    uri="boe://help",
                    name="Ayuda del MCP BOE",
                    description="Guía de uso de las herramientas del BOE",
                    mimeType="text/markdown",
                ),
                types.Resource(
                    uri="boe://status",
                    name="Estado del servicio",
                    description="Estado actual de la conectividad con la API del BOE",
                    mimeType="text/plain",
                ),
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Lee un recurso específico."""
            if uri == "boe://help":
                return self._get_help_content()
            elif uri == "boe://status":
                return await self._get_status_content()
            else:
                raise ValueError(f"Recurso desconocido: {uri}")

    def _get_help_content(self) -> str:
        """Genera el contenido de ayuda."""
        return """# 📖 Guía del MCP BOE

## 🔍 Herramientas de Legislación Consolidada

### `search_consolidated_legislation`
Busca normas en la legislación consolidada del BOE.

**Ejemplos:**
- `"query": "Ley 40/2015"` - Busca por título
- `"query": "procedimiento administrativo"` - Búsqueda por texto
- `"department_code": "7723"` - Filtrar por Jefatura del Estado
- `"from_date": "20200101", "to_date": "20201231"` - Rango de fechas

### `get_consolidated_law`
Obtiene información completa de una norma específica.

**Ejemplo:**
```json
{
  "law_id": "BOE-A-2015-10566",
  "include_analysis": true,
  "include_full_text": false
}
```

### `get_law_text_block`
Obtiene una sección específica de una norma.

**Ejemplo:**
```json
{
  "law_id": "BOE-A-2015-10566",
  "block_id": "a1"
}
```

### `get_law_structure`
Obtiene el índice/estructura de una norma.

### `find_related_laws`
Encuentra normas relacionadas (modificaciones, derogaciones).

## 📰 Herramientas de Sumarios

### `get_boe_summary`
Obtiene el sumario del BOE para una fecha específica.

**Ejemplo:**
```json
{
  "date": "20240529",
  "section_filter": "1",
  "max_items": 20
}
```

### `get_borme_summary`
Obtiene el sumario del BORME para una fecha específica.

### `search_recent_boe`
Busca en los BOE de los últimos días.

### `get_weekly_summary`
Resumen estadístico semanal del BOE.

## 📊 Herramientas de Tablas Auxiliares

### `get_departments_table`
Lista de departamentos oficiales con sus códigos.

### `get_legal_ranges_table`
Tipos de normas (Ley, Real Decreto, etc.).

### `get_matters_table`
Vocabulario controlado de materias/temáticas.

### `search_auxiliary_data`
Búsqueda general en todas las tablas auxiliares.

### `get_code_description`
Obtiene la descripción de un código específico.

## 💡 Consejos de uso

- **Fechas:** Siempre en formato AAAAMMDD (ej: 20240529)
- **IDs de normas:** Formato BOE-A-YYYY-NNNNN (ej: BOE-A-2015-10566)
- **Filtros:** Use códigos de departamentos y rangos para búsquedas precisas
- **Límites:** Ajuste el parámetro `limit` para controlar el número de resultados
- **Texto completo:** Use `include_full_text: false` por defecto para evitar respuestas muy largas

## 📋 Códigos útiles

**Departamentos principales:**
- 7723: Jefatura del Estado
- 1430: Ministerio de Justicia
- 1470: Ministerio del Interior

**Rangos normativos:**
- 1300: Ley
- 1200: Real Decreto
- 1100: Real Decreto-ley
- 800: Orden ministerial

**Secciones del BOE:**
- 1: Disposiciones generales
- 2A: Autoridades y personal - Nombramientos
- 2B: Autoridades y personal - Oposiciones
- 3: Otras disposiciones
- 4: Administración de Justicia
- 5: Anuncios
"""

    async def _get_status_content(self) -> str:
        """Genera el contenido de estado del servicio."""
        try:
            if self.http_client:
                is_healthy = await self.http_client.health_check()
                if is_healthy:
                    return "✅ Servicio operativo - API del BOE accesible"
                else:
                    return "⚠️ Servicio con problemas - API del BOE no responde"
            else:
                return "❌ Servicio no inicializado"
        except Exception as e:
            return f"❌ Error verificando estado: {str(e)}"

    async def initialize(self):
        """Inicializa el servidor y sus dependencias."""
        logger.info("Inicializando servidor MCP BOE...")
        
        # Inicializar cliente HTTP
        self.http_client = BOEHTTPClient()
        
        # Inicializar herramientas
        self.legislation_tools = LegislationTools(self.http_client)
        self.summary_tools = SummaryTools(self.http_client)
        self.auxiliary_tools = AuxiliaryTools(self.http_client)
        
        logger.info("Servidor MCP BOE inicializado correctamente")

    async def cleanup(self):
        """Limpia recursos al cerrar el servidor."""
        logger.info("Cerrando servidor MCP BOE...")
        
        if self.http_client:
            await self.http_client.close()
        
        logger.info("Servidor MCP BOE cerrado correctamente")

    def run(self):
        """Ejecuta el servidor MCP."""
        async def run_server():
            # Inicializar servidor
            await self.initialize()
            
            try:
                # Configuración de inicialización
                async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                    await self.server.run(
                        read_stream,
                        write_stream,
                        InitializationOptions(
                            server_name="mcp-boe",
                            server_version="0.1.0",
                            capabilities=self.server.get_capabilities(
                                notification_options=NotificationOptions(),
                                experimental_capabilities={},
                            ),
                        ),
                    )
            finally:
                # Limpiar recursos
                await self.cleanup()

        # Ejecutar servidor
        if sys.platform == "win32":
            # En Windows, usar ProactorEventLoop para stdio
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        try:
            asyncio.run(run_server())
        except KeyboardInterrupt:
            logger.info("Servidor interrumpido por el usuario")
        except (BrokenPipeError, EOFError):
            logger.info("Conexión cerrada por el cliente")
        except Exception as e:
            logger.error(f"Error fatal en el servidor: {e}")
            sys.exit(1)


# ============================================================================
# FUNCIONES DE ENTRADA
# ============================================================================

def main():
    """Función principal del programa."""
    config = BOEMCPConfig()
    config.configure_logging()
    logger.info(f"Iniciando MCP BOE Server v0.1.0 (timeout: {config.http_timeout}s, retries: {config.max_retries})")

    server = BOEMCPServerWithConfig(config)
    server.run()


# ============================================================================
# FUNCIONES AUXILIARES PARA TESTING Y DESARROLLO
# ============================================================================

async def test_server():
    """Función para probar el servidor en desarrollo."""
    server = BOEMCPServer()
    await server.initialize()
    
    try:
        # Probar conectividad
        status = await server._get_status_content()
        print(f"Estado: {status}")
        
        # Probar una herramienta simple
        if server.legislation_tools:
            results = await server.legislation_tools.search_consolidated_legislation({
                "query": "Constitución",
                "limit": 3
            })
            print(f"Resultados de prueba: {len(results)} elementos")
            if results:
                print(f"Primer resultado: {results[0].text[:200]}...")
    
    finally:
        await server.cleanup()


def run_test():
    """Ejecuta las pruebas de desarrollo."""
    asyncio.run(test_server())


# ============================================================================
# CONFIGURACIÓN ADICIONAL PARA DIFERENTES ENTORNOS
# ============================================================================

class BOEMCPConfig:
    """Configuración del servidor MCP BOE."""
    
    def __init__(self):
        import os
        
        # Configuración HTTP
        self.http_timeout = float(os.getenv('BOE_HTTP_TIMEOUT', '30.0'))
        self.max_retries = int(os.getenv('BOE_MAX_RETRIES', '3'))
        self.retry_delay = float(os.getenv('BOE_RETRY_DELAY', '1.0'))
        
        # Configuración de logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Cache (para futuras versiones)
        self.enable_cache = os.getenv('ENABLE_CACHE', 'false').lower() == 'true'
        
        # Rate limiting (para ser respetuosos con la API del BOE)
        self.rate_limit_requests = int(os.getenv('RATE_LIMIT_REQUESTS', '10'))
        self.rate_limit_window = int(os.getenv('RATE_LIMIT_WINDOW', '60'))

    def configure_logging(self):
        """Configura el sistema de logging."""
        logging.basicConfig(
            level=getattr(logging, self.log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stderr)
            ]
        )


class BOEMCPServerWithConfig(BOEMCPServer):
    """Servidor MCP con configuración avanzada."""
    
    def __init__(self, config: BOEMCPConfig = None):
        super().__init__()
        self.config = config or BOEMCPConfig()
        self.config.configure_logging()

    async def initialize(self):
        """Inicializa el servidor con configuración personalizada."""
        logger.info("Inicializando servidor MCP BOE con configuración personalizada...")
        
        # Inicializar cliente HTTP con configuración
        self.http_client = BOEHTTPClient(
            timeout=self.config.http_timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay
        )
        
        # Inicializar herramientas
        self.legislation_tools = LegislationTools(self.http_client)
        self.summary_tools = SummaryTools(self.http_client)
        self.auxiliary_tools = AuxiliaryTools(self.http_client)
        
        logger.info("Servidor MCP BOE inicializado con configuración personalizada")


# ============================================================================
# PUNTO DE ENTRADA ALTERNATIVO CON CONFIGURACIÓN
# ============================================================================

def main_with_config():
    """Función principal con configuración avanzada."""
    config = BOEMCPConfig()
    logger.info(f"Iniciando MCP BOE Server v0.1.0 (timeout: {config.http_timeout}s, retries: {config.max_retries})")
    
    # Crear y ejecutar servidor
    server = BOEMCPServerWithConfig(config)
    server.run()


# ============================================================================
# UTILIDADES DE DIAGNÓSTICO
# ============================================================================

async def diagnose_connectivity():
    """Diagnostica la conectividad con la API del BOE."""
    print("🔍 Diagnosticando conectividad con la API del BOE...")
    print()
    
    client = BOEHTTPClient(timeout=10.0, max_retries=1)
    
    try:
        # Test 1: Conectividad básica
        print("1️⃣ Probando conectividad básica...")
        try:
            result = await client.search_legislation(limit=1)
            print("   ✅ Conectividad básica: OK")
        except Exception as e:
            print(f"   ❌ Conectividad básica: ERROR - {e}")
            return
        
        # Test 2: Búsqueda de legislación
        print("2️⃣ Probando búsqueda de legislación...")
        try:
            result = await client.search_legislation(
                query='{"query":{"query_string":{"query":"constitución"}}}', 
                limit=1
            )
            print("   ✅ Búsqueda de legislación: OK")
        except Exception as e:
            print(f"   ❌ Búsqueda de legislación: ERROR - {e}")
        
        # Test 3: Obtener norma específica
        print("3️⃣ Probando obtención de norma específica...")
        try:
            # Usar la Constitución como ejemplo
            result = await client.get_law_by_id("BOE-A-1978-31229", "metadatos")
            print("   ✅ Obtención de norma: OK")
        except Exception as e:
            print(f"   ❌ Obtención de norma: ERROR - {e}")
        
        # Test 4: Sumario BOE
        print("4️⃣ Probando sumario BOE...")
        try:
            from datetime import datetime
            today = datetime.now()
            # Probar con fecha reciente (día laborable)
            test_date = "20240529"  # Un día conocido que tiene BOE
            result = await client.get_boe_summary(test_date)
            print("   ✅ Sumario BOE: OK")
        except Exception as e:
            print(f"   ❌ Sumario BOE: ERROR - {e}")
        
        # Test 5: Tablas auxiliares
        print("5️⃣ Probando tablas auxiliares...")
        try:
            result = await client.get_auxiliary_table("departamentos")
            print("   ✅ Tablas auxiliares: OK")
        except Exception as e:
            print(f"   ❌ Tablas auxiliares: ERROR - {e}")
        
        print()
        print("✅ Diagnóstico completado. El servidor debería funcionar correctamente.")
        
    except Exception as e:
        print(f"❌ Error general durante el diagnóstico: {e}")
        
    finally:
        await client.close()


def run_diagnostics():
    """Ejecuta el diagnóstico de conectividad."""
    asyncio.run(diagnose_connectivity())


# ============================================================================
# HERRAMIENTAS DE LÍNEA DE COMANDOS
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    try:
        parser = argparse.ArgumentParser(description="Servidor MCP para el BOE")
        parser.add_argument(
            "--mode", 
            choices=["server", "test", "diagnose"],
            default="server",
            help="Modo de operación"
        )
        parser.add_argument(
            "--config",
            action="store_true",
            help="Usar configuración avanzada"
        )
        
        args = parser.parse_args()
        
        if args.mode == "server":
            if args.config:
                main_with_config()
            else:
                main()
        elif args.mode == "test":
            run_test()
        elif args.mode == "diagnose":
            run_diagnostics()
    except (SystemExit, ValueError):
        # Manejar errores de argparse cuando stdout está cerrado
        main()