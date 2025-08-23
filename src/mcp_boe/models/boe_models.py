"""
Modelos de datos para la API del BOE usando Pydantic.

Estos modelos definen la estructura de los datos que recibimos de la API del BOE
y aseguran que estén correctamente tipados y validados.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, model_validator
import re


# ============================================================================
# MODELOS BASE Y UTILITARIOS
# ============================================================================

class CodedValue(BaseModel):
    """Representa un valor con código y descripción textual."""
    codigo: str = Field(..., description="Código numérico o alfanumérico")
    texto: str = Field(..., description="Descripción textual del código")

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "1300", 
                "texto": "Ley"
            }
        }


class APIResponse(BaseModel):
    """Respuesta base de la API del BOE."""
    status: Dict[str, Union[str, int]] = Field(..., description="Estado de la respuesta")
    data: Optional[Any] = Field(None, description="Datos de la respuesta")

    @validator('status')
    def validate_status(cls, v):
        if 'code' not in v or 'text' not in v:
            raise ValueError("El status debe contener 'code' y 'text'")
        return v


# ============================================================================
# MODELOS PARA LEGISLACIÓN CONSOLIDADA
# ============================================================================

class ConsolidatedLawMetadata(BaseModel):
    """Metadatos de una norma consolidada."""
    fecha_actualizacion: datetime = Field(..., description="Fecha de última actualización")
    identificador: str = Field(..., description="Identificador único BOE (ej: BOE-A-2015-10566)")
    
    ambito: CodedValue = Field(..., description="Ámbito (estatal/autonómico)")
    departamento: CodedValue = Field(..., description="Departamento emisor")
    rango: CodedValue = Field(..., description="Rango normativo")
    
    titulo: str = Field(..., description="Título de la norma")
    diario: str = Field(..., description="Nombre del diario oficial")
    
    fecha_disposicion: Optional[str] = Field(None, description="Fecha de la disposición (AAAAMMDD)")
    numero_oficial: Optional[str] = Field(None, description="Número oficial")
    fecha_publicacion: str = Field(..., description="Fecha de publicación (AAAAMMDD)")
    diario_numero: str = Field(..., description="Número del diario")
    fecha_vigencia: Optional[str] = Field(None, description="Fecha entrada en vigor (AAAAMMDD)")
    
    # Estados de la norma
    estatus_derogacion: str = Field(..., description="¿Está derogada? (S/N)")
    fecha_derogacion: Optional[str] = Field(None, description="Fecha de derogación (AAAAMMDD)")
    estatus_anulacion: str = Field(..., description="¿Está anulada? (S/N)")
    fecha_anulacion: Optional[str] = Field(None, description="Fecha de anulación (AAAAMMDD)")
    vigencia_agotada: str = Field(..., description="¿Vigencia agotada? (S/N)")
    
    estado_consolidacion: CodedValue = Field(..., description="Estado de consolidación")
    
    # URLs
    url_eli: Optional[str] = Field(None, description="URL ELI (European Legislation Identifier)")
    url_html_consolidada: str = Field(..., description="URL del texto consolidado en BOE.es")

    @validator('identificador')
    def validate_identificador(cls, v):
        # Formato: BOE-A-YYYY-NNNNN
        pattern = r'^BOE-[A-Z]-\d{4}-\d{1,5}$'
        if not re.match(pattern, v):
            raise ValueError(f"Identificador inválido: {v}")
        return v

    @validator('fecha_disposicion', 'fecha_publicacion', 'fecha_vigencia', 'fecha_derogacion', 'fecha_anulacion')
    def validate_dates(cls, v):
        if v and len(v) == 8:
            try:
                datetime.strptime(v, '%Y%m%d')
            except ValueError:
                raise ValueError(f"Fecha inválida: {v}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "fecha_actualizacion": "2023-10-09T12:23:33Z",
                "identificador": "BOE-A-2015-10566",
                "ambito": {"codigo": "1", "texto": "Estatal"},
                "departamento": {"codigo": "7723", "texto": "Jefatura del Estado"},
                "rango": {"codigo": "1300", "texto": "Ley"},
                "titulo": "Ley 40/2015, de 1 de octubre, de Régimen Jurídico del Sector Público.",
                "fecha_publicacion": "20151002"
            }
        }


class LawMatter(BaseModel):
    """Materia sobre la que versa una norma."""
    codigo: str = Field(..., description="Código de la materia")
    texto: str = Field(..., description="Descripción de la materia")


class LawNote(BaseModel):
    """Nota adicional de una norma."""
    texto: str = Field(..., description="Contenido de la nota")


class LawReference(BaseModel):
    """Referencia entre normas (modificaciones, derogaciones, etc)."""
    id_norma: str = Field(..., description="ID de la norma referenciada")
    relacion: CodedValue = Field(..., description="Tipo de relación")
    texto: str = Field(..., description="Descripción detallada de la relación")


class LawAnalysis(BaseModel):
    """Análisis jurídico de una norma."""
    materias: Optional[List[LawMatter]] = Field(None, description="Materias de la norma")
    notas: Optional[List[LawNote]] = Field(None, description="Notas adicionales")
    referencias_anteriores: Optional[List[LawReference]] = Field(None, description="Referencias a normas anteriores")
    referencias_posteriores: Optional[List[LawReference]] = Field(None, description="Referencias a normas posteriores")


class TextBlockVersion(BaseModel):
    """Versión específica de un bloque de texto."""
    fecha_publicacion: str = Field(..., description="Fecha publicación norma modificadora")
    fecha_vigencia: Optional[str] = Field(None, description="Fecha entrada en vigor")
    id_norma: str = Field(..., description="ID norma modificadora")
    contenido_html: str = Field(..., description="Contenido HTML del bloque")


class TextBlock(BaseModel):
    """Bloque de texto de una norma (artículo, disposición, etc)."""
    id: str = Field(..., description="Identificador único del bloque")
    tipo: str = Field(..., description="Tipo de bloque")
    titulo: str = Field(..., description="Título del bloque") 
    fecha_caducidad: Optional[str] = Field(None, description="Fecha caducidad del bloque")
    versiones: List[TextBlockVersion] = Field(..., description="Versiones del bloque")

    @validator('tipo')
    def validate_tipo(cls, v):
        tipos_validos = [
            'nota_inicial', 'precepto', 'encabezado', 'firma',
            'parte_dispositiva', 'parte_final', 'preambulo', 'instrumento'
        ]
        if v not in tipos_validos:
            raise ValueError(f"Tipo de bloque inválido: {v}")
        return v


class ConsolidatedLaw(BaseModel):
    """Norma consolidada completa."""
    metadatos: ConsolidatedLawMetadata = Field(..., description="Metadatos de la norma")
    analisis: Optional[LawAnalysis] = Field(None, description="Análisis jurídico")
    metadata_eli: Optional[Dict[str, Any]] = Field(None, description="Metadatos ELI")
    texto: Optional[List[TextBlock]] = Field(None, description="Texto consolidado por bloques")

    class Config:
        json_schema_extra = {
            "example": {
                "metadatos": {
                    "identificador": "BOE-A-2015-10566",
                    "titulo": "Ley 40/2015, de 1 de octubre, de Régimen Jurídico del Sector Público"
                }
            }
        }


class ConsolidatedLawSearchResult(BaseModel):
    """Resultado de búsqueda de legislación consolidada."""
    total_results: Optional[int] = Field(None, description="Total de resultados encontrados")
    results: List[ConsolidatedLawMetadata] = Field(..., description="Lista de normas encontradas")

    class Config:
        json_schema_extra = {
            "example": {
                "total_results": 150,
                "results": [
                    {
                        "identificador": "BOE-A-2015-10566",
                        "titulo": "Ley 40/2015, de 1 de octubre..."
                    }
                ]
            }
        }


# ============================================================================
# MODELOS PARA SUMARIOS BOE/BORME
# ============================================================================

class SummaryMetadata(BaseModel):
    """Metadatos de un sumario."""
    publicacion: str = Field(..., description="Tipo de publicación (BOE/BORME)")
    fecha_publicacion: str = Field(..., description="Fecha de publicación (AAAAMMDD)")

    @validator('publicacion')
    def validate_publicacion(cls, v):
        if v not in ['BOE', 'BORME']:
            raise ValueError("La publicación debe ser 'BOE' o 'BORME'")
        return v


class SummaryDocument(BaseModel):
    """Documento individual en un sumario."""
    identificador: str = Field(..., description="Identificador único del documento")
    control: Optional[str] = Field(None, description="Número de control interno")
    titulo: str = Field(..., description="Título del documento")
    
    # URLs y formatos
    url_pdf: str = Field(..., description="URL del documento PDF")
    url_html: str = Field(..., description="URL del documento HTML")
    url_xml: str = Field(..., description="URL del documento XML")
    
    # Información del PDF
    size_bytes: int = Field(..., description="Tamaño en bytes")
    size_kbytes: int = Field(..., description="Tamaño en KB")
    pagina_inicial: Optional[int] = Field(None, description="Página inicial en el BOE")
    pagina_final: Optional[int] = Field(None, description="Página final en el BOE")

    @validator('identificador')
    def validate_identificador_summary(cls, v):
        # Formato: BOE-A-YYYY-NNNNN o BOE-B-YYYY-NNNNN
        pattern = r'^BOE-[AB]-\d{4}-\d{1,5}$'
        if not re.match(pattern, v):
            raise ValueError(f"Identificador de sumario inválido: {v}")
        return v


class SummaryEpigrafe(BaseModel):
    """Epígrafe dentro de una sección del sumario."""
    nombre: str = Field(..., description="Nombre del epígrafe")
    documentos: List[SummaryDocument] = Field(..., description="Documentos del epígrafe")


class SummaryDepartment(BaseModel):
    """Departamento dentro de una sección del sumario."""
    codigo: str = Field(..., description="Código del departamento")
    nombre: str = Field(..., description="Nombre del departamento")
    epigrafes: Optional[List[SummaryEpigrafe]] = Field(None, description="Epígrafes del departamento")
    documentos: Optional[List[SummaryDocument]] = Field(None, description="Documentos directos del departamento")

    @model_validator(mode='after')
    def validate_content(self):
        """Al menos debe tener epígrafes o documentos directos."""
        if not self.epigrafes and not self.documentos:
            raise ValueError("El departamento debe tener al menos epígrafes o documentos")
        return self


class SummarySection(BaseModel):
    """Sección del sumario (ej: I. Disposiciones generales)."""
    codigo: str = Field(..., description="Código de la sección")
    nombre: str = Field(..., description="Nombre de la sección")
    departamentos: List[SummaryDepartment] = Field(..., description="Departamentos de la sección")

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "1",
                "nombre": "I. Disposiciones generales",
                "departamentos": [
                    {
                        "codigo": "7723",
                        "nombre": "Jefatura del Estado"
                    }
                ]
            }
        }


class DailySummaryInfo(BaseModel):
    """Información del sumario diario."""
    identificador: str = Field(..., description="Identificador del sumario")
    url_pdf: str = Field(..., description="URL del sumario PDF completo")
    size_bytes: int = Field(..., description="Tamaño en bytes del PDF")
    size_kbytes: int = Field(..., description="Tamaño en KB del PDF")

    @validator('identificador')
    def validate_identificador_daily(cls, v):
        # Formato: BOE-S-YYYY-NNN o BORME-S-YYYY-NNN
        pattern = r'^(BOE|BORME)-S-\d{4}-\d{1,3}$'
        if not re.match(pattern, v):
            raise ValueError(f"Identificador de sumario diario inválido: {v}")
        return v


class DailyJournal(BaseModel):
    """Diario completo (BOE o BORME) para una fecha."""
    numero: str = Field(..., description="Número del diario")
    sumario_diario: DailySummaryInfo = Field(..., description="Información del sumario")
    secciones: List[SummarySection] = Field(..., description="Secciones del diario")

    @validator('numero')
    def validate_numero(cls, v):
        if not v.isdigit() or int(v) < 1:
            raise ValueError("El número de diario debe ser un entero positivo")
        return v


class Summary(BaseModel):
    """Sumario completo de una fecha (puede incluir varios diarios)."""
    metadatos: SummaryMetadata = Field(..., description="Metadatos del sumario")
    diarios: List[DailyJournal] = Field(..., description="Diarios de la fecha")

    class Config:
        json_schema_extra = {
            "example": {
                "metadatos": {
                    "publicacion": "BOE",
                    "fecha_publicacion": "20240529"
                },
                "diarios": [
                    {
                        "numero": "130",
                        "sumario_diario": {
                            "identificador": "BOE-S-2024-130"
                        }
                    }
                ]
            }
        }


# ============================================================================
# MODELOS PARA TABLAS AUXILIARES
# ============================================================================

class AuxiliaryTableEntry(BaseModel):
    """Entrada en una tabla auxiliar."""
    codigo: str = Field(..., description="Código de la entrada")
    descripcion: str = Field(..., description="Descripción de la entrada")
    activo: Optional[bool] = Field(True, description="¿Está activa?")
    fecha_creacion: Optional[str] = Field(None, description="Fecha de creación")
    fecha_modificacion: Optional[str] = Field(None, description="Fecha de última modificación")


class AuxiliaryTable(BaseModel):
    """Tabla auxiliar completa."""
    nombre: str = Field(..., description="Nombre de la tabla")
    descripcion: str = Field(..., description="Descripción de la tabla")
    fecha_actualizacion: datetime = Field(..., description="Última actualización")
    entradas: List[AuxiliaryTableEntry] = Field(..., description="Entradas de la tabla")
    total_entradas: int = Field(..., description="Total de entradas")

    @model_validator(mode='after')
    def validate_total(self):
        if self.total_entradas != len(self.entradas):
            raise ValueError("total_entradas debe coincidir con la longitud de entradas")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "departamentos",
                "descripcion": "Códigos de departamentos oficiales",
                "total_entradas": 150,
                "entradas": [
                    {
                        "codigo": "7723",
                        "descripcion": "Jefatura del Estado"
                    }
                ]
            }
        }


# ============================================================================
# MODELOS PARA BÚSQUEDAS Y CONSULTAS
# ============================================================================

class SearchQuery(BaseModel):
    """Consulta de búsqueda estructurada."""
    query_string: Optional[str] = Field(None, description="Cadena de búsqueda libre")
    fields: Optional[Dict[str, str]] = Field(None, description="Búsqueda por campos específicos")
    date_range: Optional[Dict[str, str]] = Field(None, description="Rango de fechas")
    sort: Optional[List[Dict[str, str]]] = Field(None, description="Criterios de ordenación")

    @validator('date_range')
    def validate_date_range(cls, v):
        if v:
            for key, value in v.items():
                if key not in ['gte', 'lte', 'gt', 'lt']:
                    raise ValueError(f"Operador de rango inválido: {key}")
                if len(value) == 8:
                    try:
                        datetime.strptime(value, '%Y%m%d')
                    except ValueError:
                        raise ValueError(f"Fecha inválida en rango: {value}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "query_string": "crisis sanitaria",
                "fields": {
                    "titulo": "Ley 40/2015",
                    "departamento@codigo": "7723"
                },
                "date_range": {
                    "gte": "20200101",
                    "lte": "20201231"
                },
                "sort": [
                    {"fecha_publicacion": "desc"},
                    {"titulo": "asc"}
                ]
            }
        }


class SearchParameters(BaseModel):
    """Parámetros para búsquedas en la API."""
    query: Optional[SearchQuery] = Field(None, description="Consulta estructurada")
    from_date: Optional[str] = Field(None, description="Fecha inicio (AAAAMMDD)")
    to_date: Optional[str] = Field(None, description="Fecha fin (AAAAMMDD)")
    offset: int = Field(0, description="Primer resultado a devolver")
    limit: int = Field(50, description="Número máximo de resultados")

    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError("El limit debe estar entre 1 y 1000")
        return v

    @validator('offset')
    def validate_offset(cls, v):
        if v < 0:
            raise ValueError("El offset debe ser >= 0")
        return v

    @validator('from_date', 'to_date')
    def validate_search_dates(cls, v):
        if v and len(v) == 8:
            try:
                datetime.strptime(v, '%Y%m%d')
            except ValueError:
                raise ValueError(f"Fecha inválida: {v}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "from_date": "20200101",
                "to_date": "20201231",
                "offset": 0,
                "limit": 50
            }
        }


# ============================================================================
# MODELOS PARA RESPUESTAS DE ERROR
# ============================================================================

class APIError(BaseModel):
    """Error de la API del BOE."""
    codigo: int = Field(..., description="Código de error HTTP")
    mensaje: str = Field(..., description="Mensaje de error")
    detalles: Optional[str] = Field(None, description="Detalles adicionales del error")
    timestamp: datetime = Field(default_factory=datetime.now, description="Momento del error")

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": 404,
                "mensaje": "La información solicitada no existe",
                "detalles": "El identificador BOE-A-2025-99999 no se encontró",
                "timestamp": "2025-01-23T10:30:00Z"
            }
        }


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def validate_boe_identifier(identifier: str) -> bool:
    """Valida que un identificador BOE tenga el formato correcto."""
    pattern = r'^(BOE|BORME)-S-\d{4}-\d{1,3}$'
    return bool(re.match(pattern, identifier))


def validate_date_format(date_str: str) -> bool:
    """Valida que una fecha tenga el formato AAAAMMDD."""
    if len(date_str) != 8:
        return False
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False


def format_date_for_api(date_input: Union[str, datetime]) -> str:
    """Convierte una fecha al formato AAAAMMDD requerido por la API."""
    if isinstance(date_input, datetime):
        return date_input.strftime('%Y%m%d')
    elif isinstance(date_input, str):
        if validate_date_format(date_input):
            return date_input
        else:
            # Intenta parsear otros formatos comunes
            try:
                dt = datetime.strptime(date_input, '%Y-%m-%d')
                return dt.strftime('%Y%m%d')
            except ValueError:
                raise ValueError(f"Formato de fecha no reconocido: {date_input}")
    else:
        raise ValueError("La fecha debe ser str o datetime")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Modelos base
    'CodedValue',
    'APIResponse',
    'APIError',
    
    # Legislación consolidada
    'ConsolidatedLawMetadata',
    'LawMatter',
    'LawNote', 
    'LawReference',
    'LawAnalysis',
    'TextBlockVersion',
    'TextBlock',
    'ConsolidatedLaw',
    'ConsolidatedLawSearchResult',
    
    # Sumarios
    'SummaryMetadata',
    'SummaryDocument',
    'SummaryEpigrafe',
    'SummaryDepartment',
    'SummarySection',
    'DailySummaryInfo',
    'DailyJournal',
    'Summary',
    
    # Tablas auxiliares
    'AuxiliaryTableEntry',
    'AuxiliaryTable',
    
    # Búsquedas
    'SearchQuery',
    'SearchParameters',
    
    # Utilidades
    'validate_boe_identifier',
    'validate_date_format',
    'format_date_for_api',
]