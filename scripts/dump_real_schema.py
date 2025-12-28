import asyncio
from sqlalchemy import text, inspect
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
# Silence SQL engine logs to see clean output
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

async def dump_schema():
    print("🔍 Analisando Schema REAL do Banco de Dados...")
    
    # We need a synchronous engine for reflection usually, or run sync code in executor
    # SQLAlchemy AsyncEngine supports run_sync
    
    async with engine.connect() as conn:
        def get_schema(connection):
            inspector = inspect(connection)
            table_names = inspector.get_table_names()
            schema_info = {}
            for table in table_names:
                columns = inspector.get_columns(table)
                schema_info[table] = [
                    f"{col['name']} ({str(col['type'])})" 
                    for col in columns
                ]
            return schema_info

        schema = await conn.run_sync(get_schema)
        
        # Sort tables alphabetically
        tables_sorted = sorted(schema.keys())
        
        # Generate Markdown
        md_content = "# Schema REAL do Banco de Dados (Gerado Automaticamente)\n\n"
        md_content += f"Gerado em: {asyncio.get_event_loop().time()}\n\n"
        
        for table in tables_sorted:
            if not table.startswith("sentinel_"): continue # Filter only our tables
            
            md_content += f"### `{table}`\n"
            for col in schema[table]:
                md_content += f"- {col}\n"
            md_content += "\n"
            
        print(md_content)
        
        # Save to file
        with open("REAL_DB_SCHEMA.md", "w", encoding="utf-8") as f:
            f.write(md_content)
            print("\n✅ Salvo em 'REAL_DB_SCHEMA.md'")

if __name__ == "__main__":
    asyncio.run(dump_schema())
