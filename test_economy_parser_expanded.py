#!/usr/bin/env python3
"""
Test script para validar os novos parsers de economia expandidos.
Testa todos os padrões: trades, balances, bank transactions, mechanic services, cards.
"""

import sys
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')

from app.services.parsers_v2.economy import EconomyParserV2
from app.models.economy_v2 import (
    SentinelEconomyTrade,
    SentinelEconomyBalance,
    SentinelBankTransaction,
    SentinelMechanicService,
    SentinelBankCard,
    SentinelUnparsedLog
)

# ============================================================================
# TEST CASES
# ============================================================================

test_cases = [
    # PURCHASE
    {
        "name": "Purchase - Basic",
        "line": "2025.12.21-16.23.35: [Trade] Tradeable (BP_BCUUpgradeService (x1)) purchased by VINI SEAL W2(76561199211519717) for 5000 money from trader A_0_Hospital, old amount in store was -1, new amount is -1, and effective users online: 5",
        "expected_type": SentinelEconomyTrade,
        "expected_fields": {
            "trade_type": "Purchase",
            "item_class": "BP_BCUUpgradeService",
            "item_count": 1,
            "total_price": 5000.0,
            "users_online": 5
        }
    },
    
    # SELL
    {
        "name": "Sell - With Health and Uses",
        "line": "2025.12.21-16.24.38: [Trade] Tradeable (Cal_5_56x45mm_Ammobox (health: 100.00, uses: 1)) sold by VINI SEAL W2(76561199211519717) for 498 (498 + 0 worth of contained items) to trader A_0_Armory, old amount in store is -1, new amount is -1, and effective users online: 5",
        "expected_type": SentinelEconomyTrade,
        "expected_fields": {
            "trade_type": "Sell",
            "item_class": "Cal_5_56x45mm_Ammobox",
            "item_health": 100.0,
            "item_uses": 1,
            "total_price": 498.0
        }
    },
    
    # BALANCE
    {
        "name": "Balance - Before",
        "line": "2025.12.21-16.23.35: [Trade] Before purchasing tradeales from trader A_0_Hospital, player VINI SEAL W2(76561199211519717) had 0 cash, 41967 account balance and 127 gold and trader had 100000 funds.",
        "expected_type": SentinelEconomyBalance,
        "expected_fields": {
            "trigger_event": "Before",
            "cash": 0.0,
            "bank": 41967.0,
            "gold": 127.0,
            "trader_funds": 100000.0
        }
    },
    
    # BANK DEPOSIT
    {
        "name": "Bank Deposit",
        "line": "2025.12.21-17.56.19: [Bank] Apocalipse(ID:76561199485971199)(Account Number:717600024910) deposited 4966(4866 was added) to Account Number: 717600024910(Apocalipse)(76561199485971199) at X=20805.250 Y=-676730.438 Z=345.170",
        "expected_type": SentinelBankTransaction,
        "expected_fields": {
            "transaction_type": "deposited",
            "gross_amount": 4966.0,
            "net_amount": 4866.0,
            "fee": 100.0,
            "pos_x": 20805.250
        }
    },
    
    # CARD PURCHASE
    {
        "name": "Card Purchase - Gold",
        "line": "2025.12.21-16.23.19: [Bank] VINI SEAL W2(ID:76561199211519717)(Account Number:715204003927) purchased Gold card (free renewal: yes), new account balance is 41967 credits, at X=-623708.188 Y=-559208.938 Z=2557.000.",
        "expected_type": SentinelBankCard,
        "expected_fields": {
            "action": "purchased",
            "card_type": "Gold card",
            "free_renewal": True,
            "new_balance": 41967.0
        }
    },
    
    # CARD DESTROY
    {
        "name": "Card Destroy - Starter",
        "line": "2025.12.21-16.23.11: [Bank] VINI SEAL W2(ID:76561199211519717)(Account Number:715204003927) manually destroyed Starter card belonging to Account Number:719100007328, at X=-623708.188 Y=-559208.938 Z=2557.000.",
        "expected_type": SentinelBankCard,
        "expected_fields": {
            "action": "manually destroyed",
            "card_type": "Starter card",
            "destroyed_account": "719100007328"
        }
    },
    
    # UNPARSED (should create unparsed log)
    {
        "name": "Unparsed - Unknown Bank Event",
        "line": "2025.12.21-16.23.11: [Bank] Some unknown event that doesn't match any pattern",
        "expected_type": SentinelUnparsedLog,
        "expected_fields": {
            "log_type": "economy"
        }
    }
]

# ============================================================================
# RUN TESTS
# ============================================================================

def run_tests():
    print("=" * 80)
    print("🧪 TESTANDO PARSERS DE ECONOMIA EXPANDIDOS")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print(f"  Line: {test['line'][:80]}...")
        
        try:
            result = EconomyParserV2.parse(test['line'])
            
            # Check type
            if not isinstance(result, test['expected_type']):
                print(f"  ❌ FAILED: Expected {test['expected_type'].__name__}, got {type(result).__name__}")
                failed += 1
                print()
                continue
            
            # Check fields
            all_fields_ok = True
            for field, expected_value in test['expected_fields'].items():
                actual_value = getattr(result, field, None)
                if actual_value != expected_value:
                    print(f"  ❌ Field '{field}': expected {expected_value}, got {actual_value}")
                    all_fields_ok = False
            
            if all_fields_ok:
                print(f"  ✅ PASSED")
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        
        print()
    
    print("=" * 80)
    print(f"📊 RESULTADOS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
