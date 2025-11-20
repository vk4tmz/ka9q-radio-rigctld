
from __future__ import annotations

import asyncio
import logging
import sys

from zeroconf import AddressResolver, IPVersion
from zeroconf.asyncio import AsyncZeroconf

async def resolve_name(name: str) -> None:
    aiozc = AsyncZeroconf()
    await aiozc.zeroconf.async_wait_for_start()
    resolver = AddressResolver(name)
    if await resolver.async_request(aiozc.zeroconf, 3000):
        res = resolver.ip_addresses_by_version(IPVersion.All)
        res = resolver.
        if (res and len(res) >= 1):
            print(f"Multiple addresses discovered for name: [{name}], using 1st")
        addr = res[0]
        print(f"{name} IP addresses: {addr.}")
        
    else:
        print(f"Name {name} not resolved")
    await aiozc.async_close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    argv = sys.argv.copy()
    if "--debug" in argv:
        logging.getLogger("zeroconf").setLevel(logging.DEBUG)
        argv.remove("--debug")

    if len(argv) < 2 or not argv[1]:
        raise ValueError("Usage: resolve_address.py [--debug] <name>")

    name = argv[1]
    if not name.endswith("."):
        name += "."

    asyncio.run(resolve_name(name)) 

# from zeroconf import ZeroconfServiceTypes
# print('\n'.join(ZeroconfServiceTypes.find()))