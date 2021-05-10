import os

from bs4 import BeautifulSoup
import json
import re


ITEM_BONUSES = {
    27886: "idol_of_the_emerald_queen",
    22398: "idol_of_rejuvenation",
    25643: "harolds_rejuvenating_broach",
    28355: "gladiators_idol_of_tenacity",
    33076: "merciless_gladiators_idol_of_tenacity",
    33841: "vengeful_gladiators_idol_of_tenacity",
    35021: "brutal_gladiators_idol_of_tenacity",
    32387: "idol_of_the_raven_goddess",
    28568: "idol_of_the_avian_heart",
    19288: "darkmoon_card_blue_dragon",
    30841: "lower_city_prayer_book",
    32496: "memento_of_tyrande",
    34430: "glimmering_naaru_sliver",
    33508: "idol_of_budding_life",
    30051: "idol_of_the_crescent_goddess"
}

ITEM_SETS = {
    "t2_stormrage_raiment": {16903, 16898, 16904, 16897, 16900, 16899, 16901, 16902},
    "t3_dreamwalker_raiment": {22492, 22494, 22493, 22490, 22489, 22491, 22488, 22495, 23064},
    "t4_malorne_raiment": {29087, 29086, 29090, 29088, 29089},
    "t5_nordrassil_raiment": {30216, 30217, 30219, 30220, 30221},
    "t6_thunderheart_raiment": {31041, 31032, 31037, 31045, 31047, 34571, 34445, 34554},
    "primal_mooncloth": {21875, 21874, 21873},
    "whitemend": {24264, 24261}
}

ITEM_SETS_BONUSES = {
    "t2_stormrage_raiment": [5, 8],
    "t3_dreamwalker_raiment": [4, 8],
    "t4_malorne_raiment": [2, 4],
    "t5_nordrassil_raiment": [2, 4],
    "t6_thunderheart_raiment": [2, 4],
    "primal_mooncloth": [3],
    "whitemend": [2]
}


def get_bonuses(equipped):
    bonuses = list()
    for _id in equipped:
        if _id in ITEM_BONUSES:
            bonuses.append(ITEM_BONUSES[_id])

    for set_name, ids in ITEM_SETS.items():
        inter = ids.intersection(equipped)
        if len(inter) > 0:
            for bonus_count in ITEM_SETS_BONUSES[set_name]:
                if bonus_count <= len(inter):
                    bonuses.append(set_name + "_{}p".format(bonus_count))

    return bonuses


def normalize_stat_name(n):
    return {
       "mana_per_5_sec.": "mp5",
       "healing": "bonus_healing",
       "healingDamage": "spell_damage",
       "spellHasteRating": "spell_haste_rating"
    }.get(n, n)


def normalize_stat_value(v):
    if isinstance(v, str) and "%" in v:
        return float(v[:-1]) / 100
    else:
        return int(v)


def parse(filename="set.html", url=""):
    with open(filename, "r") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

        player_name = soup.find("title").text.split("-")[1].strip()
        stats = dict()
        tag = soup.select("div[class*=\"set-stats_setStats\"]")[0]
        sections = tag.find_all("section")
        for section in sections:
            header = section.select("div[class*=\"stat-section_sectionHeader\"]")[0].find("h3")
            if header.text == "Equivalency Points":
                continue
            stat_values = section.select("div[class*=\"stat-value_statValue__\"]")
            for value in stat_values:
                key = normalize_stat_name(re.sub(r"\s+", "_", value.find("label").text).lower())
                value = normalize_stat_value(value.find("span").text)
                stats[key] = value

        # look for gems and remove their effect
        # parse equipped items
        equipped = set()
        gem_slots = []
        counted_gems = set()
        gem_color_counts = dict()
        gem_requirements = []
        sources = soup.select("div[class*=\"source-category_category__\"]")
        for source in sources:
            rows = source.select("div[class*=\"item-table-row_row__\"]")
            for row in rows:
                outers = row.select("div[class*=\"item-table-row_cellContent__\"]")
                if len(outers) == 0:
                    continue
                links = [item for outer in outers for item in outer.select("a[class*=\"item-cell_itemCell__\"]")]
                if len(links) == 0:
                    continue
                data_tip = json.loads(links[0].attrs["data-tip"])
                if data_tip["type"] == "gem" and data_tip["id"] not in counted_gems:
                    counted_gems.add(int(data_tip["id"]))
                    gem_color_counts[data_tip["gemColor"]] = data_tip.get("equippedCount", 1)
                    if data_tip["gemRequirements"] is not None:
                        gem_requirements.append({
                            "requirement": (data_tip["gemRequirements"][0]["name"], data_tip["gemRequirements"][0]["value"]),
                            "stats": data_tip["stats"]
                        })
                    for stat in data_tip["stats"]:
                        stats[normalize_stat_name(stat["name"])] -= data_tip.get("equippedCount", 1) * stat["value"]
                elif data_tip["type"] == "armor" or data_tip["type"] == "weapon":
                    equipped.add(int(data_tip["id"]))

                    if data_tip["socketOrder"] is None:
                        continue

                    socket_bonus = data_tip.get("socketBonus", list())
                    if socket_bonus is None:
                        socket_bonus = list()
                    gem_slots.append({
                        "name": data_tip["name"].lower().replace(" ", "_").replace("-", "_"),
                        "slots": data_tip["socketOrder"],
                        "bonus": [{"stat": normalize_stat_name(bonus["name"]), "value": normalize_stat_value(bonus["value"])} for bonus in socket_bonus]
                    })

        bonuses = get_bonuses(equipped)

        for requirement in gem_requirements:
            by_color = requirement["requirement"]
            if gem_color_counts.get(by_color[0], 0) <= gem_color_counts.get(by_color[1], 0):
                for stat in requirement["stats"]:
                    stats[normalize_stat_name(stat["name"])] += stat["value"]

        if "whitemend_2p" in set(bonuses):
            stats["bonus_healing"] -= 0.1 * stats["intellect"]
            stats["bonus_healing"] = round(stats["bonus_healing"])

        set_name = soup.select("span[class*=\"set-card_setName\"]")[0].text
        set_phase = soup.select("span[class*=\"set-card_phase\"]")[0].text

        descriptor = {
            "name": "{}_{}_{}".format(set_phase.lower().replace(" ", "_"), player_name.lower(), set_name.lower().replace(" ", "_")),
            "description": url,
            "level": 70,
            "stats": {s: stats[s] for s in ["strength", "agility", "stamina", "intellect", "spirit", "spell_damage", "bonus_healing", "spell_crit_rating", "spell_haste_rating", "mp5"]},
            "bonuses": bonuses,
            "gems": gem_slots
        }

        return json.dumps(descriptor, sort_keys=True, indent=2)


dir = "./html"

l = [
    # ("https://seventyupgrades.com/set/mPnHLS3HsALjwr1ZeSgxmh", "3p T4 Ench - Manarius - Seventy Upgrades (04_05_2021 01_41_17).html"),
    # ("https://seventyupgrades.com/set/vJbNVaHuoFumufZzb7kYEZ", "2p T4 3p Windhawk - Manarius - Seventy Upgrades (04_05_2021 01_41_19).html"),
    # ("https://seventyupgrades.com/set/ef7CYKysXRE4qTUfaA9J9Z", "2p T4 3p PMC - Manarius - Seventy Upgrades (04_05_2021 01_41_20).html"),
    # ("https://seventyupgrades.com/set/4JBauw3SowxcgzsdPx5Tdi", "2p T4 2p Whitemend - Manarius - Seventy Upgrades (04_05_2021 01_41_22).html"),
    # ("https://seventyupgrades.com/set/vV1zuctLqKHKGnC8FJynDX", "2p T4 Tailor 1p PMC 2p WM LW 2p WH - Manarius - Seventy Upgrades (04_05_2021 01_41_24).html"),
    # ("https://seventyupgrades.com/set/9ijrYdV8DAdqQ1xfMfZ8Hh", "3p PMC 2p Whitemend - Manarius - Seventy Upgrades (04_05_2021 01_41_25).html"),
    # ("https://seventyupgrades.com/set/fzhK4g2D75taA4KSNuDnse", "8p T3 Classic - Manarius - Seventy Upgrades (04_05_2021 01_49_40).html"),
    # ("https://seventyupgrades.com/set/bCE5WYPxnLjb7fKdJhvQHy", "8p T2 classic - Manarius - Seventy Upgrades (04_05_2021 01_50_10).html"),
    # ("https://seventyupgrades.com/set/o3z4p853mW1x61QU2FxhPV", "T4 Tailor - Druid - Seventy Upgrades (04_05_2021 01_41_30).html"),
    # ("https://seventyupgrades.com/set/ubPGejqfkakv4TaJajaYa2", "T4 LW - Druid - Seventy Upgrades (04_05_2021 01_41_32).html"),
    # ("https://seventyupgrades.com/set/fCAB7ThwoutabqBUKBC38E", "T4 No Craft - Druid - Seventy Upgrades (04_05_2021 01_41_34).html"),
    # ("https://seventyupgrades.com/set/iQdupV181SV59tA5JWn2MY", "T4 PMC - Druid - Seventy Upgrades (04_05_2021 01_41_36).html"),
    # ("https://seventyupgrades.com/set/iXkwdz184rwRXPxXH3BaDf", "T4 LW_Tailor - Druid - Seventy Upgrades (04_05_2021 01_41_38).html"),
    # ("https://seventyupgrades.com/set/s487BqHyjE3ReAaEAyXTiC", "T4 LW - Druid - Seventy Upgrades (04_05_2021 01_41_32).html"),
    # ("https://seventyupgrades.com/set/ubPGejqfkakv4TaJajaYa2", "T4_LW - Druid - Seventy Upgrades (04_05_2021 01_41_40).html"),
    # ("https://seventyupgrades.com/set/4BwWqU8xMUwFjwB2kFB4MY", "T5 Tailor - Druid - Seventy Upgrades (04_05_2021 02_05_17).html"),
    # ("https://seventyupgrades.com/set/eN4DP3v6oLJWrJ3yXjcvAN", "T5 - Druid - Seventy Upgrades (04_05_2021 02_05_20).html"),
    # ("https://seventyupgrades.com/set/a8E5fLPk6pUWaYFn3cmfdB", "T5 PMC - Druid - Seventy Upgrades (04_05_2021 18_12_32).html"),
    # ("https://seventyupgrades.com/set/dcbPo56tk7MxnU5LRuwpK4", "Ph5 HT Memes - Eliza - Seventy Upgrades (04_05_2021 02_09_25).html"),
    # ("https://seventyupgrades.com/set/diCncVKKJyZuGhpVpnaweZ", "2p T5 w_ Chest Tailor 2p WM Alch - Manarius - Seventy Upgrades (07_05_2021 14_44_47).html"),
    # ("https://seventyupgrades.com/set/pNSvru2zheLv6CJgpT5GHg", "2p T5 w_ Gloves Tailor 2p WM Alch - Manarius - Seventy Upgrades (07_05_2021 14_44_57).html"),
    # ("https://seventyupgrades.com/set/5hzS8dY9AvvdVfPiLM3bTD", "Full Tailor Alch - Manarius - Seventy Upgrades (07_05_2021 14_44_54).html"),
    # ("https://seventyupgrades.com/set/63DfBdGNmokxXkaHLrSUo", "Full Tailor Ench - Manarius - Seventy Upgrades (07_05_2021 14_44_55).html"),
    # ("https://seventyupgrades.com/set/peqadEif8J7MY1kABQcAAq", "T5 Alch Ench - Manarius - Seventy Upgrades (07_05_2021 14_44_46).html"),
    # ("https://seventyupgrades.com/set/uyuMBCQZytMWkmMeWe1P92", "T5 Ench LW - Manarius - Seventy Upgrades (07_05_2021 14_44_54).html"),
    ("https://seventyupgrades.com/set/3nHX95D9xW8EoCshi12LPk", "Tailor WM Alch - Manarius - Seventy Upgrades (09_05_2021 02_09_21).html")
]

for url, name in l:
    print(parse(os.path.join(dir, name), url=url))