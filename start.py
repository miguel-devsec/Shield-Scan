#!/usr/bin/env python3
"""
Script de inicio para WordPress Security Auditor
"""

import uvicorn
import sys
import os
from pathlib import Path

def main():
    """Función principal para iniciar el servidor"""

    # Verificar que estamos en el directorio correcto
    if not Path("main.py").exists():
        print("❌ Error: No se encontró main.py en el directorio actual")
        print("   Asegúrate de ejecutar este script desde el directorio del proyecto")
        sys.exit(1)

    # Verificar dependencias
    try:
        import fastapi
        import httpx
        import jinja2
        print("✅ Dependencias verificadas correctamente")
    except ImportError as e:
        print(f"❌ Error: Dependencias faltantes: {e}")
        print("   Ejecuta: pip install -r requirements.txt")
        sys.exit(1)

    # Configuración del servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    print("🚀 Iniciando WordPress Security Auditor...")
    print(f"   Host: {host}")
    print(f"   Puerto: {port}")
    print(f"   Debug: {debug}")
    print(f"   URL: http://{host}:{port}")
    print("\n📋 Características disponibles:")
    print("   • Auditoría de headers de seguridad")
    print("   • Verificación de WordPress")
    print("   • Generación de reportes profesionales")
    print("   • API REST completa")
    print("\n🔒 Presiona Ctrl+C para detener el servidor")
    print("-" * 50)

    try:
        # Iniciar servidor
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info" if not debug else "debug"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido. ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
