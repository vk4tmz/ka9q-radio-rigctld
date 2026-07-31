from __future__ import annotations

import logging
import sys

from zeroconf import Zeroconf, AddressResolver, IPVersion
from ipaddress import IPv4Address, IPv6Address


def resolve_name(name: str) -> list[ZeroconfIPv4Address] | list[ZeroconfIPv6Address] | None:
    
    if not name.endswith("."):
        name += "."

    zc = Zeroconf()
    resolver = AddressResolver(name)
    if resolver.request(zc, 3000):
        res = resolver.ip_addresses_by_version(IPVersion.All)       
        return res
    else:
        return None
        

def main():
    logging.basicConfig(level=logging.DEBUG)
    argv = sys.argv.copy()
    if "--debug" in argv:
        logging.getLogger("zeroconf").setLevel(logging.DEBUG)
        argv.remove("--debug")

    if len(argv) < 2 or not argv[1]:
        raise ValueError("Usage: resolve_address.py [--debug] <name>")

    name = argv[1]
    addrList = resolve_name(name) 
    if (addrList):
        print(f"Resolved: [{name}] to Address: [{addrList}]")


if __name__ == "__main__":
    main()