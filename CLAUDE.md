# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP-BOE is a Model Context Protocol (MCP) server that provides access to the Spanish Official State Gazette (BOE - Boletín Oficial del Estado) API. It allows LLMs like Claude to search consolidated legislation, daily BOE/BORME summaries, and auxiliary reference tables.

## Build & Development Commands

```bash
# Install for development
pip install -e ".[dev]"

# Install with REST API support
pip install -e ".[api]"

# Run the MCP server
python -m mcp_boe.server

# Server modes
python -m mcp_boe.server --mode server      # Run MCP server (default)
python -m mcp_boe.server --mode test        # Run test function
python -m mcp_boe.server --mode diagnose    # Diagnose API connectivity

# Test connectivity
python examples/basic_usage.py connectivity

# Run all tests
python examples/basic_usage.py all

# Run specific tests
python examples/basic_usage.py search       # Legislation search
python examples/basic_usage.py summary      # BOE summaries
python examples/basic_usage.py departments  # Auxiliary tables

# Start REST API wrapper
python rest_api_wrapper.py

# Linting and formatting
python -m black src/
python -m flake8 src/
python -m mypy src/

# Run pytest
python -m pytest tests/
```

## Architecture

### Core Components

- **`src/mcp_boe/server.py`**: Main MCP server (`BOEMCPServer`) that registers tool handlers and coordinates communication with MCP clients. Entry point is `main()`.

- **`src/mcp_boe/utils/http_client.py`**: `BOEHTTPClient` - async HTTP client for BOE API with retry logic, timeout handling, and XML/JSON parsing. Base URL: `https://www.boe.es/datosabiertos/api`

- **`src/mcp_boe/tools/`**: MCP tool implementations, each class provides `get_tools()` returning tool definitions and async methods for tool execution:
  - `legislation.py` - `LegislationTools`: Search and retrieve consolidated legislation
  - `summaries.py` - `SummaryTools`: BOE/BORME daily summaries
  - `auxiliary.py` - `AuxiliaryTools`: Reference tables (departments, legal ranges, matters)

- **`src/mcp_boe/models/boe_models.py`**: Pydantic models and validation helpers (`validate_boe_identifier`, `validate_date_format`)

### Tool Registration Pattern

Tools are registered in `BOEMCPServer._setup_handlers()` via `@self.server.list_tools()` and `@self.server.call_tool()` decorators. Each tool class implements:
1. `get_tools()` - Returns list of `mcp.types.Tool` with JSON Schema input definitions
2. Async handler methods that return `List[TextContent]`

### API Endpoints Used

```
/legislacion-consolidada        - Legislation search and retrieval
/boe/sumario/{date}            - BOE daily summaries
/borme/sumario/{date}          - BORME daily summaries
/tablas-auxiliares/{table}     - Auxiliary tables (departamentos, rangos, materias, etc.)
```

### Key Identifiers

- BOE document IDs: `BOE-A-YYYY-NNNNN` (e.g., `BOE-A-2015-10566`)
- Date format: `YYYYMMDD` (e.g., `20240529`)
- Department codes: 4-digit strings (e.g., `7723` for Jefatura del Estado)
- Legal range codes: 4-digit strings (e.g., `1300` for Ley, `1200` for Real Decreto)

## Configuration

Environment variables for advanced configuration (see `BOEMCPConfig`):
- `BOE_HTTP_TIMEOUT`: Request timeout (default: 30s)
- `BOE_MAX_RETRIES`: Max retry attempts (default: 3)
- `BOE_RETRY_DELAY`: Delay between retries (default: 1s)
- `LOG_LEVEL`: Logging level (default: INFO)

## MCP Client Configuration

For Claude Code with uvx:
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
