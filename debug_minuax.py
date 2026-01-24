
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.players_registry_v2 import SentinelPlayerRegistry
from app.models.clan_v2 import SentinelClan, SentinelClanMember
from sqlalchemy.ext.asyncio import AsyncSession

async def check_minuax():
    async with AsyncSession(engine) as session:
        print("--- Checking Minuax ---")
        q = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.steam_id == '76561198092850970')
        res = await session.execute(q)
        p = res.scalars().first()
        
        if p:
            print(f"Player: {p.current_name}")
            print(f"Phone: {p.phone_number}")
            print(f"Tier: {p.plan_tier}")
            
            # Check Clan
            q_mem = select(SentinelClanMember).where(SentinelClanMember.steam_id == p.steam_id)
            mem = (await session.execute(q_mem)).scalar_one_or_none()
            
            if mem:
                print(f"Clan ID: {mem.clan_id}")
                q_clan = select(SentinelClan).where(SentinelClan.scum_clan_id == mem.clan_id)
                clan = (await session.execute(q_clan)).scalar_one_or_none()
                if clan:
                    print(f"Clan Name: {clan.name}")
                    print(f"Clan Tier: {getattr(clan, 'plan_tier', 'N/A')}")
            else:
                print("No Clan Membership found.")
                
        else:
            print("Minuax DOES NOT EXIST in Registry.")

if __name__ == "__main__":
    asyncio.run(check_minuax())
