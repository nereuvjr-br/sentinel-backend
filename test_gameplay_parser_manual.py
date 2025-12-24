from app.services.parsers_v2.gameplay import GameplayParserV2

def test():
    # TEST 1: Bunker
    line1 = "2025.12.23-06.01.36: [LogBunkerLock] C4 Bunker is Active. Activated 00h 00m 00s ago. X=446323.000 Y=263051.188 Z=18552.514"
    res1 = GameplayParserV2.parse(line1)
    print(f"Bunker Test: {res1}")
    
    # TEST 2: Explosives (Hypothetical, based on typical format)
    # 2025.12.21-19.34.02: [LogExplosives] User: Player(123) Action: Armed Item: C4 Location: ...
    line2 = "2025.12.21-19.34.02: [LogExplosives] User: Player (123, 76561198051746684) Action: Armed Item: BP_C4_Item Location: X=100.0 Y=200.0 Z=300.0"
    res2 = GameplayParserV2.parse(line2)
    print(f"Explosives Test: {res2}")

if __name__ == "__main__":
    test()
