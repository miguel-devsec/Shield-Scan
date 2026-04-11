#!/usr/bin/env python3
"""
Script de prueba para las verificaciones generales de seguridad
"""

import asyncio
import sys
import os

# Agregar el directorio actual al path para importar main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import WordPressSecurityChecker

async def test_general_security():
    """Prueba las verificaciones generales de seguridad"""
    
    # Sitios de prueba (no WordPress)
    test_sites = [
        {
            'url': 'https://github.com',
            'name': 'GitHub (no WordPress)'
        },
        {
            'url': 'https://www.google.com',
            'name': 'Google (no WordPress)'
        },
        {
            'url': 'https://gopass.com.co/',
            'name': 'GoPass (no WordPress)'
        }
    ]
    
    print("Probando Verificaciones Generales de Seguridad")
    print("=" * 60)
    
    async with WordPressSecurityChecker() as checker:
        for site in test_sites:
            print(f"\nProbando: {site['name']}")
            print(f"URL: {site['url']}")
            print("-" * 40)
            
            try:
                result = await checker.check_general_security(site['url'])
                
                print(f"Resultado: {result['message']}")
                print(f"Estado: {result['status']}")
                print(f"Servidor: {result.get('server_technology', 'Unknown')}")
                
                if result.get('detected_technologies'):
                    print(f"Tecnologias: {', '.join(result['detected_technologies'])}")
                
                if result.get('detected_frameworks'):
                    print(f"Frameworks: {', '.join(result['detected_frameworks'])}")
                
                if result.get('exposed_sensitive_files'):
                    print(f"Archivos expuestos: {', '.join(result['exposed_sensitive_files'])}")
                else:
                    print("Archivos expuestos: Ninguno")
                
                print(f"Explicacion: {result.get('risk_explanation', 'N/A')}")
                print(f"Recomendacion: {result.get('recommendation', 'N/A')}")
                
            except Exception as e:
                print(f"Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Pruebas completadas")

if __name__ == "__main__":
    asyncio.run(test_general_security())
