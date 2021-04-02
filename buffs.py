from statistics import Stats
from statsmodifiers import StatsModifier, ConstantStatsModifier


class Buff(StatsModifier):
    GIFT_OF_THE_WILD = "gift_of_the_wild"
    ARCANE_INTELLECT = "arcane_intellect"
    BENEDICTION_OF_KING = "benediction_of_king"
    BENEDICTION_OF_WISDOM = "benediction_of_wisdom"
    BENEDICTION_OF_WISDOM_TAL = "benediction_of_wisdom_tal"
    MANA_TIDE_TOTEM = "mana_tide_totem"
    MANA_TIDE_TOTEM_TAL = "mana_tide_totem_tal"
    WRATH_OF_AIR_TOTEM = "wrath_of_air_totem"
    TOTEM_OF_WRATH = "totem_of_wrath"
    MOONKIN_AURA = "moonkin_aura"
    MARK_OF_BITE = "mark_of_bite"
    ELIXIR_OF_DRAENIC_WISDOM = "elixir_of_draenic_wisdom"
    ELIXIR_OF_MAJOR_MAGEBLOOD = "elixir_of_major_mageblood"
    ELIXIR_OF_HEALING_POWER = "elixir_of_healing_power"
    ELIXIR_OF_MASTERY = "elixir_of_mastery"
    GOLDEN_FISH_STICKS = "golden_fish_sticks"
    DAMPEN_MAGIC = "dampen_magic"
    AMPLIFY_MAGIC = "amplify_magic"
    TREE_OF_LIFE_HEALING = "tree_of_life_healing"
    TREE_OF_LIFE_MANA = "tree_of_life_mana"

    @staticmethod
    def player_buffs():
        return {Buff.GIFT_OF_THE_WILD,
                Buff.ARCANE_INTELLECT,
                Buff.BENEDICTION_OF_KING,
                Buff.BENEDICTION_OF_WISDOM,
                Buff.BENEDICTION_OF_WISDOM_TAL,
                Buff.MANA_TIDE_TOTEM,
                Buff.MANA_TIDE_TOTEM_TAL,
                Buff.WRATH_OF_AIR_TOTEM,
                Buff.TOTEM_OF_WRATH,
                Buff.MOONKIN_AURA,
                Buff.MARK_OF_BITE,
                Buff.ELIXIR_OF_DRAENIC_WISDOM,
                Buff.ELIXIR_OF_MAJOR_MAGEBLOOD,
                Buff.ELIXIR_OF_HEALING_POWER,
                Buff.ELIXIR_OF_MASTERY,
                Buff.GOLDEN_FISH_STICKS,
                Buff.TREE_OF_LIFE_MANA}

    @staticmethod
    def target_buffs():
        return {Buff.DAMPEN_MAGIC,
                Buff.AMPLIFY_MAGIC,
                Buff.TREE_OF_LIFE_HEALING}

    @staticmethod
    def all_buffs():
        return Buff.target_buffs().union(Buff.player_buffs())


_constant_buffs = [
    # buffs
    (Buff.GIFT_OF_THE_WILD, StatsModifier.TYPE_ADDITIVE, [(p, 18) for p in Stats.primary()]),
    (Buff.ARCANE_INTELLECT, StatsModifier.TYPE_ADDITIVE, [(Stats.INTELLIGENCE, 40)]),
    (Buff.BENEDICTION_OF_KING, StatsModifier.TYPE_MULTIPLICATIVE, [(p, 1.1) for p in Stats.primary()]),
    (Buff.BENEDICTION_OF_WISDOM, StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 41)]),
    (Buff.BENEDICTION_OF_WISDOM_TAL, StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 49)]),
    (Buff.MANA_TIDE_TOTEM, StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 50)]),
    (Buff.MANA_TIDE_TOTEM_TAL, StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 50)]),
    (Buff.WRATH_OF_AIR_TOTEM, StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 101), (Stats.SPELL_DAMAGE, 101)]),
    (Buff.TOTEM_OF_WRATH, StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_CRIT, 0.03)]),
    (Buff.MOONKIN_AURA, StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_CRIT, 0.05)]),
    (Buff.MARK_OF_BITE, StatsModifier.TYPE_MULTIPLICATIVE, [(p, 1.05) for p in Stats.primary()]),
    # TODO ("vampiric_touchStats.)])
    # consumables
    (Buff.ELIXIR_OF_DRAENIC_WISDOM, StatsModifier.TYPE_ADDITIVE, [(Stats.SPIRIT, 30), (Stats.INTELLIGENCE, 30)]),
    (Buff.ELIXIR_OF_MAJOR_MAGEBLOOD, StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 16)]),
    (Buff.ELIXIR_OF_HEALING_POWER, StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 50)]),
    (Buff.ELIXIR_OF_MASTERY, StatsModifier.TYPE_ADDITIVE, [(p, 15) for p in Stats.primary()]),
    (Buff.GOLDEN_FISH_STICKS, StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 44), (Stats.SPIRIT, 20)]),
    (Buff.DAMPEN_MAGIC, StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_DAMAGE, -120), (Stats.BONUS_HEALING, -240)]),
    (Buff.AMPLIFY_MAGIC, StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_DAMAGE, 120), (Stats.BONUS_HEALING, 240)])
]

_formula_buffs = [
    (Buff.TREE_OF_LIFE_HEALING, StatsModifier.TYPE_ADDITIVE, [Stats.BONUS_HEALING], [lambda c: c.get_stat(Stats.SPIRIT) * 0.25], ["(#Stats.{}# * 0.25)".format(Stats.SPIRIT)]),
    (Buff.TREE_OF_LIFE_MANA, StatsModifier.TYPE_ADDITIVE, [], [], [])
]

ALL_BUFFS = dict()
ALL_BUFFS.update({n: ConstantStatsModifier(n, t, e, cond_cm_group="Buff" if n not in Buff.target_buffs() else "Target") for n, t, e in _constant_buffs})
ALL_BUFFS.update({n: StatsModifier(n, s, fu, fo, t, cond_cm_group="Buff" if n not in Buff.target_buffs() else "Target") for n, t, s, fu, fo in _formula_buffs})

PLAYER_BUFFS = {n: b for n, b in ALL_BUFFS.items() if n in Buff.player_buffs()}
TARGET_BUFFS = {n: b for n, b in ALL_BUFFS.items() if n in Buff.target_buffs()}
