import math
from abc import abstractmethod, ABC

from buffs import ALL_STATS_BUFFS, ALL_SPELL_BUFFS
from items import Gear, ALL_ITEMS_GEAR
from statsmodifiers import StatsModifierArray, StatsModifier
from statistics import Stats, linear, BASE_MANA_LOOKUP, linear_params, RATING_FORMULA
from talents import Talents, DruidTalents


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
    def stats_buffs(self):
        """returns a buff array"""
        pass

    @property
    @abstractmethod
    def spell_buffs(self):
        """returns a spell buff array"""
        pass

    @property
    @abstractmethod
    def stats_effects(self):
        """return a buff array taking into account actual buffs and talents buffing the character"""
        pass

    @property
    @abstractmethod
    def spell_effects(self):
        """return a buff array taking into account actual buffs and talents buffing the character spells"""
        pass

    @property
    @abstractmethod
    def gear(self):
        """return the character gear"""
        pass

    @property
    @abstractmethod
    def base_stats(self):
        """Returns a dictionary mapping base stats with their values (base = untalented and unbuffed)
        """
        pass

    def get_stat(self, stat, **context):
        """get buffed and talented stat value"""
        base = self.get_base_stat(stat)
        return self.stats_effects.apply(stat, base, self, **context)

    def get_base_stat(self, stat):
        """get base stat value"""
        return self.base_stats.get(stat, 0)

    def get_formula(self, stat, **context):
        """get full formula for a stat"""
        base = "#Stats.{stat}#".format(stat=Stats.base(stat))
        return self.stats_effects.formula(stat, base, **context)

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
        functions=[lambda char: char.get_stat(Stats.INTELLIGENCE) / ((60 + (0 if char.level <= 0 else (2 * (70 - char.level)))) * 100)],
        formula=["(#Stats.{}# / ((60 + IF(#Character.level#<=60;0;(#Character.level# - 60) * 2)) * 100))".format(Stats.INTELLIGENCE)])
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
    def __init__(self, stats, talents: Talents, stats_buffs: StatsModifierArray, spell_buffs: StatsModifierArray, gear: Gear=None, level=70):
        self._level = level
        self._talents = talents
        self._stats_buffs = stats_buffs
        self._spell_buffs = spell_buffs
        self._gear = gear if gear is not None else Gear([], [])
        self._base_stats = dict()
        base = druid_base()
        for stat in Stats.all_stats():
            self._base_stats[stat] = stats.get(stat, 0) + base.get(stat, 0)
        self._effects = StatsModifierArray.merge(
            self._talents.buff_array, self._stats_buffs, druid_stats(), self._gear.stats_effects)
        self._spell_effects = StatsModifierArray.merge(
            self._gear.spell_effects, self._spell_buffs, self._talents.spell_buff_array)

    @property
    def level(self):
        return self._level

    @property
    def talents(self):
        return self._talents

    @property
    def stats_buffs(self):
        return self._stats_buffs

    @property
    def spell_buffs(self):
        return self._spell_buffs

    @property
    def stats_effects(self):
        return self._effects

    @property
    def spell_effects(self):
        return self._spell_effects

    @property
    def gear(self):
        return self._gear

    @property
    def base_stats(self):
        return self._base_stats


class BuffedCharacter(Character, ABC):
    def __init__(self, character, stats_buffs=None, spell_buffs=None):
        self._character = character
        self._other_stats_buffs = stats_buffs
        self._other_spell_buffs = spell_buffs

        if stats_buffs is not None:
            self._merged_stats_effects = StatsModifierArray.merge(stats_buffs, self._character.stats_effects)
        else:
            self._merged_stats_effects = self._character.stats_effects

        if spell_buffs is not None:
            self._merged_spell_effects = StatsModifierArray.merge(spell_buffs, self._character.spell_effects)
        else:
            self._merged_spell_effects = self._character.spell_effects

    @property
    def level(self):
        return self._character.level

    @property
    def talents(self):
        return self._character.talents

    @property
    def stats_buffs(self):
        return StatsModifierArray.merge(self._character.stats_buffs, self._other_stats_buffs)

    @property
    def spell_buffs(self):
        return StatsModifierArray.merge(self._character.spell_effects, self._other_spell_buffs)

    @property
    def stats_effects(self):
        return self._merged_stats_effects

    @property
    def spell_effects(self):
        return self._merged_spell_effects

    @property
    def gear(self):
        return self._character.gear

    @property
    def base_stats(self):
        return self._character.base_stats


# character with all bonuses
def create_full_druid_character():
    return DruidCharacter(
        dict(),
        talents=DruidTalents({k: v for k, v, _ in DruidTalents.all()}),
        stats_buffs=StatsModifierArray(ALL_STATS_BUFFS.values()),
        spell_buffs=StatsModifierArray(ALL_SPELL_BUFFS.values()),
        gear=ALL_ITEMS_GEAR, level=70)


FULL_DRUID = create_full_druid_character()