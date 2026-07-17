#===========================================================
#using bleak : Bluetooth Scanner
# %> pip install bleak
#===========================================================

import asyncio
from bleak import BleakScanner, BleakClient

COMPANIES = {
    76: "Apple",
    6: "Microsoft",
    15: "Broadcom",
    224: "Google",
    117: "Samsung Electronics",
    301: "Garmin",
    1027: "Nordic Semiconductor",
}

# Scan for Bluetooth emitters

async def main():
    devices = await BleakScanner.discover(timeout=5.0, return_adv=True)

    print(f"Found {len(devices)} BLE devices\n")

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
# If you want a simpler Scanner, this is enough:
# %> pip install bleak
"""

import asyncio
from bleak import BleakScanner, BleakClient

# Scan for Bluetooth emitters

async def main():
    devices = await BleakScanner.discover()

    for d in devices:
        print(f"Found {d.address=} ; {d.name=}")

asyncio.run(main())
