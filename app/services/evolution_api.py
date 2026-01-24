import httpx
from typing import Optional
from app.core.config import settings
from app.core.logger import logger

class EvolutionService:
    def __init__(self):
        # We access settings dynamically in methods usually, but init is fine if settings are static
        pass

    @property
    def base_url(self):
        return settings.EVOLUTION_API_URL

    @property
    def token(self):
        return settings.EVOLUTION_API_TOKEN

    @property
    def instance(self):
        return settings.EVOLUTION_INSTANCE_NAME

    async def send_message(self, number: str, text: str) -> bool:
        """
        Send a text message via Evolution API.
        :param number: Phone number (e.g. 5511999999999) or Group JID
        :param text: Message content
        """
        if not self.base_url or not self.token:
            logger.warning("Evolution API not configured (URL or Token missing).")
            return False

        if not number:
            return False

        # Remove @s.whatsapp.net or @g.us if user typed it, though EvoAPI might need it depending on version.
        # Usually EvoAPI takes just the number for private, but for groups it needs the JID.
        # Let's assume number is passed correctly.
        
        url = f"{self.base_url}/message/sendText/{self.instance}"
        
        headers = {
            "apikey": self.token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "number": number,
            "text": text,
            "delay": 1200,
            "linkPreview": False
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
                
                if response.status_code == 201 or response.status_code == 200:
                    logger.info(f"📨 WhatsApp sent to {number}")
                    return True
                else:
                    logger.error(f"❌ Failed to send WhatsApp to {number}: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                logger.error(f"❌ Error sending WhatsApp message: {e}")
                return False

    async def check_number(self, number: str) -> dict:
        """
        Check if a number exists on WhatsApp.
        Returns dict with status and details.
        """
        if not self.base_url or not self.token:
             return {"exists": False, "error": "API Not Configured"}

        # Use Evo API v2 format 
        # Endpoint: /chat/whatsappNumbers/{instance}
        # Body: {"numbers": ["55..."]}
        url = f"{self.base_url}/chat/whatsappNumbers/{self.instance}"
        
        headers = {
            "apikey": self.token,
            "Content-Type": "application/json"
        }
        
        # Ensure number has no special chars and isn't group JID (unless it is?)
        # Just clean basic chars
        clean_number = number.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")

        payload = {
            "numbers": [clean_number]
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    # Response format usually: [{"number": "...", "exists": true, "jid": "..."}]
                    if isinstance(data, list) and len(data) > 0:
                        first = data[0]
                        exists = first.get("exists", False)
                        return {"exists": exists, "jid": first.get("jid"), "formatted": clean_number}
                    return {"exists": False, "error": "No data returned"}
                else:
                    return {"exists": False, "error": f"API Error: {response.status_code}"}
            except Exception as e:
                logger.error(f"Error checking WA number: {e}")
                return {"exists": False, "error": str(e)}

    async def check_group(self, group_jid: str) -> dict:
        """
        Check if a Group JID is valid and bot is in it.
        """
        if not self.base_url or not self.token:
             return {"exists": False, "error": "API Not Configured"}

        # Endpoint: /group/findGroupInfos/{instance}?groupJid=...
        url = f"{self.base_url}/group/findGroupInfos/{self.instance}"
        
        headers = {
            "apikey": self.token
        }
        
        params = {"groupJid": group_jid}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    # If data has 'subject' or 'id', it exists
                    if data and (data.get("subject") or data.get("id")):
                        return {"exists": True, "name": data.get("subject"), "jid": data.get("id")}
                    return {"exists": False}
                elif response.status_code == 404:
                     return {"exists": False, "error": "Group Not Found"}
                else:
                    return {"exists": False, "error": f"API Error: {response.status_code}"}
            except Exception as e:
                logger.error(f"Error checking WA group: {e}")
                return {"exists": False, "error": str(e)}

evolution_service = EvolutionService()
