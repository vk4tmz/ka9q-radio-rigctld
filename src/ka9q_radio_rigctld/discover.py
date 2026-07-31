#!/usr/bin/env python

"""Example of browsing for a service.

The default is HTTP and HAP; use --find to search for all available services in the network
"""

from __future__ import annotations

import argparse
import logging
from time import sleep
from typing import cast

from zeroconf import (
    IPVersion,
    ServiceBrowser,
    ServiceStateChange,
    Zeroconf,
    ZeroconfServiceTypes,
    ServiceInfo
)

KA9Q_RADIO_CTL_SVC = "_ka9q-ctl._udp.local."
KA9Q_RADIO_RTP_SVC = "_rtp._udp.local."

KA9Q_RADIO_SVC_TYPES_ALL = [
        KA9Q_RADIO_CTL_SVC,    # Controller
        KA9Q_RADIO_RTP_SVC,    # RTP Streams
    ]

class KA9QRadioServiceDiscovery:

    serviceTypes: list[str]
    serviceTypeInfos: dict[str, list[ServiceInfo]]

    def __init__(self, serviceTypes: list=KA9Q_RADIO_SVC_TYPES_ALL, ipVersion:IPVersion=IPVersion.All) -> None:
        self.zeroconf = Zeroconf(ip_version=ipVersion)
        self.serviceTypes = serviceTypes
        self.serviceTypeInfos = {}
        self.browser = ServiceBrowser(self.zeroconf, serviceTypes, handlers=[self.on_service_state_change])

    def close(self):
        self.zeroconf.close()

    def on_service_state_change(
        self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange
    ) -> None:
        #print(f"Service {name} of type {service_type} state changed: {state_change}")

        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if (info):
                if (not self.serviceTypeInfos or (service_type not in self.serviceTypeInfos.keys())):
                    self.serviceTypeInfos[service_type] = [info]
                else:
                    self.serviceTypeInfos[service_type].append(info)


def listServiceTypes(ip_version:IPVersion) -> list[str]:
    zeroconf = Zeroconf(ip_version=ip_version)
    try:
        return list(ZeroconfServiceTypes.find(zc=zeroconf))
    finally:
        zeroconf.close()

def printServiceInfo(info:ServiceInfo):
        if info:
            addresses = [f"{addr}:{cast(int, info.port)}" for addr in info.parsed_scoped_addresses()]
            print(f"  Addresses: {', '.join(addresses)}")
            print(f"  Weight: {info.weight}, priority: {info.priority}")
            print(f"  Server: {info.server}")
            if info.properties:
                print("  Properties are:")
                for key, value in info.properties.items():
                    print(f"    {key!r}: {value!r}")
            else:
                print("  No properties")
        else:
            print("  No info")
        print("\n")


def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--find", action="store_true", help="Browse all available services")
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument("--v6-only", action="store_true")
    version_group.add_argument("--v4-only", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger("zeroconf").setLevel(logging.DEBUG)
    if args.v6_only:
        ip_version = IPVersion.V6Only
    elif args.v4_only:
        ip_version = IPVersion.V4Only
    else:
        ip_version = IPVersion.All

    serviceTypes = KA9Q_RADIO_SVC_TYPES_ALL
    if args.find:
        # Warning: this will discovery and include NON KA9Q Radio Service Types.
        serviceTypes = listServiceTypes(ip_version)

    print(f"\nBrowsing {len(serviceTypes)} service types(s), press Ctrl-C to exit...\n")
    
    dss = KA9QRadioServiceDiscovery(serviceTypes=serviceTypes, ipVersion=ip_version)

    try:
        # while True:
            # sleep(0.1)
        sleep(2.0)
    except KeyboardInterrupt:
        pass
    finally:
        dss.close()

    for st in dss.serviceTypeInfos.keys():
        infos = dss.serviceTypeInfos[st]
        print(f"Discovered {len(infos)} services for Service Type: [{st}]")
        for info in infos:
            print(f"Info from zeroconf.get_service_info: {info!r}")
            printServiceInfo(info)  
    


if __name__ == "__main__":
    main()