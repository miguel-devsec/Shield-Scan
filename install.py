#!/usr/bin/env python3
"""
Script de instalación para WordPress Security Auditor
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Verifica la versión de Python"""
    print("🐍 Verificando versión de Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detectado")
        print("   Se requiere Python 3.8 o superior")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_pip():
    """Verifica que pip esté disponible"""
    print("📦 Verificando pip...")
    
    try:
        import pip
        print("✅ pip disponible")
        return True
    except ImportError:
        print("❌ pip no encontrado")
        print("   Instala pip: https://pip.pypa.io/en/stable/installation/")
        return False

def install_dependencies():
    """Instala las dependencias del proyecto"""
    print("📦 Instalando dependencias...")
    
    try:
        # Actualizar pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip actualizado")
        
        # Instalar dependencias
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencias instaladas")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def create_directories():
    """Crea directorios necesarios"""
    print("📁 Creando directorios...")
    
    directories = ['static', 'reports', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directorio {directory}/ creado")
    
    return True

def create_env_file():
    """Crea archivo .env si no existe"""
    print("⚙️ Configurando variables de entorno...")
    
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# WordPress Security Auditor - Configuración
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# Configuración de auditoría
REQUEST_TIMEOUT=30.0
MAX_REDIRECTS=5

# Configuración de reportes
COMPANY_NAME=Equipo de Seguridad y Operaciones
AUDITOR_NAME=Equipo de Seguridad y Operaciones
CITY=Bogotá, Colombia
"""
        env_file.write_text(env_content)
        print("✅ Archivo .env creado")
    else:
        print("✅ Archivo .env ya existe")
    
    return True

def test_installation():
    """Prueba la instalación"""
    print("🧪 Probando instalación...")
    
    try:
        # Importar módulos principales
        import fastapi
        import httpx
        import jinja2
        import uvicorn
        
        print("✅ Módulos principales importados correctamente")
        
        # Probar configuración
        from config import Config
        print("✅ Configuración cargada correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def show_next_steps():
    """Muestra los siguientes pasos"""
    print("\n" + "=" * 60)
    print("🎉 ¡Instalación completada exitosamente!")
    print("=" * 60)
    print("\n📋 Próximos pasos:")
    print("   1. Ejecutar pruebas: python test_auditor.py")
    print("   2. Iniciar servidor: python start.py")
    print("   3. Abrir navegador: http://localhost:8000")
    print("\n🐳 Para usar Docker:")
    print("   docker-compose up --build")
    print("\n📚 Documentación:")
    print("   Ver README.md para más información")
    print("\n🆘 Soporte:")
    print("   Crear issue en el repositorio para reportar problemas")

def main():
    """Función principal de instalación"""
    print("🚀 WordPress Security Auditor - Instalador")
    print("=" * 60)
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Verificar pip
    if not check_pip():
        sys.exit(1)
    
    # Crear directorios
    if not create_directories():
        sys.exit(1)
    
    # Instalar dependencias
    if not install_dependencies():
        sys.exit(1)
    
    # Crear archivo .env
    if not create_env_file():
        sys.exit(1)
    
    # Probar instalación
    if not test_installation():
        print("⚠️ Instalación completada con advertencias")
        print("   Algunos módulos podrían no funcionar correctamente")
    else:
        print("✅ Instalación verificada correctamente")
    
    # Mostrar siguientes pasos
    show_next_steps()

if __name__ == "__main__":
    main()
