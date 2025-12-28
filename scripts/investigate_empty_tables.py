"""
Script para investigar por que as tabelas vazias não estão sendo populadas
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def investigate_empty_tables():
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        print("\n🔍 INVESTIGANDO TABELAS VAZIAS:\n")
        print("=" * 80)
        
        # 1. Verificar se há dados de veículos nos logs não parseados
        print("\n1️⃣ VEÍCULOS (sentinel_vehicles):")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM sentinel_unparsed_logs 
            WHERE raw_line ILIKE '%vehicle%' OR raw_line ILIKE '%car%'
        """))
        vehicle_logs = result.scalar()
        print(f"   📝 Logs não parseados com 'vehicle': {vehicle_logs}")
        
        # 2. Verificar crafting
        print("\n2️⃣ CRAFTING (sentinel_gameplay_crafting):")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM sentinel_unparsed_logs 
            WHERE raw_line ILIKE '%craft%'
        """))
        craft_logs = result.scalar()
        print(f"   📝 Logs não parseados com 'craft': {craft_logs}")
        
        # 3. Verificar explosivos
        print("\n3️⃣ EXPLOSIVOS (sentinel_gameplay_explosives):")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM sentinel_unparsed_logs 
            WHERE raw_line ILIKE '%explos%' OR raw_line ILIKE '%grenade%' OR raw_line ILIKE '%mine%'
        """))
        explosive_logs = result.scalar()
        print(f"   📝 Logs não parseados com explosivos: {explosive_logs}")
        
        # 4. Verificar mudanças de nome
        print("\n4️⃣ MUDANÇAS DE NOME (sentinel_name_changes):")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM sentinel_unparsed_logs 
            WHERE raw_line ILIKE '%name change%' OR raw_line ILIKE '%renamed%'
        """))
        name_logs = result.scalar()
        print(f"   📝 Logs não parseados com mudança de nome: {name_logs}")
        
        # 5. Verificar ações de admin na economia
        print("\n5️⃣ ADMIN ECONOMY (sentinel_admin_economy_actions):")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM sentinel_admin_commands 
            WHERE raw_command ILIKE '%money%' 
            OR raw_command ILIKE '%gold%'
            OR raw_command ILIKE '%setbalance%'
        """))
        admin_econ = result.scalar()
        print(f"   📝 Comandos de admin relacionados a economia: {admin_econ}")
        
        # 6. Verificar se há dados para popular player_wallets
        print("\n6️⃣ PLAYER WALLETS (sentinel_player_wallets):")
        result = await conn.execute(text("""
            SELECT COUNT(DISTINCT steam_id) 
            FROM sentinel_economy_balances
        """))
        unique_players = result.scalar()
        print(f"   📝 Jogadores únicos em balances: {unique_players}")
        print(f"   ⚠️  Esta tabela precisa ser populada via script de agregação")
        
        # 7. Verificar registry de jogadores
        print("\n7️⃣ PLAYERS REGISTRY (sentinel_players_registry):")
        # Contar de cada tabela separadamente
        result1 = await conn.execute(text("SELECT COUNT(DISTINCT steam_id) FROM sentinel_logins"))
        logins_count = result1.scalar()
        
        result2 = await conn.execute(text("SELECT COUNT(DISTINCT killer_steam_id) FROM sentinel_kills WHERE killer_steam_id IS NOT NULL"))
        kills_count = result2.scalar()
        
        result3 = await conn.execute(text("SELECT COUNT(DISTINCT steam_id) FROM sentinel_economy_balances"))
        balances_count = result3.scalar()
        
        print(f"   📝 Jogadores únicos em logins: {logins_count}")
        print(f"   📝 Jogadores únicos em kills: {kills_count}")
        print(f"   📝 Jogadores únicos em balances: {balances_count}")
        print(f"   ⚠️  Esta tabela precisa ser populada via script de agregação")
        
        # 8. Verificar NPC kill stats
        print("\n8️⃣ NPC KILL STATS (sentinel_npc_kill_stats):")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM sentinel_kills 
            WHERE victim_name LIKE 'BP_%' OR victim_name LIKE '%Puppet%'
        """))
        npc_kills = result.scalar()
        print(f"   📝 Kills de NPCs: {npc_kills}")
        print(f"   ⚠️  Esta tabela precisa ser populada via script de agregação")
        
        # 9. Verificar account registry
        print("\n9️⃣ ACCOUNT REGISTRY (sentinel_account_registry):")
        result = await conn.execute(text("""
            SELECT COUNT(DISTINCT account_number) 
            FROM sentinel_bank_transactions
        """))
        accounts = result.scalar()
        print(f"   📝 Contas bancárias únicas em transações: {accounts}")
        print(f"   ⚠️  Esta tabela precisa ser populada via script de agregação")
        
        # 10. Verificar item economy
        print("\n🔟 ITEM ECONOMY (sentinel_item_economy):")
        result = await conn.execute(text("""
            SELECT COUNT(DISTINCT item_class) 
            FROM sentinel_economy_trades
        """))
        items = result.scalar()
        print(f"   📝 Items únicos em trades: {items}")
        print(f"   ⚠️  Esta tabela precisa ser populada via script de agregação")
        
        # 11. Verificar trader inventory
        print("\n1️⃣1️⃣ TRADER INVENTORY (sentinel_trader_inventory):")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM sentinel_unparsed_logs 
            WHERE raw_line ILIKE '%trader%' AND raw_line ILIKE '%stock%'
        """))
        trader_logs = result.scalar()
        print(f"   📝 Logs não parseados com trader/stock: {trader_logs}")
        
        # 12. Verificar economy alerts
        print("\n1️⃣2️⃣ ECONOMY ALERTS (sentinel_economy_alerts):")
        print(f"   ⚠️  Sistema de alertas automáticos - precisa de lógica de detecção")
        
        # 13. Verificar system alerts
        print("\n1️⃣3️⃣ SYSTEM ALERTS (sentinel_system_alerts):")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM sentinel_database_health 
            WHERE is_healthy = false
        """))
        unhealthy = result.scalar()
        print(f"   📝 Snapshots de DB não saudáveis: {unhealthy}")
        print(f"   ⚠️  Sistema de alertas de monitoramento - populado automaticamente")
        
        print("\n" + "=" * 80)
        print("\n📋 RESUMO:")
        print("\n✅ TABELAS QUE PODEM SER POPULADAS AGORA:")
        print("   - sentinel_player_wallets (via script)")
        print("   - sentinel_players_registry (via script)")
        print("   - sentinel_npc_kill_stats (via script)")
        print("   - sentinel_account_registry (via script)")
        print("   - sentinel_item_economy (via script)")
        
        print("\n⚠️  TABELAS SEM DADOS NOS LOGS:")
        print("   - sentinel_vehicles (sem logs de veículos)")
        print("   - sentinel_gameplay_crafting (sem logs de crafting)")
        print("   - sentinel_gameplay_explosives (sem logs de explosivos)")
        print("   - sentinel_name_changes (sem logs de mudança de nome)")
        print("   - sentinel_trader_inventory (sem logs de inventário)")
        
        print("\n🔄 TABELAS AUTOMÁTICAS:")
        print("   - sentinel_economy_alerts (precisa de lógica de detecção)")
        print("   - sentinel_system_alerts (populado pelo sistema de monitoramento)")
        print("   - sentinel_admin_economy_actions (precisa de parser específico)")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(investigate_empty_tables())
