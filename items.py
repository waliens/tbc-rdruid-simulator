from buffs import Buff
from gems import GemSlotsCollection
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
    def __init__(self, stats_items, spell_items, all_gem_slots=None):
        self._stats_items = stats_items
        self._spell_items = spell_items
        self._all_slots = all_gem_slots if all_gem_slots is not None else GemSlotsCollection([])
        self._stats_modifiers = StatsModifierArray.merge(*[item.stats_effects for item in self._stats_items], self._all_slots.modifiers)
        self._spell_modifiers = StatsModifierArray.merge(*[item.spell_effects for item in self._spell_items])

    @property
    def stats_effects(self):
        return self._stats_modifiers

    @property
    def spell_effects(self):
        return self._spell_modifiers

    def apply_spell_effect(self, spell_name, spell_part, base_value, character):
        return self._spell_modifiers.apply((spell_name, spell_part), base_value, character)


def darkmoon_blue_dragon(char):
    from talents import DruidTalents
    base_regen_percent = 0.1 * char.talents.get(DruidTalents.INTENSITY)
    if char.effects.has_modifier("primal_mooncloth_3p"):
        base_regen_percent += 0.05
    # probability of it to be active at a given tick given 8 casts in the last 15 sec: 0.1389000853
    p = 0.1389000853
    return char.get_stat(Stats.REGEN_5SR) * p * (1 - base_regen_percent)


_stats_items = [
    ItemBonus(name="idol_of_the_emerald_queen",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="idol_of_the_emerald_queen", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 88)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.TICK)
              ])),
    ItemBonus(name="idol_of_rejuvenation",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="idol_of_rejuvenation", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 50)], cond_cm_group="Gear",
                                        spell_name="rejuvenation", spell_part=HealParts.TICK)
              ])),
    ItemBonus(name="harolds_rejuvenating_broach",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="harolds_rejuvenating_broach", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 86)], cond_cm_group="Gear",
                                        spell_name="rejuvenation", spell_part=HealParts.TICK)
              ])),
    ItemBonus(name="gladiators_idol_of_tenacity",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="gladiators_idol_of_tenacity", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 87)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.DIRECT)
              ])),
    ItemBonus(name="merciless_gladiators_idol_of_tenacity",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="merciless_gladiators_idol_of_tenacity", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 105)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.DIRECT)
              ])),
    ItemBonus(name="vengeful_gladiators_idol_of_tenacity",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="vengeful_gladiators_idol_of_tenacity", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 116)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.DIRECT)
              ])),
    ItemBonus(name="brutal_gladiators_idol_of_tenacity",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="brutal_gladiators_idol_of_tenacity", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 131)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.DIRECT)
              ])),
    ItemBonus(name="brutal_gladiators_idol_of_tenacity",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="brutal_gladiators_idol_of_tenacity", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 131)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.DIRECT)
              ])),
    ItemBonus(name="idol_of_the_raven_goddess",
              stats_effects=StatsModifierArray([
                  StatsModifier(name="idol_of_the_raven_goddess", _type=StatsModifier.TYPE_ADDITIVE,
                                stats=[Stats.BONUS_HEALING],
                                functions=[lambda char: (44 if char.stats_buff.has_modifier(Buff.TREE_OF_LIFE_HEALING) else 0)],
                                formula=["IF(#Target.{}#; 44; 0)".format(Buff.TREE_OF_LIFE_HEALING)], cond_cm_group="Gear")
              ])),
    ItemBonus(name="idol_of_the_avian_heart",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="idol_of_the_avian_heart", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 136)], cond_cm_group="Gear",
                                        spell_name="healing_touch", spell_part=HealParts.DIRECT)
              ])),
    ItemBonus(name="t5_nordrassil_raiment_4p",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="t5_nordrassil_raiment_4p", _type=StatsModifier.TYPE_ADDITIVE,
                                        effects=[(Stats.BONUS_HEALING, 150)], cond_cm_group="Gear",
                                        spell_name="lifebloom", spell_part=HealParts.DIRECT)
              ])),
    ItemBonus(name="primal_mooncloth_3p",
              stats_effects=StatsModifierArray([
                  StatsModifier(name="primal_mooncloth_3p", stats=[Stats.MP5],
                                functions=[lambda char: 0.05 * char.get_stat(Stats.REGEN_5SR)],
                                formula=["(0.05 * #Stats.{}#)".format(Stats.REGEN_5SR)],
                                _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="whitemend_2p",
              stats_effects=StatsModifierArray([
                  StatsModifier(name="whitemend_2p", stats=[Stats.BONUS_HEALING],
                                functions=[lambda char: 0.1 * char.get_stat(Stats.INTELLECT)],
                                formula=["(0.1 * #Stats.{}#)".format(Stats.INTELLECT)],
                                _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="t2_stormrage_raiment_3p",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="t2_stormrage_raiment_3p", effects=[(Stats.MP5, 20)],
                                        _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="t1_cenarion_raiment_5p",
              stats_effects=StatsModifierArray([
                  ConstantStatsModifier(name="t1_cenarion_raiment_5p", effects=[(Stats.SPELL_CRIT_RATING, 48)],
                                        _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="darkmoon_card_blue_dragon",
              stats_effects=StatsModifierArray([
                  StatsModifier(name="darkmoon_card_blue_dragon", stats=[Stats.MP5],
                                functions=[darkmoon_blue_dragon],
                                formula=["(#Stats.{regen}# * 0.1389000853 * (1 - (IF(#Gear.{pmc}#; 0.05; 0) "
                                         "+ #Talents.{intens}# * 0.1)))".format(
                                    regen=Stats.REGEN_5SR, pmc="primal_mooncloth_3p", intens="intensity")],
                                _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="lower_city_prayer_book",
              stats_effects=StatsModifierArray([
                  StatsModifier(name="lower_city_prayer_book", stats=[Stats.MP5],
                                functions=[lambda char: (8 * 22) / 12],  # activated on timer, 8 cast during activity
                                formula=["(8 * 22 / 12)"],
                                _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ]))
]

_spell_items = [
    ItemBonus(name="t5_nordrassil_raiment_2p",
              spell_effects=StatsModifierArray([
                  ConstantStatsModifier(name="t5_nordrassil_raiment_2p", effects=[(("regrowth", HealParts.DURATION), 6)],
                                        _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="t3_dreamwalker_raiment_4p",
              spell_effects=StatsModifierArray([
                  ConstantStatsModifier(name="t3_dreamwalker_raiment_4p", effects=[((spell, HealParts.MANA_COST), 0.97)],
                                        _type=StatsModifier.TYPE_MULTIPLICATIVE, cond_cm_group="Gear")
                  for spell in ["healing_touch", "rejuvenation", "tranquility", "regrowth"]
              ])),
    ItemBonus(name="t2_stormrage_raiment_5p",
              spell_effects=StatsModifierArray([
                  ConstantStatsModifier(name="t2_stormrage_raiment_5p", effects=[(("regrowth", HealParts.CAST_TIME), -0.2)],
                                        _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="t2_stormrage_raiment_8p",
              spell_effects=StatsModifierArray([
                  ConstantStatsModifier(name="t2_stormrage_raiment_8p", effects=[(("rejuvenation", HealParts.DURATION), 3)],
                                        _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="t6_thunderheart_raiment_4p",
              spell_effects=StatsModifierArray([
                  ConstantStatsModifier(name="t6_thunderheart_raiment_4p", effects=[(("healing_touch", HealParts.FINAL_DIRECT), 1.1)],
                                        _type=StatsModifier.TYPE_MULTIPLICATIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="idol_of_budding_life",
              spell_effects=StatsModifierArray([
                  ConstantStatsModifier(name="idol_of_budding_life", effects=[(("rejuvenation", HealParts.MANA_COST), -36)],
                                        _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ])),
    ItemBonus(name="idol_of_the_crescent_goddess",
              spell_effects=StatsModifierArray([
                  ConstantStatsModifier(name="idol_of_the_crescent_goddess", effects=[(("regrowth", HealParts.MANA_COST), -65)],
                                        _type=StatsModifier.TYPE_ADDITIVE, cond_cm_group="Gear")
              ]))
]

ALL_STATS_ITEMS = {item.name: item for item in _stats_items}
ALL_SPELL_ITEMS = {item.name: item for item in _spell_items}
ALL_ITEMS_GEAR = Gear(list(ALL_STATS_ITEMS.values()), list(ALL_SPELL_ITEMS.values()))


def get_items(names):
    spell_items, stats_items = list(), list()
    stats_items.extend([ALL_STATS_ITEMS[n] for n in names if n in ALL_STATS_ITEMS])
    spell_items.extend([ALL_SPELL_ITEMS[n] for n in names if n in ALL_SPELL_ITEMS])
    return stats_items, spell_items