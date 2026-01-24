import asyncio
from sqlalchemy.future import select
from app.core.database import get_session
from app.models.players_registry_v2 import SentinelPlayerRegistry, SentinelNameChange
from app.models.all_models import LogLogin, LogKill, LogChat

async def main():
    async for session in get_session():
        # 1. Find Tsunaga by SteamID (76561198171854818)
        stmt = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.steam_id == "76561198171854818")
        result = await session.execute(stmt)
        players = result.scalars().all()
        
        if not players:
            print("❌ Player 'Tsunaga' not found in registry.")
            return

        for p in players:
            print(f"🆔 SteamID: {p.steam_id} | Name: {p.current_name} | Last Seen: {p.last_seen}")
            
            # Check recent Name Changes
            stmt_changes = select(SentinelNameChange).where(SentinelNameChange.steam_id == p.steam_id).order_by(SentinelNameChange.changed_at.desc())
            res_changes = await session.execute(stmt_changes)
            changes = res_changes.scalars().all()
            print(f"   📜 History: {[c.old_name + '->' + c.new_name for c in changes]}")

            # Check recent Logins
            # stmt_login = select(LogLogin).where(LogLogin.steam_id == p.steam_id).order_by(LogLogin.timestamp.desc()).limit(3)
            # res_login = await session.execute(stmt_login)
            # logins = res_login.scalars().all()
            # print("   🚪 Recent Logins:")
            # for l in logins:
            #     print(f"      - {l.timestamp}: {l.player_name}")

            # Check recent Kills (as Killer)
            # stmt_kill = select(LogKill).where(LogKill.killer_id == p.steam_id).order_by(LogKill.timestamp.desc()).limit(3)
            # res_kill = await session.execute(stmt_kill)
            # kills = res_kill.scalars().all()
            # print("   🔫 Recent Kills:")
            # for k in kills:
            #     print(f"      - {k.timestamp}: {k.killer_name}")

if __name__ == "__main__":
    asyncio.run(main())
