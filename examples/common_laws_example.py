#!/usr/bin/env python3
"""
Ejemplo de uso del diccionario de leyes comunes del BOE.

Este script muestra cómo utilizar el diccionario de identificadores
de las leyes españolas más importantes.
"""

import asyncio
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp_boe.data.common_laws import (
    COMMON_LAWS,
    LAW_CATEGORIES,
    CONSTITUCION,
    LOPD,
    LEY_39_2015,
    LEY_40_2015,
    get_laws_by_category,
    search_laws_by_keyword,
    get_recent_laws
)
from mcp_boe.utils.http_client import BOEHTTPClient
from mcp_boe.tools.legislation import LegislationTools


async def show_common_laws():
    """Muestra las leyes comunes del diccionario."""
    print("=" * 80)
    print("📚 DICCIONARIO DE LEYES ESPAÑOLAS IMPORTANTES")
    print("=" * 80)
    print()
    
    # Mostrar categorías disponibles
    print("CATEGORÍAS DISPONIBLES:")
    print("-" * 40)
    for cat_key, cat_desc in LAW_CATEGORIES.items():
        laws_count = len(get_laws_by_category(cat_key))
        print(f"  • {cat_key}: {cat_desc} ({laws_count} leyes)")
    print()
    
    # Mostrar algunas leyes importantes
    print("LEYES FUNDAMENTALES:")
    print("-" * 40)
    fundamental_laws = get_laws_by_category("fundamental")
    for law_id, law_info in fundamental_laws:
        print(f"  📜 {law_info['titulo']}")
        print(f"     ID: {law_id}")
        print(f"     {law_info['descripcion']}")
        print()
    
    # Búsqueda de ejemplo
    print("BÚSQUEDA POR PALABRA CLAVE - 'datos':")
    print("-" * 40)
    data_laws = search_laws_by_keyword("datos")
    for law_id, law_info in data_laws:
        print(f"  🔐 {law_info['titulo']}")
        print(f"     ID: {law_id}")
        print()
    
    # Leyes recientes
    print("LEYES IMPORTANTES DE LOS ÚLTIMOS 5 AÑOS:")
    print("-" * 40)
    recent = get_recent_laws(5)
    for law_id, law_info in recent:
        print(f"  📅 {law_info['titulo']} ({law_info['fecha']})")
        print(f"     ID: {law_id}")
        print()


async def get_law_example():
    """Ejemplo de cómo obtener una ley usando su ID del diccionario."""
    print("=" * 80)
    print("📖 EJEMPLO: OBTENER LA CONSTITUCIÓN ESPAÑOLA")
    print("=" * 80)
    print()
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Usar el ID de la Constitución desde el diccionario
        print(f"Obteniendo la ley con ID: {CONSTITUCION}")
        print("-" * 40)
        
        result = await tools.get_consolidated_law({
            "law_id": CONSTITUCION,
            "include_metadata": True,
            "include_analysis": False,
            "include_full_text": False
        })
        
        if result:
            print(result[0].text)


async def compare_search_methods():
    """Compara la búsqueda por texto (que no funciona) con el uso del diccionario."""
    print("=" * 80)
    print("⚖️ COMPARACIÓN: BÚSQUEDA vs DICCIONARIO")
    print("=" * 80)
    print()
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Intento 1: Búsqueda por texto (NO funciona correctamente)
        print("1️⃣ BÚSQUEDA POR TEXTO (Método problemático):")
        print("-" * 40)
        print("Buscando: 'Ley 39/2015'")
        
        search_results = await tools.search_consolidated_legislation({
            "query": "Ley 39/2015",
            "limit": 3
        })
        
        if search_results:
            # Mostrar solo primeras líneas para no saturar
            lines = search_results[0].text.split('\n')
            for line in lines[:15]:
                print(line)
        print()
        print("⚠️ NOTA: Los resultados pueden NO corresponder a la búsqueda")
        print()
        
        # Intento 2: Uso del diccionario (SÍ funciona)
        print("2️⃣ USO DEL DICCIONARIO (Método recomendado):")
        print("-" * 40)
        print(f"Obteniendo directamente con ID: {LEY_39_2015}")
        
        direct_result = await tools.get_consolidated_law({
            "law_id": LEY_39_2015,
            "include_metadata": True,
            "include_analysis": False,
            "include_full_text": False
        })
        
        if direct_result:
            # Mostrar solo primeras líneas
            lines = direct_result[0].text.split('\n')
            for line in lines[:15]:
                print(line)
        print()
        print("✅ NOTA: Este método garantiza obtener la norma correcta")


async def main():
    """Función principal del ejemplo."""
    try:
        # Mostrar el diccionario de leyes
        await show_common_laws()
        
        # Ejemplo de obtención de una ley
        await get_law_example()
        
        # Comparación de métodos
        await compare_search_methods()
        
        print("=" * 80)
        print("✅ EJEMPLO COMPLETADO")
        print("=" * 80)
        print()
        print("💡 CONCLUSIONES:")
        print("  • Use el diccionario de IDs para acceder a leyes importantes")
        print("  • Evite la búsqueda por texto en legislación consolidada")
        print("  • Para leyes no incluidas, use filtros por fecha o departamento")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())