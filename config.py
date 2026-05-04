"""
Configuración para WordPress Security Auditor
"""

import os
from typing import List, Dict, Any

class Config:
    """Configuración de la aplicación"""

    # Configuración del servidor
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Configuración de auditoría
    REQUEST_TIMEOUT = 30.0
    MAX_REDIRECTS = 5
    USER_AGENT = "WordPress Security Auditor/1.0.0"

    # Configuración de reportes
    SHOW_WP_DETECTION_INDICATORS = os.getenv("SHOW_WP_DETECTION_INDICATORS", "False").lower() == "true"
    SHOW_TECHNICAL_DETAILS = os.getenv("SHOW_TECHNICAL_DETAILS", "False").lower() == "true"
    PRODUCTION_MODE = os.getenv("PRODUCTION_MODE", "True").lower() == "true"

    # Versión de la aplicación
    VERSION = "1.2.0"

    # Headers de seguridad críticos
    CRITICAL_SECURITY_HEADERS = [
        'Strict-Transport-Security',
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection'
    ]

    # Headers de seguridad recomendados
    RECOMMENDED_SECURITY_HEADERS = [
        'Content-Security-Policy',
        'Referrer-Policy',
        'Permissions-Policy'
    ]

    # Rutas de WordPress a verificar
    WORDPRESS_PATHS = {
        'wp_admin': '/wp-admin/',
        'xmlrpc': '/xmlrpc.php',
        'wp_config': '/wp-config.php',
        'wp_content': '/wp-content/',
        'wp_includes': '/wp-includes/',
        'wp_login': '/wp-login.php'
    }

    # Configuración de reportes
    REPORT_CONFIG = {
        'company_name': 'ArthurTech',
        'auditor_name': 'ArthurTech - Equipo de Seguridad y Operaciones',
        'city': 'Bogotá, Colombia',
        'version': '1.1.0'
    }

    # Estados de seguridad
    SECURITY_STATUS = {
        'PASS': {
            'color': '#28a745',
            'icon': '✅',
            'description': 'Configuración correcta'
        },
        'WARNING': {
            'color': '#ffc107',
            'icon': '⚠️',
            'description': 'Mejora recomendada'
        },
        'CRITICAL': {
            'color': '#dc3545',
            'icon': '🚨',
            'description': 'Vulnerabilidad crítica'
        },
        'ERROR': {
            'color': '#6c757d',
            'icon': '❌',
            'description': 'Error en la verificación'
        }
    }

    # Recomendaciones por tipo de hallazgo
    RECOMMENDATIONS = {
        'missing_hsts': 'Implementar Strict-Transport-Security para forzar HTTPS',
        'missing_xcto': 'Agregar X-Content-Type-Options: nosniff',
        'missing_xfo': 'Configurar X-Frame-Options para prevenir clickjacking',
        'missing_csp': 'Implementar Content-Security-Policy',
        'wp_admin_exposed': 'Restringir acceso a wp-admin con autenticación, IP whitelist, o cambiar URL de login',
        'xmlrpc_enabled': 'Deshabilitar XML-RPC completamente mediante .htaccess, plugin de seguridad, o configuración del servidor',
        'wp_config_exposed': 'Mover wp-config.php fuera del directorio web público o configurar el servidor para denegar el acceso',
        'directory_listing': 'Deshabilitar el listado de directorios en el servidor web (Apache: Options -Indexes, Nginx: autoindex off)',
        'no_ssl': 'Implementar certificado SSL válido y configurar redirección automática de HTTP a HTTPS'
    }

    # Explicaciones de riesgo detalladas
    RISK_EXPLANATIONS = {
        'wp_admin_login_exposed': 'CRÍTICO: El panel de login de WordPress es accesible públicamente. Esto permite a atacantes realizar ataques de fuerza bruta, identificar usuarios válidos y explotar vulnerabilidades conocidas en wp-login.php.',
        'xmlrpc_enabled': 'CRÍTICO: XML-RPC está habilitado y accesible. Esto permite ataques de fuerza bruta masivos, ataques DDoS amplificados, y explotación de vulnerabilidades remotas.',
        'wp_config_exposed': 'CRÍTICO: El archivo wp-config.php está accesible públicamente. Esto puede revelar información sobre la configuración del sitio, rutas del servidor, y otros datos sensibles.',
        'wp_config_credentials_exposed': 'CRÍTICO: El archivo wp-config.php está accesible públicamente y contiene credenciales de base de datos. Esto permite a atacantes obtener acceso completo a la base de datos.',
        'directory_listing_enabled': 'CRÍTICO: El listado de directorios está habilitado. Esto permite a atacantes explorar la estructura del sitio, identificar archivos sensibles, y planificar ataques más precisos.',
        'no_ssl': 'CRÍTICO: El sitio no utiliza HTTPS, lo que significa que toda la comunicación es transmitida en texto plano. Esto permite a atacantes interceptar credenciales y cookies de sesión.'
    }

    # Configuración de logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def get_security_headers_config(cls) -> Dict[str, Dict[str, Any]]:
        """Obtiene configuración de headers de seguridad"""
        return {
            'Strict-Transport-Security': {
                'required': True,
                'description': 'HSTS - Fuerza conexiones HTTPS',
                'recommended': 'max-age=31536000; includeSubDomains; preload',
                'priority': 'HIGH'
            },
            'X-Content-Type-Options': {
                'required': True,
                'description': 'Previene MIME type sniffing',
                'recommended': 'nosniff',
                'priority': 'HIGH'
            },
            'X-Frame-Options': {
                'required': True,
                'description': 'Previene clickjacking',
                'recommended': 'DENY o SAMEORIGIN',
                'priority': 'HIGH'
            },
            'X-XSS-Protection': {
                'required': True,
                'description': 'Protección XSS del navegador',
                'recommended': '1; mode=block',
                'priority': 'HIGH'
            },
            'Content-Security-Policy': {
                'required': False,
                'description': 'Política de seguridad de contenido',
                'recommended': 'default-src \'self\'',
                'priority': 'MEDIUM'
            },
            'Referrer-Policy': {
                'required': False,
                'description': 'Control de información de referrer',
                'recommended': 'strict-origin-when-cross-origin',
                'priority': 'MEDIUM'
            },
            'Permissions-Policy': {
                'required': False,
                'description': 'Control de permisos de navegador',
                'recommended': 'geolocation=(), microphone=(), camera=()',
                'priority': 'LOW'
            }
        }
