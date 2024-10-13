import asyncio
import os.path
from json import loads, dumps

import aiofiles
import aiohttp

PVPOKE_DATA_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/refs/heads/master/src/data/gamemaster/pokemon.json"

MOVES_DATA_URL = "https://raw.githubusercontent.com/JustaSqu1d/EternaCalc/refs/heads/master/pokemon/game_data/moves.json"

filepath = os.path.dirname(__file__)


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
    async with aiofiles.open(filepath + "/gamedata/pokemon.json", "w") as file:
        await file.write(dumps(pvpoke_data, indent=4))

    moves_data = await fetch_moves_data()
    async with aiofiles.open(filepath + "/gamedata/moves.json", "w") as file:
        await file.write(dumps(moves_data, indent=4))


if __name__ == "__main__":
    asyncio.run(main())
