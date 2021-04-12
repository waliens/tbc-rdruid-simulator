from abc import abstractmethod

from character import FULL_DRUID
from heal_parts import HealParts
from items import ALL_ITEMS_GEAR
from statistics import Stats
from talents import DruidTalents

HEAL_GENERIC_FORMULA = "(({base} + {coef} * {bh}) * {gift})"
HOT_GENERIC_FORMULA = "({} / {{ticks}})".format(HEAL_GENERIC_FORMULA)


class SpellCoefficientPolicy(object):
    @abstractmethod
    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        pass

    @property
    @abstractmethod
    def formula(self):
        pass


class Under20CoefficientPolicy(SpellCoefficientPolicy):
    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        return min(1, 1 - (20 - spell.level) * 0.0375)

    @property
    def formula(self):
        return "MIN(1; 1-(20 - #Spell.level#) * 0.0375)"


class DownrankCoefficientPolicy(SpellCoefficientPolicy):
    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        return min(1, (spell.level + 11) / character.level)

    @property
    def formula(self):
        return "MIN(1; (#Spell.level# + 11) / #Character.level#)"


class CastTimePolicy(SpellCoefficientPolicy):
    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        return min(1, cast_time / 3.5) * (1 + empowered)

    @property
    def formula(self):
        return "(MIN(1; #Spell.base_cast_time# / 3.5) * (1 + #Talents.empowered#))"


class HotPolicy(SpellCoefficientPolicy):
    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        return min(1, hot_duration / 15) * (1 + empowered)

    @property
    def formula(self):
        return "(MIN(1; #Spell.base_hot_duration# / 15) * (1 + #Talents.empowered#))"


class DirectCoefficient(SpellCoefficientPolicy):
    def __init__(self):
        self.under20 = Under20CoefficientPolicy()
        self.downrank = DownrankCoefficientPolicy()
        self.cast_policy = CastTimePolicy()

    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        return self.under20.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered) * \
                self.downrank.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered) * \
                self.cast_policy.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered)

    @property
    def formula(self):
        return "({} * {} * {})".format(self.under20.formula, self.downrank.formula, self.cast_policy.formula)


class HoTCoefficient(SpellCoefficientPolicy):
    def __init__(self):
        self.under20 = Under20CoefficientPolicy()
        self.downrank = DownrankCoefficientPolicy()
        self.hot_policy = HotPolicy()

    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        return self.under20.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered) * \
               self.downrank.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered) * \
               self.hot_policy.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered)

    @property
    def formula(self):
        return "({} * {} * {})".format(self.under20.formula, self.downrank.formula,
                                       self.hot_policy.formula)


class HybridCoefficient(SpellCoefficientPolicy):
    """Vanilla"""

    def __init__(self):
        self.under20 = Under20CoefficientPolicy()
        self.downrank = DownrankCoefficientPolicy()
        self.cast_policy = CastTimePolicy()
        self.hot_policy = HotPolicy()

    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        cast_coef = self.cast_policy.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=0)
        hot_coef = self.hot_policy.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=0)
        over_time_portion = hot_coef / (hot_coef + cast_coef)
        direct_portion = 1 - over_time_portion
        under20 = self.under20.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered)
        down = self.downrank.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered)
        return direct_portion * cast_coef * under20 * down, over_time_portion * hot_coef * under20 * down

    @property
    def formula(self):
        cast_coef_formula = self.cast_policy.formula.replace(" * (1 + #Talents.empowered#)", "")
        hot_coef_formula = self.hot_policy.formula.replace(" * (1 + #Talents.empowered#)", "")
        over_time_portion = "({} / ({} + {}))".format(hot_coef_formula, hot_coef_formula, cast_coef_formula)
        direct_portion = "(1 - {})".format(over_time_portion)
        under20 = self.under20.formula
        down = self.downrank.formula
        return "({} * {} * {} * {})".format(direct_portion, self.cast_policy.formula, under20, down), \
               "({} * {} * {} * {})".format(over_time_portion, self.hot_policy.formula, under20, down)


class RegrowthSpellCoefficient(SpellCoefficientPolicy):
    def __init__(self):
        self.under20 = Under20CoefficientPolicy()
        self.downrank = DownrankCoefficientPolicy()

    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        down = self.downrank.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration,
                                             empowered=empowered)
        under = self.under20.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration,
                                             empowered=empowered)
        return down * under * 0.286 * (1 + empowered), down * under * 0.6914 * (1 + empowered)

    @property
    def formula(self):
        under20 = self.under20.formula
        down = self.downrank.formula
        return "({} * {} * 0.286 * (1 + #Talents.empowered#))".format(under20, down), \
               "({} * {} * 0.7 * (1 + #Talents.empowered#))".format(under20, down)


class TranquilityCoefficient(SpellCoefficientPolicy):
    def __init__(self):
        self.under20 = Under20CoefficientPolicy()
        self.down = DownrankCoefficientPolicy()

    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        down = self.down.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered)
        under = self.under20.get_coefficient(spell, character, cast_time=cast_time, hot_duration=hot_duration, empowered=empowered)
        return down * under * 1.1399 * (1 + empowered)

    @property
    def formula(self):
        return "({} * {} * 1.1399 * (1 + #Talents.empowered#))".format(self.under20.formula, self.down.formula)


class LifebloomCoefficient(SpellCoefficientPolicy):
    def get_coefficient(self, spell, character, cast_time=0, hot_duration=0, empowered=0):
        return 0.3422 * (1 + empowered), 0.5194 * (1 + empowered)

    @property
    def formula(self):
        return "(0.3422 * (1 + #Talents.empowered#))", "(0.5194 * (1 + #Talents.empowered#))"


class HealingSpell(object):
    TYPE_HOT = "HOT"
    TYPE_DIRECT = "DIRECT"
    TYPE_HYBRID = "HYBRID"
    TYPE_CHANNELED = "CHANNELED"

    def __init__(self, coef_policy, name, type, rank, mana_cost, lvl, cast_time=0.0, duration=0, tick_period=0, max_stacks=0, direct_first=True):
        self._coef_policy = coef_policy
        self._name = name
        self._rank = rank
        self._level = lvl
        self._type = type
        self._direct_first = direct_first
        self._base_spell_data = {
            HealParts.TICK_PERIOD: tick_period,
            HealParts.N_TICKS: duration // tick_period if tick_period > 0 else 0,
            HealParts.DURATION: duration,
            HealParts.CAST_TIME: cast_time,
            HealParts.MAX_STACKS: max_stacks,  # 0 direct, 1 hot, n stackable hot
            HealParts.MANA_COST: mana_cost
        }

    @abstractmethod
    def get_healing(self, character):
        pass

    @property
    @abstractmethod
    def formula(self):
        pass

    @property
    @abstractmethod
    def coef_formula(self):
        pass

    @property
    def base_data(self):
        return self._base_spell_data

    @property
    def direct_first(self):
        return self._direct_first

    @property
    def coef_policy(self):
        return self._coef_policy

    @property
    def name(self):
        return self._name

    @property
    def cname(self):
        return self.name.lower().replace(" ", "_")

    @property
    def rank(self):
        return self._rank

    @property
    def type(self):
        return self._type

    @property
    def level(self):
        return self._level

    @property
    def base_mana_cost(self):
        return self.base_data[HealParts.MANA_COST]

    @property
    def base_cast_time(self):
        return self.base_data[HealParts.CAST_TIME]

    @property
    def base_duration(self):
        return self.base_data[HealParts.DURATION]

    @property
    def base_n_ticks(self):
        return self.base_data[HealParts.N_TICKS]

    @property
    def base_tick_period(self):
        return self.base_data[HealParts.TICK_PERIOD]

    @property
    def base_max_stacks(self):
        return self.base_data[HealParts.MAX_STACKS]

    def mana_cost(self, character):
        return self.spell_info(HealParts.MANA_COST, character)

    def cast_time(self, character):
        return self.spell_info(HealParts.CAST_TIME, character) / (1 + character.get_stat(Stats.SPELL_HASTE))

    def duration(self, character):
        return self.spell_info(HealParts.DURATION, character)

    def n_ticks(self, character):
        return self.duration(character) // self.tick_period(character)

    def tick_period(self, character):
        return self.spell_info(HealParts.TICK_PERIOD, character)

    def max_stacks(self, character):
        return self.spell_info(HealParts.MAX_STACKS, character)

    def spell_info(self, info, character, **context):
        return character.gear.apply_spell_effect(self.name, info, self.base_data[info], character, **context)

    def spell_info_formula(self, info, **context):
        if info == HealParts.N_TICKS:
            return "QUOTIENT(#{spell}.{duration}#; #{spell}.{period}#)".format(
                spell=self.identifier, duration=HealParts.DURATION, period=HealParts.TICK_PERIOD)
        elif info == HealParts.CAST_TIME:
            base_formula = "((#{spell}.base_{time}#) / (1 + #Stats.{haste}#))".format(spell=self.identifier, time=HealParts.CAST_TIME, haste=Stats.SPELL_HASTE)
        else:
            base_formula = "#{}.base_{}#".format(self.identifier, info)
        return FULL_DRUID.spell_effects.formula((self.name, info), base_formula, **context)

    @property
    def identifier(self):
        return self.name + "-" + str(self.rank)

    def __repr__(self):
        return self.identifier


class HealingTouch(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, avg_heal, cast_time):
        super().__init__(coef_policy, "healing_touch", HealingSpell.TYPE_DIRECT, rank, mana_cost, lvl, cast_time=cast_time)
        self.avg_heal = avg_heal

    def get_healing(self, character):
        bh = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealParts.DIRECT)
        coef = self._get_spell_coefficient(character, self.coef_policy)
        gift = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02
        direct_heal = (self.avg_heal + coef * bh) * gift
        return character.gear.apply_spell_effect(self.name, HealParts.FINAL_DIRECT, direct_heal, character)

    @property
    def formula(self):
        from character import FULL_DRUID
        gift_formula = "(1 + #Talents.{}# * 0.02)".format(DruidTalents.GIFT_OF_NATURE[0])
        stat_formula = "#Stats.{}#".format(Stats.BONUS_HEALING)
        bh = FULL_DRUID.stats_effects.formula(Stats.BONUS_HEALING, stat_formula, spell_name=self.name, spell_part=HealParts.DIRECT)
        formula = HEAL_GENERIC_FORMULA.format(
            base="#{}.base_avg_heal#".format(self.identifier),
            coef="#{}.coef#".format(self.identifier),
            bh=bh, gift=gift_formula
        )
        return FULL_DRUID.gear.spell_effects.formula((self.name, HealParts.FINAL_DIRECT), formula)

    @property
    def coef_formula(self):
        return self.coef_policy.formula \
            .replace("#Talents.empowered#", "0.1 * #Talents.{}#".format(DruidTalents.EMPOWERED_TOUCH[0])) \
            .replace("Spell.", self.identifier + ".")

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, self.cast_time,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_TOUCH) * 0.1)

    def spell_info_formula(self, info, **context):
        formula = super().spell_info_formula(info, **context)
        if info == HealParts.CAST_TIME:
            base = "#{spell}.base_{time}#".format(spell=self.identifier, time=HealParts.CAST_TIME)
            formula = formula.replace(
                "({base})".format(base=base),
                "({base} - 0.1 * #Talents.{nat}#)".format(base=base, nat=DruidTalents.NATURALIST[0]))
        return formula

    def cast_time(self, character):
        haste = character.get_stat(Stats.SPELL_HASTE)
        naturalist = character.talents.get(DruidTalents.NATURALIST)
        return (self.base_cast_time - 0.1 * naturalist) / (1 + haste)


class Rejuvenation(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, hot_heal, duration, tick_period=3):
        super().__init__(coef_policy, "rejuvenation", HealingSpell.TYPE_HOT, rank, mana_cost, lvl, tick_period=tick_period, duration=duration)
        self.hot_heal = hot_heal

    @property
    def hot_heal_tick(self):
        return self.hot_heal / self.base_n_ticks

    def get_healing(self, character):
        bh = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealParts.TICK)
        coef = self._get_spell_coefficient(character, self.coef_policy)
        improved = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02 + character.talents.get(DruidTalents.IMPROVED_REJUVENATION) * 0.05
        hot_heal = (self.hot_heal_tick + bh * coef / self.base_n_ticks) * improved
        return character.gear.apply_spell_effect(self.name, HealParts.FINAL_TICK, hot_heal, character)

    @property
    def formula(self):
        from character import FULL_DRUID
        gift_improved_formula = "(1 + #Talents.{}# * 0.02 + #Talents.{}# * 0.05)".format(
            DruidTalents.GIFT_OF_NATURE[0], DruidTalents.IMPROVED_REJUVENATION[0])
        stat_formula = "#Stats.{}#".format(Stats.BONUS_HEALING)
        bh = FULL_DRUID.stats_effects.formula(Stats.BONUS_HEALING, stat_formula, spell_name=self.name, spell_part=HealParts.TICK)
        formula = HOT_GENERIC_FORMULA.format(
            base="#{}.base_hot_total#".format(self.identifier),
            bh=bh, gift=gift_improved_formula,
            coef="#{}.coef#".format(self.identifier),
            ticks=self.base_n_ticks)
        return FULL_DRUID.gear.spell_effects.formula((self.name, HealParts.FINAL_TICK), formula)

    @property
    def coef_formula(self):
        return self.coef_policy.formula \
            .replace("#Talents.empowered#", "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])) \
            .replace("Spell.", self.identifier + ".")

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, hot_duration=self.base_duration,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_REJUVENATION) * 0.04)


class Regrowth(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, avg_direct_heal, hot_heal, cast_time, tick_period, duration):
        super().__init__(coef_policy, "regrowth", HealingSpell.TYPE_HYBRID, rank, mana_cost, lvl,
                         cast_time=cast_time, duration=duration, tick_period=tick_period, max_stacks=1)
        self.avg_direct_heal = avg_direct_heal
        self.hot_heal = hot_heal

    @property
    def hot_heal_tick(self):
        return self.hot_heal / self.base_n_ticks

    def get_healing(self, character):
        bh_direct = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.TYPE_DIRECT)
        bh_hot = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.TYPE_HOT)
        coef_direct, coef_hot = self._get_spell_coefficient(character, self.coef_policy)
        gift = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02
        direct_heal = (self.avg_direct_heal + coef_direct * bh_direct) * gift
        hot_heal = (self.hot_heal_tick + bh_hot * coef_hot / self.base_n_ticks) * gift
        return character.gear.apply_spell_effect(self.name, HealParts.FINAL_DIRECT, direct_heal, character), \
            character.gear.apply_spell_effect(self.name, HealParts.FINAL_TICK, hot_heal, character)

    @property
    def formula(self):
        from character import FULL_DRUID
        gift_formula = "(1 + #Talents.{}# * 0.02)".format(DruidTalents.GIFT_OF_NATURE[0])
        stat_formula = "#Stats.{}#".format(Stats.BONUS_HEALING)
        bh_hot = FULL_DRUID.stats_effects.formula(Stats.BONUS_HEALING, stat_formula, spell_name=self.name, spell_part=HealParts.TICK)
        bh_direct = FULL_DRUID.stats_effects.formula(Stats.BONUS_HEALING, stat_formula, spell_name=self.name, spell_part=HealParts.DIRECT)
        direct_formula = HEAL_GENERIC_FORMULA.format(
            base="#{}.base_avg_direct_heal#".format(self.identifier),
            bh=bh_direct,
            gift=gift_formula,
            coef="#{}.direct_coef#".format(self.identifier)
        )
        hot_formula = HOT_GENERIC_FORMULA.format(
            base="#{}.base_hot_total#".format(self.identifier),
            bh=bh_hot,
            gift=gift_formula,
            coef="#{}.hot_coef#".format(self.identifier),
            ticks=self.base_n_ticks
        )
        return FULL_DRUID.gear.spell_effects.formula((self.name, HealParts.FINAL_DIRECT), direct_formula), \
            FULL_DRUID.gear.spell_effects.formula((self.name, HealParts.FINAL_TICK), hot_formula)

    @property
    def coef_formula(self):
        coef_direct_formula, coef_hot_formula = self.coef_policy.formula
        return coef_direct_formula.replace("#Talents.empowered#", "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])).replace("Spell.", self.identifier + "."), \
               coef_hot_formula.replace("#Talents.empowered#", "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])).replace("Spell.", self.identifier + ".")

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, self.cast_time, self.base_duration,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_REJUVENATION) * 0.04)


class Lifebloom(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, direct_heal, hot_heal, tick_period, duration):
        super().__init__(coef_policy, "lifebloom", HealingSpell.TYPE_HYBRID, rank, mana_cost, lvl,
                         duration=duration, tick_period=tick_period, max_stacks=3, direct_first=False)
        self.direct_heal = direct_heal
        self.hot_heal = hot_heal

    @property
    def hot_heal_tick(self):
        return self.hot_heal / self.base_n_ticks

    def get_healing(self, character):
        bh_direct = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealParts.DIRECT)
        bh_hot = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealParts.TICK)
        coef_direct, coef_hot = self._get_spell_coefficient(character, self.coef_policy)
        gift = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02
        direct_heal = (self.direct_heal + coef_direct * bh_direct) * gift
        hot_heal = (self.hot_heal_tick + bh_hot * coef_hot / self.base_n_ticks) * gift
        return character.gear.apply_spell_effect(self.name, HealParts.FINAL_DIRECT, direct_heal, character), \
            character.gear.apply_spell_effect(self.name, HealParts.FINAL_TICK, hot_heal, character)

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, self.cast_time, self.base_duration,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_REJUVENATION) * 0.04)

    @property
    def formula(self):
        from character import FULL_DRUID
        gift_formula = "(1 + #Talents.{}# * 0.02)".format(DruidTalents.GIFT_OF_NATURE[0])
        stat_formula = "#Stats.{}#".format(Stats.BONUS_HEALING)
        bh_hot = FULL_DRUID.stats_effects.formula(Stats.BONUS_HEALING, stat_formula, spell_name=self.name, spell_part=HealParts.TICK)
        bh_direct = FULL_DRUID.stats_effects.formula(Stats.BONUS_HEALING, stat_formula, spell_name=self.name, spell_part=HealParts.DIRECT)
        direct_formula = HEAL_GENERIC_FORMULA.format(
            base="#{}.base_direct_heal#".format(self.identifier),
            bh=bh_direct, gift=gift_formula,
            coef="#{}.direct_coef#".format(self.identifier)
        )
        hot_formula = HOT_GENERIC_FORMULA.format(
            base="#{}.base_hot_total#".format(self.identifier),
            bh=bh_hot, gift=gift_formula,
            coef="#{}.hot_coef#".format(self.identifier),
            ticks=self.base_n_ticks
        )
        return FULL_DRUID.gear.spell_effects.formula((self.name, HealParts.FINAL_DIRECT), direct_formula), \
            FULL_DRUID.gear.spell_effects.formula((self.name, HealParts.FINAL_TICK), hot_formula)

    @property
    def coef_formula(self):
        coef_direct_formula, coef_hot_formula = self.coef_policy.formula
        return coef_direct_formula.replace("#Talents.empowered#",
                                           "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])).replace("Spell.", self.identifier + "."), \
               coef_hot_formula.replace("#Talents.empowered#",
                                        "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])).replace("Spell.", self.identifier + ".")


class Tranquility(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, hot_heal, duration, tick_period):
        super().__init__(coef_policy, "tranquility", HealingSpell.TYPE_CHANNELED, rank, mana_cost, lvl,
                         duration=duration, tick_period=tick_period)
        self.hot_heal = hot_heal

    @property
    def hot_heal_tick(self):
        return self.hot_heal / self.base_n_ticks

    def get_healing(self, character):
        bh = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealParts.TICK)
        coef = self._get_spell_coefficient(character, self.coef_policy)
        improved = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02
        hot_heal = (self.hot_heal_tick + bh * coef / self.base_n_ticks) * improved
        return character.gear.apply_spell_effect(self.name, HealParts.FINAL_TICK, hot_heal, character)

    @property
    def formula(self):
        from character import FULL_DRUID
        gift_improved_formula = "(1 + #Talents.{}# * 0.02)".format(DruidTalents.GIFT_OF_NATURE[0])
        stat_formula = "#Stats.{}#".format(Stats.BONUS_HEALING)
        bh_hot = FULL_DRUID.stats_effects.formula(Stats.BONUS_HEALING, stat_formula, spell_name=self.name, spell_part=HealParts.TICK)
        formula = HOT_GENERIC_FORMULA.format(
            base="#{}.base_hot_total#".format(self.identifier),
            bh=bh_hot, gift=gift_improved_formula,
            coef="#{}.coef#".format(self.identifier),
            ticks=self.base_n_ticks
        )
        return FULL_DRUID.spell_effects.formula((self.name, HealParts.FINAL_TICK), formula)

    @property
    def coef_formula(self):
        return self.coef_policy.formula \
            .replace("#Talents.empowered#", "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])) \
            .replace("Spell.", self.identifier + ".")

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, hot_duration=self.base_duration,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_REJUVENATION) * 0.04)


DIRECT_HEAL_COEF = DirectCoefficient()
HOT_HEAL_COEF = HoTCoefficient()
REGROWTH_COEF = RegrowthSpellCoefficient()
LIFEBLOOM_COEF = LifebloomCoefficient()
TRANQUILITY_COEF = TranquilityCoefficient()

LIFEBLOOM = [
    Lifebloom(LIFEBLOOM_COEF, rank=1, mana_cost=220, lvl=64, direct_heal=600, hot_heal=39 * 7, tick_period=1, duration=7)
]

HEALING_TOUCH = [
    HealingTouch(DIRECT_HEAL_COEF, rank=1, mana_cost=25, lvl=1, avg_heal=47, cast_time=1.5),  # min_heal=37, max_heal=52
    HealingTouch(DIRECT_HEAL_COEF, rank=2, mana_cost=55, lvl=8, avg_heal=106, cast_time=2),  # min_heal=88, max_heal=113
    HealingTouch(DIRECT_HEAL_COEF, rank=3, mana_cost=110, lvl=14, avg_heal=228, cast_time=2.5),  # min_heal=195, max_heal=244
    HealingTouch(DIRECT_HEAL_COEF, rank=4, mana_cost=185, lvl=20, avg_heal=417, cast_time=3),  # min_heal=363, max_heal=446
    HealingTouch(DIRECT_HEAL_COEF, rank=5, mana_cost=270, lvl=26, avg_heal=650, cast_time=3.5),  # min_heal=572, max_heal=695
    HealingTouch(DIRECT_HEAL_COEF, rank=6, mana_cost=335, lvl=32, avg_heal=838, cast_time=3.5),  # min_heal=742, max_heal=895
    HealingTouch(DIRECT_HEAL_COEF, rank=7, mana_cost=405, lvl=38, avg_heal=1050, cast_time=3.5),  # min_heal=936, max_heal=1121
    HealingTouch(DIRECT_HEAL_COEF, rank=8, mana_cost=495, lvl=44, avg_heal=1339, cast_time=3.5),  # min_heal=1199, max_heal=1428
    HealingTouch(DIRECT_HEAL_COEF, rank=9, mana_cost=600, lvl=50, avg_heal=1685, cast_time=3.5),  # min_heal=1516, max_heal=1797
    HealingTouch(DIRECT_HEAL_COEF, rank=10, mana_cost=720, lvl=56, avg_heal=2086, cast_time=3.5),  # min_heal=1890, max_heal=2231
    HealingTouch(DIRECT_HEAL_COEF, rank=11, mana_cost=800, lvl=60, avg_heal=2472, cast_time=3.5),  # min_heal=2267, max_heal=2678
    HealingTouch(DIRECT_HEAL_COEF, rank=12, mana_cost=820, lvl=62, avg_heal=2577, cast_time=3.5),  # min_heal=2364, max_heal=2791
    HealingTouch(DIRECT_HEAL_COEF, rank=13, mana_cost=935, lvl=69, avg_heal=2952, cast_time=3.5)  # min_heal=2707, max_heal=3198
]

REJUVENATION = [
    Rejuvenation(HOT_HEAL_COEF, rank=1, mana_cost=25, tick_period=3, duration=12, lvl=4, hot_heal=32),
    Rejuvenation(HOT_HEAL_COEF, rank=2, mana_cost=40, tick_period=3, duration=12, lvl=10, hot_heal=56),
    Rejuvenation(HOT_HEAL_COEF, rank=3, mana_cost=75, tick_period=3, duration=12, lvl=16, hot_heal=116),
    Rejuvenation(HOT_HEAL_COEF, rank=4, mana_cost=105, tick_period=3, duration=12, lvl=22, hot_heal=180),
    Rejuvenation(HOT_HEAL_COEF, rank=5, mana_cost=135, tick_period=3, duration=12, lvl=28, hot_heal=244),
    Rejuvenation(HOT_HEAL_COEF, rank=6, mana_cost=160, tick_period=3, duration=12, lvl=34, hot_heal=304),
    Rejuvenation(HOT_HEAL_COEF, rank=7, mana_cost=195, tick_period=3, duration=12, lvl=40, hot_heal=388),
    Rejuvenation(HOT_HEAL_COEF, rank=8, mana_cost=235, tick_period=3, duration=12, lvl=46, hot_heal=488),
    Rejuvenation(HOT_HEAL_COEF, rank=9, mana_cost=280, tick_period=3, duration=12, lvl=52, hot_heal=608),
    Rejuvenation(HOT_HEAL_COEF, rank=10, mana_cost=335, tick_period=3, duration=12, lvl=58, hot_heal=756),
    Rejuvenation(HOT_HEAL_COEF, rank=11, mana_cost=360, tick_period=3, duration=12, lvl=60, hot_heal=888),
    Rejuvenation(HOT_HEAL_COEF, rank=12, mana_cost=370, tick_period=3, duration=12, lvl=63, hot_heal=932),
    Rejuvenation(HOT_HEAL_COEF, rank=13, mana_cost=415, tick_period=3, duration=12, lvl=69, hot_heal=1060)
]

REGROWTH = [
    Regrowth(REGROWTH_COEF, rank=1, lvl=12, mana_cost=80, cast_time=2, tick_period=3, duration=21, avg_direct_heal=100, hot_heal=98),  # min_direct_heal=93, max_direct_heal=107,
    Regrowth(REGROWTH_COEF, rank=2, lvl=18, mana_cost=135, cast_time=2, tick_period=3, duration=21, avg_direct_heal=188, hot_heal=175),  # min_direct_heal=175, max_direct_heal=201,
    Regrowth(REGROWTH_COEF, rank=3, lvl=24, mana_cost=185, cast_time=2, tick_period=3, duration=21, avg_direct_heal=272, hot_heal=259),  # min_direct_heal=255, max_direct_heal=289,
    Regrowth(REGROWTH_COEF, rank=4, lvl=30, mana_cost=230, cast_time=2, tick_period=3, duration=21, avg_direct_heal=357, hot_heal=343),  # min_direct_heal=336, max_direct_heal=378,
    Regrowth(REGROWTH_COEF, rank=5, lvl=36, mana_cost=275, cast_time=2, tick_period=3, duration=21, avg_direct_heal=451, hot_heal=427),  # min_direct_heal=424, max_direct_heal=478,
    Regrowth(REGROWTH_COEF, rank=6, lvl=42, mana_cost=335, cast_time=2, tick_period=3, duration=21, avg_direct_heal=566, hot_heal=546),  # min_direct_heal=535, max_direct_heal=597,
    Regrowth(REGROWTH_COEF, rank=7, lvl=48, mana_cost=405, cast_time=2, tick_period=3, duration=21, avg_direct_heal=711, hot_heal=686),  # min_direct_heal=672, max_direct_heal=750,
    Regrowth(REGROWTH_COEF, rank=8, lvl=54, mana_cost=485, cast_time=2, tick_period=3, duration=21, avg_direct_heal=887, hot_heal=861),  # min_direct_heal=839, max_direct_heal=935,
    Regrowth(REGROWTH_COEF, rank=9, lvl=60, mana_cost=575, cast_time=2, tick_period=3, duration=21, avg_direct_heal=1061, hot_heal=1064),  # min_direct_heal=1003, max_direct_heal=1119,
    Regrowth(REGROWTH_COEF, rank=10, lvl=65, mana_cost=675, cast_time=2, tick_period=3, duration=21, avg_direct_heal=1285, hot_heal=1274)  # min_direct_heal=1215, max_direct_heal=1356,
]

TRANQUILITY = [
    Tranquility(TRANQUILITY_COEF, rank=1, mana_cost=525, lvl=30, hot_heal=4 * 350, tick_period=2, duration=8),
    Tranquility(TRANQUILITY_COEF, rank=2, mana_cost=705, lvl=40, hot_heal=4 * 514, tick_period=2, duration=8),
    Tranquility(TRANQUILITY_COEF, rank=3, mana_cost=975, lvl=50, hot_heal=4 * 764, tick_period=2, duration=8),
    Tranquility(TRANQUILITY_COEF, rank=4, mana_cost=1295, lvl=60, hot_heal=4 * 1096, tick_period=2, duration=8),
    Tranquility(TRANQUILITY_COEF, rank=5, mana_cost=1650, lvl=70, hot_heal=4 * 1517, tick_period=2, duration=8)
]

