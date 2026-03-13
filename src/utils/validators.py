from __future__ import annotations

import ipaddress


def is_valid_ipv4(ip: str) -> bool:
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False


def is_non_empty(value: str | None) -> bool:
    return bool(value and value.strip())


def is_valid_location(location: str) -> bool:
    # Por ahora solo verificamos que no esté vacío
    # Se puede endurecer después según reglas de negocio
    return is_non_empty(location)


def normalize_string(value: str | None) -> str:
    return value.strip() if value else ""