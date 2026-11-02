"""
Utilidades de red y resolución determinista de IP de cliente.
"""

import ipaddress
from typing import Sequence

PROXY_HEADERS: Sequence[str] = (
    'X-Forwarded-For',
    'X-Real-IP',
    'X-Client-IP',
    'CF-Connecting-IP',
    'True-Client-IP',
)


def is_valid_ip(ip: str) -> bool:
    """
    Valida si una cadena es una dirección IPv4 o IPv6 válida.

    WHEN `ip` tiene formato IPv4 o IPv6 válido THEN retorna `True`.
    IF `ip` es inválida o vacía THEN retorna `False`.
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def get_real_client_ip(request, proxy_support_enabled: bool = True) -> str:
    """
    Obtiene la dirección IP real del cliente evaluando cabeceras de proxy reverso.

    IF `proxy_support_enabled` es `False` THEN retorna `request.remote` o `'127.0.0.1'`.
    WHEN `proxy_support_enabled` es `True` THEN inspecciona `PROXY_HEADERS` en orden
    de prioridad y retorna la primera IP válida encontrada.
    """
    if not proxy_support_enabled:
        return getattr(request, 'remote', None) or '127.0.0.1'

    headers = getattr(request, 'headers', {}) or {}
    for header in PROXY_HEADERS:
        if header in headers:
            ip_value = headers[header].strip()
            if ip_value:
                if ',' in ip_value:
                    ip_value = ip_value.split(',')[0].strip()
                if is_valid_ip(ip_value):
                    return ip_value

    return getattr(request, 'remote', None) or '127.0.0.1'

