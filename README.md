# MCP BOE 🇪🇸

**Model Context Protocol para el Boletín Oficial del Estado español**

<img width="512" height="512" alt="image" src="https://github.com/user-attachments/assets/cd1c5e79-add7-466c-bcbd-554b81a2fef9" />

Un servidor MCP que permite a Claude y otros LLMs acceder a la API oficial del BOE para consultar legislación consolidada, sumarios diarios y tablas auxiliares del gobierno español.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Características

- **🔍 Búsqueda de Legislación**: Buscar en más de 50.000 normas consolidadas con filtros por departamento, rango normativo, materia y fechas
- **📰 Sumarios del BOE/BORME**: Acceder a publicaciones diarias, búsquedas recientes y resúmenes semanales
- **🏛️ Tablas Auxiliares**: Consultar códigos de departamentos, materias, rangos normativos y ámbitos
- **📄 Lectura de PDFs**: Descargar y extraer el texto de cualquier documento del BOE para analizarlo
- **💬 Prompts integrados**: Plantillas de consulta listas para usar en Claude
- **📊 Datos Oficiales**: Conecta directamente con la API oficial del BOE
- **⚙️ Configurable**: Timeout, reintentos y nivel de log via variables de entorno

## 📋 Tabla de Contenidos

- [Instalación](#-instalación)
- [Configuración con Claude Desktop](#-configuración-con-claude-desktop)
- [Configuración con Claude Code](#-configuración-con-claude-code)
- [Prompts disponibles](#-prompts-disponibles)
- [Herramientas disponibles](#-herramientas-disponibles)
- [Lectura de PDFs](#-lectura-de-pdfs)
- [Variables de entorno](#-variables-de-entorno)
- [Ejemplos de uso](#-ejemplos-de-uso)
- [Solución de problemas](#-solución-de-problemas)
- [Estructura del proyecto](#-estructura-del-proyecto)

## 🛠️ Instalación

### Prerrequisitos

- Python **3.10 o superior** (requerido por la librería `mcp`)
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

### Opción 1: uvx — sin instalación (Recomendado)

Con [uvx](https://docs.astral.sh/uv/guides/tools/) no necesitas clonar el repositorio ni gestionar dependencias:

```bash
uvx --from git+https://github.com/ComputingVictor/MCP-BOE.git mcp-boe
```

### Opción 2: Desde el código fuente con uv

```bash
git clone https://github.com/ComputingVictor/MCP-BOE.git
cd MCP-BOE

# Instalar dependencias y ejecutar
uv run python -m mcp_boe.server
```

### Opción 3: Instalación con pip

```bash
git clone https://github.com/ComputingVictor/MCP-BOE.git
cd MCP-BOE
pip install -e .
```

## 🖥️ Configuración con Claude Desktop

Edita el archivo de configuración de Claude Desktop:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Con uv (Recomendado)

```json
{
  "mcpServers": {
    "mcp-boe": {
      "command": "uv",
      "args": [
        "run",
        "--python", "3.12",
        "--project", "/ruta/absoluta/a/MCP-BOE",
        "python", "-m", "mcp_boe.server"
      ]
    }
  }
}
```

> Sustituye `/ruta/absoluta/a/MCP-BOE` por la ruta real donde clonaste el repositorio.

### Con uvx

```json
{
  "mcpServers": {
    "mcp-boe": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/ComputingVictor/MCP-BOE.git", "mcp-boe"]
    }
  }
}
```

Reinicia Claude Desktop tras guardar los cambios.

## ⚡ Configuración con Claude Code

### Con uvx

```json
{
  "mcpServers": {
    "mcp-boe": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/ComputingVictor/MCP-BOE.git", "mcp-boe"],
      "transport": "stdio"
    }
  }
}
```

También puedes usar el archivo incluido en el repositorio:

```bash
# Desde el directorio del proyecto
claude --mcp-config claude_mcp_config_uvx.json
```

## 💬 Prompts disponibles

El servidor incluye 4 prompts integrados accesibles desde el selector de prompts de Claude:

### `buscar_legislacion`
Busca y resume normas del BOE.

| Argumento | Descripción | Requerido |
|-----------|-------------|-----------|
| `tema` | Texto o nombre de la norma a buscar | ✅ |
| `departamento` | Ministerio u organismo emisor | ❌ |

**Ejemplos:**
- tema: `protección de datos` → encuentra RGPD y LOPDGDD
- tema: `Ley 40/2015` → Ley de Régimen Jurídico del Sector Público
- tema: `tráfico`, departamento: `Ministerio del Interior`

---

### `analizar_norma`
Análisis completo de una norma: metadatos, estado de vigencia, estructura y relaciones con otras normas.

| Argumento | Descripción | Requerido |
|-----------|-------------|-----------|
| `id_norma` | Identificador BOE (ej: `BOE-A-2015-10566`) | ✅ |

**Ejemplos:**
- `BOE-A-1978-31229` → Constitución Española
- `BOE-A-2015-10566` → Ley 40/2015 de Régimen Jurídico del Sector Público
- `BOE-A-2018-16673` → Ley Orgánica de Protección de Datos

---

### `resumen_boe_dia`
Resumen de las publicaciones más relevantes del BOE de una fecha concreta.

| Argumento | Descripción | Requerido |
|-----------|-------------|-----------|
| `fecha` | Fecha en formato AAAAMMDD | ✅ |
| `seccion` | Sección del BOE: `1`, `2A`, `2B`, `3`, `4`, `5` | ❌ |

**Ejemplos:**
- fecha: `20250101` → publicaciones del 1 de enero de 2025
- fecha: `20240529`, seccion: `1` → solo disposiciones generales

---

### `comparar_normas`
Compara dos normas e identifica relaciones de modificación o derogación entre ellas.

| Argumento | Descripción | Requerido |
|-----------|-------------|-----------|
| `id_norma_1` | Identificador de la primera norma | ✅ |
| `id_norma_2` | Identificador de la segunda norma | ✅ |

**Ejemplo:**
- `BOE-A-2015-10566` y `BOE-A-2015-10565` → Ley 40/2015 y Ley 39/2015 (las dos grandes leyes administrativas)

## 🔧 Herramientas disponibles

### 📜 Legislación Consolidada (5 herramientas)

| Herramienta | Descripción | Parámetros clave |
|-------------|-------------|------------------|
| `search_consolidated_legislation` | Busca en más de 50.000 normas consolidadas | `query`, `title`, `department_code`, `legal_range_code`, `matter_code`, `from_date`, `to_date`, `limit`, `include_derogated` |
| `get_consolidated_law` | Obtiene metadatos, análisis jurídico y texto de una norma | `law_id`, `include_metadata`, `include_analysis`, `include_full_text`, `include_eli_metadata` |
| `get_law_structure` | Índice completo de una norma (artículos, disposiciones, anexos) | `law_id` |
| `get_law_text_block` | Texto de un artículo o disposición específica | `law_id`, `block_id` |
| `find_related_laws` | Normas que modifican, derogan o son modificadas por una norma | `law_id`, `relation_type` |

### 📰 Sumarios BOE/BORME (4 herramientas)

| Herramienta | Descripción | Parámetros clave |
|-------------|-------------|------------------|
| `get_boe_summary` | Sumario completo del BOE para una fecha | `date`, `section_filter`, `department_filter`, `max_items` |
| `get_borme_summary` | Sumario del BORME (Registro Mercantil) | `date`, `province_filter`, `max_items` |
| `search_recent_boe` | Busca documentos en los últimos N días | `days_back`, `search_terms`, `section_filter` |
| `get_weekly_summary` | Estadísticas y resumen de una semana completa | `start_date`, `include_statistics` |

### 🏛️ Tablas Auxiliares (7 herramientas)

| Herramienta | Descripción |
|-------------|-------------|
| `get_departments_table` | Lista de departamentos oficiales con sus códigos |
| `get_legal_ranges_table` | Rangos normativos (Ley, Real Decreto, Orden, etc.) |
| `get_matters_table` | Vocabulario controlado de materias temáticas |
| `get_scopes_table` | Ámbitos normativos (estatal, autonómico) |
| `get_consolidation_states_table` | Estados de consolidación |
| `search_auxiliary_data` | Búsqueda en todas las tablas a la vez |
| `get_code_description` | Descripción de un código específico |

### 📄 Lectura de PDFs (1 herramienta)

| Herramienta | Descripción | Parámetros clave |
|-------------|-------------|------------------|
| `read_boe_pdf` | Descarga y extrae el texto de un PDF del BOE | `source`, `max_pages` |

**`source`** acepta dos formatos:
- **URL directa**: la que aparece en el campo `url_pdf` de los sumarios  
  `https://www.boe.es/boe/dias/2025/03/28/pdfs/BOE-A-2025-6192.pdf`
- **Identificador BOE**: el servidor consulta la API para obtener la fecha y construye la URL  
  `BOE-A-2025-6192` o `BOE-A-2015-10566`

**`max_pages`** — páginas máximas a leer (por defecto `30`, máximo `100`).

Límites aplicados: PDFs de hasta **10 MB** y **80.000 caracteres** de texto devuelto al LLM.

**Ejemplos de uso en Claude:**

```
Lee el PDF de BOE-A-2015-10566 y explícame qué regula la Ley 40/2015
```
```
Descarga https://www.boe.es/boe/dias/2025/03/28/pdfs/BOE-A-2025-6192.pdf y resume su contenido
```
```
Busca el sumario del BOE de hoy y léeme el PDF del primer real decreto que aparezca
```

### 📌 Formatos y valores útiles

**Secciones del BOE:**
| Código | Descripción |
|--------|-------------|
| `1` | Disposiciones generales |
| `2A` | Autoridades y personal — Nombramientos |
| `2B` | Autoridades y personal — Oposiciones |
| `3` | Otras disposiciones |
| `4` | Administración de Justicia |
| `5` | Anuncios |

**Departamentos frecuentes:**
| Código | Departamento |
|--------|-------------|
| `7723` | Jefatura del Estado |
| `1430` | Ministerio de Justicia |
| `1470` | Ministerio del Interior |

**Rangos normativos frecuentes:**
| Código | Rango |
|--------|-------|
| `1300` | Ley |
| `1250` | Ley Orgánica |
| `1200` | Real Decreto |
| `1100` | Real Decreto-ley |
| `800` | Orden ministerial |

## ⚙️ Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `BOE_HTTP_TIMEOUT` | Timeout en segundos para peticiones HTTP | `30.0` |
| `BOE_MAX_RETRIES` | Número máximo de reintentos ante errores de red o 5xx | `3` |
| `BOE_RETRY_DELAY` | Segundos de espera base entre reintentos (backoff lineal) | `1.0` |
| `LOG_LEVEL` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

Ejemplo de configuración en Claude Desktop:

```json
{
  "mcpServers": {
    "mcp-boe": {
      "command": "uv",
      "args": ["run", "--project", "/ruta/a/MCP-BOE", "python", "-m", "mcp_boe.server"],
      "env": {
        "BOE_HTTP_TIMEOUT": "60",
        "LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

## 💡 Ejemplos de uso

### Buscar legislación desde Python

```python
import asyncio
from mcp_boe.utils.http_client import BOEHTTPClient
from mcp_boe.tools.legislation import LegislationTools

async def main():
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        resultados = await tools.search_consolidated_legislation({
            "query": "Ley 40/2015",
            "limit": 3
        })
        for r in resultados:
            print(r.text)

asyncio.run(main())
```

### Obtener sumario del BOE

```python
import asyncio
from datetime import datetime, timedelta
from mcp_boe.utils.http_client import BOEHTTPClient
from mcp_boe.tools.summaries import SummaryTools

async def main():
    async with BOEHTTPClient() as client:
        tools = SummaryTools(client)
        fecha = (datetime.now() - timedelta(days=2)).strftime("%Y%m%d")
        resultados = await tools.get_boe_summary({
            "date": fecha,
            "section_filter": "1",
            "max_items": 10
        })
        for r in resultados:
            print(r.text)

asyncio.run(main())
```

### Diagnóstico de conectividad

```bash
# Verificar que la API del BOE es accesible
python -m mcp_boe.server --mode diagnose
```

## 🐛 Solución de problemas

### El servidor no aparece en Claude Desktop

1. Verifica que Python 3.10+ está disponible: `python3 --version`
2. Comprueba la ruta en el config: debe ser absoluta, no relativa
3. Reinicia completamente Claude Desktop (no solo la ventana)
4. Revisa los logs en Claude Desktop → Ayuda → Abrir carpeta de logs

### Error: `requires-python` / incompatibilidad de versión

La librería `mcp` requiere Python 3.10 o superior. Fuerza la versión con `uv`:

```json
"args": ["run", "--python", "3.12", "--project", "/ruta/MCP-BOE", "python", "-m", "mcp_boe.server"]
```

### Error: `No module named 'mcp_boe'`

Asegúrate de pasar `--project` al directorio raíz del repositorio (donde está `pyproject.toml`), no al directorio `src/`.

### La API del BOE no responde

```bash
python -m mcp_boe.server --mode diagnose
```

La API del BOE no publica horarios de mantenimiento. Los errores 5xx se reintentan automáticamente hasta 3 veces.

## 📊 Estructura del proyecto

```
MCP-BOE/
├── src/mcp_boe/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py               # Servidor MCP: tools, prompts, resources
│   ├── models/
│   │   └── boe_models.py       # Modelos Pydantic y validadores
│   ├── tools/
│   │   ├── legislation.py      # 5 herramientas de legislación consolidada
│   │   ├── summaries.py        # 4 herramientas de sumarios BOE/BORME
│   │   ├── auxiliary.py        # 7 herramientas de tablas auxiliares
│   │   └── documents.py        # 1 herramienta de lectura de PDFs
│   └── utils/
│       └── http_client.py      # Cliente HTTP asíncrono con reintentos
├── examples/
│   └── basic_usage.py
├── tests/
├── pyproject.toml
├── claude_mcp_config.json      # Config de ejemplo para instalación local
├── claude_mcp_config_uvx.json  # Config de ejemplo con uvx
└── rest_api_wrapper.py         # API REST opcional (FastAPI)
```

## 🤝 Contribuir

1. Fork del proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de los cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Desarrollo local

```bash
git clone https://github.com/ComputingVictor/MCP-BOE.git
cd MCP-BOE
uv sync --extra dev
uv run python -m pytest tests/
uv run black src/
```

## 📝 Changelog

### v0.1.0

- Implementación inicial del servidor MCP
- **17 herramientas**: 5 de legislación, 4 de sumarios, 7 de tablas auxiliares, 1 de lectura de PDFs
- Herramienta `read_boe_pdf`: descarga y extrae texto de PDFs del BOE por URL o por ID de norma
- 4 prompts integrados: `buscar_legislacion`, `analizar_norma`, `resumen_boe_dia`, `comparar_normas`
- 2 recursos MCP: `boe://help` y `boe://status`
- Cliente HTTP asíncrono con reintentos en errores de red y 5xx
- Configurable via variables de entorno
- Soporte para Python 3.10+

## 🔒 Seguridad

- La API del BOE es pública y no requiere autenticación
- No se almacenan datos localmente
- El servidor respeta automáticamente los límites de la API mediante reintentos con backoff

## 📚 Referencias

- [API Oficial del BOE](https://www.boe.es/datosabiertos/documentos/Manual_API.pdf)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Documentación de Claude](https://docs.anthropic.com/claude/docs)

## 📄 Licencia

MIT — ver [LICENSE](LICENSE) para más detalles.

## 👤 Autor

**Víctor Viloria**
- Email: vvictor.97@gmail.com
- GitHub: [@ComputingVictor](https://github.com/ComputingVictor)

---

**¿Tienes preguntas?** Abre un [issue](https://github.com/ComputingVictor/MCP-BOE/issues).  
**¿Te gusta el proyecto?** ¡Dale una ⭐ en GitHub!
