import asyncio
import os.path
import time
from json import loads, dumps
from math import sqrt

import aiofiles
import aiohttp

PVPOKE_DATA_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/refs/heads/master/src/data/gamemaster/pokemon.json"

MOVES_DATA_URL = "https://raw.githubusercontent.com/alexelgt/game_masters/refs/heads/master/GAME_MASTER.json"

levels = ["1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0",
          "8.5", "9.0", "9.5", "10.0", "10.5", "11.0", "11.5", "12.0", "12.5", "13.0", "13.5", "14.0", "14.5",
          "15.0", "15.5", "16.0", "16.5", "17.0", "17.5", "18.0", "18.5", "19.0", "19.5", "20.0", "20.5", "21.0",
          "21.5", "22.0", "22.5", "23.0", "23.5", "24.0", "24.5", "25.0", "25.5", "26.0", "26.5", "27.0", "27.5",
          "28.0", "28.5", "29.0", "29.5", "30.0", "30.5", "31.0", "31.5", "32.0", "32.5", "33.0", "33.5", "34.0",
          "34.5", "35.0", "35.5", "36.0", "36.5", "37.0", "37.5", "38.0", "38.5", "39.0", "39.5", "40.0", "40.5",
          "41.0", "41.5", "42.0", "42.5", "43.0", "43.5", "44.0", "44.5", "45.0", "45.5", "46.0", "46.5", "47.0",
          "47.5", "48.0", "48.5", "49.0", "49.5", "50.0", "50.5", "51.0"
          ]

cp_multipliers = {
    "1.0": "0.0939999967813491",
    "1.5": "0.135137430784308",
    "2.0": "0.166397869586944",
    "2.5": "0.192650914456886",
    "3.0": "0.215732470154762",
    "3.5": "0.236572655026622",
    "4.0": "0.255720049142837",
    "4.5": "0.273530381100769",
    "5.0": "0.29024988412857",
    "5.5": "0.306057381335773",
    "6.0": "0.321087598800659",
    "6.5": "0.335445032295077",
    "7.0": "0.349212676286697",
    "7.5": "0.36245774877879",
    "8.0": "0.375235587358474",
    "8.5": "0.387592411085168",
    "9.0": "0.399567276239395",
    "9.5": "0.41119354951725",
    "10.0": "0.422500014305114",
    "10.5": "0.432926413410414",
    "11.0": "0.443107545375824",
    "11.5": "0.453059953871985",
    "12.0": "0.46279838681221",
    "12.5": "0.472336077786704",
    "13.0": "0.481684952974319",
    "13.5": "0.490855810259008",
    "14.0": "0.499858438968658",
    "14.5": "0.508701756943992",
    "15.0": "0.517393946647644",
    "15.5": "0.525942508771329",
    "16.0": "0.534354329109191",
    "16.5": "0.542635762230353",
    "17.0": "0.550792694091796",
    "17.5": "0.558830599438087",
    "18.0": "0.566754519939422",
    "18.5": "0.574569148039264",
    "19.0": "0.582278907299041",
    "19.5": "0.589887911977272",
    "20.0": "0.59740000963211",
    "20.5": "0.604823657502073",
    "21.0": "0.61215728521347",
    "21.5": "0.61940411056605",
    "22.0": "0.626567125320434",
    "22.5": "0.633649181622743",
    "23.0": "0.640652954578399",
    "23.5": "0.647580963301656",
    "24.0": "0.654435634613037",
    "24.5": "0.661219263506722",
    "25.0": "0.667934000492096",
    "25.5": "0.674581899290818",
    "26.0": "0.681164920330047",
    "26.5": "0.687684905887771",
    "27.0": "0.694143652915954",
    "27.5": "0.700542893277978",
    "28.0": "0.706884205341339",
    "28.5": "0.713169102333341",
    "29.0": "0.719399094581604",
    "29.5": "0.725575616972598",
    "30.0": "0.731700003147125",
    "30.5": "0.734741011137376",
    "31.0": "0.737769484519958",
    "31.5": "0.740785574597326",
    "32.0": "0.743789434432983",
    "32.5": "0.746781208702482",
    "33.0": "0.749761044979095",
    "33.5": "0.752729105305821",
    "34.0": "0.75568550825119",
    "34.5": "0.758630366519684",
    "35.0": "0.761563837528228",
    "35.5": "0.764486065255226",
    "36.0": "0.767397165298461",
    "36.5": "0.77029727397159",
    "37.0": "0.77318650484085",
    "37.5": "0.776064945942412",
    "38.0": "0.778932750225067",
    "38.5": "0.781790064808426",
    "39.0": "0.784636974334716",
    "39.5": "0.787473583646825",
    "40.0": "0.790300011634826",
    "40.5": "0.792803950958807",
    "41.0": "0.795300006866455",
    "41.5": "0.79780392148697",
    "42.0": "0.800300002098083",
    "42.5": "0.802803892322847",
    "43.0": "0.805299997329711",
    "43.5": "0.807803863460723",
    "44.0": "0.81029999256134",
    "44.5": "0.812803834895026",
    "45.0": "0.815299987792968",
    "45.5": "0.817803806620319",
    "46.0": "0.820299983024597",
    "46.5": "0.822803778631297",
    "47.0": "0.825299978256225",
    "47.5": "0.827803750922782",
    "48.0": "0.830299973487854",
    "48.5": "0.832803753381377",
    "49.0": "0.835300028324127",
    "49.5": "0.837803755931569",
    "50.0": "0.840300023555755",
    "50.5": "0.842803729034748",
    "51.0": "0.845300018787384",
    "51.5": "0.847803702398935",
    "52.0": "0.850300014019012",
    "52.5": "0.852803676019539",
    "53.0": "0.85530000925064",
    "53.5": "0.857803649892077",
    "54.0": "0.860300004482269",
    "54.5": "0.862803624012168",
    "55.0": "0.865299999713897"
}

filepath = os.path.dirname(__file__)


async def fetch_pvpoke_data() -> list:
    response = None
    async with aiohttp.ClientSession() as session:
        async with session.get(PVPOKE_DATA_URL) as response:
            response = await response.text()
            response = loads(response)

    response = [pokemon for pokemon in response if
                pokemon["speciesId"] != "clodsiresb"]  # remove Clodsire (Sludge Bomb)

    return response


async def fetch_moves_data() -> list:
    response = None
    async with aiohttp.ClientSession() as session:
        async with session.get(MOVES_DATA_URL) as response:
            response = await response.text()
            response = loads(response)

    if response is None:
        raise ValueError("Failed to fetch moves data")

    moves = []

    for entry in response:
        template_id = entry.get("templateId")
        if template_id.startswith("COMBAT_V"):
            move_data = await process_move_data(template_id, entry)
            moves.append(move_data)

    # handle hidden power variants
    hidden_power = next((move for move in moves if move["uniqueId"] == "HIDDEN_POWER"), None)

    # remove the original hidden power move
    if hidden_power is not None:
        moves.remove(hidden_power)

    uuid = 600
    hidden_power_types = ["bug", "dark", "dragon", "electric", "fighting", "fire", "flying", "ghost", "grass",
                          "ground", "ice", "poison", "psychic", "rock", "steel", "water"]

    for pokemon_type in hidden_power_types:
        new_move = hidden_power.copy()
        new_move["uniqueId"] = f"HIDDEN_POWER_{pokemon_type.upper()}"
        new_move["type"] = pokemon_type
        new_move["displayName"] = f"Hidden Power [{pokemon_type.title()}]"
        new_move["uuid"] = uuid
        uuid += 1
        moves.append(new_move)

    return moves


async def process_move_data(template_id: str, entry: dict) -> dict:
    assert entry.get("data") is not None

    move_data = entry.get("data").get("combatMove", {})

    move_data.pop("vfxName", None)

    move_name = move_data.get("uniqueId", "")

    move_data["energyDelta"] = abs(move_data.get("energyDelta", 0))
    move_data["power"] = abs(move_data.get("power", 0))

    move_data["turns"] = abs(move_data.get("durationTurns", 0))

    move_data["type"] = move_data.get("type", "POKEMON_TYPE_NORMAL").lower()[13:]

    move_uuid = int(template_id.split("_")[1][1:])
    move_data["uuid"] = move_uuid

    move_id = (move_data["uniqueId"]
               .replace("_FAST", "")
               .replace("FUTURESIGHT", "FUTURE_SIGHT")
               .replace("TECHNO_BLAST_WATER", "TECHNO_BLAST_DOUSE")
               )
    move_data["uniqueId"] = move_id

    move_display_name = move_data.get("uniqueId").replace("_", " ").replace("FAST", "").title()
    move_display_name = (move_display_name
                         .replace(" Blastoise", "")
                         .replace("Wrap Green", "Wrap")
                         .replace("Wrap Pink", "Wrap")
                         .replace("X Scissor", "X-Scissor")
                         .replace("Super Power", "Superpower")
                         .replace("V Create", "V-create")
                         .replace("Lock On", "Lock-On")
                         .replace("Aeroblast Plus", "Aeroblast+")
                         .replace("Aeroblast Plus Plus", "Aeroblast++")
                         .replace("Scared Fire Plus", "Sacred Fire+")
                         .replace("Scared Fire Plus Plus", "Sacred Fire++")
                         .replace("Mud Slap", "Mud-Slap")
                         .replace("Futuresight", "Future Sight")
                         .replace("Natures Madness", "Nature's Madness")
                         .replace("Weather Ball Normal", "Weather Ball [Normal]")
                         .replace("Weather Ball Fire", "Weather Ball [Fire]")
                         .replace("Weather Ball Water", "Weather Ball [Water]")
                         .replace("Weather Ball Ice", "Weather Ball [Ice]")
                         .replace("Weather Ball Rock", "Weather Ball [Rock]")
                         .replace("Techno Blast Normal", "Techno Blast")
                         .replace("Techno Blast Burn", "Techno Blast")
                         .replace("Techno Blast Chill", "Techno Blast")
                         .replace("Techno Blast Douse", "Techno Blast")
                         .replace("Techno Blast Shock", "Techno Blast")
                         .replace("Roar Of Time", "Roar of Time")
                         ).strip()

    move_data["displayName"] = move_display_name

    move_data.pop("durationTurns", None)

    if move_name.endswith("_FAST"):
        move_data["usageType"] = "fast"
        move_data["turns"] += 1
        move_data["uniqueId"] = move_name[:-5]
    else:
        move_data["usageType"] = "charge"

    return move_data


async def populate_pokemon_info(pokemon_data: list, moves_data) -> list:
    tasks = []
    temp_pokemon_data = pokemon_data

    start_time = time.time()
    print("Processing Pokémon data...")
    for pokemon in temp_pokemon_data:
        tasks.append(add_detailed_info(pokemon, moves_data))

    new_pokemon_data = await asyncio.gather(*tasks)

    pokemon_data = new_pokemon_data
    end_time = time.time()
    print(f"Processed all Pokémon in {end_time - start_time:.2f} seconds")

    return pokemon_data


async def update_highest_lowest_stats(entry, highest_data):
    # Update highest stats
    if entry["attack_stat"] > highest_data["highest_attack_stat"]["attack_stat"]:
        highest_data["highest_attack_stat"] = entry
    if entry["defense_stat"] > highest_data["highest_defense_stat"]["defense_stat"]:
        highest_data["highest_defense_stat"] = entry
    if entry["hp_stat"] > highest_data["highest_hp_stat"]["hp_stat"]:
        highest_data["highest_hp_stat"] = entry
    if entry["stat_product"] > highest_data["highest_stat_product"]["stat_product"]:
        highest_data["highest_stat_product"] = entry

    # Update lowest stats
    if entry["attack_stat"] < highest_data["lowest_attack_stat"]["attack_stat"]:
        highest_data["lowest_attack_stat"] = entry
    if entry["defense_stat"] < highest_data["lowest_defense_stat"]["defense_stat"]:
        highest_data["lowest_defense_stat"] = entry
    if entry["hp_stat"] < highest_data["lowest_hp_stat"]["hp_stat"]:
        highest_data["lowest_hp_stat"] = entry

    return highest_data


async def calculate_base_stat(base_stat, iv, level):
    level = str(float(level))
    cp_multiplier = float(cp_multipliers[level])
    return (base_stat + iv) * cp_multiplier


async def calculate_pokemon_data(base_attack, base_defense, base_hp, level, attack_iv, defense_iv, hp_iv):
    combat_power = await calculate_combat_power(base_attack, base_defense, base_hp, level, attack_iv, defense_iv, hp_iv)

    attack_stat = await calculate_base_stat(base_attack, attack_iv, level)
    defense_stat = await calculate_base_stat(base_defense, defense_iv, level)
    hp_stat = int(max(await calculate_base_stat(base_hp, hp_iv, level), 10))
    stat_product = attack_stat * defense_stat * hp_stat

    return {
        "level": float(level),
        "attack_iv": attack_iv,
        "defense_iv": defense_iv,
        "hp_iv": hp_iv,
        "combat_power": combat_power,
        "attack_stat": attack_stat,
        "defense_stat": defense_stat,
        "hp_stat": hp_stat,
        "stat_product": stat_product
    }


async def calculate_combat_power(base_attack, base_defense, base_hp, level, attack_iv, defense_iv, hp_iv):
    level = str(float(level))

    attack = base_attack + attack_iv
    defense = base_defense + defense_iv
    hp = base_hp + hp_iv
    cp_multiplier = float(cp_multipliers[level])

    combat_power = int(
        attack * sqrt(defense) * sqrt(hp) * cp_multiplier * cp_multiplier / 10
    )

    return combat_power


async def add_detailed_info(pokemon_json, moves_data) -> dict:
    base_attack = pokemon_json["baseStats"]["atk"]
    base_defense = pokemon_json["baseStats"]["def"]
    base_hp = pokemon_json["baseStats"]["hp"]

    ivs = range(0, 16)

    pokemon_ranks = []

    master_league_data_level_50 = await calculate_pokemon_data(base_attack, base_defense, base_hp, "50.0", 15, 15, 15)
    master_league_data_level_51 = await calculate_pokemon_data(base_attack, base_defense, base_hp, "51.0", 15, 15, 15)

    pokemon_json["master_league_data"] = {
        "level_50": master_league_data_level_50,
        "level_51": master_league_data_level_51
    }

    for attack_iv in ivs:
        for defense_iv in ivs:
            for hp_iv in ivs:
                is_great_league_done = False
                is_ultra_league_done = False
                for level in levels:
                    combat_power = await calculate_combat_power(base_attack, base_defense, base_hp, level, attack_iv,
                                                                defense_iv,
                                                                hp_iv)
                    if combat_power > 1500 and not is_great_league_done:
                        is_great_league_done = True

                        data = await calculate_pokemon_data(base_attack, base_defense, base_hp, str(float(level) - 0.5),
                                                            attack_iv, defense_iv,
                                                            hp_iv)
                        pokemon_ranks.append(data)

                    if combat_power > 2500 and not is_ultra_league_done:
                        is_ultra_league_done = True

                        data = await calculate_pokemon_data(base_attack, base_defense, base_hp, str(float(level) - 0.5),
                                                            attack_iv, defense_iv,
                                                            hp_iv)
                        pokemon_ranks.append(data)

                    if is_great_league_done and is_ultra_league_done:
                        break

    # check if it is under or equal to 1500 combat power
    GREAT_LEAGUE_CP_LIMIT = 1500
    highest_great_league_data = {
        "highest_attack_stat": {
            "attack_stat": 0,
        },
        "highest_defense_stat": {
            "defense_stat": 0,
        },
        "highest_hp_stat": {
            "hp_stat": 0,
        },
        "highest_stat_product": {
            "stat_product": 0,
        },
        "lowest_attack_stat": {
            "attack_stat": 9999,
        },
        "lowest_defense_stat": {
            "defense_stat": 9999,
        },
        "lowest_hp_stat": {
            "hp_stat": 9999,
        }
    }
    ULTRA_LEAGUE_CP_LIMIT = 2500
    highest_ultra_league_data = {
        "highest_attack_stat": {
            "attack_stat": 0,
        },
        "highest_defense_stat": {
            "defense_stat": 0,
        },
        "highest_hp_stat": {
            "hp_stat": 0,
        },
        "highest_stat_product": {
            "stat_product": 0,
        },
        "lowest_attack_stat": {
            "attack_stat": 9999,
        },
        "lowest_defense_stat": {
            "defense_stat": 9999,
        },
        "lowest_hp_stat": {
            "hp_stat": 9999,
        }
    }

    for entry in pokemon_ranks:
        if entry["combat_power"] <= GREAT_LEAGUE_CP_LIMIT:
            highest_great_league_data = await update_highest_lowest_stats(entry, highest_great_league_data)

        if GREAT_LEAGUE_CP_LIMIT < entry["combat_power"] <= ULTRA_LEAGUE_CP_LIMIT:
            highest_ultra_league_data = await update_highest_lowest_stats(entry, highest_ultra_league_data)

    default_great_league_level, default_great_league_attack_iv, default_great_league_defense_iv, default_great_league_hp_iv = \
        pokemon_json["defaultIVs"]["cp1500"]

    default_great_league_data = await calculate_pokemon_data(
        base_attack, base_defense, base_hp, default_great_league_level, default_great_league_attack_iv,
        default_great_league_defense_iv, default_great_league_hp_iv
    )

    default_ultra_league_level, default_ultra_league_attack_iv, default_ultra_league_defense_iv, default_ultra_league_hp_iv = \
        pokemon_json["defaultIVs"]["cp2500"]

    default_ultra_league_data = await calculate_pokemon_data(
        base_attack, base_defense, base_hp, default_ultra_league_level, default_ultra_league_attack_iv,
        default_ultra_league_defense_iv, default_ultra_league_hp_iv
    )

    highest_great_league_data["default"] = default_great_league_data
    highest_ultra_league_data["default"] = default_ultra_league_data

    pokemon_json["great_league_data"] = highest_great_league_data
    pokemon_json["ultra_league_data"] = highest_ultra_league_data

    pacing_data = {}

    for fast_move in pokemon_json["fastMoves"]:
        for move in moves_data:
            if move["uniqueId"] == fast_move:
                fast_move_data = move
                break
        else:
            raise ValueError(f"Fast move {fast_move} not found in move data")

        pacing_data[fast_move_data["uniqueId"]] = {}

        for charge_move in pokemon_json["chargedMoves"]:
            for move in moves_data:
                if move["uniqueId"] == charge_move:
                    charge_move_data = move
                    break
            else:
                raise ValueError(f"Charge move {charge_move} not found in move data")

            # how many fast moves are needed to charge the charge move
            fast_move_energy = fast_move_data["energyDelta"]
            charge_move_energy = charge_move_data["energyDelta"]

            pacing = []

            energy = 0
            turns = 0
            while len(pacing) < 5:
                energy += fast_move_energy
                turns += 1
                if energy >= charge_move_energy or turns > 100:
                    pacing.append(turns)
                    energy -= charge_move_energy
                    turns = 0

            pacing_data[fast_move_data["uniqueId"]][charge_move_data["uniqueId"]] = pacing

    pokemon_json["pacing_data"] = pacing_data

    return pokemon_json


async def main():
    pvpoke_data = await fetch_pvpoke_data()
    moves_data = await fetch_moves_data()

    pvpoke_data = await populate_pokemon_info(pvpoke_data, moves_data)

    async with aiofiles.open(filepath + "/gamedata/pokemon.json", "w") as file:
        await file.write(dumps(pvpoke_data, indent=4))

    async with aiofiles.open(filepath + "/gamedata/moves.json", "w") as file:
        await file.write(dumps(moves_data, indent=4))


if __name__ == "__main__":
    asyncio.run(main())
