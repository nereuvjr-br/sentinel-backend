
content = """ENV=dev
LOG_LEVEL=INFO
LOG_RETENTION_HOURS=24
WIPE_DATE=2025-12-22T12:30:00
TIMEZONE=America/Sao_Paulo

# --- DATABASE ---
DATABASE_URL=postgresql://admin:da139c45ed91909b2856206092736e80@159.65.174.208:5432/sentinel_dev

# --- SFTP CREDENTIALS ---
SFTP_HOST=138.199.5.114
SFTP_PORT=8822
SFTP_USER=diegosz28@gmail.com
SFTP_PASS=P@s$w0rd010701
REMOTE_LOG_PATH=/138.199.5.114_7122/SaveFiles/Logs

# --- SECURITY ---
SECRET_KEY=development_secret_key_only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# --- WEBHOOKS ---
DISCORD_WEBHOOK_ALERTS=
DISCORD_WEBHOOK_KILLFEED=

# --- BUSINESS LOGIC ---
EXCLUDED_ITEMS=Improvised_Metal_Chest,BPC_WolfsWagen,BPC_Laika,BPC_Rager,BPC_RIS,Improved_Wooden_Chest,Hiking_Backpack_01_02,Hiking_Backpack_01_01
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(content)

print("Arquivo .env atualizado com novos itens excluídos.")
