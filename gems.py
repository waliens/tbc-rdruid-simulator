from collections import defaultdict

from statistics import Stats
from statsmodifiers import ConstantStatsModifier, StatsModifier, StatsModifierArray


class Gem(ConstantStatsModifier):
    RED = "red"
    BLUE = "blue"
    YELLOW = "yellow"
    ORANGE = "orange"
    PURPLE = "purple"
    GREEN = "green"
    META = "meta"
    PRISMATIC = "prismatic"

    def __init__(self, name, effects, color, **context):
        super().__init__(name, StatsModifier.TYPE_ADDITIVE, effects, cond_cm_group="Gem", **context)
        self._color = color

    @property
    def color(self):
        return self._color

    @staticmethod
    def match_colors(slot, gem):
        return gem is not None and gem.color == Gem.PRISMATIC or gem.color == slot or \
            (gem.color == Gem.PURPLE and slot in {Gem.RED, Gem.BLUE}) or \
            (gem.color == Gem.GREEN and slot in {Gem.YELLOW, Gem.BLUE}) or \
            (gem.color == Gem.ORANGE and slot in {Gem.RED, Gem.YELLOW})


class ItemGemSlots(object):
    def __init__(self, name, slots, bonus: StatsModifier):
        """slots: list of colors"""
        self._name = name
        self._slots = sorted(slots)
        self._gems = [None] * len(slots)
        self._bonus = bonus

    @property
    def bonus_active(self):
        return all([(Gem.match_colors(s, g)) for g, s in zip(self._gems, self._slots)])

    @property
    def modifiers(self):
        gems = [g for g in self._gems if g is not None]
        if self._bonus is not None and self.bonus_active:
            return StatsModifierArray([*gems, self._bonus])
        else:
            return StatsModifierArray(gems)

    @property
    def slot_colors(self):
        return self._slots

    def add_gem(self, gem, match=False):
        for i, color in enumerate(self.slot_colors):
            if (not match or Gem.match_colors(color, gem)) and self._gems[i] is None:
                self._gems[i] = gem
                return True
        return False

    @property
    def open_slots(self):
        return len([v for v in self._gems if v is None])

    def clear_gems(self):
        self._gems = [None] * len(self._slots)

    @property
    def gems(self):
        return [g for g in self._gems if g is not None]


class GemSlotsCollection(object):
    def __init__(self, item_gem_slots):
        self._item_gem_slots = item_gem_slots

    @property
    def slots(self):
        return self._item_gem_slots

    def add_gem(self, gem, match=False):
        for item_slots in self._item_gem_slots:
            if item_slots.add_gem(gem, match=match):
                return True
        return False

    @property
    def open_slots(self):
        return sum([igs.open_slots for igs in self._item_gem_slots])

    def clear_gems(self):
        for item_slots in self._item_gem_slots:
            item_slots.clear_gems()

    @property
    def gems(self):
        return [g for item_slots in self._item_gem_slots for g in item_slots.gems]

    @property
    def modifiers(self):
        all_modifiers = [item_slots.modifiers for item_slots in self._item_gem_slots]
        if "bracing_earthstorm_diamond" in {g.name for g in self.gems}:
            # count red and blue
            red_count, blue_count = 0, 0
            for gem in self.gems:
                if gem.color in {Gem.RED, Gem.ORANGE, Gem.PURPLE, Gem.PRISMATIC}:
                    red_count += 1
                if gem.color in {Gem.BLUE, Gem.GREEN, Gem.PURPLE, Gem.PRISMATIC}:
                    blue_count += 1
            if red_count <= blue_count:
                modifier = ConstantStatsModifier("meta_malus", _type=StatsModifier.TYPE_ADDITIVE,
                                                 effects=[(Stats.BONUS_HEALING, -26), (Stats.SPELL_DAMAGE, -9)],
                                                 cond_cm_group="Gem")
                all_modifiers.append(StatsModifierArray([modifier]))
        return StatsModifierArray.merge(*all_modifiers)


STRATEGY_MATCHING = "match_slots"
STRATEGY_STACK_HEALING = "stack_healing"


def _bonus(modifier, stat):
    return modifier.apply(stat, 0, None)


def optimize_slots(slots: GemSlotsCollection, strategy=STRATEGY_MATCHING, heroic=True, jewelcrafting=False):
    slots.clear_gems()
    gem_set = set(ALL_GEMS.keys())
    if not heroic:
        gem_set = gem_set.difference(HEROIC)
    if not jewelcrafting:
        gem_set = gem_set.difference(JEWELCRAFTING)
    used = set()
    gem_list = sorted(gem_set, key=lambda g: -_bonus(ALL_GEMS[g], Stats.BONUS_HEALING))
    for gem_name in gem_list:
        gem = ALL_GEMS[gem_name]
        while slots.open_slots > 0 and (gem_name not in UNIQUE or gem_name not in used):
            added = slots.add_gem(gem, match=True)
            if not added and strategy != STRATEGY_MATCHING:
                added = slots.add_gem(gem, match=False)
            if added:
                used.add(gem_name)
            else:
                break
    return slots


_gems = [
    # bh - meta
    Gem("bracing_earthstorm_diamond", [(Stats.BONUS_HEALING, 26), (Stats.SPELL_DAMAGE, 9)], Gem.META),
    # bh - rouge
    Gem("kailees_rose", [(Stats.BONUS_HEALING, 26), (Stats.SPELL_DAMAGE, 9)], Gem.RED),
    Gem("teardrop_living_ruby", [(Stats.BONUS_HEALING, 18), (Stats.SPELL_DAMAGE, 6)], Gem.RED),
    # bh - orange
    Gem("luminous_pyrestone", [(Stats.BONUS_HEALING, 11), (Stats.SPELL_DAMAGE, 4), (Stats.INTELLECT, 5)], Gem.ORANGE),
    Gem("luminous_fire_opal", [(Stats.BONUS_HEALING, 11), (Stats.SPELL_DAMAGE, 4), (Stats.INTELLECT, 4)], Gem.ORANGE),
    Gem("luminous_noble_topaz", [(Stats.BONUS_HEALING, 9), (Stats.SPELL_DAMAGE, 3), (Stats.INTELLECT, 4)], Gem.ORANGE),
    Gem("iridescent_fire_opal", [(Stats.BONUS_HEALING, 11), (Stats.SPELL_DAMAGE, 4), (Stats.SPELL_CRIT_RATING, 4)], Gem.ORANGE),
    # bh - purple
    Gem("royal_shadowsong_amethyst", [(Stats.BONUS_HEALING, 11), (Stats.SPELL_DAMAGE, 4), (Stats.MP5, 2)], Gem.PURPLE),
    Gem("soothing_amethyst", [(Stats.BONUS_HEALING, 11), (Stats.SPELL_DAMAGE, 4), (Stats.STAMINA, 6)], Gem.PURPLE),
    Gem("royal_tanzanite", [(Stats.BONUS_HEALING, 11), (Stats.MP5, 2)], Gem.PURPLE),
    Gem("imperial_tanzanite", [(Stats.BONUS_HEALING, 11), (Stats.MP5, 2)], Gem.PURPLE),
    Gem("royal_nightseye", [(Stats.BONUS_HEALING, 9), (Stats.MP5, 2)], Gem.PURPLE),
    # haste gems
    Gem("reckless_pyrolithe", [(Stats.SPELL_HASTE_RATING, 5), (Stats.SPELL_DAMAGE, 6), (Stats.BONUS_HEALING, 6)], Gem.ORANGE),
    Gem("quick_dawnstone", [(Stats.SPELL_HASTE_RATING, 8)], Gem.YELLOW),
    Gem("quick_lionseye", [(Stats.SPELL_HASTE_RATING, 10)], Gem.YELLOW),
    Gem("reckless_noble_topaz", [(Stats.SPELL_HASTE_RATING, 4), (Stats.SPELL_DAMAGE, 5), (Stats.BONUS_HEALING, 5)], Gem.ORANGE),
]


HEROIC = {"imperial_tanzanite", "royal_tanzanite", "luminous_fire_opal", "iridescent_fire_opal"}
JEWELCRAFTING = {"kailees_rose", "luminous_pyrestone"}
UNIQUE = {"bracing_earthstorm_diamond"}.union(HEROIC, JEWELCRAFTING)

ALL_GEMS = {g.name: g for g in _gems}

# if __name__ == "__main__":
#     slots = AllSlots([
#         ItemGemSlots([Gem.RED, Gem.META, Gem.YELLOW], ConstantStatsModifier("", StatsModifier.TYPE_ADDITIVE, [(Stats.INTELLIGENCE, 4)])),
#         ItemGemSlots([Gem.RED, Gem.BLUE, Gem.BLUE], None),
#         ItemGemSlots([Gem.RED, Gem.BLUE, Gem.YELLOW], None)
#     ])
#     slots = optimize_slots(slots, strategy=STRATEGY_MATCHING, heroic=False, jewelcrafting=False)
#     print(slots.gems)
#     print(slots.modifiers.apply(Stats.BONUS_HEALING, 0, None))