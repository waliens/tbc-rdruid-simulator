import itertools
import json
import math
import os
import sys
from argparse import ArgumentParser

from buffs import ALL_STATS_BUFFS, ALL_SPELL_BUFFS
from items import Gear, get_items
from statsmodifiers import StatsModifierArray
from character import DruidCharacter, FULL_DRUID
from excel import write_compare_setups_wb, write_spells_wb
from plot import plot_rotation
from rotation import Rotation, Assignments
from talents import DruidTalents


def main(argv):
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", type=str, dest="config_filepath", required=True)
    parser.add_argument("-g", "--graphs", action="store_true", dest="graphs")
    parser.add_argument("-s", "--spreadsheets", action="store_true", dest="spreadsheets")
    parser.add_argument("-o", "--out_folder", dest="out_folder", default="./generated")
    parser.set_defaults(graphs=False, spreadsheet=False)
    args, _ = parser.parse_known_args(argv)

    os.makedirs(args.out_folder, exist_ok=True)

    with open(args.config_filepath, "r", encoding="utf-8") as file:
        _in = json.load(file)

    all_buffs = []
    for buff in _in["buffs"]:
        all_buffs.append((
            StatsModifierArray([ALL_STATS_BUFFS[b] for b in buff["active"] if b in ALL_STATS_BUFFS], name=buff["name"]),
            StatsModifierArray([ALL_SPELL_BUFFS[b] for b in buff["active"] if b in ALL_SPELL_BUFFS], name=buff["name"])
        ))
    all_talents = [DruidTalents(talent["points"], name=talent["name"]) for talent in _in["talents"]]
    all_assignments = [Assignments.from_dict(rotation) for rotation in _in["rotations"]]

    combinations = list()
    n_comb = len(_in["characters"]) * len(all_buffs) * len(all_talents) * len(all_assignments)
    for i, (charac_info, (stats_buffs, spell_buffs), talents, assignments) in enumerate(itertools.product(_in["characters"], all_buffs, all_talents, all_assignments)):
        print("#{: <3} ({:3.2f}%) char:{} buffs:{} tal:{} assign:{}".format(i + 1, 100 * i / n_comb, charac_info["name"], stats_buffs.name, talents.name, assignments.name))
        character = DruidCharacter(
            stats=charac_info["stats"],
            talents=talents,
            stats_buffs=stats_buffs,
            spell_buffs=spell_buffs,
            gear=Gear(*get_items(charac_info.get("bonuses"))),
            level=charac_info["level"]
        )

        comb_name = "_".join([charac_info["name"], talents.name, stats_buffs.name, assignments.name])
        rotation = Rotation(assignments)
        rotation.optimal_rotation(character, _in["fight_duration"])
        stats = rotation.stats(character, start=0, end=_in["fight_duration"])
        combinations.append((charac_info["name"], charac_info["description"], character, assignments, rotation, stats))

        if args.graphs:
            plot_rotation(
                path=os.path.join(args.out_folder, "{}.png".format(comb_name)),
                rotation=rotation,
                maxx=_in["fight_duration"]
            )

    if args.spreadsheets:
        write_spells_wb(FULL_DRUID, "spells", outfolder=args.out_folder)
        write_compare_setups_wb(combinations, _in["fight_duration"], outfolder=args.out_folder)

    with open(os.path.join(args.out_folder, "output.json"), mode="w+", encoding="utf8") as file:
        json.dump({n: d for n, _, _, _, _, d in combinations}, file)



if __name__ == "__main__":
    main(sys.argv[1:])