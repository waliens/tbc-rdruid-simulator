import itertools
import json
import os
import sys
from argparse import ArgumentParser

from buffs import ALL_BUFFS, TARGET_BUFFS
from statsmodifiers import StatsModifierArray
from character import Character, DruidCharacter, BuffedCharacter
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

    all_buffs = [StatsModifierArray([ALL_BUFFS[b] for b in buff["active"]], name=buff["name"]) for buff in _in["buffs"]]
    all_talents = [DruidTalents(talent["points"], name=talent["name"]) for talent in _in["talents"]]
    all_assignments = [Assignments.from_dict(rotation) for rotation in _in["rotations"]]

    combinations = list()
    for charac_info, buffs, talents, assignments in itertools.product(_in["characters"], all_buffs, all_talents, all_assignments):
        character = DruidCharacter(
            stats=charac_info["stats"],
            talents=talents,
            buffs=buffs,
            level=charac_info["level"]
        )

        comb_name = "_".join([charac_info["name"], talents.name, buffs.name, assignments.name])
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
        base_char = combinations[0][2]
        character = DruidCharacter(_in["characters"][0]["stats"], base_char.talents, StatsModifierArray(ALL_BUFFS.values()))
        write_spells_wb(character, "spells", outfolder=args.out_folder)
        write_compare_setups_wb(combinations, _in["fight_duration"], outfolder=args.out_folder)


if __name__ == "__main__":
    main(sys.argv[1:])