# 📋 Como Processar Logs Locais

## 🎯 Objetivo
Processar arquivos de log do diretório local `C:\Servers\logs\logs\novos` e salvá-los no banco de dados `sentinel_dev`.

---

## 🚀 Método 1: Script Automático (Recomendado)

### Executar o script:
```bash
cd c:\Users\nnvlj\scm-sentinel\sentinel-backend
python scripts/process_local_logs.py
```

### O que o script faz:
1. ✅ Lê todos os arquivos `.log` do diretório
2. ✅ Detecta automaticamente o tipo de log (kill, economy, chat, etc)
3. ✅ Usa os parsers V2 apropriados
4. ✅ Salva em lotes de 100 registros
5. ✅ Mostra progresso em tempo real
6. ✅ Exibe resumo final

### Tipos de log detectados:
- `kill*.log` → KillParserV2
- `login*.log` → LoginParserV2
- `chat*.log` → ChatParserV2
- `economy*.log` ou `trade*.log` → EconomyParserV2
- `admin*.log` → AdminParserV2
- `gameplay*.log` ou `raid*.log` → GameplayParserV2
- `chest*.log` → ChestFameParserV2 (chest)
- `fame*.log` → ChestFameParserV2 (fame)
- `violation*.log` ou `anticheat*.log` → ViolationParserV2
- `vehicle*.log` → VehicleParserV2

---

## 🔧 Método 2: Script Interativo (Avançado)

Se quiser mais controle, crie um script interativo:

```python
# scripts/process_local_logs_interactive.py
import asyncio
from pathlib import Path

LOCAL_LOGS_DIR = r"C:\Servers\logs\logs\novos"

async def main():
    logs_dir = Path(LOCAL_LOGS_DIR)
    log_files = list(logs_dir.glob("*.log"))
    
    print(f"Encontrados {len(log_files)} arquivos:")
    for idx, f in enumerate(log_files, 1):
        print(f"  {idx}. {f.name}")
    
    choice = input("\nProcessar todos? (s/n): ")
    if choice.lower() == 's':
        # Processar todos
        pass
    else:
        # Escolher arquivos específicos
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 Saída Esperada

```
🚀 Iniciando processamento de logs locais...
📂 Diretório: C:\Servers\logs\logs\novos

📊 Encontrados 15 arquivo(s) .log

[1/15] Processando: kill_20251226.log
  📋 Tipo detectado: kill
  ✅ Processado: 1250 registros
  ⏱️  Tempo: 3.45s

[2/15] Processando: economy_20251226.log
  📋 Tipo detectado: economy
  ✅ Processado: 890 registros
  ⏱️  Tempo: 2.12s

...

============================================================
✅ PROCESSAMENTO CONCLUÍDO!
============================================================
📊 Total de arquivos processados: 15
✅ Total de registros salvos: 12,450
============================================================
```

---

## ⚠️ Tratamento de Erros

### Erros comuns:

1. **Diretório não encontrado**
   ```
   ❌ Diretório não encontrado: C:\Servers\logs\logs\novos
   ```
   **Solução:** Verifique se o caminho está correto

2. **Nenhum arquivo .log**
   ```
   ⚠️  Nenhum arquivo .log encontrado no diretório
   ```
   **Solução:** Verifique se há arquivos .log no diretório

3. **Erro de parsing**
   ```
   ⚠️  Erro na linha 123: Invalid timestamp format
   ```
   **Solução:** O script continua processando as outras linhas

4. **Erro de banco de dados**
   ```
   ❌ Erro ao processar arquivo: Connection refused
   ```
   **Solução:** Verifique se o PostgreSQL está rodando

---

## 🔍 Verificar Resultados

Após processar, verifique os dados:

```bash
python scripts/list_tables.py
```

Ou consulte diretamente:

```sql
-- Ver total de kills processados
SELECT COUNT(*) FROM sentinel_kills;

-- Ver total de economy trades
SELECT COUNT(*) FROM sentinel_economy_trades;

-- Ver últimos 10 registros
SELECT * FROM sentinel_kills ORDER BY timestamp DESC LIMIT 10;
```

---

## 💡 Dicas

### 1. Processar apenas um tipo de log:
Modifique o script para filtrar:
```python
log_files = list(logs_dir.glob("kill*.log"))  # Apenas kills
```

### 2. Processar apenas logs recentes:
```python
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=7)
log_files = [f for f in logs_dir.glob("*.log") 
             if datetime.fromtimestamp(f.stat().st_mtime) > cutoff]
```

### 3. Modo dry-run (sem salvar):
Comente a linha de commit:
```python
# await session.commit()  # Comentar para não salvar
```

---

## 🚨 Importante

1. **Backup:** Faça backup do banco antes de processar muitos logs
2. **Performance:** Processar muitos arquivos pode demorar
3. **Duplicatas:** O script não verifica duplicatas automaticamente
4. **Memória:** Arquivos muito grandes são processados em lotes

---

## ✅ Checklist

Antes de executar:
- [ ] PostgreSQL está rodando
- [ ] Banco `sentinel_dev` existe
- [ ] Todas as tabelas foram criadas
- [ ] Diretório `C:\Servers\logs\logs\novos` existe
- [ ] Há arquivos `.log` no diretório

Após executar:
- [ ] Verificar total de registros salvos
- [ ] Verificar se há erros
- [ ] Validar dados no banco
- [ ] Testar APIs com novos dados

---

## 🎉 Pronto!

Execute o script e os logs locais serão processados automaticamente!

```bash
python scripts/process_local_logs.py
```
