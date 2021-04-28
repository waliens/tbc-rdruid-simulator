from heal_parts import HealParts
from statistics import Stats
from statsmodifiers import StatsModifier, ConstantStatsModifier


class Buff(StatsModifier):
    GIFT_OF_THE_WILD = "gift_of_the_wild"
    GIFT_OF_THE_WILD_TAL = "gift_of_the_wild_tal"
    DIVINE_SPIRIT = "divine_spirit"
    DIVINE_SPIRIT_TAL = "divine_spirit_tal"
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
    ATIESH_DRUID = "atiesh_druid"
    ATIESH_PRIEST = "atiesh_priest"
    ATIESH_MAGE = "atiesh_mage"
    ATIESH_LOCK = "atiesh_lock"

    @staticmethod
    def player_buffs():
        return {Buff.GIFT_OF_THE_WILD,
                Buff.GIFT_OF_THE_WILD_TAL,
                Buff.DIVINE_SPIRIT,
                Buff.DIVINE_SPIRIT_TAL,
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
                Buff.TREE_OF_LIFE_MANA,
                Buff.ATIESH_DRUID,
                Buff.ATIESH_PRIEST,
                Buff.ATIESH_MAGE,
                Buff.ATIESH_LOCK}

    @staticmethod
    def target_buffs():
        return {Buff.DAMPEN_MAGIC,
                Buff.AMPLIFY_MAGIC,
                Buff.TREE_OF_LIFE_HEALING}

    @staticmethod
    def consumables():
        return {Buff.ELIXIR_OF_DRAENIC_WISDOM,
                Buff.ELIXIR_OF_MAJOR_MAGEBLOOD,
                Buff.ELIXIR_OF_HEALING_POWER,
                Buff.ELIXIR_OF_MASTERY,
                Buff.GOLDEN_FISH_STICKS}

    @staticmethod
    def all_buffs():
        return Buff.target_buffs().union(Buff.player_buffs())


_constant_buffs = [
    # buffs
    (Buff.GIFT_OF_THE_WILD, StatsModifier.TYPE_ADDITIVE, [(p, 12) for p in Stats.primary()]),
    (Buff.GIFT_OF_THE_WILD_TAL, StatsModifier.TYPE_ADDITIVE, [(p, 16) for p in Stats.primary()]),
    (Buff.DIVINE_SPIRIT, StatsModifier.TYPE_ADDITIVE, [(Stats.SPIRIT, 50)]),
    (Buff.ARCANE_INTELLECT, StatsModifier.TYPE_ADDITIVE, [(Stats.INTELLECT, 40)]),
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
    (Buff.ELIXIR_OF_DRAENIC_WISDOM, StatsModifier.TYPE_ADDITIVE, [(Stats.SPIRIT, 30), (Stats.INTELLECT, 30)]),
    (Buff.ELIXIR_OF_MAJOR_MAGEBLOOD, StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 16)]),
    (Buff.ELIXIR_OF_HEALING_POWER, StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 50)]),
    (Buff.ELIXIR_OF_MASTERY, StatsModifier.TYPE_ADDITIVE, [(p, 15) for p in Stats.primary()]),
    (Buff.GOLDEN_FISH_STICKS, StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 44), (Stats.SPIRIT, 20)]),
    (Buff.DAMPEN_MAGIC, StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_DAMAGE, -120), (Stats.BONUS_HEALING, -240)]),
    (Buff.AMPLIFY_MAGIC, StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_DAMAGE, 120), (Stats.BONUS_HEALING, 240)]),
    (Buff.ATIESH_DRUID, StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 11)]),
    (Buff.ATIESH_PRIEST, StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 64)]),
    (Buff.ATIESH_MAGE, StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_CRIT_RATING, 28)]),
    (Buff.ATIESH_LOCK, StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_DAMAGE, 33)])
]

_formula_buffs = [
    (Buff.TREE_OF_LIFE_HEALING, StatsModifier.TYPE_ADDITIVE, [Stats.BONUS_HEALING],
     [lambda c: c.get_stat(Stats.SPIRIT) * 0.25],
     ["(#Stats.{}# * 0.25)".format(Stats.SPIRIT)]),
    (Buff.DIVINE_SPIRIT_TAL, StatsModifier.TYPE_ADDITIVE,
     [Stats.SPIRIT, Stats.BONUS_HEALING, Stats.SPELL_DAMAGE],
     [(lambda c: 50),
      (lambda c: c.get_stat(Stats.SPIRIT) * 0.10),
      (lambda c: c.get_stat(Stats.SPIRIT) * 0.10)],
     ["(50)", *(["(#Stats.{}# * 0.1)".format(Stats.SPIRIT)] * 2)])
]

_spell_buffs = [
    (Buff.TREE_OF_LIFE_MANA, StatsModifier.TYPE_MULTIPLICATIVE,
        [(spell, HealParts.MANA_COST) for spell in ["rejuvenation", "regrowth", "lifebloom", "tranquility"]],
        [(lambda c: (0.8 if c.talents.get(("tree_of_life", 1, "restoration")) > 0 else 1.0)) for _ in range(4)],
        ["IF(#Talents.tree_of_life#; 1.0; 0.8)" for _ in range(4)])
]

ALL_STATS_BUFFS = dict()
ALL_STATS_BUFFS.update({n: ConstantStatsModifier(n, t, e, cond_cm_group="Buff" if n not in Buff.target_buffs() else "Target") for n, t, e in _constant_buffs})
ALL_STATS_BUFFS.update({n: StatsModifier(n, s, fu, fo, t, cond_cm_group="Buff" if n not in Buff.target_buffs() else "Target") for n, t, s, fu, fo in _formula_buffs})

PLAYER_BUFFS = {n: b for n, b in ALL_STATS_BUFFS.items() if n in Buff.player_buffs()}
CONSUMABLES = {n: b for n, b in ALL_STATS_BUFFS.items() if n in Buff.consumables()}
TARGET_BUFFS = {n: b for n, b in ALL_STATS_BUFFS.items() if n in Buff.target_buffs()}

ALL_SPELL_BUFFS = dict()
ALL_SPELL_BUFFS.update({n: StatsModifier(n, s, fu, fo, t, cond_cm_group="Buff" if n not in Buff.target_buffs() else "Target") for n, t, s, fu, fo in _spell_buffs})
