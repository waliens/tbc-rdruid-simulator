from collections import defaultdict

from statistics import Stats


class Buff(object):
    TYPE_ADDITIVE = "ADDITIVE"
    TYPE_MULTIPLICATIVE = "MULTIPLICATIVE"

    def __init__(self, name, effects):
        self._name = name
        self._addi_effects = {s: v for s, t, v in effects if t == self.TYPE_ADDITIVE}
        self._mult_effects = {s: v for s, t, v in effects if t == self.TYPE_MULTIPLICATIVE}

        both_effects = set(self._addi_effects.keys()).intersection(set(self._mult_effects.keys()))
        if len(both_effects) > 0:
            raise ValueError("Buff '{}' cannot have both an additive and a multiplicative effect on stats '{}'".format(
                name, ",".join(map(str, both_effects))))

    def apply(self, stat, base_value):
        return (base_value + self._addi_effects.get(stat, 0)) * self._mult_effects.get(stat, 1)

    def excel_formula(self, stat, base_formula):
        if stat in self._addi_effects:
            return "{formula} + IF(#Buff.{buff}#; {val}; 0)".format(formula=base_formula, buff=self.name, val=self._addi_effects[stat])
        else:
            return "{formula} * IF(#Buff.{buff}#; {val}; 1)".format(formula=base_formula, buff=self.name, val=self._mult_effects[stat])

    @property
    def affected_stats(self):
        return [(self.TYPE_ADDITIVE, s) for s in self._addi_effects.keys()] \
                + [(self.TYPE_MULTIPLICATIVE, s) for s in self._mult_effects.keys()]

    @property
    def name(self):
        return self._name


class BuffArray(object):
    def __init__(self, buffs, name=""):
        self._name = name
        self._buffs = buffs
        self._additive = defaultdict(lambda: list())
        self._multiplicative = defaultdict(lambda: list())

        for buff in self._buffs:
            for type, stat in buff.affected_stats:
                if type == Buff.TYPE_ADDITIVE:
                    self._additive[stat].append(buff)
                elif type == Buff.TYPE_MULTIPLICATIVE:
                    self._multiplicative[stat].append(buff)

    @property
    def name(self):
        return self._name

    def __len__(self):
        return len(self._buffs)

    def apply(self, stat, base_value):
        stat_value = base_value
        for buff in self._additive[stat]:
            stat_value = buff.apply(stat, stat_value)
        for buff in self._multiplicative[stat]:
            stat_value = buff.apply(stat, stat_value)
        return stat_value

    def excel_formula(self, stat, stat_formula):
        formula = stat_formula
        for buff in self._additive[stat]:
            formula = buff.excel_formula(stat, formula)
        formula = "({})".format(formula)
        for buff in self._multiplicative[stat]:
            formula = buff.excel_formula(stat, formula)
        return "({})".format(formula)

    def has_buff(self, name):
        return name in {b.name for b in self._buffs}


_buffs = [
    # buffs
    ("gift_of_the_wild", [(p, Buff.TYPE_ADDITIVE, 18) for p in Stats.primary()]),
    ("arcane_intellect", [(Stats.INTELLIGENCE, Buff.TYPE_ADDITIVE, 40)]),
    ("benediction_of_king", [(p, Buff.TYPE_MULTIPLICATIVE, 1.1) for p in Stats.primary()]),
    ("benediction_of_wisdom", [(Stats.MP5, Buff.TYPE_ADDITIVE, 41)]),
    ("benediction_of_wisdom_tal", [(Stats.MP5, Buff.TYPE_ADDITIVE, 49)]),
    ("mana_tide_totem", [(Stats.MP5, Buff.TYPE_ADDITIVE, 50)]),
    ("mana_tide_totem_tal", [(Stats.MP5, Buff.TYPE_ADDITIVE, 50)]),
    ("wrath_of_air_totem", [(Stats.BONUS_HEALING, Buff.TYPE_ADDITIVE, 101), (Stats.SPELL_DAMAGE, Buff.TYPE_ADDITIVE, 101)]),
    ("totem_of_wrath", [(Stats.SPELL_CRIT, Buff.TYPE_ADDITIVE, 0.03)]),
    ("moonkin_aura", [(Stats.SPELL_CRIT, Buff.TYPE_ADDITIVE, 0.05)]),
    ("mark_of_bite", [(p, Buff.TYPE_MULTIPLICATIVE, 1.05) for p in Stats.primary()]),
    # TODO ("vampiric_touch", [(Stats.)])
    # consumables
    ("elixir_of_draenic_wisdom", [(Stats.SPIRIT, Buff.TYPE_ADDITIVE, 30), (Stats.INTELLIGENCE, Buff.TYPE_ADDITIVE, 30)]),
    ("elixir_of_major_mageblood", [(Stats.MP5, Buff.TYPE_ADDITIVE, 16)]),
    ("elixir_of_healing_power", [(Stats.BONUS_HEALING, Buff.TYPE_ADDITIVE, 50)]),
    ("elixir_of_mastery",  [(p, Buff.TYPE_ADDITIVE, 15) for p in Stats.primary()]),
    ("golden_fish_sticks", [(Stats.BONUS_HEALING, Buff.TYPE_ADDITIVE, 44), (Stats.SPIRIT, Buff.TYPE_ADDITIVE, 20)])
]

BUFFS = {n: Buff(n, e) for n, e in _buffs}
