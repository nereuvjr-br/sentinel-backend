from app.services.parsers_v2.admin import AdminParserV2
import json

lines = [
    "2025.12.21-18.06.15: '76561199817469068:BOT_Oblivion(21)' Command: 'teleport 0 0 0'",
    "2025.12.21-18.06.34: '76561199817469068:BOT_Oblivion(21)' Command: 'DestroyCorpsesWithinRadius 100000000 false'",
    '2025.12.21-18.07.12: \'76561199817469068:BOT_Oblivion(21)\' Command: \'SpawnItem Weapon_MK18 1 Location "-409464.75000000 -9808.16600000 37995.66800000"\'',
    '2025.12.21-18.07.13: \'76561199817469068:BOT_Oblivion(21)\' Command: \'SpawnItem Magazine_M16 3 Location "-409464.75000000 -9808.16600000 37995.66800000" AmmoCount 30\''
]

print("=== Testing Admin Parser V2 ===")
for line in lines:
    result = AdminParserV2.parse(line)
    if result:
        print(f"\nCMD: {result.command_type}")
        print(f"BOT: {result.is_automated}")
        if result.item_class:
            print(f"ITEM: {result.item_class} (x{result.item_count})")
        if result.location:
            print(f"LOC: {result.location}")
        if result.item_args:
            print(f"ARGS: {result.item_args}")
    else:
        print(f"FAILED: {line}")
