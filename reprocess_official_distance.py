import asyncio
import os
import glob
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import engine
from app.models.kill_v2 import SentinelKill
from app.services.parsers_v2.kill import KillParserV2

LOG_DIR = "../logs-exemple"

async def reprocess_official_distance():
    print("🔄 Iniciando reprocessamento para obter Distância Oficial dos logs locais...")
    
    # Encontrar todos os logs de kill
    log_files = glob.glob(os.path.join(LOG_DIR, "kill_*.log"))
    if not log_files:
        # Tenta subdiretório new também
        log_files.extend(glob.glob(os.path.join(LOG_DIR, "new", "kill_*.log")))
    
    print(f"📂 Arquivos encontrados: {len(log_files)}")
    
    async with AsyncSession(engine) as session:
        updates_count = 0
        
        for file_path in log_files:
            print(f"📄 Processando: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.readlines()
                    
                for line in content:
                    # Parse using the UPDATED logic (which captures official distance)
                    parsed_kill = KillParserV2.parse(line)
                    
                    if parsed_kill and parsed_kill.distance > 0:
                        # Se temos um kill parseado COM distância oficial, vamos atualizar o banco
                        # Precisamos encontrar o registro correspondente
                        
                        # Busca por Timestamp exato e Killer ID
                        statement = select(SentinelKill).where(
                            SentinelKill.timestamp == parsed_kill.timestamp,
                            SentinelKill.killer_id == parsed_kill.killer_id,
                            SentinelKill.victim_id == parsed_kill.victim_id
                        )
                        result = await session.exec(statement)
                        existing_kill = result.first()
                        
                        if existing_kill:
                            # Se a distância atual for diferente da oficial (provavelmente é a calculada)
                            # Atualizamos
                            diff = abs(existing_kill.distance - parsed_kill.distance)
                            if diff > 0.01: # Tolerância pequena
                                print(f"   ✏️ Atualizando ID {existing_kill.id}: {existing_kill.distance:.2f}m -> {parsed_kill.distance:.2f}m (Oficial)")
                                existing_kill.distance = parsed_kill.distance
                                
                                # Se o ViolationScore estiver zerado no banco mas a gente pode recalcular com mais precisão
                                if parsed_kill.violation_score > 0 and existing_kill.violation_score == 0:
                                     existing_kill.violation_score = parsed_kill.violation_score
                                
                                session.add(existing_kill)
                                updates_count += 1
                                
            except Exception as e:
                print(f"❌ Erro ao ler {file_path}: {e}")
        
        await session.commit()
        print(f"✅ Reprocessamento concluído!")
        print(f"📊 Registros atualizados para a distância oficial: {updates_count}")

if __name__ == "__main__":
    asyncio.run(reprocess_official_distance())
