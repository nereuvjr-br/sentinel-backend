import asyncio
import math
from sqlmodel import Session, select
from app.core.database import engine
from app.models.kill_v2 import SentinelKill

def calculate_distance_3d(loc1, loc2):
    if not loc1 or not loc2:
        return 0.0
    
    # Normaliza chaves (X/x, Y/y, Z/z)
    x1 = loc1.get('X') or loc1.get('x') or 0.0
    y1 = loc1.get('Y') or loc1.get('y') or 0.0
    z1 = loc1.get('Z') or loc1.get('z') or 0.0
    
    x2 = loc2.get('X') or loc2.get('x') or 0.0
    y2 = loc2.get('Y') or loc2.get('y') or 0.0
    z2 = loc2.get('Z') or loc2.get('z') or 0.0
    
    dx = x1 - x2
    dy = y1 - y2
    dz = z1 - z2
    
    # Retorna em Metros (SCUM usa CM)
    return math.sqrt(dx*dx + dy*dy + dz*dz) / 100.0

from sqlmodel.ext.asyncio.session import AsyncSession

async def fix_data():
    print("🔄 Iniciando correção de dados (Distância e Violation Score)...")
    
    async with AsyncSession(engine) as session:
        statement = select(SentinelKill)
        result = await session.exec(statement)
        results = result.all()
        
        count = 0
        fixed_dist = 0
        fixed_violation = 0
        
        for kill in results:
            changed = False
            
            # 1. Corrigir Distância (Killer vs Victim)
            if (kill.distance == 0 or kill.distance is None) and kill.killer_loc_server and kill.victim_loc:
                dist = calculate_distance_3d(kill.killer_loc_server, kill.victim_loc)
                if dist > 0:
                    kill.distance = dist
                    fixed_dist += 1
                    changed = True
            
            # 2. Corrigir Violation Score (Killer Server vs Killer Client)
            if (kill.violation_score == 0 or kill.violation_score is None) and kill.killer_loc_server and kill.killer_loc_client:
                violation = calculate_distance_3d(kill.killer_loc_server, kill.killer_loc_client)
                if violation > 0:
                    kill.violation_score = violation
                    fixed_violation += 1
                    changed = True
            
            if changed:
                session.add(kill)
                count += 1
        
        await session.commit()
        print(f"✅ Concluído!")
        print(f"📊 Registros atualizados: {count}")
        print(f"📏 Distâncias corrigidas: {fixed_dist}")
        print(f"🛡️ Scores de violação calculados: {fixed_violation}")

if __name__ == "__main__":
    asyncio.run(fix_data())
