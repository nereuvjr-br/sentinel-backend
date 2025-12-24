#!/usr/bin/env python3
"""
Cria dados de teste para demonstração do Dashboard Econômico V2.
"""

import sys
import asyncio
from datetime import datetime, timedelta
import random
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.models.economy_v2 import (
    SentinelBankTransaction,
    SentinelMechanicService,
    SentinelBankCard
)

async def create_test_data():
    print("🎨 Criando dados de teste para o Dashboard Econômico...")
    print()
    
    players = [
        ("76561199485971199", "Apocalipse"),
        ("76561199211519717", "VINI SEAL W2"),
        ("76561199442829827", "P S I C O P A T A"),
        ("76561198153826477", "ⓋⒾⓃⒾヅ"),
        ("76561199173075358", "MAVERICK"),
    ]
    
    async with AsyncSession(engine) as session:
        created = {
            "bank_transactions": 0,
            "mechanic_services": 0,
            "bank_cards": 0
        }
        
        # ====================================================================
        # TRANSAÇÕES BANCÁRIAS
        # ====================================================================
        print("💰 Criando transações bancárias...")
        for i in range(15):
            player = random.choice(players)
            tx_type = random.choice(["deposited", "withdrew", "transfer"])
            gross = random.randint(1000, 50000)
            fee = int(gross * 0.02)  # 2% de taxa
            
            tx = SentinelBankTransaction(
                timestamp=datetime.now() - timedelta(hours=random.randint(0, 48)),
                steam_id=player[0],
                player_name=player[1],
                account_number=f"71{random.randint(1000000000, 9999999999)}",
                transaction_type=tx_type,
                gross_amount=float(gross),
                net_amount=float(gross - fee),
                fee=float(fee) if tx_type != "transfer" else None,
                target_account=f"71{random.randint(1000000000, 9999999999)}" if tx_type == "transfer" else None,
                target_name=random.choice(players)[1] if tx_type == "transfer" else None,
                target_steam_id=random.choice(players)[0] if tx_type == "transfer" else None,
                pos_x=float(random.randint(-700000, 700000)),
                pos_y=float(random.randint(-700000, 700000)),
                pos_z=float(random.randint(0, 50000))
            )
            session.add(tx)
            created["bank_transactions"] += 1
        
        # ====================================================================
        # SERVIÇOS MECÂNICOS
        # ====================================================================
        print("🔧 Criando serviços mecânicos...")
        services = ["Install", "Repair", "Remove", "Buy"]
        parts = [
            "Engine_Part", "Wheel", "Battery", "Spark_Plug",
            "Oil_Filter", "Brake_Pads", "Radiator", "Alternator"
        ]
        
        for i in range(12):
            player = random.choice(players)
            service = random.choice(services)
            part = random.choice(parts)
            
            mechanic = SentinelMechanicService(
                timestamp=datetime.now() - timedelta(hours=random.randint(0, 48)),
                steam_id=player[0],
                player_name=player[1],
                service_type=service,
                item_class=part,
                price=float(random.randint(100, 2000)),
                trader_name=random.choice(["Mechanic_Shop_A", "Mechanic_Shop_B", "Mechanic_Shop_C"]),
                pos_x=float(random.randint(-700000, 700000)),
                pos_y=float(random.randint(-700000, 700000)),
                pos_z=float(random.randint(0, 50000))
            )
            session.add(mechanic)
            created["mechanic_services"] += 1
        
        # ====================================================================
        # CARTÕES BANCÁRIOS
        # ====================================================================
        print("💳 Criando eventos de cartões...")
        card_types = ["Starter card", "Gold card", "Classic card"]
        actions = ["purchased", "manually destroyed"]
        
        for i in range(8):
            player = random.choice(players)
            action = random.choice(actions)
            card_type = random.choice(card_types)
            
            card = SentinelBankCard(
                timestamp=datetime.now() - timedelta(hours=random.randint(0, 48)),
                steam_id=player[0],
                player_name=player[1],
                account_number=f"71{random.randint(1000000000, 9999999999)}",
                action=action,
                card_type=card_type,
                free_renewal=random.choice([True, False]) if action == "purchased" else None,
                new_balance=float(random.randint(0, 100000)) if action == "purchased" else None,
                destroyed_account=f"71{random.randint(1000000000, 9999999999)}" if action == "manually destroyed" else None,
                pos_x=float(random.randint(-700000, 700000)),
                pos_y=float(random.randint(-700000, 700000)),
                pos_z=float(random.randint(0, 50000))
            )
            session.add(card)
            created["bank_cards"] += 1
        
        # Commit
        await session.commit()
        
        print()
        print("✅ Dados de teste criados com sucesso!")
        print()
        print(f"📊 Resumo:")
        print(f"   💰 Transações Bancárias: {created['bank_transactions']}")
        print(f"   🔧 Serviços Mecânicos: {created['mechanic_services']}")
        print(f"   💳 Eventos de Cartões: {created['bank_cards']}")
        print()
        print("🎯 Próximos passos:")
        print("   1. Acesse: http://localhost:3000/logs/economy")
        print("   2. Navegue pelas 4 abas")
        print("   3. Veja os KPIs no topo da página")
        print()
        print("🔗 Verificar API:")
        print("   curl http://localhost:8000/v2/logs/economy-extended/stats/ | jq")

if __name__ == "__main__":
    asyncio.run(create_test_data())
