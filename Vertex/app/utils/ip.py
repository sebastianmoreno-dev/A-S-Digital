"""Resolución de la IP real del visitante detrás de Cloudflare."""
from flask import request


def get_client_ip() -> str:
    """Devuelve la IP real del cliente.

    Cloudflare siempre inyecta CF-Connecting-IP con la IP original del
    visitante, sin importar cuántos proxies haya detrás (Nginx, etc.).
    Es más confiable que X-Forwarded-For, que puede traer una lista y
    depende de que cada hop lo respete correctamente.
    """
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip.strip()

    xff = request.headers.get('X-Forwarded-For')
    if xff:
        return xff.split(',')[0].strip()

    return request.remote_addr or '0.0.0.0'
