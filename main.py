#!/usr/bin/env python3
"""
Tech Web Server - Servidor web alternativo a Apache2
Construido con Python y asyncio para alta concurrencia
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from server.web_server import main

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 TECH WEB SERVER")
    print("Servidor web de alta concurrencia con Python")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
