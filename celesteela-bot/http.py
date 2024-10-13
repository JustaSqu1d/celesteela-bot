import aiohttp
import asyncio
import aiofiles
from json import loads, dumps

PVPOKE_DATA_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/refs/heads/master/src/data/gamemaster/pokemon.json"

MOVES_DATA_URL = "https://raw.githubusercontent.com/JustaSqu1d/EternaCalc/refs/heads/master/pokemon/game_data/moves.json"

async def fetch_pvpoke_data() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(PVPOKE_DATA_URL) as response:
            return loads(await response.text())

async def fetch_moves_data() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(MOVES_DATA_URL) as response:
            return loads(await response.text())

async def main():
    pvpoke_data = await fetch_pvpoke_data()
    async with aiofiles.open("gamedata/pokemon.json", "w") as file:
        await file.write(dumps(pvpoke_data, indent=4))

    moves_data = await fetch_moves_data()
    async with aiofiles.open("gamedata/moves.json", "w") as file:
        await file.write(dumps(moves_data, indent=4))


if __name__ == "__main__":
    asyncio.run(main())