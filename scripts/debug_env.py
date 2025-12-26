from app.core.config import settings
import socket

print(f"DEBUG: SFTP_HOST='{settings.SFTP_HOST}'")
print(f"DEBUG: Type={type(settings.SFTP_HOST)}")
print(f"DEBUG: Length={len(settings.SFTP_HOST)}")

try:
    socket.gethostbyname(settings.SFTP_HOST)
    print("DEBUG: DNS Resolve SUCCESS")
except Exception as e:
    print(f"DEBUG: DNS Resolve FAILED: {e}")
