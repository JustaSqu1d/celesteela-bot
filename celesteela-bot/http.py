import aiohttp
import asyncio
from json import loads, dump

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
    with open("gamedata/pokemon.json", "w") as file:
        dump(pvpoke_data, file, indent=4)

    moves_data = await fetch_moves_data()
    with open("gamedata/moves.json", "w") as file:
        dump(moves_data, file, indent=4)


if __name__ == "__main__":
    asyncio.run(main())