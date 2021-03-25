import itertools
import json
import os
import sys
from argparse import ArgumentParser

from buff import BUFFS, BuffArray
from character import Character
from excel import write_compare_setups_wb, write_spells_wb
from plot import plot_rotation
from rotation import Assignment, Rotation
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

    characters = [
        (
            character["name"],
            character["description"],
            Character(
                primary=character["stats"]["primary"],
                secondary=character["stats"]["secondary"],
                talents=Talents(character["talents"]),
                buffs=BuffArray([BUFFS[b] for b in character["buffs"]]),
                level=character["level"],
                tree_form=character["tree_form"]
            )
        ) for character in _in["characters"]
    ]

    rotations = [
        (
            rotation["name"],
            rotation["description"],
            [Assignment(spell=get_spell_from_assign(assign),
                        target=assign["target"],
                        allow_fade=assign.get("allow_fade", True),
                        fade_at_stacks=assign.get("fade_at_stacks", 1))
             for assign in rotation["assignments"]]
        )
        for rotation in _in["rotations"]
    ]

    combinations = list()
    for (c_name, c_description, character), (r_name, r_description, assigments) in itertools.product(characters, rotations):
        rotation = Rotation(assigments)
        rotation.optimal_rotation(character, _in["fight_duration"])
        stats = rotation.stats(character, start=0, end=_in["fight_duration"])
        combinations.append((c_name, character, c_description, r_name, assigments, r_description, stats))

        if args.graphs:
            plot_rotation(
                path=os.path.join(args.out_folder, "{}_{}.png".format(c_name, r_name)),
                rotation=rotation,
                maxx=_in["fight_duration"]
            )

    if args.spreadsheets:
        write_spells_wb(combinations[0][1], "rdruid", outfolder=args.out_folder)
        write_compare_setups_wb(combinations, outfolder=args.out_folder)


if __name__ == "__main__":
    main(sys.argv[1:])