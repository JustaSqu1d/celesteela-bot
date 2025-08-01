import io
import json
import math
import os
import random
import string
from math import sqrt

import aiofiles
import discord
import dotenv
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rapidfuzz import process, fuzz
from scipy.stats import norm

activity = discord.Activity(
    name="Trainers throw on alignment",
    type=discord.ActivityType.watching
)

intents = discord.Intents.default()
intents.typing = False
bot = discord.Bot(activity=activity, intents=intents)
move_data = {}
pokemon_data = []
pokemon_list = set()
move_list = set()
cp_multipliers = {}
type_chart = {}

dotenv.load_dotenv()
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

levels = ["1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0",
          "8.5", "9.0", "9.5", "10.0", "10.5", "11.0", "11.5", "12.0", "12.5", "13.0", "13.5", "14.0", "14.5",
          "15.0", "15.5", "16.0", "16.5", "17.0", "17.5", "18.0", "18.5", "19.0", "19.5", "20.0", "20.5", "21.0",
          "21.5", "22.0", "22.5", "23.0", "23.5", "24.0", "24.5", "25.0", "25.5", "26.0", "26.5", "27.0", "27.5",
          "28.0", "28.5", "29.0", "29.5", "30.0", "30.5", "31.0", "31.5", "32.0", "32.5", "33.0", "33.5", "34.0",
          "34.5", "35.0", "35.5", "36.0", "36.5", "37.0", "37.5", "38.0", "38.5", "39.0", "39.5", "40.0", "40.5",
          "41.0", "41.5", "42.0", "42.5", "43.0", "43.5", "44.0", "44.5", "45.0", "45.5", "46.0", "46.5", "47.0",
          "47.5", "48.0", "48.5", "49.0", "49.5", "50.0", "50.5", "51.0"
          ]

filepath = os.path.dirname(__file__)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    await load_data()
    print("Data loaded")


async def get_type_emoji(type):
    switcher = {
        "bug": "<:bug:1295144501563756544>",
        "water": "<:water:1295144230335025182>",
        "steel": "<:steel:1295144256046108743>",
        "rock": "<:rock:1295144274043867156>",
        "psychic": "<:psychic:1295144291168944179>",
        "poison": "<:poison:1295144321825378345>",
        "normal": "<:normal:1295144347754299462>",
        "ice": "<:ice:1295144359980961822>",
        "ground": "<:ground:1295144370760060949>",
        "grass": "<:grass:1295144382449586316>",
        "ghost": "<:ghost:1295144395515101216>",
        "flying": "<:flying:1295144408534093864>",
        "fire": "<:fire:1295144424921104414>",
        "fighting": "<:fighting:1295144437856600095>",
        "fairy": "<:fairy:1295144452578480238>",
        "electric": "<:electric:1295144464427520110>",
        "dragon": "<:dragon:1295144476595060778>",
        "dark": "<:dark:1295144488934703134>"
    }

    return switcher.get(type, "")


async def load_data():
    global cp_multipliers, move_data, pokemon_data, type_chart

    async with aiofiles.open(filepath + "/gamedata/cp_multipliers.json", "r") as file:
        file_string = await file.read()
        cp_multipliers = json.loads(file_string)

    async with aiofiles.open(filepath + "/gamedata/moves.json", "r") as file:
        file_string = await file.read()
        move_data = json.loads(file_string)

    async with aiofiles.open(filepath + "/gamedata/pokemon.json", "r") as file:
        file_string = await file.read()
        pokemon_data = json.loads(file_string)

    async with aiofiles.open(filepath + "/gamedata/type_chart.json", "r") as file:
        file_string = await file.read()
        type_chart = json.loads(file_string)

    for pokemon in pokemon_data:
        pokemon_list.add(pokemon["speciesName"])

    for move in move_data:
        move_list.add(move["displayName"])


async def format_move_name(move_name):
    for move in move_data:
        if move["uniqueId"].lower() == move_name.lower():
            type_string = await get_type_emoji(move["type"])
            return f"{type_string} {move['displayName']}"


async def get_type_multiplier(move_type, defender_types):
    multiplier = 1.0
    multiplier_dict = {
        "SUPER_EFFECTIVE": 1.60000002384185791015625, # 32-bit float representation of 1.6
        "NEUTRAL": 1.0,
        "NOT_VERY_EFFECTIVE": 0.625,
        "IMMUNE": 0.390625,
    }

    for defender_type in defender_types:
        effectiveness_string = type_chart.get(move_type).get(defender_type, "NEUTRAL")
        multiplier *= multiplier_dict.get(effectiveness_string, 1.0)

    return multiplier


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


async def get_all_attack_spreads(base_attack: int, base_defense: int, base_hp: int, max_cp: object = 1500) -> list[
    float]:
    ivs = range(0, 16)

    spreads = []

    highest_possible_cp = await calculate_combat_power(base_attack, base_defense, base_hp, "51.0", 15, 15, 15)

    if highest_possible_cp > max_cp:
        for attack_iv in ivs:
            for defense_iv in ivs:
                for hp_iv in ivs:
                    for level in levels:
                        combat_power = await calculate_combat_power(base_attack, base_defense, base_hp, level,
                                                                    attack_iv, defense_iv,
                                                                    hp_iv)
                        if combat_power > max_cp:
                            new_level = float(level) - 0.5

                            calculated_attack = await calculate_base_stat(base_attack, attack_iv, new_level)
                            spreads.append(calculated_attack)
                            break

    else:
        for attack_iv in ivs:
            for level in ["50.0", "50.5", "51.0"]:
                calculated_attack = await calculate_base_stat(base_attack, attack_iv, level)
                spreads.append(calculated_attack)

    return spreads


async def create_pacing_table(pacing_data):
    column_count = len(next(iter(pacing_data.values()))) + 1
    row_count = len(pacing_data) + 1

    cell_width = 450
    cell_height = 100

    image_width = column_count * cell_width
    image_height = row_count * cell_height
    background_color = (34, 34, 34)
    text_color = (255, 255, 255)

    image = Image.new('RGB', (image_width, image_height), background_color)
    draw = ImageDraw.Draw(image)
    font_path = filepath + "/fonts/Lato-Regular.ttf"
    font = ImageFont.truetype(font_path, 50)

    x_offset = cell_width

    for fast_move in next(iter(pacing_data.values())).keys():
        fast_move = await format_move_name(fast_move)
        fast_move = fast_move.split("> ")[1]
        draw.text((x_offset, 20), fast_move, fill=text_color, font=font)
        x_offset += cell_width

    y_offset = cell_height
    for charge_move in pacing_data.keys():
        charge_move = await format_move_name(charge_move)
        charge_move = charge_move.split("> ")[1]
        draw.text((20, y_offset), charge_move, fill=text_color, font=font)
        y_offset += cell_height

    y_offset = cell_height

    for move_type, attacks in pacing_data.items():
        x_offset = cell_width
        for attack, values in attacks.items():
            values = ", ".join(map(str, values))
            if values.startswith("101"):
                values = "∞"
            draw.text((x_offset, y_offset), values, fill=text_color, font=font)
            x_offset += cell_width
        y_offset += cell_height

    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    return image_bytes


class PokemonStats:
    def __init__(self, pokemon_json):
        self._pokemon_json = pokemon_json

    async def great_league_highest_attack_stat(self):
        return self._pokemon_json["great_league_data"]["highest_attack_stat"]["attack_stat"]

    async def great_league_default_attack_stat(self):
        return self._pokemon_json["great_league_data"]["default"]["attack_stat"]

    async def great_league_lowest_attack_stat(self):
        return self._pokemon_json["great_league_data"]["lowest_attack_stat"]["attack_stat"]

    async def great_league_highest_defense_stat(self):
        return self._pokemon_json["great_league_data"]["highest_defense_stat"]["defense_stat"]

    async def great_league_default_defense_stat(self):
        return self._pokemon_json["great_league_data"]["default"]["defense_stat"]

    async def great_league_lowest_defense_stat(self):
        return self._pokemon_json["great_league_data"]["lowest_defense_stat"]["defense_stat"]

    async def great_league_highest_hp_stat(self):
        return self._pokemon_json["great_league_data"]["highest_hp_stat"]["hp_stat"]

    async def great_league_default_hp_stat(self):
        return self._pokemon_json["great_league_data"]["default"]["hp_stat"]

    async def great_league_lowest_hp_stat(self):
        return self._pokemon_json["great_league_data"]["lowest_hp_stat"]["hp_stat"]

    async def ultra_league_highest_attack_stat(self):
        return self._pokemon_json["ultra_league_data"]["highest_attack_stat"]["attack_stat"]

    async def ultra_league_default_attack_stat(self):
        return self._pokemon_json["ultra_league_data"]["default"]["attack_stat"]

    async def ultra_league_lowest_attack_stat(self):
        return self._pokemon_json["ultra_league_data"]["lowest_attack_stat"]["attack_stat"]

    async def ultra_league_highest_defense_stat(self):
        return self._pokemon_json["ultra_league_data"]["highest_defense_stat"]["defense_stat"]

    async def ultra_league_default_defense_stat(self):
        return self._pokemon_json["ultra_league_data"]["default"]["defense_stat"]

    async def ultra_league_lowest_defense_stat(self):
        return self._pokemon_json["ultra_league_data"]["lowest_defense_stat"]["defense_stat"]

    async def ultra_league_highest_hp_stat(self):
        return self._pokemon_json["ultra_league_data"]["highest_hp_stat"]["hp_stat"]

    async def ultra_league_default_hp_stat(self):
        return self._pokemon_json["ultra_league_data"]["default"]["hp_stat"]

    async def ultra_league_lowest_hp_stat(self):
        return self._pokemon_json["ultra_league_data"]["lowest_hp_stat"]["hp_stat"]

    async def master_league_level_50_attack(self):
        return self._pokemon_json["master_league_data"]["level_50"]["attack_stat"]

    async def master_league_level_50_defense(self):
        return self._pokemon_json["master_league_data"]["level_50"]["defense_stat"]

    async def master_league_level_50_hp(self):
        return self._pokemon_json["master_league_data"]["level_50"]["hp_stat"]

    async def master_league_level_51_attack(self):
        return self._pokemon_json["master_league_data"]["level_51"]["attack_stat"]

    async def master_league_level_51_defense(self):
        return self._pokemon_json["master_league_data"]["level_51"]["defense_stat"]

    async def master_league_level_51_hp(self):
        return self._pokemon_json["master_league_data"]["level_51"]["hp_stat"]

    async def great_league_default_combat_power(self):
        return self._pokemon_json["great_league_data"]["default"]["combat_power"]

    async def ultra_league_default_combat_power(self):
        return self._pokemon_json["ultra_league_data"]["default"]["combat_power"]

    async def master_league_level_50_combat_power(self):
        return self._pokemon_json["master_league_data"]["level_50"]["combat_power"]

    async def master_league_level_51_combat_power(self):
        return self._pokemon_json["master_league_data"]["level_51"]["combat_power"]


async def get_pokemon_stat(pokemon_json):
    great_league_data = pokemon_json["great_league_data"]
    ultra_league_data = pokemon_json["ultra_league_data"]
    master_league_data = pokemon_json["master_league_data"]

    if great_league_data["highest_attack_stat"]["attack_stat"] == 0:
        great_league_data["highest_attack_stat"]["attack_stat"], great_league_data["highest_defense_stat"][
            "defense_stat"], great_league_data["highest_hp_stat"]["hp_stat"] = \
            master_league_data["level_51"]["attack_stat"], master_league_data["level_51"]["defense_stat"], \
                master_league_data["level_51"]["hp_stat"]

    if ultra_league_data["highest_attack_stat"]["attack_stat"] == 0:
        ultra_league_data["highest_attack_stat"]["attack_stat"], ultra_league_data["highest_defense_stat"][
            "defense_stat"], ultra_league_data["highest_hp_stat"]["hp_stat"] = \
            master_league_data["level_51"]["attack_stat"], master_league_data["level_51"]["defense_stat"], \
                master_league_data["level_51"]["hp_stat"]

    if great_league_data["lowest_attack_stat"]["attack_stat"] == 9999:
        great_league_data["lowest_attack_stat"]["attack_stat"], great_league_data["lowest_defense_stat"][
            "defense_stat"], great_league_data["lowest_hp_stat"]["hp_stat"] = \
            great_league_data["default"]["attack_stat"], great_league_data["default"]["defense_stat"], \
                great_league_data["default"]["hp_stat"]

    if ultra_league_data["lowest_attack_stat"]["attack_stat"] == 9999:
        ultra_league_data["lowest_attack_stat"]["attack_stat"], ultra_league_data["lowest_defense_stat"][
            "defense_stat"], ultra_league_data["lowest_hp_stat"]["hp_stat"] = \
            ultra_league_data["default"]["attack_stat"], ultra_league_data["default"]["defense_stat"], \
                ultra_league_data["default"]["hp_stat"]

    pokemon_json["great_league_data"], pokemon_json["ultra_league_data"], pokemon_json["master_league_data"] = \
        great_league_data, ultra_league_data, master_league_data

    return PokemonStats(pokemon_json)


async def pokemon_autocomplete_search(ctx: discord.AutocompleteContext):
    search = ctx.value.lower()
    matches = process.extract(search, pokemon_list, scorer=fuzz.WRatio, limit=25)  # type: ignore
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
    global pokemon_data

    for data in pokemon_data:
        if data["speciesName"].lower() == pokemon.lower():
            final_data = data
            break
    else:
        embed = discord.Embed(
            title="Pokémon not found",
            description=f"The Pokémon (`{pokemon}`) does not exist.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed)
        return

    type_string = ""

    for type in final_data["types"]:
        if type != "none":
            type_emoji = await get_type_emoji(type)
            type_string += f"{type_emoji} {type.capitalize()}, "

    type_string = type_string[:-2]

    embed = discord.Embed()

    embed.title = f"#{final_data['dex']} {final_data['speciesName']}"

    embed.description = f"**Type**: {type_string}"

    fast_move_string, charged_move_string = "", ""

    is_smeargle_or_mew = final_data["dex"] == 235 or final_data["dex"] == 151

    if not is_smeargle_or_mew:  # Smeargle and Mew have too many moves

        for move in final_data["fastMoves"]:
            fast_move_string += await format_move_name(move) + "\n"

        fast_move_string = fast_move_string[:-1]

        for move in final_data["chargedMoves"]:
            charged_move_string += await format_move_name(move) + "\n"

        charged_move_string = charged_move_string[:-1]
    else:
        fast_move_string = "Too many moves to display."
        charged_move_string = "Too many moves to display."

    embed.add_field(
        name="Fast Moves",
        value=fast_move_string
    )
    embed.add_field(
        name="Charged Moves",
        value=charged_move_string
    )

    pokemon_stat_data = await get_pokemon_stat(final_data)

    great_default_combat_power = await pokemon_stat_data.great_league_default_combat_power()
    great_default_attack_stat = await pokemon_stat_data.great_league_default_attack_stat()
    great_lowest_attack_stat = await pokemon_stat_data.great_league_lowest_attack_stat()
    great_highest_attack_stat = await pokemon_stat_data.great_league_highest_attack_stat()
    great_default_defense_stat = await pokemon_stat_data.great_league_default_defense_stat()
    great_lowest_defense_stat = await pokemon_stat_data.great_league_lowest_defense_stat()
    great_highest_defense_stat = await pokemon_stat_data.great_league_highest_defense_stat()
    great_default_hp_stat = await pokemon_stat_data.great_league_default_hp_stat()
    great_lowest_hp_stat = await pokemon_stat_data.great_league_lowest_hp_stat()
    great_highest_hp_stat = await pokemon_stat_data.great_league_highest_hp_stat()

    ultra_default_combat_power = await pokemon_stat_data.ultra_league_default_combat_power()
    ultra_default_attack_stat = await pokemon_stat_data.ultra_league_default_attack_stat()
    ultra_lowest_attack_stat = await pokemon_stat_data.ultra_league_lowest_attack_stat()
    ultra_highest_attack_stat = await pokemon_stat_data.ultra_league_highest_attack_stat()
    ultra_default_defense_stat = await pokemon_stat_data.ultra_league_default_defense_stat()
    ultra_lowest_defense_stat = await pokemon_stat_data.ultra_league_lowest_defense_stat()
    ultra_highest_defense_stat = await pokemon_stat_data.ultra_league_highest_defense_stat()
    ultra_default_hp_stat = await pokemon_stat_data.ultra_league_default_hp_stat()
    ultra_lowest_hp_stat = await pokemon_stat_data.ultra_league_lowest_hp_stat()
    ultra_highest_hp_stat = await pokemon_stat_data.ultra_league_highest_hp_stat()

    master_league_level_50_combat_power = await pokemon_stat_data.master_league_level_50_combat_power()
    master_league_level_50_attack_stat = await pokemon_stat_data.master_league_level_50_attack()
    master_league_level_50_defense_stat = await pokemon_stat_data.master_league_level_50_defense()
    master_league_level_50_hp_stat = await pokemon_stat_data.master_league_level_50_hp()

    master_league_level_51_combat_power = await pokemon_stat_data.master_league_level_51_combat_power()
    master_league_level_51_attack_stat = await pokemon_stat_data.master_league_level_51_attack()
    master_league_level_51_defense_stat = await pokemon_stat_data.master_league_level_51_defense()
    master_league_level_51_hp_stat = await pokemon_stat_data.master_league_level_51_hp()

    embed.add_field(
        name="Great League Stats <:pogo_great_league:1295173042443391027>",
        value=f"**CP: {great_default_combat_power}**"
              f"\n**Attack: {great_default_attack_stat:.2f}** ({great_lowest_attack_stat:.2f} - {great_highest_attack_stat:.2f})"
              f"\n**Defense: {great_default_defense_stat:.2f}** ({great_lowest_defense_stat:.2f} - {great_highest_defense_stat:.2f})"
              f"\n**HP: {great_default_hp_stat}** ({great_lowest_hp_stat} - {great_highest_hp_stat})",
        inline=False
    )

    embed.add_field(
        name="Ultra League Stats <:pogo_ultra_league:1295173106662379610>",
        value=f"**CP: {ultra_default_combat_power}**"
              f"\n**Attack: {ultra_default_attack_stat:.2f}** ({ultra_lowest_attack_stat:.2f} - {ultra_highest_attack_stat:.2f})"
              f"\n**Defense: {ultra_default_defense_stat:.2f}** ({ultra_lowest_defense_stat:.2f} - {ultra_highest_defense_stat:.2f})"
              f"\n**HP: {ultra_default_hp_stat}** ({ultra_lowest_hp_stat} - {ultra_highest_hp_stat})",
        inline=False
    )

    embed.add_field(
        name="Master League Stats <:pogo_master_league:1295173143522050080>",
        value=f"**CP: {master_league_level_50_combat_power}** ({master_league_level_51_combat_power} <:best_buddy_ribbon:1299902932111855629>)"
              f"\n**Attack: {master_league_level_50_attack_stat:.2f}** ({master_league_level_51_attack_stat:.2f} <:best_buddy_ribbon:1299902932111855629>)"
              f"\n**Defense: {master_league_level_50_defense_stat:.2f}** ({master_league_level_51_defense_stat:.2f} <:best_buddy_ribbon:1299902932111855629>)"
              f"\n**HP: {master_league_level_50_hp_stat}** ({master_league_level_51_hp_stat} <:best_buddy_ribbon:1299902932111855629>)",
        inline=False
    )

    if not is_smeargle_or_mew:  # Smeargle and Mew have too many moves

        table = await create_pacing_table(final_data["pacing_data"])

        file = discord.File(table, filename="pacing_table.png")

        await ctx.respond(embed=embed, file=file)

    else:
        await ctx.respond(embed=embed)


@bot.slash_command(
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    },
    description="Find the stats of a Pokémon.",
    name="stats"
)
@discord.option(name="name", description="The Pokémon to search for.", autocomplete=pokemon_autocomplete_search)
@discord.option(name="attack_iv", description="The base_attack IV of the Pokémon.",
                type=discord.SlashCommandOptionType.integer, min_value=0, max_value=15)
@discord.option(name="defense_iv", description="The base_defense IV of the Pokémon.",
                type=discord.SlashCommandOptionType.integer, min_value=0, max_value=15)
@discord.option(name="hp_iv", description="The HP IV of the Pokémon.", type=discord.SlashCommandOptionType.integer,
                min_value=0, max_value=15)
async def _stats(ctx, name, attack_iv, defense_iv, hp_iv):
    final_data = None
    for data in pokemon_data:
        if data["speciesName"].lower() == name.lower():
            final_data = data
            break
    else:
        await ctx.respond("Pokémon not found", ephemeral=True)

    type_string = ""

    for type in final_data["types"]:
        if type != "none":
            type_emoji = await get_type_emoji(type)
            type_string += f"{type_emoji} {type.capitalize()}, "

    type_string = type_string[:-2]

    base_attack, base_defense, base_hp = final_data["baseStats"]["atk"], final_data["baseStats"]["def"], \
        final_data["baseStats"]["hp"]

    great_league_level = 1
    ultra_league_level = 1
    for level in levels:
        level_combat_power = await calculate_combat_power(base_attack, base_defense, base_hp, level, attack_iv,
                                                          defense_iv, hp_iv)

        if level_combat_power <= 1500:
            great_league_level = level
        if level_combat_power <= 2500:
            ultra_league_level = level

    great_league_combat_power = await calculate_combat_power(base_attack, base_defense, base_hp, great_league_level,
                                                             attack_iv, defense_iv, hp_iv)
    great_league_attack_stat = await calculate_base_stat(base_attack, attack_iv, great_league_level)
    great_league_defense_stat = await calculate_base_stat(base_defense, defense_iv, great_league_level)
    great_league_hp_stat = max(int(await calculate_base_stat(base_hp, hp_iv, great_league_level)), 10)

    ultra_league_combat_power = await calculate_combat_power(base_attack, base_defense, base_hp, ultra_league_level,
                                                             attack_iv, defense_iv, hp_iv)
    ultra_league_attack_stat = await calculate_base_stat(base_attack, attack_iv, ultra_league_level)
    ultra_league_defense_stat = await calculate_base_stat(base_defense, defense_iv, ultra_league_level)
    ultra_league_hp_stat = max(int(await calculate_base_stat(base_hp, hp_iv, ultra_league_level)), 10)

    master_league_combat_power = await calculate_combat_power(base_attack, base_defense, base_hp, 50, attack_iv,
                                                              defense_iv, hp_iv)
    master_league_attack_stat = await calculate_base_stat(base_attack, attack_iv, 50)
    master_league_defense_stat = await calculate_base_stat(base_defense, defense_iv, 50)
    master_league_hp_stat = max(int(await calculate_base_stat(base_hp, hp_iv, 50)), 10)

    master_league_high_combat_power = await calculate_combat_power(base_attack, base_defense, base_hp, 51, attack_iv,
                                                                   defense_iv, hp_iv)
    master_league_high_attack_stat = await calculate_base_stat(base_attack, attack_iv, 51)
    master_league_high_defense_stat = await calculate_base_stat(base_defense, defense_iv, 51)
    master_league_high_hp_stat = max(int(await calculate_base_stat(base_hp, hp_iv, 51)), 10)

    embed = discord.Embed()

    embed.title = f"#{final_data['dex']} {final_data['speciesName']} ({attack_iv}/{defense_iv}/{hp_iv})"

    embed.description = f"**Type**: {type_string}"

    embed.add_field(
        name="Great League Stats <:pogo_great_league:1295173042443391027>",
        value=f"**CP: {great_league_combat_power}**"
              f"\n**Attack: {great_league_attack_stat:.2f}**"
              f"\n**Defense: {great_league_defense_stat:.2f}**"
              f"\n**HP: {great_league_hp_stat}**",
        inline=False
    )

    embed.add_field(
        name="Ultra League Stats <:pogo_ultra_league:1295173106662379610>",
        value=f"**CP: {ultra_league_combat_power}**"
              f"\n**Attack: {ultra_league_attack_stat:.2f}**"
              f"\n**Defense: {ultra_league_defense_stat:.2f}**"
              f"\n**HP: {ultra_league_hp_stat}**",
        inline=False
    )

    embed.add_field(
        name="Master League Stats <:pogo_master_league:1295173143522050080>",
        value=f"**CP: {master_league_combat_power}** ({master_league_high_combat_power} <:best_buddy_ribbon:1299902932111855629>)"
              f"\n**Attack: {master_league_attack_stat:.2f}** ({master_league_high_attack_stat:.2f} <:best_buddy_ribbon:1299902932111855629>)"
              f"\n**Defense: {master_league_defense_stat:.2f}** ({master_league_high_defense_stat:.2f} <:best_buddy_ribbon:1299902932111855629>)"
              f"\n**HP: {master_league_hp_stat}** ({master_league_high_hp_stat} <:best_buddy_ribbon:1299902932111855629>)",
        inline=False
    )

    await ctx.respond(embed=embed)


@bot.slash_command(
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    },
    description="Get info about a move."
)
@discord.option(name="move", description="The move to search for.",
                autocomplete=discord.utils.basic_autocomplete(move_list))
async def move(ctx, move: str):
    final_data = None
    for data in move_data:
        if data["displayName"].lower() == move.lower():
            final_data = data
            break
    else:
        await ctx.respond("Move not found", ephemeral=True)

    final_data["power"] = int(final_data["power"])

    type_string = await get_type_emoji(final_data["type"])

    fast_or_charge = "Fast" if final_data["turns"] > 0 else "Charge"

    move_string = ""

    if fast_or_charge == "Fast":
        turns = final_data["turns"]
        energy_per_turn = final_data["energyDelta"] / final_data["turns"]
        damage_per_turn = final_data["power"] / final_data["turns"]

        move_string += f"**Turns**: {turns}\n" \
                       f"**Energy per Turn**: {energy_per_turn:.2f}\n" \
                       f"**Damage per Turn**: {damage_per_turn:.2f}\n"
    else:
        damage_per_energy = final_data["power"] / final_data["energyDelta"]
        move_string += f"**Damage per Energy**: {damage_per_energy:.2f}\n"

        if final_data.get("buffs"):
            buff = final_data["buffs"]
            move_string += "\nAdditional Effects:\n"
            if buff.get("buffActivationChance"):
                move_string += f"**Chance**: {(buff['buffActivationChance'] * 100):.2f}%\n"
            if buff.get("attackerDefenseStatStageChange"):
                move_string += f"**User's Defense**: {buff['attackerDefenseStatStageChange']}\n"
            if buff.get("attackerAttackStatStageChange"):
                move_string += f"**User's Attack**: {buff['attackerAttackStatStageChange']}\n"
            if buff.get("targetAttackStatStageChange"):
                move_string += f"**Target's Attack**: {buff['targetAttackStatStageChange']}\n"
            if buff.get("targetDefenseStatStageChange"):
                move_string += f"**Target's Defense**: {buff['targetDefenseStatStageChange']}\n"

    embed = discord.Embed()

    embed.title = f"{final_data['displayName']}"

    embed.description = f"**Type**: {type_string} {final_data['type'].capitalize()}\n**Damage**: {final_data['power']}\n" \
                        f"**Energy**: {final_data['energyDelta']}\n"
    embed.description += move_string

    await ctx.respond(embed=embed)


@bot.slash_command(
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    },
    description="Find the stats of a Pokémon.",
    name="reverse_iv"
)
@discord.option(name="name", description="The Pokémon to search for.", autocomplete=pokemon_autocomplete_search)
@discord.option(name="cp", description="The CP of the Pokémon.", type=discord.SlashCommandOptionType.integer)
@discord.option(name="level", description="The level of the Pokémon.", type=discord.SlashCommandOptionType.number,
                required=False, min_value=1, max_value=51)
@discord.option(name="floor_iv", description="The floor IV of the Pokémon.",
                type=discord.SlashCommandOptionType.integer, required=False, default=0, min_value=0, max_value=15)
@discord.option(name="hp", description="The HP of the Pokémon.", type=discord.SlashCommandOptionType.integer,
                required=False)
async def reverse_iv(ctx, name, cp, level, floor_iv, hp):
    final_data = None
    for data in pokemon_data:
        if data["speciesName"].lower() == name.lower():
            final_data = data
            break
    else:
        await ctx.respond("Pokémon not found", ephemeral=True)

    # round level to nearest 0.5
    if level:
        level = round(level * 2) / 2

    combinations = []

    levels_list = [level] if level else levels

    for attack_iv in range(floor_iv, 16):
        for defense_iv in range(floor_iv, 16):
            for hp_iv in range(floor_iv, 16):
                for level_iter in levels_list:
                    combat_power = await calculate_combat_power(final_data["baseStats"]["atk"],
                                                                final_data["baseStats"]["def"],
                                                                final_data["baseStats"]["hp"], level_iter, attack_iv,
                                                                defense_iv, hp_iv)
                    if combat_power == cp:
                        if hp:
                            hp_stat = await calculate_base_stat(final_data["baseStats"]["hp"], hp_iv, level_iter)
                            hp_stat = max(int(hp_stat), 10)
                            if hp_stat == hp:
                                combinations.append((attack_iv, defense_iv, hp_iv))
                        else:
                            combinations.append((attack_iv, defense_iv, hp_iv))

    solutions = len(combinations)

    embed = discord.Embed()

    embed.title = f"#{final_data['dex']} {final_data['speciesName']} (CP: {cp})"
    embed.description = ""

    if solutions == 0:
        embed.description += "**No results found.**"
    else:
        embed.description += f"**{solutions} solutions found:**\n"
        for attack_iv, defense_iv, hp_iv in combinations:
            embed.description += f"{attack_iv}/{defense_iv}/{hp_iv}\n"

    level_str = f"Level: {level}" if level else "Level: Any"

    hp_str = f"HP: {hp}" if hp else "HP: Any"

    embed.set_footer(text=f"Possible IV Combinations at CP: {cp} | {level_str} | {hp_str} | Floor IV: {floor_iv}")

    await ctx.respond(embed=embed)


@bot.slash_command(
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    },
    description="Attack histogram"
)
@discord.option(name="league", description="The league", choices=["great", "ultra"])
@discord.option(name="name", description="The first Pokémon to graph.", autocomplete=pokemon_autocomplete_search)
@discord.option(name="name2", description="The second Pokémon to graph.", autocomplete=pokemon_autocomplete_search,
                required=False)
@discord.option(name="name3", description="The third Pokémon to graph.", autocomplete=pokemon_autocomplete_search,
                required=False)
async def histogram(ctx, league, name, name2, name3):
    # allow up to 3 separate pokemon to be graphed

    await ctx.defer()

    max_cp_leagues = {
        "great": 1500,
        "ultra": 2500,
        "master": float("inf")
    }

    max_cp = max_cp_leagues.get(league)

    pokemon_count = 1
    if name2:
        pokemon_count += 1
    if name3:
        pokemon_count += 1

    if not name2:
        name2 = ""

    if not name3:
        name3 = ""

    final_data = []
    for data in pokemon_data:
        if data["speciesName"].lower() == name.lower() or data["speciesName"].lower() == name2.lower() or \
                data["speciesName"].lower() == name3.lower():
            final_data.append(data)

    if len(final_data) != pokemon_count:
        await ctx.respond("One or more Pokémon not found", ephemeral=True)
        return

    attack_spreads_dict = {}

    for data in final_data:
        base_attack, base_defense, base_hp = data["baseStats"]["atk"], data["baseStats"]["def"], data["baseStats"]["hp"]
        attack_spreads_dict[data["speciesName"]] = {}
        attack_spreads_dict[data["speciesName"]]["attack_spreads"] = await get_all_attack_spreads(base_attack,
                                                                                                  base_defense, base_hp,
                                                                                                  max_cp)
        attack_spreads_dict[data["speciesName"]]["default_spreads"] = data[f"{league}_league_data"]["default"][
            "attack_stat"]
        attack_spreads_dict[data["speciesName"]]["species_name"] = data["speciesName"]

    # create a histogram using matplotlib
    data_stream = io.BytesIO()

    curves = []

    for pokemon_spread in attack_spreads_dict.values():
        attack_spreads = pokemon_spread["attack_spreads"]
        species_name = pokemon_spread["species_name"]

        bins = []
        max_attack = max(attack_spreads)
        min_attack = min(attack_spreads)
        for i in range(int(min_attack), int(max_attack) + 1):
            bins.append(i + 0.05)

        counts, bins = np.histogram(attack_spreads, bins=bins)

        curves.append(plt.stairs(counts, bins, fill=True, alpha=0.35, label=species_name))

        mean_attack = np.mean(attack_spreads)
        std_attack = np.std(attack_spreads)
        x_values = np.linspace(min_attack, max_attack, 1000)
        bell_curve = norm.pdf(x_values, mean_attack, std_attack)

        bell_curve = bell_curve * max(counts) / max(bell_curve)

        plt.plot(x_values, bell_curve, color="red", linewidth=2)

        default_attack = pokemon_spread["default_spreads"]

        # add a line for default ivs
        plt.axvline(default_attack, color="black", linestyle="--")
        plt.text(default_attack - 0.75, max(counts) * 0.4, f"{species_name} Default ({default_attack:.2f})",
                 color="black",
                 rotation=90)

    plt.title(f"Attack Stat Distribution ({league.capitalize()} League)")
    plt.legend(handles=curves)

    plt.xlabel("Attack Stat")

    plt.ylabel("Frequency")

    plt.savefig(data_stream, format='png', bbox_inches="tight", dpi=120, pad_inches=0.2)

    plt.clf()

    data_stream.seek(0)

    file = discord.File(data_stream, filename="histogram.png")

    await ctx.respond(file=file)


async def calculate_damage(attack_stat, defense_stat, attacker, defender):
    damage_dict = {}

    is_attacker_shadow = "shadow" in attacker.get("tags", [])
    is_defender_shadow = "shadow" in defender.get("tags", [])

    for move in attacker["chargedMoves"] + attacker["fastMoves"]:
        for data in move_data:
            if data["uniqueId"].lower() == move.lower():
                current_move = data
                move_name = data["displayName"]
                break
        else:
            continue

        power = current_move["power"]
        stab = 1.2000000476837158203125 if current_move["type"] in attacker["types"] else 1
        effectiveness = await get_type_multiplier(current_move["type"], defender["types"])

        trainer_constant = 1.2999999523162841796875 # 32-bit float representation of 1.3
        shadow_attack_constant = 1.2000000476837158203125 # 32-bit float representation of 1.2
        shadow_defense_constant = 0.833333313465118408203125 # 32-bit float representation of 0.8333333

        actual_attack_stat = attack_stat * shadow_attack_constant if is_attacker_shadow else attack_stat
        actual_defense_stat = defense_stat * shadow_defense_constant if is_defender_shadow else defense_stat

        damage = int(
            0.5 * power * (actual_attack_stat / actual_defense_stat) * stab * effectiveness * trainer_constant) + 1
        damage_dict[move_name] = damage

    return damage_dict


def get_pokemon_by_name(name: str):
    for data in pokemon_data:
        if data["speciesName"].lower() == name.lower():
            return data
    return None


async def determine_league_level(base_stats, league_data, max_cp: int):
    level = 1
    for lvl in levels:
        cp = await calculate_combat_power(
            base_stats["atk"],
            base_stats["def"],
            base_stats["hp"],
            lvl,
            league_data["attack_stat"],
            league_data["defense_stat"],
            league_data["hp_stat"]
        )
        if cp <= max_cp:
            level = lvl
    return level


async def compute_attack_stat(pokemon: dict, league: str):
    base_stats = pokemon["baseStats"]
    if league == "master":
        # For master league, IV is fixed at 15 and level is fixed at 50.
        return await calculate_base_stat(base_stats["atk"], 15, 50)
    else:
        # For ultra and great leagues, get the league-specific data and determine level.
        league_data = pokemon[f"{league}_league_data"]["default"]
        max_cp = 2500 if league == "ultra" else 1500
        level = await determine_league_level(base_stats, league_data, max_cp)
        return await calculate_base_stat(base_stats["atk"], league_data["attack_stat"], level)


async def compute_defense_stats(pokemon: dict, league: str):
    base_stats = pokemon["baseStats"]
    if league == "master":
        level = 50
        iv = 15
        defense = await calculate_base_stat(base_stats["def"], iv, level)
        # Ensure a minimum HP of 10.
        hp = max(int(await calculate_base_stat(base_stats["hp"], iv, level)), 10)
    else:
        league_data = pokemon[f"{league}_league_data"]["default"]
        max_cp = 2500 if league == "ultra" else 1500
        level = await determine_league_level(base_stats, league_data, max_cp)
        defense = await calculate_base_stat(base_stats["def"], league_data["defense_stat"], level)
        hp = int(await calculate_base_stat(base_stats["hp"], league_data["hp_stat"], level))
    return defense, hp


@bot.slash_command(
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    },
    description="Damage calculator"
)
@discord.option(name="league", choices=["great", "ultra", "master"])
@discord.option(name="attacker", description="The attacker's Pokémon.", autocomplete=pokemon_autocomplete_search)
@discord.option(name="defender", description="The defender's Pokémon.", autocomplete=pokemon_autocomplete_search)
async def damage(ctx, league, attacker, defender):
    attacker_data = get_pokemon_by_name(attacker)
    if not attacker_data:
        await ctx.respond("Attacking Pokémon not found", ephemeral=True)
        return

    defender_data = get_pokemon_by_name(defender)
    if not defender_data:
        await ctx.respond("Defending Pokémon not found", ephemeral=True)
        return

    attack_stat = await compute_attack_stat(attacker_data, league)
    defense_stat, hp_stat = await compute_defense_stats(defender_data, league)

    damages = await calculate_damage(attack_stat, defense_stat, attacker_data, defender_data)
    damages = {move: dmg for move, dmg in sorted(damages.items(), key=lambda item: item[1], reverse=True)}

    embed = discord.Embed(
        title=f"{attacker_data['speciesName']} vs {defender_data['speciesName']} ({league.capitalize()} League)"
    )

    description_lines = []
    for move, dmg in damages.items():
        hits_to_ko = math.ceil(hp_stat / dmg)
        hits_display = "O" if hits_to_ko == 1 else hits_to_ko

        percentage_string = f"{(dmg / hp_stat) * 100:.2f}%"

        description_lines.append(f"**{move}**: {dmg} damage | {percentage_string} | {hits_display}HKO")

    embed.description = "\n".join(description_lines)
    await ctx.respond(embed=embed)


@bot.slash_command(
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    }
)
async def sableye(ctx):
    # 12 random letters is the code

    code = ''.join(random.choices(string.ascii_letters, k=12))
    code = code.upper()

    embed = discord.Embed(
        title="Sableye Drop!",
        description=f"Claim your free Sableye!\nCode: {code}",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://i.imgur.com/ug1evlY.png")
    embed.set_footer(text="!sableye (Parody)")

    await ctx.respond(embed=embed)


@bot.slash_command(
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    }
)
async def ping(ctx):
    latency = int(bot.latency * 1000)

    embed = discord.Embed(
        title="Pong!",
        description=f"{latency} ms",
        color=discord.Color.from_rgb(r=31, g=82, b=82)
    )

    await ctx.respond(embed=embed)


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
