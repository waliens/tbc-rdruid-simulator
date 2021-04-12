from pprint import pprint

from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox

import matplotlib.image as mpimg
from matplotlib import pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

from rotation import SpellEvent, Rotation, SingleAssignment
from spell import Regrowth, Rejuvenation, HealingTouch, Lifebloom, HealingSpell

HT_COLOR = "#4B7494"
LB_COLOR = "#31642C"
RG_COLOR = "#5ACD1A"
RJ_COLOR = "#B01ADB"
GCD_COLOR = "#BDBEFF"
CAST_COLOR = "#FFFD97"


def plot_timeline(timeline, y, maxx, color, height=2., eps=0.03):
    for i, event in enumerate(timeline):
        if event.start > maxx:
            break
        plt.axhspan(y - height / 2, y + height / 2,
                    xmin=event.start/maxx, xmax=min(event.end, maxx)/maxx,
                    facecolor=color, alpha=0.8, edgecolor="k")

        if isinstance(event, SpellEvent):
            dec_height = (1 - eps) * height

            spell = event.spell
            if spell.type == HealingSpell.TYPE_HOT or spell.type == HealingSpell.TYPE_HYBRID:
                period = spell.base_tick_period
                n_tick = round(event.duration / spell.base_tick_period)
                x = np.linspace(event.start + period, event.start + n_tick * period, n_tick)
                plt.vlines(x, y - dec_height / 2, y + dec_height / 2, color="w", linewidth=2, alpha=0.5)

            if isinstance(event.spell, HealingTouch):
                path = 'images/spell_nature_healingtouch.png'
            elif isinstance(event.spell, Rejuvenation):
                path = 'images/spell_nature_rejuvenation.png'
            elif isinstance(event.spell, Regrowth):
                path = 'images/spell_nature_regrowth.png'
            else:
                path = 'images/spell_nature_lifebloom.png'
            spell_img = mpimg.imread(path)
            img_extent = (event.start + eps, event.start + dec_height, y - dec_height / 2, y + dec_height / 2)
            plt.imshow(spell_img, extent=img_extent, aspect="equal", zorder=2)

            if event.spell.base_max_stacks > 1:
                plt.text(event.start + eps, y - dec_height / 2 + eps, str(event.stacks),
                         fontfamily="serif", color="w", fontsize="large", fontweight="bold")


def plot_rotation(path, rotation, maxx, height=0.5):
    duration = rotation.end
    n_assigments = len(rotation.timelines)
    n_timelines = 2 + n_assigments
    plt.figure(figsize=(duration / 2, n_timelines / 2))
    plt.xlim(rotation.start, maxx)
    plt.ylim(-height + height / 2, (n_timelines - 0.5) * height)

    plt.gca().tick_params(axis='x', which='minor')
    plt.gca().xaxis.set_major_locator(MultipleLocator(5))
    plt.gca().xaxis.set_minor_locator(MultipleLocator(1))
    plt.grid(which="major", axis="x", color="k", alpha=0.5)
    plt.grid(which="minor", axis="x", color="k", alpha=0.5, linestyle="--")
    plt.gca().set_axisbelow(True)

    plot_timeline(rotation.gcd_timeline, 0, maxx, color=GCD_COLOR, height=height)
    plot_timeline(rotation.cast_timeline, height, maxx, color=CAST_COLOR, height=height)
    color_dict = {Regrowth: RG_COLOR, Rejuvenation: RJ_COLOR, HealingTouch: HT_COLOR, Lifebloom: LB_COLOR}
    yticks = np.arange(n_timelines) * height
    ylabels = ["GCD", "Casts", *[a.target.capitalize() for a in rotation.assignments], *rotation.filler_targets]
    for i, (assignment, timeline) in enumerate(rotation.timelines):
        plot_timeline(
            timeline, (i+2) * height, maxx,
            color=color_dict[assignment.spell.__class__],
            height=height)
    plt.gca().set_yticks(yticks)
    plt.gca().set_yticklabels(ylabels)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
