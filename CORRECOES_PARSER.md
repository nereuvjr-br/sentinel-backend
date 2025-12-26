# Melhorias e Correções para o Parser Sentinel V2 (Baseado no SCTL)

Com base na análise do repositório consolidado `base/sctl` e comparação com o `sentinel-backend`, identificamos as seguintes melhorias e correções para elevar a qualidade, robustez e manutenibilidade do parser do Sentinel.

## 1. Robustez na Extração de IDs (SteamID / UserID)

O `sctl` implementa uma função `extractUserId` (`src/utils/utils.ts`) extremamente robusta que aceita múltiplos formatos de entrada. O parser atual do Sentinel muitas vezes captura apenas dígitos (`\d+`), o que pode falhar se o log vier com prefixos ou formatações diferentes no futuro.

**Módulo de Referência:** `sctl/src/utils/utils.ts`

**Recomendação:**
Atualizar `KillParserV2`, `AdminParserV2` e outros para utilizar uma lógica unificada de extração que suporte:
- Inputs puros: `76561198000000000`
- Prefixos Steam: `steam:76561198000000000`
- Prefixos Profile: `profile:123`, `uid:123`
- Validação de comprimento (SteamID64 vs IDs internos).

```python
# Exemplo de melhoria sugerida para utils/parsers.py
import re

LOG_ID_REGEX = re.compile(r"^(?:(?:steam|sid|s|profile|uid|p):)?(\d+)$", re.IGNORECASE)

def extract_user_id(input_str: str) -> str | None:
    match = LOG_ID_REGEX.search(input_str)
    return match.group(1) if match else None
```

## 2. Sistema de Logging Estruturado

O `sctl` possui um `LogManager` (`src/classes/log-manager.ts`) baseado em `winston`, com níveis claros (FATAL, ERROR, WARN, INFO, DEBUG, TRACE) e formatação consistente.
O `sentinel_v2.py` atualmente utiliza muitos `print()` e capturas de exceção genéricas (`except: pass`) ou logs simples.

**Correção Imediata:**
Substituir `print()` por um logger configurado (`logging` do Python) que:
1.  Escreva em arquivos rotacionados (`logs/sentinel.log`).
2.  Mantenha o output no console para Docker.
3.  Padronize o formato: `[TIMESTAMP] [LEVEL] MESSAGE`.

## 3. Tratamento de Erros (Pattern Result)

O `sctl` utiliza a biblioteca `neverthrow` para encapsular sucessos e falhas, evitando o "GoTo" caótico de `try/catch` aninhados.
O Parser do Sentinel (`ingest_file`) tem blocos `try/except` muito longos onde falhas silenciosas podem ocorrer.

**Recomendação:**
 Refatorar o loop principal de ingestão para tratar erros de forma granular:
*   Erro de Conexão SFTP (Retry com backoff).
*   Erro de Parsing de Linha (Logar linha inválida em tabela separada `unparsed_logs` e continuar).
*   Erro de Banco de Dados (Rollback e alertar).

## 4. Hashing Consistente

O `sctl` usa `utf-16le` antes de fazer o hash SHA1 de strings (`hashSteamId64` em `src/utils/utils.ts`).
O Sentinel deve garantir que qualquer operação de hash (para IDs de entidade ou anônimos) siga o mesmo padrão de codificação do jogo (UTF-16LE) para garantir compatibilidade com dados extraídos do jogo.

---

### Ações Executadas
- [x] Análise do código fonte `sctl`.
- [x] Identificação de divergências arquiteturais e melhorias de robustez.
- [x] Implementação de melhorias no parser de texto (IDs e Logs).
- [x] Implementação do novo Logger no Sentinel.
- [x] Refatoração do loop principal (Retry SFTP, Commit Granular).
- [x] Revisão de Hashing Consistente (Nenhum uso de hash identificado no backend atual).

