#===========================================================
#using bleak : Bluetooth Scanner
# %> pip install bleak
#===========================================================

import asyncio
from bleak import BleakScanner, BleakClient

COMPANIES = {
    # Computing
    0: "<Placeholder> or Ericsson",
    2: "Intel",
    6: "Microsoft",
    13: "Texas Instruments",
    15: "Broadcom",
    48: "STMicroelectronics",
    57: "Murata",
    76: "Apple",
    89: "Nordic Semiconductor",
    93: "BlackBerry",
    117: "Samsung Electronics",
    224: "Google",
    301: "Garmin",
    429: "Qualcomm",
    480: "Huawei",
    518: "Xiaomi",
    637: "OnePlus",
    741: "Fitbit",
    1027: "Nordic Semiconductor",
    1177: "Sony",
    1361: "Meta",
    2247: "Espressif Systems",

    # Audio
    158: "Bose",
    196: "Jabra",
    205: "Plantronics",
    215: "GN Netcom",
    470: "Anker",
    538: "JBL",
    559: "Skullcandy",
    655: "Sennheiser",
    889: "Shokz",

    # Fitness / Health
    301: "Garmin",
    741: "Fitbit",
    1664: "Peloton",
    1718: "Whoop",

    # Smart Home / IoT
    466: "Tuya",
    647: "Tuya Smart",
    1037: "Shelly",
    1190: "Aqara",

    # Development boards
    89: "Nordic Semiconductor",
    2247: "Espressif Systems",
    305: "Dialog Semiconductor",
    889: "Silicon Labs",
}

# Scan for Bluetooth emitters

async def main():
    devices = await BleakScanner.discover(timeout=5.0, return_adv=True)

    print(f"Found {len(devices)} BLE device{"s" if len(devices) > 1 else ""}\n")

    for address, (dev, adv) in devices.items():
        print("-" * 60)
        print(f"| Found {dev.address=} ; {dev.name=}") # {dev.details=}
        print("-" * 60)

        print(f"\tName:        {dev.name}")
        print(f"\tAddress:     {dev.address}")
        print(f"\tRSSI:        {adv.rssi} dBm")
        print(f"\tServices:    {', '.join(adv.service_uuids) if adv.service_uuids else 'none'}")
        print(f"\tManufacturer data: {adv.manufacturer_data}\n")
        
        if adv.service_uuids:
            for s in adv.service_uuids:
                print(f"\tServices:  {s}")
        else:
            print("\tServices:   none")

        if adv.manufacturer_data:
            print("\tManufacturer:")
            for company_id, data in adv.manufacturer_data.items():
                company = COMPANIES.get(company_id, "Unknown")
                print(f"\t\t  {company} (ID {company_id})")
                print(f"\t\t  Data: {data.hex()}")
        else:
            print("\tManufacturer: none")

        print()

asyncio.run(main())

raise SystemExit

"""
#-----------------------------------------------------------------------------------------------------------
# If you want a simpler Scanner, this script is enough:
# %> pip install bleak

import asyncio
from bleak import BleakScanner, BleakClient

# Scan for Bluetooth emitters

async def main():
    devices = await BleakScanner.discover()

    for d in devices:
        print(f"Found {d.address=} ; {d.name=}")

asyncio.run(main())
"""
