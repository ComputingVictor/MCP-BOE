#!/usr/bin/env python3
"""
API REST wrapper para el MCP BOE.
Permite usar las funcionalidades desde cualquier cliente HTTP.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import sys
import os

# Agregar el path del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_boe.utils.http_client import BOEHTTPClient
from mcp_boe.tools.legislation import LegislationTools
from mcp_boe.tools.summaries import SummaryTools
from mcp_boe.tools.auxiliary import AuxiliaryTools

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BOE MCP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de request
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class SummaryRequest(BaseModel):
    date: Optional[str] = None  # Si no se proporciona, usa fecha reciente
    max_items: Optional[int] = 10

class DepartmentRequest(BaseModel):
    search_term: Optional[str] = None
    limit: Optional[int] = 10

class CodeRequest(BaseModel):
    code: str

# Cliente HTTP global
client = None

@app.on_event("startup")
async def startup_event():
    global client
    client = BOEHTTPClient()

@app.on_event("shutdown")
async def shutdown_event():
    global client
    if client:
        await client.close()

@app.get("/")
async def root():
    return {
        "message": "BOE MCP API",
        "version": "0.1.0",
        "endpoints": {
            "search_legislation": "/search/legislation",
            "get_boe_summary": "/summary/boe",
            "search_departments": "/auxiliary/departments",
            "get_code_description": "/auxiliary/code/{code}"
        }
    }

@app.post("/search/legislation")
async def search_legislation(request: SearchRequest):
    """Buscar en legislación consolidada."""
    try:
        tools = LegislationTools(client)
        results = await tools.search_consolidated_legislation({
            "query": request.query,
            "limit": request.limit
        })
        
        return {
            "success": True,
            "results": [{"content": r.text} for r in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summary/boe")
async def get_boe_summary(request: SummaryRequest):
    """Obtener sumario del BOE."""
    try:
        from datetime import datetime, timedelta
        
        date = request.date
        if not date:
            # Usar fecha reciente si no se especifica
            date = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")
        
        tools = SummaryTools(client)
        results = await tools.get_boe_summary({
            "date": date,
            "max_items": request.max_items
        })
        
        return {
            "success": True,
            "date": date,
            "results": [{"content": r.text} for r in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auxiliary/departments")
async def search_departments(request: DepartmentRequest):
    """Buscar departamentos."""
    try:
        tools = AuxiliaryTools(client)
        args = {"limit": request.limit}
        if request.search_term:
            args["search_term"] = request.search_term
            
        results = await tools.get_departments_table(args)
        
        return {
            "success": True,
            "results": [{"content": r.text} for r in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auxiliary/code/{code}")
async def get_code_description(code: str):
    """Obtener descripción de un código."""
    try:
        tools = AuxiliaryTools(client)
        results = await tools.get_code_description({"code": code})
        
        return {
            "success": True,
            "code": code,
            "results": [{"content": r.text} for r in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando BOE MCP API en http://localhost:8000")
    print("📖 Documentación en http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)