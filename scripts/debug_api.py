import asyncio
import httpx

async def check():
    async with httpx.AsyncClient() as client:
        # Tenta pegar kills e ver a estrutura do primeiro item
        r = await client.get("http://localhost:8000/v2/logs/kills/?limit=1")
        if r.status_code == 200:
            data = r.json()
            if data:
                print("First Log Item Keys:", data[0].keys())
                print("Location Data:", data[0].get("killer_loc_server"))
                print("Distance Data:", data[0].get("distance"))
            else:
                print("No logs returned.")
        else:
            print("Error:", r.status_code, r.text)

if __name__ == "__main__":
    asyncio.run(check())
