import json
from argparse import ArgumentParser
from collections import defaultdict


def main(argv):
    parser = ArgumentParser()
    parser.add_argument("-f", "--filepath", type=str, dest="filepath", required=True)
    args, _ = parser.parse_known_args(argv)

    with open(args.filepath, "r", encoding="utf8") as file:
        data = json.load(file)

    rotations = defaultdict(list)

    for comb in data:
        phase = None
        character = comb["character"]
        if "phase" in character:
            phase = character[:7]
            character = character[8:]

        descr_tuple = (phase, character, comb["spec"], "_".join([str(s) for s in comb["gems"].values()]))
        rotations[comb["assignments"]].append((comb["stats"]["hps"], descr_tuple))

    for name, all_descr in sorted(rotations.items(), key=lambda v: v[0]):
        if len(all_descr) == 0:
            continue
        tsize = len(all_descr[0][1])
        values = [set() for _ in range(tsize)]
        for hps, desc in all_descr:
            for i, v in enumerate(desc):
                values[i].add(v)

        print("----------")
        print(name)
        print()
        to_display_index = [i for i, s in enumerate(values) if len(s) > 1]

        best = None
        for hps, descr in sorted(all_descr, key=lambda v: -v[0]):
            if best is None:
                best = hps
                print("{:.1f}".format(best).rjust(8), end=" ")
            else:
                print("{:.1f}".format(hps - best).rjust(8), end=" ")

            for i in to_display_index:
                print(descr[i], end=" ")

            print()

        print()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])