import re
from datetime import datetime, timezone
from typing import Optional, Union, List
from app.models.economy_v2 import (
    SentinelEconomyTrade, 
    SentinelEconomyBalance,
    SentinelBankTransaction,
    SentinelMechanicService,
    SentinelBankCard,
    SentinelUnparsedLog
)

class EconomyParserV2:
    # ========================================================================
    # TRADE PATTERNS - Compras e Vendas
    # ========================================================================
    
    # PURCHASE FORMAT: Tradeable (Item (x1)) purchased by Player(ID) for 100 money from trader Name
    # ENHANCED: Agora captura coordenadas se disponíveis
    REGEX_PURCHASE = re.compile(
        r"(?P<timestamp>[\d\.-]+): \[Trade\] Tradeable \((?P<item>.*?) \(x(?P<count>\d+)\)\) "
        r"purchased by (?P<name>.*?)\((?P<steam_id>\d+)\) for (?P<price>\d+) money from trader (?P<trader>.*?)"
        r"(?:, old amount.*: (?P<stock_old>[\d-]+), new amount.*: (?P<stock_new>[\d-]+))?"
        r"(?:.*users online: (?P<users>\d+))?"
        r"(?:.*at X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+))?"
    )
    
    # SELL FORMAT: Tradeable (Item (health: X, uses: Y)) sold by Player(ID) for 100 (X + Y worth of contained items)
    # ENHANCED: Captura health e uses separadamente
    REGEX_SELL = re.compile(
        r"(?P<timestamp>[\d\.-]+): \[Trade\] Tradeable \((?P<item>.*?)"
        r"(?: \(health: (?P<health>[\d\.]+)(?:, uses: (?P<uses>\d+))?\))?\) "
        r"sold by (?P<name>.*?)\((?P<steam_id>\d+)\) for (?P<price>\d+) "
        r"\((?P<base_price>\d+) \+ (?P<items_price>\d+) worth of contained items\) to trader (?P<trader>.*?)"
        r"(?:, old amount.*: (?P<stock_old>[\d-]+), new amount.*: (?P<stock_new>[\d-]+))?"
        r"(?:.*users online: (?P<users>\d+))?"
        r"(?:.*at X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+))?"
    )

    # ========================================================================
    # BALANCE PATTERNS - Snapshots de Saldo
    # ========================================================================
    REGEX_BALANCE = re.compile(
        r"(?P<timestamp>[\d\.-]+): \[Trade\] (?P<context>Before|After).*?trader (?P<trader>.*?), "
        r"player (?P<name>.*?)\((?P<steam_id>\d+)\) (?:has|had) "
        r"(?P<cash>[\d\.]+) cash, (?P<bank>[\d\.]+) (?:bank )?account balance and (?P<gold>[\d\.]+) gold"
        r".*trader (?:has|had) (?P<funds>[\d\.]+) funds"
    )
    
    # ========================================================================
    # BANK TRANSACTION PATTERNS - Saques, Depósitos e Transferências
    # ========================================================================
    
    # Depósitos e Saques
    REGEX_BANK_DEPOSIT_WITHDRAW = re.compile(
        r"(?P<timestamp>[\d\.-]+): \[Bank\] (?P<name>.*?)\(ID:(?P<steam_id>\d+)\)\(Account Number:(?P<account>\d+)\) "
        r"(?P<action>deposited|withdrew) (?P<gross>\d+)\((?P<net>\d+) was (?:added|removed)\) "
        r"(?:from |to )?Account Number: (?P<account_ref>\d+)\((?P<name_ref>.*?)\)\((?P<steam_ref>\d+)\) "
        r"at X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)"
    )
    
    # Transferências entre jogadores
    REGEX_BANK_TRANSFER = re.compile(
        r"(?P<timestamp>[\d\.-]+): \[Bank\] (?P<name>.*?)\(ID:(?P<steam_id>\d+)\)\(Account Number:(?P<account>\d+)\) "
        r"transferred (?P<gross>\d+)\((?P<net>\d+) was removed\) "
        r"from Account Number: (?P<account_from>\d+).*?"
        r"to Account Number: (?P<account_to>\d+)\((?P<target_name>.*?)\)\((?P<target_id>\d+)\) "
        r"at X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)"
    )
    
    # ========================================================================
    # MECHANIC SERVICE PATTERNS - Serviços de Mecânico
    # ========================================================================
    REGEX_MECHANIC = re.compile(
        r"(?P<timestamp>[\d\.-]+): \[Trade-Mechanic\] Service \((?P<service>Buy|Install|Repair|Remove) attachment (?P<item>.*?)\) "
        r"purchased by (?P<name>.*?)\((?P<steam_id>\d+)\) for (?P<price>\d+) money from trader (?P<trader>.*?)"
        r"(?:.*at X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+))?"
    )
    
    # ========================================================================
    # BANK CARD PATTERNS - Gestão de Cartões
    # ========================================================================
    
    # Compra de Cartão
    REGEX_CARD_PURCHASE = re.compile(
        r"(?P<timestamp>[\d\.-]+): \[Bank\] (?P<name>.*?)\(ID:(?P<steam_id>\d+)\)\(Account Number:(?P<account>\d+)\) "
        r"purchased (?P<card_type>.*? card) \(free renewal: (?P<renewal>yes|no)\), "
        r"new account balance is (?P<balance>\d+) credits, "
        r"at X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)\."
    )
    
    # Destruição de Cartão
    REGEX_CARD_DESTROY = re.compile(
        r"(?P<timestamp>[\d\.-]+): \[Bank\] (?P<name>.*?)\(ID:(?P<steam_id>\d+)\)\(Account Number:(?P<account>\d+)\) "
        r"manually destroyed (?P<card_type>.*? card) belonging to Account Number:(?P<destroyed_account>\d+), "
        r"at X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)\."
    )

    @staticmethod
    def parse(line: str) -> Union[
        SentinelEconomyTrade, 
        SentinelEconomyBalance,
        SentinelBankTransaction,
        SentinelMechanicService,
        SentinelBankCard,
        SentinelUnparsedLog,
        None
    ]:
        """
        Parser principal que tenta todos os padrões em ordem de prioridade.
        Retorna o model apropriado ou SentinelUnparsedLog se nada der match.
        RESPEITA O WIPE_DATE: Se o log for anterior ao wipe, retorna None.
        """
        line = line.strip()
        if not line:
            return None
        
        # 1. Parse the line
        result = EconomyParserV2._try_parse_all(line)
        
        # 2. Check Wipe Date (if parsed successfully and is not UnparsedLog)
        if result and not isinstance(result, SentinelUnparsedLog):
            from app.core.config import settings
            
            if settings.WIPE_DATE:
                try:
                    # Parse wipe date (assumes ISO format in settings)
                    wipe_date = datetime.fromisoformat(settings.WIPE_DATE)
                    if wipe_date.tzinfo is None:
                        # If naive, assume UTC or configure tz
                        from zoneinfo import ZoneInfo
                        tz = ZoneInfo(settings.TIMEZONE)
                        wipe_date = wipe_date.replace(tzinfo=tz)
                    
                    # Ensure comparison in UTC
                    wipe_date_utc = wipe_date.astimezone(timezone.utc)
                    
                    # Comparar: Se log timestamp < wipe_date, ignorar
                    if result.timestamp < wipe_date_utc:
                        return None
                        
                except Exception as e:
                    # Se falhar ao checar data, loga erro mas permite passar (ou bloqueia?)
                    # Por segurança, melhor deixar passar e corrigir configuração
                    print(f"Error checking WIPE_DATE: {e}")
                    pass
        
        return result

    @staticmethod
    def _try_parse_all(line: str):
        """Helper to try all parsers in order"""
        
        # Lista de parsers tentados (para debug)
        attempted = []
        
        # ====================================================================
        # 1. MECHANIC SERVICES (Prioridade alta - padrão específico)
        # ====================================================================
        result = EconomyParserV2._parse_mechanic(line)
        if result:
            return result
        attempted.append("mechanic")
        
        # ====================================================================
        # 2. BANK CARDS (Compra e Destruição)
        # ====================================================================
        result = EconomyParserV2._parse_card_purchase(line)
        if result:
            return result
        attempted.append("card_purchase")
        
        result = EconomyParserV2._parse_card_destroy(line)
        if result:
            return result
        attempted.append("card_destroy")
        
        # ====================================================================
        # 3. BANK TRANSACTIONS (Transferências, Depósitos, Saques)
        # ====================================================================
        result = EconomyParserV2._parse_bank_transfer(line)
        if result:
            return result
        attempted.append("bank_transfer")
        
        result = EconomyParserV2._parse_bank_deposit_withdraw(line)
        if result:
            return result
        attempted.append("bank_deposit_withdraw")
        
        # ====================================================================
        # 4. TRADES (Purchase e Sell)
        # ====================================================================
        result = EconomyParserV2._parse_purchase(line)
        if result:
            return result
        attempted.append("purchase")
        
        result = EconomyParserV2._parse_sell(line)
        if result:
            return result
        attempted.append("sell")
        
        # ====================================================================
        # 5. BALANCE SNAPSHOTS
        # ====================================================================
        result = EconomyParserV2._parse_balance(line)
        if result:
            return result
        attempted.append("balance")
        
        # ====================================================================
        # FALLBACK: Log não reconhecido (Anti-Fuga)
        # ====================================================================
        # Só registra se a linha parece ser um log de economia válido
        if "[Trade]" in line or "[Bank]" in line or "[Trade-Mechanic]" in line:
            return SentinelUnparsedLog(
                log_type="economy",
                filename="unknown",  # Será preenchido pelo daemon
                raw_line=line,
                attempted_parsers=", ".join(attempted)
            )
        
        return None

    # ========================================================================
    # HELPER PARSERS - Métodos específicos para cada tipo
    # ========================================================================
    
    @staticmethod
    def _parse_purchase(line: str) -> Optional[SentinelEconomyTrade]:
        match = EconomyParserV2.REGEX_PURCHASE.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        return SentinelEconomyTrade(
            timestamp=EconomyParserV2._ts(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            trade_type="Purchase",
            item_class=data["item"],
            item_count=int(data["count"]),
            total_price=float(data["price"]),
            trader_name=data["trader"].rstrip(','),
            users_online=int(data["users"]) if data.get("users") else None,
            store_stock_before=int(data["stock_old"]) if data.get("stock_old") else None,
            store_stock_after=int(data["stock_new"]) if data.get("stock_new") else None,
            pos_x=float(data["x"]) if data.get("x") else None,
            pos_y=float(data["y"]) if data.get("y") else None,
            pos_z=float(data["z"]) if data.get("z") else None
        )
    
    @staticmethod
    def _parse_sell(line: str) -> Optional[SentinelEconomyTrade]:
        match = EconomyParserV2.REGEX_SELL.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        
        return SentinelEconomyTrade(
            timestamp=EconomyParserV2._ts(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            trade_type="Sell",
            item_class=data["item"],
            item_count=1,  # Sells are always 1 item
            item_health=float(data["health"]) if data.get("health") else None,
            item_uses=int(data["uses"]) if data.get("uses") else None,
            total_price=float(data["price"]),
            trader_name=data["trader"].rstrip(','),
            users_online=int(data["users"]) if data.get("users") else None,
            store_stock_before=int(data["stock_old"]) if data.get("stock_old") else None,
            store_stock_after=int(data["stock_new"]) if data.get("stock_new") else None,
            pos_x=float(data["x"]) if data.get("x") else None,
            pos_y=float(data["y"]) if data.get("y") else None,
            pos_z=float(data["z"]) if data.get("z") else None
        )

    @staticmethod
    def _parse_balance(line: str) -> Optional[SentinelEconomyBalance]:
        match = EconomyParserV2.REGEX_BALANCE.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        return SentinelEconomyBalance(
            timestamp=EconomyParserV2._ts(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            trigger_event=data["context"],
            trader_name=data["trader"],
            cash=float(data["cash"]),
            bank=float(data["bank"]),
            gold=float(data["gold"]),
            trader_funds=float(data["funds"])
        )
    
    @staticmethod
    def _parse_bank_deposit_withdraw(line: str) -> Optional[SentinelBankTransaction]:
        match = EconomyParserV2.REGEX_BANK_DEPOSIT_WITHDRAW.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        gross = float(data["gross"])
        net = float(data["net"])
        
        return SentinelBankTransaction(
            timestamp=EconomyParserV2._ts(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            account_number=data["account"],
            transaction_type=data["action"],  # "deposited" or "withdrew"
            gross_amount=gross,
            net_amount=net,
            fee=abs(gross - net) if gross != net else None,
            pos_x=float(data["x"]),
            pos_y=float(data["y"]),
            pos_z=float(data["z"])
        )
    
    @staticmethod
    def _parse_bank_transfer(line: str) -> Optional[SentinelBankTransaction]:
        match = EconomyParserV2.REGEX_BANK_TRANSFER.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        gross = float(data["gross"])
        net = float(data["net"])
        
        return SentinelBankTransaction(
            timestamp=EconomyParserV2._ts(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            account_number=data["account_from"],
            transaction_type="transfer",
            gross_amount=gross,
            net_amount=net,
            fee=abs(gross - net) if gross != net else None,
            target_account=data["account_to"],
            target_name=data["target_name"],
            target_steam_id=data["target_id"],
            pos_x=float(data["x"]),
            pos_y=float(data["y"]),
            pos_z=float(data["z"])
        )
    
    @staticmethod
    def _parse_mechanic(line: str) -> Optional[SentinelMechanicService]:
        match = EconomyParserV2.REGEX_MECHANIC.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        return SentinelMechanicService(
            timestamp=EconomyParserV2._ts(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            service_type=data["service"],
            item_class=data["item"],
            price=float(data["price"]),
            trader_name=data["trader"],
            pos_x=float(data["x"]) if data.get("x") else None,
            pos_y=float(data["y"]) if data.get("y") else None,
            pos_z=float(data["z"]) if data.get("z") else None
        )
    
    @staticmethod
    def _parse_card_purchase(line: str) -> Optional[SentinelBankCard]:
        match = EconomyParserV2.REGEX_CARD_PURCHASE.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        return SentinelBankCard(
            timestamp=EconomyParserV2._ts(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            account_number=data["account"],
            action="purchased",
            card_type=data["card_type"],
            free_renewal=(data["renewal"] == "yes"),
            new_balance=float(data["balance"]),
            pos_x=float(data["x"]),
            pos_y=float(data["y"]),
            pos_z=float(data["z"])
        )
    
    @staticmethod
    def _parse_card_destroy(line: str) -> Optional[SentinelBankCard]:
        match = EconomyParserV2.REGEX_CARD_DESTROY.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        return SentinelBankCard(
            timestamp=EconomyParserV2._ts(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            account_number=data["account"],
            action="manually destroyed",
            card_type=data["card_type"],
            destroyed_account=data["destroyed_account"],
            pos_x=float(data["x"]),
            pos_y=float(data["y"]),
            pos_z=float(data["z"])
        )

    @staticmethod
    def _ts(ts_str: str):
        """Parse timestamp from SCUM log format"""
        from datetime import datetime, timezone
        
        try:
            dt = datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
            
            # Return as UTC
            return dt.astimezone(timezone.utc)
        except:
            return datetime.now(timezone.utc)


