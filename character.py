import math

from buff import BuffArray, BUFFS
from statistics import Stats, linear, BASE_MANA_LOOKUP
from talents import Talents


class Character(object):
    def __init__(self, stats, talents, buffs, level=70, tree_form=False):
        self._level = level
        self._stats_dict = dict()
        self._buffs = buffs
        self._all_buffs = BuffArray(BUFFS.values())
        
        for stat in Stats.all_stats():
            self._stats_dict[stat] = stats.get(stat, 0)
            self._stats_dict[Stats.base(stat)] = stats.get(stat, 0)

        self._stats_dict[Stats.REGEN_5SR] = 5 * 0.00932715221261 * math.sqrt(self._stats_dict[Stats.INTELLIGENCE]) * self._stats_dict[Stats.SPIRIT]
        self._stats_dict[Stats.SPELL_HASTE] = linear(60, 1/10, 70, 1/15.8)(level) * self._stats_dict[Stats.SPELL_HASTE_RATING] / 100
        self._stats_dict[Stats.SPELL_CRIT] = (1.85 + (self._stats_dict[Stats.INTELLIGENCE] / 80) + linear(60, 1/14, 70, 1/22.1)(level) * self._stats_dict[Stats.SPELL_CRIT_RATING]) / 100
        self._stats_dict[Stats.GCD] = 1.5 / (1 + self._stats_dict[Stats.SPELL_HASTE])
        self._stats_dict[Stats.MANA] = BASE_MANA_LOOKUP[level - 1] + (min(20, self._stats_dict[Stats.INTELLIGENCE])+15*(self._stats_dict[Stats.INTELLIGENCE] - min(self._stats_dict[Stats.INTELLIGENCE], 20)))

        self._stats_dict[Stats.SPIRIT] = self._stats_dict[Stats.base(Stats.SPIRIT)] * (1 + 0.05 * talents.get(talents.LIVING_SPIRIT))
        lunar_guidance = [0, 0.08, 0.16, 0.25][talents.get(Talents.LUNAR_GUIDANCE)]
        self._stats_dict[Stats.SPELL_DAMAGE] += lunar_guidance * self._stats_dict[Stats.INTELLIGENCE]
        self._stats_dict[Stats.BONUS_HEALING] += lunar_guidance * self._stats_dict[Stats.INTELLIGENCE]
        dreamstate = [0, 0.04, 0.07, 0.1][talents.get(Talents.DREAMSTATE)]
        self._stats_dict[Stats.MP5] += dreamstate * self._stats_dict[Stats.INTELLIGENCE]

        self._talents = talents
        self._tree_form = tree_form and talents.get(Talents.TREE_OF_LIFE) == 1

    @property
    def talents(self):
        return self._talents

    @property
    def buffs(self):
        return self._buffs

    @property
    def level(self):
        return self._level

    @property
    def tree_form(self):
        return self._tree_form

    def get_talent_points(self, talent):
        return self._talents.get(talent)

    def get_stat(self, stat):
        """get final value of buffed stat"""
        effect = self._stats_dict.get(stat, None)
        if effect is not None:
            return self._buffs.apply(stat, effect)
        return effect

    def get_buffed_stat(self, stat):
        return self.get_stat(stat)

    def get_base_stat(self, stat):
        return self._stats_dict.get(Stats.base(stat), None)

    def get_buffed_excel_formula(self, stat):
        buffed_base = "#Stats.{stat}#".format(stat=Stats.base(stat))
        if stat in Stats.computed():
            buffed_base = Stats.get_computed_excel_formula(stat)
        formula = self._all_buffs.excel_formula(stat, buffed_base)
        if stat == Stats.SPIRIT:
            formula = "(({}) * (1 + 0.05 * #Talents.{}#))".format(formula, Talents.LIVING_SPIRIT[0])
        return formula

    def get_base_excel_formula(self, stat):
        return str(self.get_base_stat(stat))
