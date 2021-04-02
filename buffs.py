from statistics import Stats
from statsmodifiers import StatsModifier, ConstantStatsModifier

Buff = StatsModifier

_constant_buffs = [
    # buffs
    ("gift_of_the_wild", StatsModifier.TYPE_ADDITIVE, [(p, 18) for p in Stats.primary()]),
    ("arcane_intellect", StatsModifier.TYPE_ADDITIVE, [(Stats.INTELLIGENCE, 40)]),
    ("benediction_of_king", StatsModifier.TYPE_MULTIPLICATIVE, [(p, 1.1) for p in Stats.primary()]),
    ("benediction_of_wisdom", StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 41)]),
    ("benediction_of_wisdom_tal", StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 49)]),
    ("mana_tide_totem", StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 50)]),
    ("mana_tide_totem_tal", StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 50)]),
    ("wrath_of_air_totem", StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 101), (Stats.SPELL_DAMAGE, 101)]),
    ("totem_of_wrath", StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_CRIT, 0.03)]),
    ("moonkin_aura", StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_CRIT, 0.05)]),
    ("mark_of_bite", StatsModifier.TYPE_MULTIPLICATIVE, [(p, 1.05) for p in Stats.primary()]),
    # TODO ("vampiric_touchStats.)])
    # consumables
    ("elixir_of_draenic_wisdom", StatsModifier.TYPE_ADDITIVE, [(Stats.SPIRIT, 30), (Stats.INTELLIGENCE, 30)]),
    ("elixir_of_major_mageblood", StatsModifier.TYPE_ADDITIVE, [(Stats.MP5, 16)]),
    ("elixir_of_healing_power", StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 50)]),
    ("elixir_of_mastery", StatsModifier.TYPE_ADDITIVE, [(p, 15) for p in Stats.primary()]),
    ("golden_fish_sticks", StatsModifier.TYPE_ADDITIVE, [(Stats.BONUS_HEALING, 44), (Stats.SPIRIT, 20)]),
    ("dampen_magic", StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_DAMAGE, -120), (Stats.BONUS_HEALING, -240)]),
    ("amplify_magic", StatsModifier.TYPE_ADDITIVE, [(Stats.SPELL_DAMAGE, 120), (Stats.BONUS_HEALING, 240)])
]

_formula_buffs = [
    ("tree_of_life", StatsModifier.TYPE_ADDITIVE, [Stats.BONUS_HEALING], [lambda c: c.get_stat(Stats.SPIRIT) * 0.25], ["(#Stats.{}# * 0.25)".format(Stats.SPIRIT)])
]


BUFFS = dict()
BUFFS.update({n: ConstantStatsModifier(n, t, e, cond_cm_group="Buff") for n, t, e in _constant_buffs})
BUFFS.update({n: StatsModifier(n, s, fu, fo, t, cond_cm_group="Buff") for n, t, s, fu, fo in _formula_buffs})
