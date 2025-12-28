"""
Script de inicialização completa do Sentinel V2
Alimenta o banco de dados via SFTP e local
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def check_database():
    """Verifica se o banco de dados está acessível"""
    print("🔍 Verificando conexão com o banco de dados...")
    try:
        async with AsyncSession(engine) as session:
            result = await session.execute(text("SELECT 1"))
            print("  ✅ Conexão com PostgreSQL OK")
            return True
    except Exception as e:
        print(f"  ❌ Erro ao conectar ao banco: {e}")
        return False

async def check_tables():
    """Verifica se todas as tabelas existem"""
    print("\n🔍 Verificando tabelas do banco...")
    
    expected_tables = [
        'sentinel_kills',
        'sentinel_logins',
        'sentinel_chat_messages',
        'sentinel_economy_trades',
        'sentinel_economy_balances',
        'sentinel_bank_transactions',
        'sentinel_mechanic_services',
        'sentinel_bank_cards',
        'sentinel_admin_commands',
        'sentinel_gameplay_raids',
        'sentinel_gameplay_crafting',
        'sentinel_gameplay_explosives',
        'sentinel_gameplay_bunkers',
        'sentinel_chest_events',
        'sentinel_fame_events',
        'sentinel_violations',
        'sentinel_vehicles',
        'sentinel_player_wallets',
        'sentinel_item_economy',
        'sentinel_economy_alerts',
        'sentinel_trader_inventory',
        'sentinel_account_registry',
        'sentinel_admin_economy_actions',
        'sentinel_players_registry',
        'sentinel_name_changes',
        'sentinel_processed_files',
        'sentinel_unparsed_logs'
    ]
    
    try:
        async with AsyncSession(engine) as session:
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            
            missing = set(expected_tables) - set(existing_tables)
            
            print(f"  📊 Tabelas encontradas: {len(existing_tables)}/27")
            
            if missing:
                print(f"  ⚠️  Tabelas faltando: {len(missing)}")
                for table in sorted(missing):
                    print(f"    - {table}")
                return False
            else:
                print("  ✅ Todas as 27 tabelas existem")
                return True
                
    except Exception as e:
        print(f"  ❌ Erro ao verificar tabelas: {e}")
        return False

async def check_sftp_config():
    """Verifica se as configurações SFTP estão definidas"""
    print("\n🔍 Verificando configurações SFTP...")
    
    from app.core.config import settings
    
    required_vars = {
        'SFTP_HOST': getattr(settings, 'SFTP_HOST', None),
        'SFTP_PORT': getattr(settings, 'SFTP_PORT', None),
        'SFTP_USER': getattr(settings, 'SFTP_USER', None),
        'SFTP_PASS': getattr(settings, 'SFTP_PASS', None),
    }
    
    missing = []
    for var, value in required_vars.items():
        if not value:
            missing.append(var)
            print(f"  ❌ {var} não configurado")
        else:
            # Ocultar senha
            display_value = "***" if 'PASS' in var else value
            print(f"  ✅ {var} = {display_value}")
    
    if missing:
        print(f"\n  ⚠️  Variáveis faltando: {', '.join(missing)}")
        print("  💡 Configure no arquivo .env")
        return False
    
    return True

async def start_daemon():
    """Inicia o daemon SFTP"""
    print("\n🚀 Iniciando Sentinel Daemon V2...")
    print("=" * 60)
    
    from sentinel_v2 import SentinelDaemonV2
    
    daemon = SentinelDaemonV2()
    await daemon.run()

async def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║     SENTINEL V2 - Sistema de Inicialização Completo     ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 1. Verificar banco de dados
    if not await check_database():
        print("\n❌ Falha na verificação do banco de dados")
        print("💡 Certifique-se de que o PostgreSQL está rodando")
        return
    
    # 2. Verificar tabelas
    if not await check_tables():
        print("\n❌ Algumas tabelas estão faltando")
        print("💡 Execute as migrações primeiro:")
        print("   python migrations/create_economy_tables.py")
        print("   python migrations/create_players_registry.py")
        print("   etc...")
        
        choice = input("\nContinuar mesmo assim? (s/n): ")
        if choice.lower() != 's':
            return
    
    # 3. Verificar configurações SFTP
    if not await check_sftp_config():
        print("\n❌ Configurações SFTP incompletas")
        
        choice = input("\nProcessar apenas logs locais? (s/n): ")
        if choice.lower() != 's':
            return
    
    # 4. Iniciar daemon
    print("\n" + "=" * 60)
    print("✅ Todas as verificações passaram!")
    print("=" * 60)
    print("\n🎯 O daemon irá:")
    print("  1. Conectar ao servidor SFTP")
    print("  2. Baixar novos arquivos de log")
    print("  3. Processar com parsers V2")
    print("  4. Salvar em todas as 27 tabelas")
    print("  5. Repetir a cada 60 segundos")
    print("\n⚠️  Pressione Ctrl+C para parar")
    print("=" * 60)
    
    input("\nPressione ENTER para iniciar...")
    
    try:
        await start_daemon()
    except KeyboardInterrupt:
        print("\n\n⏹️  Daemon interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
