import re

# Regex que captura IDs numéricos, ignorando prefixos comuns como steam:, profile:, uid:, etc.
# Suporta: 
# - 76561198000000000 (Puro)
# - steam:76561198000000000
# - profile:12345
LOG_ID_REGEX = re.compile(r"^(?:(?:steam|sid|s|profile|uid|p):)?(\d+)$", re.IGNORECASE)

def extract_user_id(input_val: str | int | None) -> str | None:
    """
    Extrai um ID numérico limpo de uma string que pode conter prefixos.
    Retorna None se a entrada for inválida ou não contiver um ID numérico.
    """
    if input_val is None:
        return None
    
    input_str = str(input_val).strip()
    if not input_str:
        return None

    match = LOG_ID_REGEX.search(input_str)
    if match:
        return match.group(1)
    
    return None
