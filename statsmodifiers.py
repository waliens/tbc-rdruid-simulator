from collections import defaultdict
from operator import add, mul


class StatsModifier(object):
    TYPE_ADDITIVE = "ADDITIVE"
    TYPE_MULTIPLICATIVE = "MULTIPLICATIVE"

    def __init__(self, name, stats, functions, formula, _type, cond_cm_group=None):
        self._name = name
        self._stats = stats
        self._functions = {s: f for s, f in zip(stats, functions)}
        self._formula = {s: f for s, f in zip(stats, formula)}
        self._type = _type
        self._cond_cm_group = cond_cm_group

    def _aggr(self):
        return add if self._type == StatsModifier.TYPE_ADDITIVE else mul

    def _str_aggr(self):
        return "+" if self._type == StatsModifier.TYPE_ADDITIVE else "*"

    def _cond(self, formula):
        if self._cond_cm_group is None:
            return formula
        return "IF(#{}.{}#; {}; {})".format(self._cond_cm_group, self.name, formula, 0 if self._type == StatsModifier.TYPE_ADDITIVE else 1)

    def apply(self, stat, base_value, character):
        if stat not in self._stats:
            return base_value
        return self._aggr()(base_value, self._functions[stat](character))

    def formula(self, stat, base_formula):
        if stat not in self._stats:
            return base_formula
        return "({} {} {})".format(base_formula, self._str_aggr(), self._cond(self._formula[stat]))

    @property
    def affected_stats(self):
        return self._stats

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type


class ConstantStatsModifier(StatsModifier):
    def __init__(self, name, _type, effects, cond_cm_group=None):
        stats, values = tuple(zip(*effects))
        super().__init__(
            name=name,
            stats=stats,
            functions=[(lambda *args, **kwargs: v) for v in values],
            formula=[str(v) for v in values],
            _type=_type,
            cond_cm_group=cond_cm_group)


class StatsModifierArray(object):
    def __init__(self, buffs, name=""):
        self._name = name
        self._buffs = buffs
        self._additive = defaultdict(lambda: list())
        self._multiplicative = defaultdict(lambda: list())

        for buff in self._buffs:
            for stat in buff.affected_stats:
                if buff.type == StatsModifier.TYPE_ADDITIVE:
                    self._additive[stat].append(buff)
                elif buff.type == StatsModifier.TYPE_MULTIPLICATIVE:
                    self._multiplicative[stat].append(buff)

    @property
    def name(self):
        return self._name

    @property
    def buffs(self):
        return self._buffs

    def __len__(self):
        return len(self._buffs)

    def apply(self, stat, base_value, character):
        stat_value = base_value
        for buff in self._additive[stat]:
            stat_value = buff.apply(stat, stat_value, character)
        for buff in self._multiplicative[stat]:
            stat_value = buff.apply(stat, stat_value, character)
        return stat_value

    def formula(self, stat, stat_formula):
        formula = stat_formula
        for buff in self._additive[stat]:
            formula = buff.formula(stat, formula)
        formula = "({})".format(formula)
        for buff in self._multiplicative[stat]:
            formula = buff.formula(stat, formula)
        return "({})".format(formula)

    def has_modifier(self, name):
        return name in {b.name for b in self._buffs}

    @staticmethod
    def merge(*buff_arrays):
        all_buffs = [buff for buff_array in buff_arrays for buff in buff_array.buffs]
        return StatsModifierArray(all_buffs, name="_".join([buff_array.name for buff_array in buff_arrays]))


