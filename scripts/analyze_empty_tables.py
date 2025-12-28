"""
Análise simplificada das tabelas vazias
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def analyze():
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        print("\n" + "=" * 80)
        print("🔍 ANÁLISE DAS TABELAS VAZIAS")
        print("=" * 80 + "\n")
        
        # Tabelas que PODEM ser populadas via script de agregação
        print("✅ TABELAS QUE PODEM SER POPULADAS (via script):\n")
        
        # 1. Player Wallets
        result = await conn.execute(text("SELECT COUNT(DISTINCT steam_id) FROM sentinel_economy_balances"))
        players = result.scalar()
        print(f"1. sentinel_player_wallets")
        print(f"   📊 {players} jogadores únicos em balances")
        print(f"   💡 Script: populate_player_wallets.py\n")
        
        # 2. Players Registry  
        result = await conn.execute(text("SELECT COUNT(DISTINCT steam_id) FROM sentinel_logins"))
        logins = result.scalar()
        print(f"2. sentinel_players_registry")
        print(f"   📊 {logins} jogadores únicos em logins")
        print(f"   💡 Script: populate_players_registry.py (precisa criar)\n")
        
        # 3. NPC Kill Stats
        result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_kills WHERE victim_is_npc = true"))
        npc_kills = result.scalar()
        print(f"3. sentinel_npc_kill_stats")
        print(f"   📊 {npc_kills} kills de NPCs")
        print(f"   💡 Script: aggregate_npc_stats.py (precisa criar)\n")
        
        # 4. Account Registry
        result = await conn.execute(text("SELECT COUNT(DISTINCT account_number) FROM sentinel_bank_transactions"))
        accounts = result.scalar()
        print(f"4. sentinel_account_registry")
        print(f"   📊 {accounts} contas bancárias únicas")
        print(f"   💡 Script: populate_account_registry.py (precisa criar)\n")
        
        # 5. Item Economy
        result = await conn.execute(text("SELECT COUNT(DISTINCT item_class) FROM sentinel_economy_trades"))
        items = result.scalar()
        print(f"5. sentinel_item_economy")
        print(f"   📊 {items} items únicos em trades")
        print(f"   💡 Script: aggregate_item_economy.py (precisa criar)\n")
        
        print("=" * 80)
        print("\n❌ TABELAS SEM DADOS NOS LOGS:\n")
        
        # Verificar logs não parseados
        result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_unparsed_logs WHERE raw_line ILIKE '%vehicle%'"))
        vehicles = result.scalar()
        
        result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_unparsed_logs WHERE raw_line ILIKE '%craft%'"))
        craft = result.scalar()
        
        result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_unparsed_logs WHERE raw_line ILIKE '%explos%'"))
        explosives = result.scalar()
        
        print(f"1. sentinel_vehicles - {vehicles} logs não parseados com 'vehicle'")
        print(f"2. sentinel_gameplay_crafting - {craft} logs não parseados com 'craft'")
        print(f"3. sentinel_gameplay_explosives - {explosives} logs não parseados com 'explos'")
        print(f"4. sentinel_name_changes - Sem dados nos logs")
        print(f"5. sentinel_trader_inventory - Sem dados nos logs")
        
        print("\n" + "=" * 80)
        print("\n🔄 TABELAS AUTOMÁTICAS/ESPECIAIS:\n")
        
        print("1. sentinel_economy_alerts")
        print("   💡 Precisa de lógica de detecção de anomalias\n")
        
        print("2. sentinel_system_alerts")
        print("   💡 Populado automaticamente pelo sistema de monitoramento\n")
        
        result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_admin_commands WHERE raw_command ILIKE '%money%' OR raw_command ILIKE '%gold%'"))
        admin_econ = result.scalar()
        
        print(f"3. sentinel_admin_economy_actions")
        print(f"   📊 {admin_econ} comandos de admin relacionados a economia")
        print(f"   💡 Precisa de parser específico para extrair ações de economia\n")
        
        print("=" * 80)
        print("\n📋 RESUMO:")
        print(f"\n   ✅ {players} jogadores podem ser agregados em player_wallets")
        print(f"   ✅ {items} items podem ser agregados em item_economy")
        print(f"   ✅ {accounts} contas podem ser agregadas em account_registry")
        print(f"   ✅ {npc_kills} kills de NPCs podem ser agregadas")
        print(f"\n   ⚠️  5 tabelas sem dados nos logs (parsers não implementados)")
        print(f"   ⚠️  3 tabelas precisam de lógica especial")
        print("\n" + "=" * 80 + "\n")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(analyze())
