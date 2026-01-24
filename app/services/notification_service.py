from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import engine
from app.core.logger import logger
from app.models.gameplay_v2 import SentinelRaidMinigame
from app.models.players_registry_v2 import SentinelPlayerRegistry
from app.models.clan_v2 import SentinelClan, SentinelClanMember
from app.models.notification_v2 import SentinelNotificationLog
from app.services.evolution_api import evolution_service
from app.services.queue_service import notification_queue
from datetime import datetime
import pytz
from app.core.config import settings

class NotificationService:
    def __init__(self):
        # Controle de Spam: { target_steam_id: {'last_alert': datetime, 'suppressed_count': int} }
        self._spam_control = {}
        self.COOLDOWN_SECONDS = 120  # Agrupa notificações por 2 minutos (exceto sucessos)

    def _resolve_plan_tier(self, entity) -> str:
        """
        Retorna o tier efetivo (free/premium) verificando a data de validade.
        Se expirou ou não tem data definida, retorna 'free'.
        """
        current_tier = getattr(entity, 'plan_tier', 'free')
        if current_tier != 'premium':
            return 'free'
        
        expires_at = getattr(entity, 'plan_expires_at', None)
        if not expires_at:
            # Regra estrita: Se é Premium mas não tem data, considera inválido/free.
            return 'free'
            
        if expires_at < datetime.utcnow():
            return 'free'
            
        return 'premium'

    def _should_throttle(self, steam_id: str, is_success: bool) -> tuple[bool, int]:
        """
        Verifica se a notificação deve ser silenciada (agrupada).
        Retorna: (deve_silenciar: bool, tentativas_acumuladas: int)
        """
        # 1. Se for SUCESSO, fura o bloqueio e notifica IMEDIATAMENTE.
        if is_success:
            if steam_id in self._spam_control:
                # Opcional: Podemos resetar ou manter para saber que houve tentativas antes
                pass 
            return False, 0

        now = datetime.utcnow()
        state = self._spam_control.get(steam_id)

        if state:
            elapsed = (now - state['last_alert']).total_seconds()
            if elapsed < self.COOLDOWN_SECONDS:
                # Ainda no cooldown -> Silencia e conta
                state['suppressed_count'] += 1
                return True, state['suppressed_count']
            
            # Cooldown acabou -> Envia e reseta contador, mas retorna quantos acumulou
            accommodated_count = state['suppressed_count']
            state['last_alert'] = now
            state['suppressed_count'] = 0
            return False, accommodated_count
        
        # Primeira ocorrência
        self._spam_control[steam_id] = {
            'last_alert': now,
            'suppressed_count': 0
        }
        return False, 0

    async def _log_notification(
        self,
        session: AsyncSession,
        notification_type: str,
        recipient_phone: str,
        recipient_type: str,
        message_content: str,
        status: str,
        recipient_steam_id: str = None,
        recipient_name: str = None,
        event_context: dict = None,
        error_message: str = None,
        api_response_code: int = None,
        api_response_body: str = None
    ):
        """
        Registra uma notificação enviada no banco de dados.
        """
        log = SentinelNotificationLog(
            sent_at=datetime.utcnow(),
            notification_type=notification_type,
            recipient_phone=recipient_phone,
            recipient_type=recipient_type,
            recipient_steam_id=recipient_steam_id,
            recipient_name=recipient_name,
            message_content=message_content,
            event_context=event_context,
            status=status,
            error_message=error_message,
            api_response_code=api_response_code,
            api_response_body=api_response_body,
            evolution_instance=evolution_service.instance
        )
        session.add(log)
        await session.commit()
        
    async def process_raid_event(self, raid: SentinelRaidMinigame):
        """
        Processa um evento de Raid e envia notificações via WhatsApp.
        """
        if not raid.target_owner_steam_id:
            return

        # --- SPAM CONTROL (Agrupamento) ---
        is_spam, missed_attempts = self._should_throttle(raid.target_owner_steam_id, raid.is_success)
        if is_spam:
            logger.info(f"🔇 Raid Notification Suppressed (Spam Control) for {raid.target_owner_steam_id}. Count: {missed_attempts}")
            return
        # ----------------------------------

        async with AsyncSession(engine, expire_on_commit=False) as session:
            try:
                # 1. Buscar Vítima
                victim = await session.get(SentinelPlayerRegistry, raid.target_owner_steam_id)
                victim_name = victim.current_name if victim else raid.target_owner_name or "Desconhecido"
                
                # 2. Formatar Mensagem
                title = "🚨 *ALARME DE BASE* 🚨"
                if raid.is_success:
                    body_status = "⚠️ *PERIGO: TRANCAS VIOLADAS!* O invasor conseguiu abrir."
                else:
                    body_status = "🛡️ *ALERTA: TENTATIVA DE INVASÃO!* A tranca está sendo atacada."
                    if missed_attempts > 0:
                        body_status += f"\n(Detectamos {missed_attempts} tentativas adicionais nos últimos minutos)"

                loc_x = raid.location.get('x', 0)
                loc_y = raid.location.get('y', 0)
                loc_z = raid.location.get('z', 0)

                # Link do SCUM-MAP (Formato: X,Y,Zoom)
                # User pediu literalmente "nesse formato ... 2.5", vou respeitar o 2.5 ou usar algo dinamico?
                # O formato do user foi um exemplo. Vou usar os valores reais de X e Y.
                map_url = f"https://scum-map.com/en/shared/scum/island/{loc_x},{loc_y},4.0"

                # Timezone Conversion
                processed_time = raid.timestamp
                if processed_time:
                    try:
                        # Assume raid.timestamp is UTC (naive)
                        utc_dt = processed_time.replace(tzinfo=pytz.UTC)
                        local_tz = pytz.timezone(settings.TIMEZONE)
                        local_dt = utc_dt.astimezone(local_tz)
                        time_str = local_dt.strftime('%H:%M:%S')
                    except Exception as e:
                        logger.error(f"Timezone conversion error: {e}")
                        time_str = processed_time.strftime('%H:%M:%S') # Fallback
                else:
                    time_str = "N/A"

                # Mensagem PREMIUM (Completa)
                message_premium = (
                    f"{title}\n\n"
                    f"{body_status}\n\n"
                    f"📦 *Alvo*: {raid.target_object} ({raid.lock_type or 'Tranca'})\n"
                    f"🛡️ *Dono*: {victim_name}\n"
                    f"🗺️ *Mapa*: {map_url}\n"
                    f"🕒 *Horário*: {time_str}\n"
                )

                # Mensagem FREE (Simplificada sem Dono/Mapa)
                message_free = (
                    f"{title}\n\n"
                    f"{body_status}\n\n"
                    f"📦 *Alvo*: {raid.target_object} ({raid.lock_type or 'Tranca'})\n"
                    f"🕒 *Horário*: {time_str}\n"
                )

                # Retrocompatibilidade (caso algo use 'message' abaixo)
                message = message_premium
                
                # Contexto do evento para logging
                event_context = {
                    "raid_id": raid.id if hasattr(raid, 'id') else None,
                    "attacker_steam_id": raid.attacker_steam_id,
                    "attacker_name": raid.attacker_name,
                    "target_object": raid.target_object,
                    "lock_type": raid.lock_type,
                    "is_success": raid.is_success,
                    "location": raid.location,
                    "timestamp": raid.timestamp.isoformat() if raid.timestamp else None
                }

                # --- PROVISORIO: Enviar SEMPRE para Grupo de Teste (DEBUG) ---
                # try:
                #     debug_group_id = "120363405194072818@g.us"
                #     debug_success = await evolution_service.send_message(debug_group_id, message)
                    
                #     await self._log_notification(
                #         session=session,
                #         notification_type="raid_alert", # Mantendo raid_alert pra aparecer nos filtros normais se quiser
                #         recipient_phone=debug_group_id,
                #         recipient_type="test_group",
                #         recipient_steam_id=raid.target_owner_steam_id,
                #         recipient_name="[DEBUG] Grupo Monitoramento",
                #         message_content=message,
                #         event_context=event_context,
                #         status="success" if debug_success else "failed",
                #         error_message=None if debug_success else "Debug Send Failed"
                #     )
                # except Exception as e_debug:
                #     logger.error(f"Erro ao enviar debug notification: {e_debug}")
                # -------------------------------------------------------------
                
                
                # Helper para envio com delay dependendo do plano
                async def _send_smart_notification(recipient_phone, plan_tier, recipient_type, s_id, r_name):
                    # Seleciona Mensagem
                    msg_content = message_free if plan_tier == 'free' else message_premium

                    # Delay Logic
                    delay_msg = ""
                    if plan_tier == 'free':
                        DELAY_MINUTES = 10
                        # Enfileira
                        await notification_queue.enqueue_notification(
                            recipient_phone=recipient_phone,
                            message=msg_content,
                            delay_minutes=DELAY_MINUTES,
                            metadata=event_context
                        )
                        status = "queued"
                        error = f"Queued for {DELAY_MINUTES}min (Free Tier)"
                        success = True # Accepted for queue
                        delay_msg = f" (Queued: {DELAY_MINUTES}m)"
                    else:
                        # Premium: Envia Agora
                        success = await evolution_service.send_message(recipient_phone, msg_content)
                        status = "success" if success else "failed"
                        error = None if success else "Evolution API Error"

                    # Log Notification Change
                    await self._log_notification(
                        session=session,
                        notification_type="raid_alert",
                        recipient_phone=recipient_phone,
                        recipient_type=recipient_type,
                        recipient_steam_id=s_id,
                        recipient_name=r_name + delay_msg,
                        message_content=msg_content,
                        event_context=event_context,
                        status=status,
                        error_message=error,
                        api_response_code=201 if success else None
                    )

                # 3. Enviar para Vítima (se tiver telefone)
                if victim and victim.phone_number:
                    # Check Plan (com expiração)
                    tier = self._resolve_plan_tier(victim)
                    await _send_smart_notification(victim.phone_number, tier, "player", raid.target_owner_steam_id, victim_name)

                # 4. Enviar para Clã (se houver)
                stmt = select(SentinelClanMember).where(SentinelClanMember.steam_id == raid.target_owner_steam_id)
                member_result = await session.execute(stmt)
                member = member_result.scalar_one_or_none()
                
                if member:
                    # FIX: Buscar Clã pelo scum_clan_id (que é o que está em member.clan_id), não pelo PK
                    clan_stmt = select(SentinelClan).where(SentinelClan.scum_clan_id == member.clan_id)
                    clan_result = await session.execute(clan_stmt)
                    clan = clan_result.scalar_one_or_none()
                    
                    if clan:
                        clan_tier = self._resolve_plan_tier(clan)

                        # Prioridade: Grupo do WhatsApp
                        if clan.whatsapp_group_id:
                            await _send_smart_notification(clan.whatsapp_group_id, clan_tier, "clan_group", raid.target_owner_steam_id, f"Clã: {clan.name}")
                        
                        # Também enviar para todos os membros que tenham telefone (exceto a própria vítima que já recebeu)
                        # Busca todos os members do clan
                        members_stmt = select(SentinelClanMember).where(SentinelClanMember.clan_id == clan.scum_clan_id)
                        all_members = (await session.execute(members_stmt)).scalars().all()
                        
                        logger.info(f"🔎 Clan Processing: Found {len(all_members)} members for Clan {clan.name} (ID: {clan.scum_clan_id})")

                        for m in all_members:
                            if m.steam_id == raid.target_owner_steam_id:
                                continue # Já enviado
                            
                            # Buscar dados do player para pegar telefone
                            p_info = await session.get(SentinelPlayerRegistry, m.steam_id)
                            
                            if p_info and p_info.phone_number:
                                # Determina qual Tier usar:
                                # Se o CLÃ for PremiumOU o MEMBRO for Premium (regra solicitada: "premium individual recebe notificação de clan members")
                                # Então o envio é instantâneo.
                                
                                member_tier = self._resolve_plan_tier(p_info)
                                
                                # Regra de Ouro Refinada:
                                # 1. PREMIUM recebe TUDO (Sua base e bases de aliados) instantaneamente.
                                # 2. FREE recebe APENAS ATAQUES NA SUA PRÓPRIA BASE (com delay).
                                #    Free NÃO recebe notificação de aliados sendo raidados.
                                
                                # Se é Premium, recebe instantâneo
                                if member_tier == 'premium' or clan_tier == 'premium':
                                     await _send_smart_notification(p_info.phone_number, 'premium', "clan_member", m.steam_id, p_info.current_name)
                                else:
                                    # Se é Free: Só recebe se a base for DELE (mas isso já foi tratado no passo 3 "Enviar para Vítima").
                                    # Portanto, aqui no loop de Clã, se o cara é Free, ele NÃO deve receber nada sobre aliados.
                                    # Passo 4 loopa SOBRE ALIDOS. Se for a própria vítima, já caiu no `continue` acima.
                                    # Logo: Free não recebe nada aqui.
                                    logger.info(f"🚫 Notification Skipped: Member {p_info.current_name} is FREE and this is not their base.")
                                    continue

            
            except Exception as e:
                logger.error(f"Erro ao processar notificação de Raid: {e}")

notification_service = NotificationService()
