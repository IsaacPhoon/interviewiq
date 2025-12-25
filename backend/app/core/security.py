from ipaddress import (
    IPv4Network,
    IPv6Network,
    ip_address,
    ip_network,
)

from fastapi import Depends, HTTPException, Request, status

# Svix webhook IP addresses
# Source: https://docs.svix.com/receiving/source-ips
ALLOWED_SVIX_IPS = [
    # us
    '44.228.126.217',
    '50.112.21.217',
    '52.24.126.164',
    '54.148.139.208',
    '2600:1f24:64:8000::/56',
    # is-east
    '54.164.207.221',
    '54.90.7.123',
    '2600:1f28:37:4000::/56',
    # ei
    '52.215.16.239',
    '54.216.8.72',
    '63.33.109.123',
    '2a05:d028:17:8000::/56',
    # in
    '13.126.41.108',
    '15.207.218.84',
    '65.2.133.31',
    # au
    '13.239.204.236',
    '54.66.246.217',
    '54.252.65.96',
    '2406:da2c:13:4000::/56',
    # ca
    '52.60.44.49',
    '3.98.68.230',
    '3.96.105.27',
    '2600:1f21:1c:4000::/56',
]

_ALLOWED_NETWORKS: list[IPv4Network | IPv6Network] = []
for ip_str in ALLOWED_SVIX_IPS:
    _ALLOWED_NETWORKS.append(ip_network(ip_str))


def _is_svix_webhook_ip(client_ip: str) -> bool:
    """Check if the client IP is in the allowed Svix IP ranges."""
    try:
        ip = ip_address(client_ip)
        return any(ip in network for network in _ALLOWED_NETWORKS)
    except ValueError:
        return False


async def verify_svix_webhook_ip(request: Request) -> None:
    """
    Verify that the request is coming from a Svix webhook IP.

    Raises HTTPException 403 if the client IP is not in the allowed list.
    Returns the client IP if allowed.
    """
    client_ip = request.client.host if request.client else None

    if not client_ip or not _is_svix_webhook_ip(client_ip):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Request not from allowed IP')


SvixWebhookIPDep = Depends(verify_svix_webhook_ip)
