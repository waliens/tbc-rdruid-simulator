from talents import Talents

BASE_MANA_LOOKUP = [50, 50, 50, 50, 50, 50, 50, 120, 134, 149, 165, 182, 200, 219, 239, 260, 282, 305, 329, 354, 380,
                    392, 420, 449, 479, 509, 524, 554, 584, 614, 629, 659, 689, 704, 734, 749, 779, 809, 824, 854, 869,
                    899, 914, 944, 959, 989, 1004, 1019, 1049, 1064, 1079, 1109, 1124, 1139, 1154, 1169, 1199, 1214,
                    1229, 1244, 1359, 1469, 1582, 1694, 1807, 1919, 2032, 2145, 2257, 2370]


def linear_params(x1, y1, x2, y2):
    coef = (y2 - y1) / (x2 - x1)
    intercep = (y2 - coef * x2)
    return coef, intercep


def linear(x1, y1, x2, y2):
    coef, intercep = linear_params(x1, y1, x2, y2)
    return lambda lvl: lvl * coef + intercep


class Stats(object):
    INTELLIGENCE = "intelligence"
    STRENGTH = "strength"
    SPIRIT = "spirit"
    STAMINA = "stamina"
    AGILITY = "agility"
    SPELL_HASTE_RATING = "spell_haste_rating"
    SPELL_CRIT_RATING = "spell_crit_rating"
    SPELL_HASTE = "spell_haste"
    SPELL_CRIT = "spell_crit"
    MP5 = "mp5"
    SPELL_DAMAGE = "spell_damage"
    BONUS_HEALING = "bonus_healing"
    REGEN_5SR = "regen_5SR"
    REGEN = "total_regen"
    GCD = "gcd"
    MANA = "mana"
    HP = "hp"

    @staticmethod
    def secondary():
        return [Stats.SPELL_HASTE_RATING, Stats.SPELL_CRIT_RATING, Stats.MP5, Stats.BONUS_HEALING, Stats.SPELL_DAMAGE]

    @staticmethod
    def primary():
        return [Stats.INTELLIGENCE, Stats.STRENGTH, Stats.SPIRIT, Stats.STAMINA, Stats.AGILITY]

    @staticmethod
    def computed():
        return [Stats.REGEN_5SR, Stats.SPELL_HASTE, Stats.SPELL_CRIT, Stats.GCD, Stats.MANA]

    @staticmethod
    def get_computed_excel_formula(stat):
        if stat == Stats.REGEN_5SR:
            return "(5 * 0.00932715221261 * SQRT(#Stats.{}#) * #Stats.{}#)".format(Stats.INTELLIGENCE, Stats.SPIRIT)
        elif stat == Stats.SPELL_HASTE:
            coef, intercep = linear_params(60, 1 / 10, 70, 1 / 15.8)
            return "(({coef} * #Character.level# + {intercep}) * #Stats.{rating}# / 100)".format(coef=coef, intercep=intercep, rating=Stats.SPELL_HASTE_RATING)
        elif stat == Stats.SPELL_CRIT:
            coef, intercep = linear_params(60, 1 / 14, 70, 1 / 22.1)
            return "(1.85 + (#Stats.{intel}# / 80) + ({coef} * #Character.level# + {intercep}) * #Stats.{rating}#) / 100".format(coef=coef, intercep=intercep, rating=Stats.SPELL_CRIT_RATING, intel=Stats.INTELLIGENCE)
        elif stat == Stats.GCD:
            return "(1.5 / (1 + #Stats.{}#))".format(Stats.SPELL_HASTE)
        elif stat == Stats.MANA:
            intel_stats = "#Stats.{}#".format(Stats.INTELLIGENCE)
            intel_mana = "MIN(20; {intel}) + (15 * ({intel} - MIN({intel}; 20)))".format(intel=intel_stats)
            return "(CHOOSE(#Character.level# - 57; {}) + {})".format(";".join(map(str, BASE_MANA_LOOKUP[57:])), intel_mana)
        else:
            raise "'{}' is not a computed stat".format(stat)

    @classmethod
    def base(cls, stat):
        return "base_" + stat