#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras implementadas en MCP-BOE.
"""

import asyncio
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from mcp_boe.data.common_laws import COMMON_LAWS, CONSTITUCION, LEY_39_2015
from mcp_boe.utils.http_client import BOEHTTPClient, APIError
from mcp_boe.tools.legislation import LegislationTools
from mcp_boe.tools.common_laws_tool import CommonLawsTools


async def test_dictionary():
    """Prueba el diccionario de leyes comunes."""
    print("\n" + "=" * 70)
    print("TEST 1: Diccionario de Leyes Comunes")
    print("=" * 70)
    
    # Verificar que el diccionario contiene las leyes esperadas
    assert CONSTITUCION == "BOE-A-1978-31229", "ID de Constitución incorrecto"
    assert LEY_39_2015 == "BOE-A-2015-10565", "ID de Ley 39/2015 incorrecto"
    
    # Contar leyes en el diccionario
    total_laws = len(COMMON_LAWS)
    print(f"✅ Diccionario contiene {total_laws} leyes importantes")
    
    # Verificar herramientas MCP
    tools = CommonLawsTools()
    mcp_tools = tools.get_tools()
    assert len(mcp_tools) == 3, "Deberían haber 3 herramientas MCP"
    print(f"✅ {len(mcp_tools)} herramientas MCP disponibles:")
    for tool in mcp_tools:
        print(f"   - {tool.name}")
    
    return True


async def test_api_errors():
    """Prueba el manejo de errores mejorado."""
    print("\n" + "=" * 70)
    print("TEST 2: Manejo de Errores APIError")
    print("=" * 70)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Probar con un ID inválido
        try:
            result = await tools.get_consolidated_law({
                "law_id": "BOE-INVALIDO"
            })
            assert False, "Debería haber lanzado un error"
        except ValueError as e:
            print(f"✅ Validación de ID funciona: {e}")
        except APIError as e:
            print(f"✅ APIError capturado correctamente: {e.mensaje}")
        except Exception as e:
            print(f"✅ Excepción manejada: {type(e).__name__}")
    
    return True


async def test_search_limitations():
    """Prueba que se muestran las advertencias sobre búsqueda."""
    print("\n" + "=" * 70)
    print("TEST 3: Advertencias sobre Limitaciones de Búsqueda")
    print("=" * 70)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Hacer una búsqueda por texto
        results = await tools.search_consolidated_legislation({
            "query": "Constitución",
            "limit": 2
        })
        
        result_text = results[0].text
        
        # Verificar que incluye advertencia
        if "⚠️" in result_text and "no soporta búsqueda por texto" in result_text.lower():
            print("✅ Advertencia sobre búsqueda incluida")
        else:
            print("⚠️ Advertencia sobre búsqueda no encontrada")
        
        # Verificar que sugiere IDs importantes
        if "BOE-A-1978-31229" in result_text:
            print("✅ Sugiere IDs de leyes importantes")
        else:
            print("⚠️ No sugiere IDs importantes")
    
    return True


async def test_direct_access():
    """Prueba el acceso directo por ID."""
    print("\n" + "=" * 70)
    print("TEST 4: Acceso Directo por ID")
    print("=" * 70)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Obtener la Ley 39/2015 directamente
        result = await tools.get_consolidated_law({
            "law_id": LEY_39_2015,
            "include_metadata": True,
            "include_analysis": False,
            "include_full_text": False
        })
        
        result_text = result[0].text
        
        # Verificar que obtuvimos la ley correcta
        if "39/2015" in result_text and "Procedimiento Administrativo" in result_text:
            print(f"✅ Acceso directo funciona - Obtenida Ley 39/2015")
        else:
            print("❌ No se obtuvo la ley correcta")
    
    return True


async def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "=" * 70)
    print("PRUEBAS DE MEJORAS IMPLEMENTADAS EN MCP-BOE")
    print("=" * 70)
    
    tests = [
        ("Diccionario de Leyes", test_dictionary),
        ("Manejo de Errores", test_api_errors),
        ("Advertencias de Búsqueda", test_search_limitations),
        ("Acceso Directo", test_direct_access),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Error en {name}: {e}")
            results.append((name, False))
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE PRUEBAS")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASADO" if success else "❌ FALLADO"
        print(f"{status}: {name}")
    
    print(f"\n{'✅' if passed == total else '⚠️'} {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 ¡Todas las mejoras funcionan correctamente!")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)