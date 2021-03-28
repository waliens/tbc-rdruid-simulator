import itertools
import json
import os
import sys
from argparse import ArgumentParser

from buff import BUFFS, BuffArray
from character import Character
from excel import write_compare_setups_wb, write_spells_wb
from plot import plot_rotation
from rotation import SingleAssignment, Rotation, Assignments
from spell import HEALING_TOUCH, REJUVENATION, REGROWTH, LIFEBLOOM
from talents import Talents


def get_spell_from_assign(assign):
    if assign["spell"] == "healing_touch":
        return HEALING_TOUCH[assign.get("rank", 13) - 1]
    elif assign["spell"] == "rejuvenation":
        return REJUVENATION[assign.get("rank", 13) - 1]
    elif assign["spell"] == "regrowth":
        return REGROWTH[assign.get("rank", 10) - 1]
    elif assign["spell"] == "lifebloom":
        return LIFEBLOOM[assign.get("rank", 1) - 1]
    else:
        raise ValueError("unknown cm_group '{}'".format(assign["spell"]))


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

    all_buffs = [BuffArray([BUFFS[b] for b in buff["active"]], name=buff["name"]) for buff in _in["buffs"]]
    all_talents = [Talents(talent["points"], name=talent["name"]) for talent in _in["talents"]]
    all_assignments = [Assignments(
        [
            SingleAssignment(
                spell=get_spell_from_assign(assign),
                target=assign["target"],
                allow_fade=assign.get("allow_fade", True),
                fade_at_stacks=assign.get("fade_at_stacks", 1)
            ) for assign in rotation["assignments"]
        ],
        name=rotation["name"],
        description=["description"]
    ) for rotation in _in["rotations"]]

    combinations = list()
    for charac_info, buffs, talents, assignments in itertools.product(_in["characters"], all_buffs, all_talents, all_assignments):
        character = Character(
            stats=charac_info["stats"],
            talents=talents,
            buffs=buffs,
            level=charac_info["level"],
            tree_form=charac_info["tree_form"]
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
        write_spells_wb(combinations[0][2], "spells", outfolder=args.out_folder)
        write_compare_setups_wb(combinations, _in["fight_duration"], outfolder=args.out_folder)


if __name__ == "__main__":
    main(sys.argv[1:])