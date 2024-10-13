import discord

activity = discord.Activity(
    name="Trainers throw on alignment",
    type=discord.ActivityType.watching
)

intents = discord.Intents.default()
intents.typing = False
bot = discord.Bot(activity=activity, intents=intents)
move_data = None
pokemon_data = None
pokemon_list = []
move_list = []
cp_multipliers = {}

import json
import os
import time
from math import sqrt
import aiofiles
import discord
import dotenv
from fuzzywuzzy import process


# Existing setup code remains unchanged...

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    global move_data, pokemon_data, pokemon_list, move_list, cp_multipliers

    async with aiofiles.open("gamedata/cp_multipliers.json", "r") as file:
        file_string = await file.read()
        cp_multipliers = json.loads(file_string)

    async with aiofiles.open("gamedata/moves.json", "r") as file:
        file_string = await file.read()
        move_data = json.loads(file_string)

    async with aiofiles.open("gamedata/pokemon.json", "r") as file:
        file_string = await file.read()
        pokemon_data = json.loads(file_string)

    new_pokemon_data = []
    start_time = time.time()
    for pokemon in pokemon_data:
        new_pokemon_data.append(add_detailed_info(pokemon))

    end_time = time.time()

    print(f"Processed all Pokémon in {end_time - start_time:.2f} seconds")

    pokemon_data = new_pokemon_data
    # Write the new data to the file
    async with aiofiles.open("gamedata/pokemon_enhanced.json", "w") as file:
        await file.write(json.dumps(pokemon_data, indent=4))

    for pokemon in pokemon_data:
        pokemon_list.append(pokemon["speciesName"])

    for move in move_data:
        move_list.append(move_data[move]["displayName"])

    print("Data loaded")


def calculate_combat_power(base_attack, base_defense, base_hp, level, attack_iv, defense_iv, hp_iv):
    level = str(float(level))

    attack = base_attack + attack_iv
    defense = base_defense + defense_iv
    hp = base_hp + hp_iv
    cp_multiplier = float(cp_multipliers[level])

    combat_power = int(
        attack * sqrt(defense) * sqrt(hp) * cp_multiplier * cp_multiplier / 10
    )

    return combat_power


def calculate_base_stat(base_stat, iv, level):
    level = str(float(level))
    cp_multiplier = float(cp_multipliers[level])
    return (base_stat + iv) * cp_multiplier


def calculate_pokemon_data(base_attack, base_defense, base_hp, level, attack_iv, defense_iv, hp_iv):
    combat_power = calculate_combat_power(base_attack, base_defense, base_hp, level, attack_iv, defense_iv, hp_iv)

    attack_stat = calculate_base_stat(base_attack, attack_iv, level)
    defense_stat = calculate_base_stat(base_defense, defense_iv, level)
    hp_stat = max(calculate_base_stat(base_hp, hp_iv, level), 10)
    stat_product = attack_stat * defense_stat * hp_stat

    return {
        "level": level,
        "attack_iv": attack_iv,
        "defense_iv": defense_iv,
        "hp_iv": hp_iv,
        "combat_power": combat_power,
        "attack_stat": attack_stat,
        "defense_stat": defense_stat,
        "hp_stat": hp_stat,
        "stat_product": stat_product
    }


def add_detailed_info(pokemon_json):
    start_time = time.time()

    base_attack = pokemon_json["baseStats"]["atk"]
    base_defense = pokemon_json["baseStats"]["def"]
    base_hp = pokemon_json["baseStats"]["hp"]

    levels = ["1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0",
              "8.5", "9.0", "9.5", "10.0", "10.5", "11.0", "11.5", "12.0", "12.5", "13.0", "13.5", "14.0", "14.5",
              "15.0", "15.5", "16.0", "16.5", "17.0", "17.5", "18.0", "18.5", "19.0", "19.5", "20.0", "20.5", "21.0",
              "21.5", "22.0", "22.5", "23.0", "23.5", "24.0", "24.5", "25.0", "25.5", "26.0", "26.5", "27.0", "27.5",
              "28.0", "28.5", "29.0", "29.5", "30.0", "30.5", "31.0", "31.5", "32.0", "32.5", "33.0", "33.5", "34.0",
              "34.5", "35.0", "35.5", "36.0", "36.5", "37.0", "37.5", "38.0", "38.5", "39.0", "39.5", "40.0", "40.5",
              "41.0", "41.5", "42.0", "42.5", "43.0", "43.5", "44.0", "44.5", "45.0", "45.5", "46.0", "46.5", "47.0",
              "47.5", "48.0", "48.5", "49.0", "49.5", "50.0", "50.5", "51.0"
              ]

    ivs = range(0, 16)

    pokemon_ranks = []

    can_break = False

    for level in levels:
        for attack_iv in ivs:
            for defense_iv in ivs:
                for hp_iv in ivs:
                    data = calculate_pokemon_data(base_attack, base_defense, base_hp, level, attack_iv, defense_iv,
                                                  hp_iv)
                    if data["combat_power"] > 2500 and attack_iv == 0 and defense_iv == 0 and hp_iv == 0:
                        can_break = True
                        break

                    pokemon_ranks.append(data)

                if can_break:
                    break
            if can_break:
                break
        if can_break:
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
        "lowest_combat_power": {
            "combat_power": 9999,
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
        "lowest_combat_power": {
            "combat_power": 9999,
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
            highest_great_league_data = update_highest_lowest_stats(entry, highest_great_league_data)

        if entry["combat_power"] <= ULTRA_LEAGUE_CP_LIMIT:
            highest_ultra_league_data = update_highest_lowest_stats(entry, highest_ultra_league_data)

    default_great_league_level, default_great_league_attack_iv, default_great_league_defense_iv, default_great_league_hp_iv = \
        pokemon_json["defaultIVs"]["cp1500"]

    default_great_league_data = calculate_pokemon_data(
        base_attack, base_defense, base_hp, default_great_league_level, default_great_league_attack_iv,
        default_great_league_defense_iv, default_great_league_hp_iv
    )

    default_ultra_league_level, default_ultra_league_attack_iv, default_ultra_league_defense_iv, default_ultra_league_hp_iv = \
        pokemon_json["defaultIVs"]["cp2500"]

    default_ultra_league_data = calculate_pokemon_data(
        base_attack, base_defense, base_hp, default_ultra_league_level, default_ultra_league_attack_iv,
        default_ultra_league_defense_iv, default_ultra_league_hp_iv
    )

    highest_great_league_data["default"] = default_great_league_data
    highest_ultra_league_data["default"] = default_ultra_league_data

    pokemon_json["great_league_data"] = highest_great_league_data
    pokemon_json["ultra_league_data"] = highest_ultra_league_data

    end_time = time.time()

    print(f"Processed {pokemon_json['speciesName']} in {end_time - start_time:.2f} seconds")

    return pokemon_json


def update_highest_lowest_stats(entry, highest_data):
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
    if entry["combat_power"] < highest_data["lowest_combat_power"]["combat_power"]:
        highest_data["lowest_combat_power"] = entry
    if entry["attack_stat"] < highest_data["lowest_attack_stat"]["attack_stat"]:
        highest_data["lowest_attack_stat"] = entry
    if entry["defense_stat"] < highest_data["lowest_defense_stat"]["defense_stat"]:
        highest_data["lowest_defense_stat"] = entry
    if entry["hp_stat"] < highest_data["lowest_hp_stat"]["hp_stat"]:
        highest_data["lowest_hp_stat"] = entry

    return highest_data


def similarity_score(search, name):
    search_set = set(search)
    name_set = set(name.lower())
    common_chars = len(search_set.intersection(name_set))
    return common_chars / max(len(search), len(name))


async def pokemon_autocomplete_search(ctx: discord.AutocompleteContext):
    search = ctx.value.lower()
    matches = process.extract(search, pokemon_list, limit=25)
    results = []
    for match in matches:
        results.append(match[0])
    return results


@bot.slash_command(
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    }
)
@discord.option(name="pokemon", description="The Pokémon to search for.", autocomplete=pokemon_autocomplete_search)
async def query(ctx, pokemon: str):
    # find the pokemon in the data

    global pokemon_data

    final_data = None

    for data in pokemon_data:
        if data["speciesName"].lower() == pokemon.lower():
            final_data = data
            break
    else:
        embed = discord.Embed(
            title="Pokemon not found",
            description=f"The Pokémon (`{pokemon}`) does not exist.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed)
        return

    await ctx.respond(str(final_data))


if __name__ == "__main__":
    dotenv.load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    bot.run(BOT_TOKEN)
