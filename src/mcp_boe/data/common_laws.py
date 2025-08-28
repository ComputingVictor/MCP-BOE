"""
Diccionario de leyes españolas frecuentemente consultadas.

Este módulo contiene identificadores BOE de las normas más importantes
y consultadas del ordenamiento jurídico español.
"""

from typing import Dict, List, Tuple
from datetime import datetime

# Diccionario principal de leyes importantes
COMMON_LAWS: Dict[str, Dict[str, str]] = {
    # Constitución y Leyes Fundamentales
    "BOE-A-1978-31229": {
        "titulo": "Constitución Española",
        "fecha": "1978-12-29",
        "categoria": "fundamental",
        "descripcion": "Norma suprema del ordenamiento jurídico español"
    },
    
    # Leyes Orgánicas principales
    "BOE-A-1985-5392": {
        "titulo": "Ley Orgánica 6/1985 del Poder Judicial (LOPJ)",
        "fecha": "1985-07-02", 
        "categoria": "organica",
        "descripcion": "Organización y funcionamiento del Poder Judicial"
    },
    "BOE-A-2018-16673": {
        "titulo": "Ley Orgánica 3/2018 de Protección de Datos (LOPDGDD)",
        "fecha": "2018-12-06",
        "categoria": "organica",
        "descripcion": "Protección de datos personales y garantía de derechos digitales"
    },
    "BOE-A-1995-25444": {
        "titulo": "Ley Orgánica 10/1995 del Código Penal",
        "fecha": "1995-11-24",
        "categoria": "organica",
        "descripcion": "Código Penal español"
    },
    
    # Procedimiento Administrativo
    "BOE-A-2015-10565": {
        "titulo": "Ley 39/2015 del Procedimiento Administrativo Común",
        "fecha": "2015-10-02",
        "categoria": "procedimiento",
        "descripcion": "Procedimiento administrativo común de las Administraciones Públicas"
    },
    "BOE-A-2015-10566": {
        "titulo": "Ley 40/2015 de Régimen Jurídico del Sector Público",
        "fecha": "2015-10-02",
        "categoria": "procedimiento",
        "descripcion": "Régimen jurídico del sector público"
    },
    
    # Derecho Civil
    "BOE-A-1889-4763": {
        "titulo": "Real Decreto de 24 de julio de 1889 - Código Civil",
        "fecha": "1889-07-25",
        "categoria": "civil",
        "descripcion": "Código Civil español"
    },
    "BOE-A-2000-323": {
        "titulo": "Ley 1/2000 de Enjuiciamiento Civil",
        "fecha": "2000-01-08",
        "categoria": "civil",
        "descripcion": "Ley de Enjuiciamiento Civil"
    },
    
    # Derecho Laboral
    "BOE-A-2015-11430": {
        "titulo": "Real Decreto Legislativo 2/2015 - Estatuto de los Trabajadores",
        "fecha": "2015-10-24",
        "categoria": "laboral",
        "descripcion": "Texto refundido del Estatuto de los Trabajadores"
    },
    "BOE-A-2015-11724": {
        "titulo": "Real Decreto Legislativo 5/2015 - Estatuto Básico del Empleado Público",
        "fecha": "2015-10-31",
        "categoria": "laboral",
        "descripcion": "Texto refundido del Estatuto Básico del Empleado Público"
    },
    
    # Derecho Mercantil
    "BOE-A-2010-10544": {
        "titulo": "Real Decreto Legislativo 1/2010 - Ley de Sociedades de Capital",
        "fecha": "2010-07-03",
        "categoria": "mercantil",
        "descripcion": "Texto refundido de la Ley de Sociedades de Capital"
    },
    "BOE-A-1885-6627": {
        "titulo": "Real Decreto de 22 de agosto de 1885 - Código de Comercio",
        "fecha": "1885-10-16",
        "categoria": "mercantil",
        "descripcion": "Código de Comercio"
    },
    
    # Contratos del Sector Público
    "BOE-A-2017-12902": {
        "titulo": "Ley 9/2017 de Contratos del Sector Público",
        "fecha": "2017-11-09",
        "categoria": "contratacion",
        "descripcion": "Contratos del Sector Público"
    },
    
    # Jurisdicción Contencioso-Administrativa
    "BOE-A-1998-16718": {
        "titulo": "Ley 29/1998 de la Jurisdicción Contencioso-administrativa",
        "fecha": "1998-07-14",
        "categoria": "procesal",
        "descripcion": "Reguladora de la Jurisdicción Contencioso-administrativa"
    },
    
    # Propiedad Intelectual
    "BOE-A-1996-8930": {
        "titulo": "Real Decreto Legislativo 1/1996 - Ley de Propiedad Intelectual",
        "fecha": "1996-04-22",
        "categoria": "propiedad_intelectual",
        "descripcion": "Texto refundido de la Ley de Propiedad Intelectual"
    },
    
    # Protección de Consumidores
    "BOE-A-2007-20555": {
        "titulo": "Real Decreto Legislativo 1/2007 - Ley General de Consumidores",
        "fecha": "2007-11-30",
        "categoria": "consumo",
        "descripcion": "Texto refundido de la Ley General para la Defensa de los Consumidores"
    },
    
    # Transparencia
    "BOE-A-2013-12887": {
        "titulo": "Ley 19/2013 de Transparencia y Buen Gobierno",
        "fecha": "2013-12-10",
        "categoria": "transparencia",
        "descripcion": "Transparencia, acceso a la información pública y buen gobierno"
    },
    
    # Igualdad
    "BOE-A-2007-6115": {
        "titulo": "Ley Orgánica 3/2007 para la Igualdad Efectiva",
        "fecha": "2007-03-23",
        "categoria": "igualdad",
        "descripcion": "Igualdad efectiva de mujeres y hombres"
    },
    
    # Educación
    "BOE-A-2020-17264": {
        "titulo": "Ley Orgánica 3/2020 de Educación (LOMLOE)",
        "fecha": "2020-12-30",
        "categoria": "educacion",
        "descripcion": "Ley Orgánica de modificación de la LOE"
    },
    
    # Sanidad
    "BOE-A-1986-10499": {
        "titulo": "Ley 14/1986 General de Sanidad",
        "fecha": "1986-04-29",
        "categoria": "sanidad",
        "descripcion": "Ley General de Sanidad"
    }
}

# Categorías de leyes para filtrado rápido
LAW_CATEGORIES = {
    "fundamental": "Normas fundamentales y Constitución",
    "organica": "Leyes Orgánicas",
    "procedimiento": "Procedimiento Administrativo",
    "civil": "Derecho Civil",
    "laboral": "Derecho Laboral",
    "mercantil": "Derecho Mercantil",
    "contratacion": "Contratación Pública",
    "procesal": "Derecho Procesal",
    "propiedad_intelectual": "Propiedad Intelectual",
    "consumo": "Consumo y Protección al Consumidor",
    "transparencia": "Transparencia y Buen Gobierno",
    "igualdad": "Igualdad",
    "educacion": "Educación",
    "sanidad": "Sanidad"
}

def get_laws_by_category(categoria: str) -> List[Tuple[str, Dict[str, str]]]:
    """
    Obtiene todas las leyes de una categoría específica.
    
    Args:
        categoria: Categoría de las leyes a buscar
        
    Returns:
        Lista de tuplas (id_boe, información_ley)
    """
    return [
        (law_id, law_info) 
        for law_id, law_info in COMMON_LAWS.items() 
        if law_info.get("categoria") == categoria
    ]

def search_laws_by_keyword(keyword: str) -> List[Tuple[str, Dict[str, str]]]:
    """
    Busca leyes que contengan una palabra clave en su título o descripción.
    
    Args:
        keyword: Palabra clave a buscar
        
    Returns:
        Lista de tuplas (id_boe, información_ley)
    """
    keyword_lower = keyword.lower()
    return [
        (law_id, law_info)
        for law_id, law_info in COMMON_LAWS.items()
        if keyword_lower in law_info["titulo"].lower() or 
           keyword_lower in law_info["descripcion"].lower()
    ]

def get_law_info(law_id: str) -> Dict[str, str]:
    """
    Obtiene la información de una ley específica.
    
    Args:
        law_id: Identificador BOE de la ley
        
    Returns:
        Información de la ley o dict vacío si no existe
    """
    return COMMON_LAWS.get(law_id, {})

def get_recent_laws(years_back: int = 5) -> List[Tuple[str, Dict[str, str]]]:
    """
    Obtiene las leyes publicadas en los últimos años.
    
    Args:
        years_back: Número de años hacia atrás desde hoy
        
    Returns:
        Lista de tuplas (id_boe, información_ley)
    """
    current_year = datetime.now().year
    min_year = current_year - years_back
    
    recent_laws = []
    for law_id, law_info in COMMON_LAWS.items():
        try:
            law_date = datetime.strptime(law_info["fecha"], "%Y-%m-%d")
            if law_date.year >= min_year:
                recent_laws.append((law_id, law_info))
        except ValueError:
            continue
    
    return sorted(recent_laws, key=lambda x: x[1]["fecha"], reverse=True)

# Alias útiles para acceso rápido
CONSTITUCION = "BOE-A-1978-31229"
LOPD = "BOE-A-2018-16673"
LEY_39_2015 = "BOE-A-2015-10565"
LEY_40_2015 = "BOE-A-2015-10566"
CODIGO_CIVIL = "BOE-A-1889-4763"
CODIGO_PENAL = "BOE-A-1995-25444"
ESTATUTO_TRABAJADORES = "BOE-A-2015-11430"
LEY_CONTRATOS = "BOE-A-2017-12902"