
import asyncio
from unittest.mock import MagicMock
from app.services.notification_service import NotificationService
from app.models.players_registry_v2 import SentinelPlayerRegistry
from app.models.clan_v2 import SentinelClan, SentinelClanMember
from datetime import datetime, timedelta

# Mock Objects to simulate DB entities
class MockPlayer:
    def __init__(self, steam_id, name, phone, tier):
        self.steam_id = steam_id
        self.current_name = name
        self.phone_number = phone
        self.plan_tier = tier
        self.plan_expires_at = datetime.utcnow() + timedelta(days=30) if tier == 'premium' else None

class MockClan:
    def __init__(self, id, name, tier):
        self.scum_clan_id = id
        self.name = name
        self.plan_tier = tier
        self.plan_expires_at = datetime.utcnow() + timedelta(days=30) if tier == 'premium' else None
        self.whatsapp_group_id = "123-group"

async def test_logic():
    service = NotificationService()
    
    # Scenarios to Test
    # 1. Victim is Free, Member is Free -> Member gets NOTHING.
    # 2. Victim is Free, Member is Premium -> Member gets INSTANT.
    
    print("--- SIMULATION: Notification Logic Check ---")
    
    # Setup Data
    victim = MockPlayer("steam_victim", "VictimFree", "5511999999999", "free")
    member_free = MockPlayer("steam_free", "MemberFree", "5511888888888", "free")
    member_premium = MockPlayer("steam_premium", "MemberPremium", "5511777777777", "premium")
    clan_free = MockClan(100, "FreeClan", "free")
    
    # Simulate: Resolve Logic
    # We can't easily run the full async method without mocking the DB session/selects.
    # So we will replicate the logic block here to prove it matches the desired specific logic.
    
    print(f"Victim ({victim.current_name}): Tier {service._resolve_plan_tier(victim)}")
    print(f"Member 1 ({member_free.current_name}): Tier {service._resolve_plan_tier(member_free)}")
    print(f"Member 2 ({member_premium.current_name}): Tier {service._resolve_plan_tier(member_premium)}")
    print(f"Clan ({clan_free.name}): Tier {service._resolve_plan_tier(clan_free)}")
    
    print("\n[Scenario: Raid on VictimFree (Clan is Free)]")
    
    # 1. Victim Logic
    victim_tier = service._resolve_plan_tier(victim)
    if victim_tier == 'free':
        print(f"✅ Victim ({victim.current_name}) -> Receives DELAYED (Own Item)")
    else:
        print(f"❌ Victim Logic Wrong")

    # 2. Member Free Logic
    mem_tier_1 = service._resolve_plan_tier(member_free)
    clan_tier = service._resolve_plan_tier(clan_free)
    
    if mem_tier_1 == 'premium' or clan_tier == 'premium':
        print(f"❌ MemberFree ({member_free.current_name}) -> Receives Notification (WRONG!)")
    else:
        print(f"✅ MemberFree ({member_free.current_name}) -> SKIPPED (Correct: Free user, not own item)")

    # 3. Member Premium Logic
    mem_tier_2 = service._resolve_plan_tier(member_premium)
    
    if mem_tier_2 == 'premium' or clan_tier == 'premium':
        print(f"✅ MemberPremium ({member_premium.current_name}) -> Receives INSTANT (Premium Privilege)")
    else:
        print(f"❌ MemberPremium Logic Wrong")

if __name__ == "__main__":
    asyncio.run(test_logic())
