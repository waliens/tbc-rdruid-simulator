from abc import abstractmethod

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
        return 0.3422 * (1 + empowered), 0.518 * (1 + empowered)

    @property
    def formula(self):
        return "(0.3422 * (1 + #Talents.empowered#))", "(0.518 * (1 + #Talents.empowered#))"


class HealingSpell(object):
    TYPE_HOT = "HOT"
    TYPE_DIRECT = "DIRECT"
    TYPE_HYBRID = "HYBRID"
    TYPE_CHANNELED = "CHANNELED"

    HEAL_TICK = "tick"
    HEAL_DIRECT = "direct"
    HEAL_CAST_TIME = "cast_time"
    HEAL_MANA_COST = "mana_cost"
    HEAL_DURATION = "duration"

    def __init__(self, coef_policy, name, type, rank, mana_cost, lvl, cast_time=0.0, duration=0.0, ticks=0, max_stacks=0, direct_first=True):
        self._coef_policy = coef_policy
        self._mana_cost = mana_cost
        self._name = name
        self._rank = rank
        self._level = lvl
        self._cast_time = cast_time
        self._duration = duration
        self._type = type
        self._ticks = ticks
        self._max_stacks = max_stacks  # 0 direct, 1 hot, n stackable hot
        self._direct_first = direct_first

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

    @abstractmethod
    def get_effective_cast_time(self, character):
        pass

    @property
    def direct_first(self):
        return self._direct_first

    @property
    def coef_policy(self):
        return self._coef_policy

    @property
    def mana_cost(self):
        return self._mana_cost

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
    def level(self):
        return self._level

    @property
    def cast_time(self):
        return self._cast_time

    @property
    def duration(self):
        return self._duration

    @property
    def type(self):
        return self._type

    @property
    def ticks(self):
        return self._ticks

    @property
    def tick_period(self):
        return self.duration / self.ticks if self.ticks > 0 else 0

    @property
    def identifier(self):
        return self.name + "-" + str(self.rank)

    @property
    def max_stacks(self):
        return self._max_stacks


class HealingTouch(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, avg_heal, cast_time):
        super().__init__(coef_policy, "Healing touch", HealingSpell.TYPE_DIRECT, rank, mana_cost, lvl, cast_time=cast_time)

        self.avg_heal = avg_heal

    def get_healing(self, character):
        bh = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.HEAL_DIRECT)
        coef = self._get_spell_coefficient(character, self.coef_policy)
        gift = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02
        return (self.avg_heal + coef * bh) * gift

    @property
    def formula(self):
        gift_formula = "(1 + #Talents.{}# * 0.02)".format(DruidTalents.GIFT_OF_NATURE[0])
        formula = HEAL_GENERIC_FORMULA.format(
            base="#{}.base_avg_heal#".format(self.identifier),
            coef="#{}.coef#".format(self.identifier),
            bh="#Stats.{}#".format(Stats.BONUS_HEALING),
            gift=gift_formula
        )
        return formula

    @property
    def coef_formula(self):
        return self.coef_policy.formula \
            .replace("#Talents.empowered#", "0.1 * #Talents.{}#".format(DruidTalents.EMPOWERED_TOUCH[0])) \
            .replace("Spell.", self.identifier + ".")

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, self.cast_time,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_TOUCH) * 0.1)

    def __repr__(self):
        return "{}(type={}, rank={}, level={}, cost={}, cast={}s, havg={})".format(
            self.name, self.type, self.rank, self.level, self.mana_cost, self.cast_time, self.avg_heal)

    def get_effective_cast_time(self, character):
        haste = character.get_stat(Stats.SPELL_HASTE)
        naturalist = character.talents.get(DruidTalents.NATURALIST)
        return (self.cast_time - 0.1 * naturalist) / (1 + haste)


class Rejuvenation(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, hot_heal, duration):
        super().__init__(coef_policy, "Rejuvenation", HealingSpell.TYPE_HOT, rank, mana_cost, lvl, duration=duration, ticks=4)
        self.hot_heal = hot_heal

    def get_healing(self, character):
        bh = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.HEAL_TICK)
        coef = self._get_spell_coefficient(character, self.coef_policy)
        improved = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02 + character.talents.get(DruidTalents.IMPROVED_REJUVENATION) * 0.05
        return (self.hot_heal + bh * coef) * improved / self.ticks

    @property
    def formula(self):
        gift_improved_formula = "(1 + #Talents.{}# * 0.02 + #Talents.{}# * 0.05)".format(
            DruidTalents.GIFT_OF_NATURE[0], DruidTalents.IMPROVED_REJUVENATION[0])
        return HOT_GENERIC_FORMULA.format(
            base="#{}.base_hot_total#".format(self.identifier),
            bh="#Stats.{}#".format(Stats.BONUS_HEALING),
            gift=gift_improved_formula,
            coef="#{}.coef#".format(self.identifier),
            ticks=self.ticks)

    @property
    def coef_formula(self):
        return self.coef_policy.formula \
            .replace("#Talents.empowered#", "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])) \
            .replace("Spell.", self.identifier + ".")

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, hot_duration=self.duration,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_REJUVENATION) * 0.04)

    def __repr__(self):
        return "{}(type={}, rank={}, level={}, cost={}, duration={}s, hot_full={}, hot_tick={})".format(
            self.name, self.type, self.rank, self.level, self.mana_cost, self.duration, self.hot_heal,
            self.hot_heal / self.ticks)

    def get_effective_cast_time(self, character):
        return self.cast_time


class Regrowth(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, avg_direct_heal, hot_heal, cast_time, duration):
        super().__init__(coef_policy, "Regrowth", HealingSpell.TYPE_HYBRID, rank, mana_cost, lvl, cast_time=cast_time, duration=duration, ticks=7, max_stacks=1)
        self.avg_direct_heal = avg_direct_heal
        self.hot_heal = hot_heal

    def get_healing(self, character):
        bh_direct = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.TYPE_DIRECT)
        bh_hot = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.TYPE_HOT)
        coef_direct, coef_hot = self._get_spell_coefficient(character, self.coef_policy)
        gift = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02
        return (self.avg_direct_heal + coef_direct * bh_direct) * gift, \
               (self.hot_heal + bh_hot * coef_hot) * gift / self.ticks

    @property
    def formula(self):
        gift_formula = "(1 + #Talents.{}# * 0.02)".format(DruidTalents.GIFT_OF_NATURE[0])
        direct_formula = HEAL_GENERIC_FORMULA.format(
            base="#{}.base_avg_direct_heal#".format(self.identifier),
            bh="#Stats.{}#".format(Stats.BONUS_HEALING),
            gift=gift_formula,
            coef="#{}.direct_coef#".format(self.identifier)
        )
        hot_formula = HOT_GENERIC_FORMULA.format(
            base="#{}.base_hot_total#".format(self.identifier),
            bh="#Stats.{}#".format(Stats.BONUS_HEALING),
            gift=gift_formula,
            coef="#{}.hot_coef#".format(self.identifier),
            ticks=self.ticks
        )
        return direct_formula, hot_formula

    @property
    def coef_formula(self):
        coef_direct_formula, coef_hot_formula = self.coef_policy.formula
        return coef_direct_formula.replace("#Talents.empowered#", "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])).replace("Spell.", self.identifier + "."), \
               coef_hot_formula.replace("#Talents.empowered#", "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])).replace("Spell.", self.identifier + ".")

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, self.cast_time, self.duration,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_REJUVENATION) * 0.04)

    def __repr__(self):
        return "{}(type={}, rank={}, level={}, cost={}, cast={}s, duration={}s, avg_heal={}, hot_full={}, hot_tick={})".format(
            self.name, self.type, self.rank, self.level, self.mana_cost, self.cast_time, self.duration,
            self.avg_direct_heal, self.hot_heal, int(self.hot_heal / self.ticks))

    def get_effective_cast_time(self, character):
        haste = character.get_stat(Stats.SPELL_HASTE)
        return self.cast_time / (1 + haste)


class Lifebloom(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, direct_heal, hot_heal, duration):
        super().__init__(coef_policy, "Lifebloom", HealingSpell.TYPE_HYBRID, rank, mana_cost, lvl,
                         duration=duration, ticks=7, max_stacks=3, direct_first=False)
        self.direct_heal = direct_heal
        self.hot_heal = hot_heal

    def get_healing(self, character):
        bh_direct = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.HEAL_DIRECT)
        bh_hot = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.HEAL_TICK)
        coef_direct, coef_hot = self._get_spell_coefficient(character, self.coef_policy)
        gift = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02
        direct_heal = (self.direct_heal + coef_direct * bh_direct) * gift
        return direct_heal, (self.hot_heal + bh_hot * coef_hot) * gift / self.ticks

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, self.cast_time, self.duration,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_REJUVENATION) * 0.04)

    @property
    def formula(self):
        gift_formula = "(1 + #Talents.{}# * 0.02)".format(DruidTalents.GIFT_OF_NATURE[0])
        direct_formula = HEAL_GENERIC_FORMULA.format(
            base="#{}.base_direct_heal#".format(self.identifier),
            bh="#Stats.{}#".format(Stats.BONUS_HEALING),
            gift=gift_formula,
            coef="#{}.direct_coef#".format(self.identifier)
        )
        hot_formula = HOT_GENERIC_FORMULA.format(
            base="#{}.base_hot_total#".format(self.identifier),
            bh="#Stats.{}#".format(Stats.BONUS_HEALING),
            gift=gift_formula,
            coef="#{}.hot_coef#".format(self.identifier),
            ticks=self.ticks
        )
        return direct_formula, hot_formula

    @property
    def coef_formula(self):
        coef_direct_formula, coef_hot_formula = self.coef_policy.formula
        return coef_direct_formula.replace("#Talents.empowered#",
                                           "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])).replace(
            "Spell.", self.identifier + "."), \
               coef_hot_formula.replace("#Talents.empowered#",
                                        "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])).replace(
                   "Spell.", self.identifier + ".")

    def __repr__(self):
        return "{}(type={}, rank={}, level={}, cost={}, duration={}s, direct_heal={}, hot_full={}, hot_tick={})".format(
            self.name, self.type, self.rank, self.level, self.mana_cost, self.duration, self.direct_heal, self.hot_heal,
            int(self.hot_heal / self.ticks))

    def get_effective_cast_time(self, character):
        return self.cast_time


class Tranquility(HealingSpell):
    def __init__(self, coef_policy, rank, mana_cost, lvl, hot_heal, duration):
        super().__init__(coef_policy, "Tranquility", HealingSpell.TYPE_CHANNELED, rank, mana_cost, lvl,
                         duration=duration, ticks=4)
        self.hot_heal = hot_heal

    def get_healing(self, character):
        bh = character.get_stat(Stats.BONUS_HEALING, spell_name=self.cname, spell_part=HealingSpell.HEAL_TICK)
        coef = self._get_spell_coefficient(character, self.coef_policy)
        improved = 1 + character.talents.get(DruidTalents.GIFT_OF_NATURE) * 0.02
        return (self.hot_heal + bh * coef) * improved / self.ticks

    @property
    def formula(self):
        gift_improved_formula = "(1 + #Talents.{}# * 0.02)".format(DruidTalents.GIFT_OF_NATURE[0])
        return HOT_GENERIC_FORMULA.format(
            base="#{}.base_hot_total#".format(self.identifier),
            bh="#Stats.{}#".format(Stats.BONUS_HEALING),
            gift=gift_improved_formula,
            coef="#{}.coef#".format(self.identifier),
            ticks=self.ticks
        )

    @property
    def coef_formula(self):
        return self.coef_policy.formula \
            .replace("#Talents.empowered#", "0.04 * #Talents.{}#".format(DruidTalents.EMPOWERED_REJUVENATION[0])) \
            .replace("Spell.", self.identifier + ".")

    def _get_spell_coefficient(self, character, coef_policy):
        return coef_policy.get_coefficient(self, character, hot_duration=self.duration,
                                           empowered=character.talents.get(DruidTalents.EMPOWERED_REJUVENATION) * 0.04)

    def get_effective_cast_time(self, character):
        return 0


DIRECT_HEAL_COEF = DirectCoefficient()
HOT_HEAL_COEF = HoTCoefficient()
REGROWTH_COEF = RegrowthSpellCoefficient()
LIFEBLOOM_COEF = LifebloomCoefficient()
TRANQUILITY_COEF = TranquilityCoefficient()

LIFEBLOOM = [
    Lifebloom(LIFEBLOOM_COEF, rank=1, mana_cost=220, lvl=64, direct_heal=600, hot_heal=39 * 7, duration=7)
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
    Rejuvenation(HOT_HEAL_COEF, rank=1, mana_cost=25, duration=12, lvl=4, hot_heal=32),
    Rejuvenation(HOT_HEAL_COEF, rank=2, mana_cost=40, duration=12, lvl=10, hot_heal=56),
    Rejuvenation(HOT_HEAL_COEF, rank=3, mana_cost=75, duration=12, lvl=16, hot_heal=116),
    Rejuvenation(HOT_HEAL_COEF, rank=4, mana_cost=105, duration=12, lvl=22, hot_heal=180),
    Rejuvenation(HOT_HEAL_COEF, rank=5, mana_cost=135, duration=12, lvl=28, hot_heal=244),
    Rejuvenation(HOT_HEAL_COEF, rank=6, mana_cost=160, duration=12, lvl=34, hot_heal=304),
    Rejuvenation(HOT_HEAL_COEF, rank=7, mana_cost=195, duration=12, lvl=40, hot_heal=388),
    Rejuvenation(HOT_HEAL_COEF, rank=8, mana_cost=235, duration=12, lvl=46, hot_heal=488),
    Rejuvenation(HOT_HEAL_COEF, rank=9, mana_cost=280, duration=12, lvl=52, hot_heal=608),
    Rejuvenation(HOT_HEAL_COEF, rank=10, mana_cost=335, duration=12, lvl=58, hot_heal=756),
    Rejuvenation(HOT_HEAL_COEF, rank=11, mana_cost=360, duration=12, lvl=60, hot_heal=888),
    Rejuvenation(HOT_HEAL_COEF, rank=12, mana_cost=370, duration=12, lvl=63, hot_heal=932),
    Rejuvenation(HOT_HEAL_COEF, rank=13, mana_cost=415, duration=12, lvl=69, hot_heal=1060)
]

REGROWTH = [
    Regrowth(REGROWTH_COEF, rank=1, lvl=12, mana_cost=80, cast_time=2, duration=21, avg_direct_heal=100, hot_heal=98),  # min_direct_heal=93, max_direct_heal=107,
    Regrowth(REGROWTH_COEF, rank=2, lvl=18, mana_cost=135, cast_time=2, duration=21, avg_direct_heal=188, hot_heal=175),  # min_direct_heal=175, max_direct_heal=201,
    Regrowth(REGROWTH_COEF, rank=3, lvl=24, mana_cost=185, cast_time=2, duration=21, avg_direct_heal=272, hot_heal=259),  # min_direct_heal=255, max_direct_heal=289,
    Regrowth(REGROWTH_COEF, rank=4, lvl=30, mana_cost=230, cast_time=2, duration=21, avg_direct_heal=357, hot_heal=343),  # min_direct_heal=336, max_direct_heal=378,
    Regrowth(REGROWTH_COEF, rank=5, lvl=36, mana_cost=275, cast_time=2, duration=21, avg_direct_heal=451, hot_heal=427),  # min_direct_heal=424, max_direct_heal=478,
    Regrowth(REGROWTH_COEF, rank=6, lvl=42, mana_cost=335, cast_time=2, duration=21, avg_direct_heal=566, hot_heal=546),  # min_direct_heal=535, max_direct_heal=597,
    Regrowth(REGROWTH_COEF, rank=7, lvl=48, mana_cost=405, cast_time=2, duration=21, avg_direct_heal=711, hot_heal=686),  # min_direct_heal=672, max_direct_heal=750,
    Regrowth(REGROWTH_COEF, rank=8, lvl=54, mana_cost=485, cast_time=2, duration=21, avg_direct_heal=887, hot_heal=861),  # min_direct_heal=839, max_direct_heal=935,
    Regrowth(REGROWTH_COEF, rank=9, lvl=60, mana_cost=575, cast_time=2, duration=21, avg_direct_heal=1061, hot_heal=1064),  # min_direct_heal=1003, max_direct_heal=1119,
    Regrowth(REGROWTH_COEF, rank=10, lvl=65, mana_cost=675, cast_time=2, duration=21, avg_direct_heal=1285, hot_heal=1274)  # min_direct_heal=1215, max_direct_heal=1356,
]

TRANQUILITY = [
    Tranquility(TRANQUILITY_COEF, rank=1, mana_cost=525, lvl=30, hot_heal=4 * 350, duration=8),
    Tranquility(TRANQUILITY_COEF, rank=2, mana_cost=705, lvl=40, hot_heal=4 * 514, duration=8),
    Tranquility(TRANQUILITY_COEF, rank=3, mana_cost=975, lvl=50, hot_heal=4 * 764, duration=8),
    Tranquility(TRANQUILITY_COEF, rank=4, mana_cost=1295, lvl=60, hot_heal=4 * 1096, duration=8),
    Tranquility(TRANQUILITY_COEF, rank=5, mana_cost=1650, lvl=70, hot_heal=4 * 1517, duration=8)
]
