from heal_parts import HealParts
from statistics import Stats
from statsmodifiers import StatsModifier, ConstantStatsModifier, StatsModifierArray


class ItemBonus(object):
    def __init__(self, name, spell_effects=None, stats_effects=None):
        self._name = name
        self._stats_effects = stats_effects if stats_effects is not None else StatsModifierArray([])
        self._spell_effects = spell_effects if spell_effects is not None else StatsModifierArray([])

    @property
    def name(self):
        return self._name

    @property
    def spell_effects(self):
        return self._spell_effects

    @property
    def stats_effects(self):
        return self._stats_effects


class Gear(object):
    def __init__(self, stats_items, spell_items):
        self._stats_items = stats_items
        self._spell_items = spell_items
        self._stats_modifiers = StatsModifierArray.merge(*[item.stats_effects for item in self._stats_items])
        self._spell_modifiers = StatsModifierArray.merge(*[item.spell_effects for item in self._spell_items])

    @property
    def stats_effects(self):
        return self._stats_modifiers

    @property
    def spell_effects(self):
        return self._spell_modifiers

    def apply_spell_effect(self, spell_name, spell_part, base_value, character):
        return self._spell_modifiers.apply((spell_name, spell_part), base_value, character)


_stats_items = [
    ItemBonus(name='idol_of_the_emerald_queen',
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name='idol_of_the_emerald_queen', _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 88)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.TICK)
              ])),
    ItemBonus(name='nordrassil_raiment_4p',
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name='nordrassil_raiment_4p', _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 150)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.DIRECT)
              ])),
    ItemBonus(name='primal_mooncloth_3p',
              stats_effects=StatsModifierArray([
                  StatsModifier(name='primal_mooncloth_3p', stats=[Stats.MP5],
                                functions=[lambda char: 0.05 * char.get_stat(Stats.REGEN_5SR)],
                                formula=["(0.05 * #Stats.{}#)".format(Stats.REGEN_5SR)],
                                _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
]

_spell_items = [
    ItemBonus(name='nordrassil_raiment_2p',
              spell_effects=StatsModifierArray([
                  ConstantStatsModifier(name='nordrassil_raiment_2p', effects=[(("regrowth", HealParts.DURATION), 6)],
                                        _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ]))
]

ALL_STATS_ITEMS = {item.name: item for item in _stats_items}
ALL_SPELL_ITEMS = {item.name: item for item in _spell_items}
ALL_ITEMS_GEAR = Gear(ALL_STATS_ITEMS.values(), ALL_SPELL_ITEMS.values())


def get_items(names):
    spell_items, stats_items = list(), list()
    stats_items.extend([ALL_STATS_ITEMS[n] for n in names if n in ALL_STATS_ITEMS])
    spell_items.extend([ALL_SPELL_ITEMS[n] for n in names if n in ALL_SPELL_ITEMS])
    return stats_items, spell_items