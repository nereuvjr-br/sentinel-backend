"""
Script de diagnóstico para verificar o conteúdo dos logs
"""
from pathlib import Path

LOCAL_LOGS_DIR = r"C:\Servers\logs\logs\novos"

def analyze_logs():
    logs_dir = Path(LOCAL_LOGS_DIR)
    log_files = list(logs_dir.glob("*.log"))
    
    print(f"📊 Analisando {len(log_files)} arquivos...\n")
    
    # Agrupar por tipo
    by_type = {}
    empty_files = []
    sample_lines = {}
    
    for filepath in log_files:
        # Detectar tipo
        filename = filepath.name.lower()
        if 'kill' in filename:
            log_type = 'kill'
        elif 'economy' in filename or 'trade' in filename:
            log_type = 'economy'
        elif 'chat' in filename:
            log_type = 'chat'
        elif 'login' in filename:
            log_type = 'login'
        elif 'admin' in filename:
            log_type = 'admin'
        elif 'vehicle' in filename:
            log_type = 'vehicle'
        elif 'violation' in filename:
            log_type = 'violation'
        else:
            log_type = 'other'
        
        # Contar
        if log_type not in by_type:
            by_type[log_type] = 0
        by_type[log_type] += 1
        
        # Verificar se está vazio
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if not lines or all(not line.strip() for line in lines):
                    empty_files.append(filepath.name)
                elif log_type not in sample_lines and len(lines) > 0:
                    # Pegar primeira linha não vazia
                    for line in lines:
                        if line.strip():
                            sample_lines[log_type] = line.strip()
                            break
        except Exception as e:
            print(f"⚠️  Erro ao ler {filepath.name}: {e}")
    
    # Resumo por tipo
    print("📋 Arquivos por tipo:")
    for log_type, count in sorted(by_type.items()):
        print(f"  {log_type:15} : {count:3} arquivos")
    
    # Arquivos vazios
    print(f"\n📭 Arquivos vazios: {len(empty_files)}")
    if empty_files and len(empty_files) <= 10:
        for f in empty_files:
            print(f"  - {f}")
    elif len(empty_files) > 10:
        print(f"  (mostrando apenas os primeiros 10)")
        for f in empty_files[:10]:
            print(f"  - {f}")
    
    # Amostras de linhas
    print("\n📄 Amostras de linhas (primeira linha de cada tipo):")
    for log_type, line in sample_lines.items():
        print(f"\n{log_type.upper()}:")
        print(f"  {line[:200]}")  # Primeiros 200 caracteres

if __name__ == "__main__":
    analyze_logs()
