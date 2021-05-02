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


def parse(filename="set.html"):
    with open(filename, "r") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

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
            "name": "{}_{}".format(set_phase.lower().replace(" ", "_"), set_name.lower().replace(" ", "_")),
            "description": "",
            "level": 70,
            "stats": {s: stats[s] for s in ["strength", "agility", "stamina", "intellect", "spirit", "spell_damage", "bonus_healing", "spell_crit_rating", "spell_haste_rating", "mp5"]},
            "bonuses": bonuses,
            "gems": gem_slots
        }

        return json.dumps(descriptor, sort_keys=True, indent=2)


dir = "./html"
for file in os.listdir(dir):
    print(parse(os.path.join(dir, file)))