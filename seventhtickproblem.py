from argparse import ArgumentParser

import numpy as np
from joblib import Parallel, delayed
from matplotlib import pyplot as plt

from character import DruidCharacter
from rotation import Timeline
from spell import LIFEBLOOM
from statistics import Stats
from statsmodifiers import StatsModifierArray
from talents import DruidTalents

DEFAULT_TALENTS = {
  "name": "deep_resto",
  "points": {
    "naturalist": 0,
    "gift_of_nature": 5,
    "tranquil_spirit": 5,
    "improved_rejuvenation": 3,
    "empowered_rejuvenation": 5,
    "living_spirit": 3,
    "empowered_touch": 0,
    "improved_regrowth": 5,
    "intensity": 3,
    "tree_of_life": 1
  }
}


def simulate_haste(rating, total_duration):
    talents = DruidTalents(DEFAULT_TALENTS["points"], DEFAULT_TALENTS["name"])
    no_buff = StatsModifierArray([])
    char = DruidCharacter({Stats.SPELL_HASTE_RATING: rating}, talents, no_buff, no_buff)
    lb_timeline = Timeline("lifebloom")
    lifebloom = LIFEBLOOM[0]
    gcd = char.get_stat(Stats.GCD)
    gcd_per_lb = int(lifebloom.duration(char) / gcd)
    t = 0
    while t < total_duration:
        # cast a lifebloom on one target
        lb_timeline.add_spell_event(t, lifebloom)
        # full spellqueuing avoiding bloom
        t += gcd * gcd_per_lb

    max_ticks_possible = int(total_duration)
    number_lifeblooms = len(lb_timeline)

    stats = lb_timeline.stats(char, 0, total_duration)
    nb_ticks = len(stats["heals"])
    return rating, gcd_per_lb - 4, 100 * nb_ticks / max_ticks_possible, nb_ticks / number_lifeblooms


def main(argv):
    parser = ArgumentParser()
    parser.add_argument("-s", "--start_rating", dest="start_rating", type=int, default=0)
    parser.add_argument("-e", "--end_rating", dest="end_rating", type=int, default=600)
    parser.add_argument("-d", "--sim_duration", dest="sim_duration", type=int, default=600)
    parser.add_argument("-j", "--n_jobs", dest="n_jobs", default=1, type=int)
    args, _ = parser.parse_known_args(argv)

    if args.start_rating >= args.end_rating + 1:
        print("empty range of haste rating")

    results = Parallel(n_jobs=args.n_jobs)(delayed(simulate_haste)(haste_rating, args.sim_duration)
                                           for haste_rating in range(args.start_rating, args.end_rating + 1))

    ratings, gcds_per_lb, heal_eff, mana_eff = zip(*results)

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex="all")
    ax1.plot(ratings, heal_eff)
    ax2.plot(ratings, mana_eff)
    ax1.set_title("healing and mana efficiency vs haste rating when spell queuing")
    ax2.set_xlabel('haste rating')
    ax1.set_ylabel('hps efficiency (%)')
    ax2.set_ylabel('nb ticks per lb')
    ax2.hlines([6], np.min(ratings), np.max(ratings), colors=['r'], alpha=0.5)

    for ax in [ax1, ax2]:
        ax.set_xlim(np.min(ratings), np.max(ratings))
        ax.pcolorfast(ax.get_xlim(), ax.get_ylim(), 2 - np.array(gcds_per_lb)[np.newaxis], cmap='RdYlGn', alpha=0.3)
        ax.grid()

    prev, prev_haste = heal_eff[0], ratings[0]
    for i, h in enumerate(heal_eff[1:]):
        if h < prev:
            print(prev_haste, prev)
        prev_haste = ratings[i+1]
        prev = h

    plt.show()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])