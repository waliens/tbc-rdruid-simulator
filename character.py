import math
from abc import abstractmethod

from statsmodifiers import StatsModifierArray, StatsModifier
from statistics import Stats, linear, BASE_MANA_LOOKUP, linear_params, RATING_FORMULA
from talents import Talents


class Character(object):
    @property
    @abstractmethod
    def level(self):
        """returns the level"""
        pass

    @property
    @abstractmethod
    def talents(self):
        """returns the talents"""
        pass

    @property
    @abstractmethod
    def buffs(self):
        """returns a buff array"""
        pass

    @property
    @abstractmethod
    def effects(self):
        """return a buff array taking into account actual buffs and talents buffing the character"""
        pass

    @property
    @abstractmethod
    def base_stats(self):
        """Returns a dictionary mapping base stats with their values (base = untalented and unbuffed)
        """
        pass

    def get_stat(self, stat):
        """get buffed and talented stat value"""
        base = self.get_base_stat(stat)
        return self.effects.apply(stat, base, self)

    def get_base_stat(self, stat):
        """get base stat value"""
        return self.base_stats.get(stat, 0)

    def get_formula(self, stat):
        """get full formula for a stat"""
        base = "#Stats.{stat}#".format(stat=Stats.base(stat))
        return self.effects.formula(stat, base)

    def get_base_formula(self, stat):
        return str(self.get_base_stat(stat))


def druid_stats():
    buffs = list()

    # regen 5-sec rule
    buffs.append(StatsModifier(
        name=Stats.REGEN_5SR, stats=[Stats.REGEN_5SR], _type=StatsModifier.TYPE_ADDITIVE,
        functions=[lambda char: 5 * 0.00932715221261 * math.sqrt(char.get_stat(Stats.INTELLIGENCE)) * char.get_stat(
            Stats.SPIRIT)],
        formula=["5 * 0.00932715221261 * SQRT(#Stats.{}#) * #Stats.{}#".format(Stats.INTELLIGENCE, Stats.SPIRIT)])
    )

    # haste from rating
    haste_data = [60, 1 / 10, 70, 1 / 15.8]
    haste_coef, haste_interc = linear_params(*haste_data)
    buffs.append(StatsModifier(
        name=Stats.SPELL_HASTE, stats=[Stats.SPELL_HASTE], _type=StatsModifier.TYPE_ADDITIVE,
        functions=[lambda char: linear(*haste_data)(char.level) * char.get_stat(Stats.SPELL_HASTE_RATING) / 100],
        formula=[RATING_FORMULA.format(coef=haste_coef, interc=haste_interc, rating=Stats.SPELL_HASTE_RATING)])
    )

    # crit from rating and intel
    crit_data = [60, 1 / 14, 70, 1 / 22.1]
    crit_coef, crit_interc = linear_params(*crit_data)
    buffs.append(StatsModifier(
        name=Stats.SPELL_CRIT + "_intel", stats=[Stats.SPELL_CRIT], _type=StatsModifier.TYPE_ADDITIVE,
        functions=[lambda char: char.get_stat(Stats.INTELLIGENCE) / (80 * 100)],
        formula=["(#Stats.{}# / (80 * 100))".format(Stats.INTELLIGENCE)])
    )
    buffs.append(StatsModifier(
        name=Stats.SPELL_CRIT + "_rating", stats=[Stats.SPELL_CRIT], _type=StatsModifier.TYPE_ADDITIVE,
        functions=[lambda char: linear(*crit_data)(char.level) * char.get_stat(Stats.SPELL_CRIT_RATING) / 100],
        formula=[RATING_FORMULA.format(coef=crit_coef, interc=crit_interc, rating=Stats.SPELL_CRIT_RATING)])
    )

    # gcd
    buffs.append(StatsModifier(
        name=Stats.GCD, stats=[Stats.GCD], _type=StatsModifier.TYPE_ADDITIVE,
        functions=[lambda char: 1.5 / (1 + char.get_stat(Stats.SPELL_HASTE))],
        formula=["(1.5 / (1 + #Stats.{}#))".format(Stats.SPELL_HASTE)])
    )

    # mana
    buffs.append(StatsModifier(
        name=Stats.MANA + "_base", stats=[Stats.MANA], _type=StatsModifier.TYPE_ADDITIVE,
        functions=[lambda char: BASE_MANA_LOOKUP[char.level - 1]],
        formula=["CHOOSE(#Character.level# - 57; {})".format(";".join(map(str, BASE_MANA_LOOKUP[57:])))]
    ))
    buffs.append(StatsModifier(
        name=Stats.MANA + "_intel", stats=[Stats.MANA], _type=StatsModifier.TYPE_ADDITIVE,
        functions=[lambda char: 15 * max(0, char.get_stat(Stats.INTELLIGENCE) - 20) + min(20, char.get_stat(
            Stats.INTELLIGENCE))],
        formula=["(15 * MAX(0; #Stats.{intel}# - 20) + MIN(20; #Stats.{intel}#))".format(intel=Stats.INTELLIGENCE)]
    ))

    return StatsModifierArray(buffs)


def druid_base():
    return {
        Stats.SPELL_CRIT: 0.0185
    }


class DruidCharacter(Character):
    def __init__(self, stats, talents: Talents, buffs: StatsModifierArray, level=70):
        self._level = level
        self._talents = talents
        self._buffs = buffs
        self._base_stats = dict()
        base = druid_base()
        for stat in Stats.all_stats():
            self._base_stats[stat] = stats.get(stat, 0) + base.get(stat, 0)
        self._effects = StatsModifierArray.merge(self._talents.buff_array, self._buffs, druid_stats())

    @property
    def level(self):
        return self._level

    @property
    def talents(self):
        return self._talents

    @property
    def buffs(self):
        return self._buffs

    @property
    def effects(self):
        return self._effects

    @property
    def base_stats(self):
        return self._base_stats


class BuffedCharacter(Character):
    def __init__(self, character, buffs):
        self._character = character
        self._other_buffs = buffs
        self._merged_buffs = StatsModifierArray.merge(buffs, self._character.effects)

    @property
    def level(self):
        return self._character.level

    @property
    def talents(self):
        return self._character.talents

    @property
    def buffs(self):
        return self.buffs

    @property
    def effects(self):
        return self._merged_buffs

    @property
    def base_stats(self):
        return self._character.base_stats
