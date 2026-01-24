
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.players_registry_v2 import SentinelPlayerRegistry
from app.models.clan_v2 import SentinelClan, SentinelClanMember
from sqlalchemy.ext.asyncio import AsyncSession

async def check_clan_linkage():
    async with AsyncSession(engine) as session:
        print("--- Checking Players ---")
        
        # Get ADM_Sabugador
        res_sab = await session.execute(select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.current_name == 'ADM_Sabugador'))
        sabugador = res_sab.scalars().first()
        
        # Get ADM_Mewtwo
        res_mew = await session.execute(select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.current_name == 'ADM_Mewtwo'))
        mewtwo = res_mew.scalars().first()
        
        if not sabugador:
            print("❌ ADM_Sabugador not found in Registry")
        else:
            print(f"✅ ADM_Sabugador: SteamID={sabugador.steam_id}, Phone={sabugador.phone_number}")

        if not mewtwo:
            print("❌ ADM_Mewtwo not found in Registry")
        else:
            print(f"✅ ADM_Mewtwo: SteamID={mewtwo.steam_id}, Phone={mewtwo.phone_number}")
            
        if not sabugador or not mewtwo:
            return

        print("\n--- Checking Clan Memberships ---")
        # Check Clan Memberships
        res_mem_sab = await session.execute(select(SentinelClanMember).where(SentinelClanMember.steam_id == sabugador.steam_id))
        mem_sab = res_mem_sab.scalar_one_or_none()
        
        res_mem_mew = await session.execute(select(SentinelClanMember).where(SentinelClanMember.steam_id == mewtwo.steam_id))
        mem_mew = res_mem_mew.scalar_one_or_none()
        
        clan_id_sab = mem_sab.clan_id if mem_sab else None
        clan_id_mew = mem_mew.clan_id if mem_mew else None
        
        print(f"Sabugador Clan ID (SCUM): {clan_id_sab}")
        print(f"Mewtwo Clan ID (SCUM): {clan_id_mew}")
        
        if clan_id_sab != clan_id_mew:
            print("❌ IMPACT: They are in DIFFERENT clans (or one is None) according to the database.")
        else:
            print("✅ Status: They are in the SAME clan ID.")
            
        if clan_id_sab:
            print("\n--- Checking Clan Details ---")
            res_clan = await session.execute(select(SentinelClan).where(SentinelClan.scum_clan_id == clan_id_sab))
            clan = res_clan.scalar_one_or_none()
            if clan:
                print(f"Clan Name: {clan.name}")
                print(f"Clan Tier: {getattr(clan, 'plan_tier', 'N/A')}")
                print(f"Whatsapp Group: {clan.whatsapp_group_id}")
            else:
                print("❌ Clan metadata not found in SentinelClan table.")

if __name__ == "__main__":
    asyncio.run(check_clan_linkage())
