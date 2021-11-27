import itertools
import json
import os
import sys
from argparse import ArgumentParser

from joblib import Parallel, delayed

from buffs import ALL_STATS_BUFFS, ALL_SPELL_BUFFS
from gems import GemSlotsCollection, ItemGemSlots, optimize_slots
from items import Gear, get_items, ALL_ON_USE_ITEMS
from statsmodifiers import StatsModifierArray, ConstantStatsModifier, StatsModifier
from character import DruidCharacter, FULL_DRUID
from excel import write_compare_setups_wb, write_spells_wb
from plot import plot_rotation
from rotation import Rotation, Assignments, make_on_use_timelines
from talents import DruidTalents


def parse_gems_slots(gems_data):
    return GemSlotsCollection([
        ItemGemSlots(
            name=slots_data["name"],
            slots=slots_data["slots"],
            bonus=ConstantStatsModifier(name="{}_gem_bonus".format(slots_data["name"]),
                                        _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(bonus["stat"], bonus["value"]) for bonus in slots_data["bonus"]]))
        for slots_data in gems_data
    ])


def sim_loop(i, n_comb, charac_info, buffs, talents, assignments, gems_policy, fight_duration, plot_graphs, out_folder, plot_gems):
    stats_buffs, spell_buffs = buffs
    gems_policy_str = "_".join(map(str, gems_policy.values()))
    print("#{: <3} ({:3.2f}%) char:{} buffs:{} tal:{} assign:{} gems:{}".format(i + 1, 100 * i / n_comb,
                                                                                charac_info["name"], stats_buffs.name,
                                                                                talents.name, assignments.name,
                                                                                gems_policy_str))
    gem_slots = optimize_slots(
        slots=parse_gems_slots(charac_info["gems"]),
        strategy=gems_policy["policy"],
        heroic=gems_policy["heroic"],
        jewelcrafting=gems_policy["jewelcrafting"]
    )
    if plot_gems:
        for item_slots in gem_slots.slots:
            print(", ".join(["{}:{}".format(c, g.name) for c, g in zip(item_slots.colors, item_slots.gems)]))
    character = DruidCharacter(
        stats=charac_info["stats"],
        talents=talents,
        stats_buffs=stats_buffs,
        spell_buffs=spell_buffs,
        gear=Gear(*get_items(charac_info.get("bonuses")), gem_slots),
        level=charac_info["level"]
    )
    comb_name = "_".join([charac_info["name"], talents.name, stats_buffs.name, assignments.name, gems_policy_str])
    rotation = Rotation(assignments)
    rotation.optimal_rotation(character, fight_duration)
    on_use_timelines = make_on_use_timelines(fight_duration,
                                             [ALL_ON_USE_ITEMS[k] for k in charac_info.get("on_use", [])],
                                             rotation.cast_timeline)
    stats = rotation.stats(character, start=0, end=fight_duration, on_use=on_use_timelines)
    if plot_graphs:
        plot_rotation(
            path=os.path.join(out_folder, "{}.png".format(comb_name)),
            rotation=rotation,
            maxx=fight_duration,
            on_use=on_use_timelines
        )
    return charac_info["name"], charac_info["description"], character, assignments, rotation, stats, gems_policy


def main(argv):
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", type=str, dest="config_filepath", required=True)
    parser.add_argument("-g", "--graphs", action="store_true", dest="graphs")
    parser.add_argument("-s", "--spreadsheets", action="store_true", dest="spreadsheets")
    parser.add_argument("-o", "--out_folder", dest="out_folder", default="./generated")
    parser.add_argument("-j", "--n_jobs", dest="n_jobs", default=1, type=int)
    parser.add_argument("--gems", dest="gems", action="store_true")
    parser.set_defaults(graphs=False, spreadsheet=False, gems=False)
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

    n_comb = len(_in["characters"]) * len(all_buffs) * len(all_talents) * len(all_assignments) * len(_in["gems_policy"])

    combinations = Parallel(n_jobs=args.n_jobs)(
        delayed(sim_loop)(i, n_comb, charac_info, buffs, talents, assignments, gems_policy, _in["fight_duration"], args.graphs, args.out_folder, args.gems)
        for i, (charac_info, buffs, talents, assignments, gems_policy)
        in enumerate(itertools.product(_in["characters"], all_buffs, all_talents, all_assignments, _in["gems_policy"])))

    if args.spreadsheets:
        write_spells_wb(FULL_DRUID, "spells", outfolder=args.out_folder)
        write_compare_setups_wb(combinations, _in["fight_duration"], outfolder=args.out_folder)

    with open(os.path.join(args.out_folder, "output.json"), mode="w+", encoding="utf8") as file:
        json.dump([{"character": c_name, "description": c_info, "stats": stats, "gems": gems,
                    "spec": char.talents.name, "assignments": assignments.name}
                   for c_name, c_info, char, assignments, _, stats, gems in combinations], file)




if __name__ == "__main__":
    main(sys.argv[1:])