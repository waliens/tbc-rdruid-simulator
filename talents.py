from abc import abstractmethod

from heal_parts import HealParts
from statsmodifiers import StatsModifier, StatsModifierArray, ConstantStatsModifier
from statistics import Stats


class Talents(object):
    def __init__(self, talents, name=""):
        self._name = name
        self._talent_tree = dict()

        for t in self.all_talents:
            name, max_points, _ = t
            if name not in talents:
                continue
            if not (0 <= talents[name] <= max_points):
                raise ValueError("Invalid number of points {} in talent '{}'".format(talents[name], name))
            self._talent_tree[t] = talents[name]

    @property
    def tree(self):
        return self._talent_tree

    @property
    @abstractmethod
    def all_talents(self):
        pass

    @property
    @abstractmethod
    def buff_array(self):
        pass

    @property
    @abstractmethod
    def spell_buff_array(self):
        pass

    @property
    def name(self):
        return self._name

    def __getitem__(self, item):
        return self.tree.get(item, 0)

    def get(self, talent):
        return self[talent]


class DruidTalents(Talents):
    NATURALIST = ("naturalist", 5, "restoration")
    GIFT_OF_NATURE = ("gift_of_nature", 5, "restoration")
    TRANQUIL_SPIRIT = ("tranquil_spirit", 5, "restoration")
    IMPROVED_REJUVENATION = ("improved_rejuvenation", 3, "restoration")
    EMPOWERED_REJUVENATION = ("empowered_rejuvenation", 5, "restoration")
    LIVING_SPIRIT = ("living_spirit", 3, "restoration")
    EMPOWERED_TOUCH = ("empowered_touch", 2, "restoration")
    IMPROVED_REGROWTH = ("improved_regrowth", 5, "restoration")
    INTENSITY = ("intensity", 3, "restoration")
    TREE_OF_LIFE = ("tree_of_life", 1, "restoration")
    LUNAR_GUIDANCE = ("lunar_guidance", 3, "balance")
    DREAMSTATE = ("dreamstate", 3, "balance")
    NURTURING_INSTINCT = ("nurturing_instinct", 2, "feralcombat")
    MOONGLOW = ("moonglow", 3, "balance")

    @property
    def all_talents(self):
        return self.all()

    @staticmethod
    def all():
        return [DruidTalents.NATURALIST, DruidTalents.GIFT_OF_NATURE, DruidTalents.TRANQUIL_SPIRIT,
                DruidTalents.IMPROVED_REJUVENATION, DruidTalents.EMPOWERED_REJUVENATION, DruidTalents.LIVING_SPIRIT,
                DruidTalents.EMPOWERED_TOUCH, DruidTalents.IMPROVED_REGROWTH, DruidTalents.INTENSITY, DruidTalents.TREE_OF_LIFE,
                DruidTalents.DREAMSTATE, DruidTalents.LUNAR_GUIDANCE, DruidTalents.MOONGLOW, DruidTalents.NURTURING_INSTINCT]

    def __len__(self):
        return len(self.all())

    @property
    def buff_array(self):
        buffs = list()
        # intensity
        is_fn = lambda char, **context: 0.1 * char.talents.get(DruidTalents.INTENSITY) * char.get_stat(Stats.REGEN_5SR)
        is_fo = "(0.1 * #Talents.{}# * #Stats.{}#)".format(DruidTalents.INTENSITY[0], Stats.REGEN_5SR)
        buffs.append(StatsModifier(name=DruidTalents.INTENSITY[0], stats=[Stats.MP5], _type=StatsModifier.TYPE_ADDITIVE, functions=[is_fn], formula=[is_fo]))
        # living spirit
        ls_fn = lambda char, **context: (1 + 0.05 * char.talents.get(DruidTalents.LIVING_SPIRIT))
        ls_fo = "(1 + 0.05 * #Talents.{}#)".format(DruidTalents.LIVING_SPIRIT[0])
        buffs.append(StatsModifier(name=DruidTalents.LIVING_SPIRIT[0], stats=[Stats.SPIRIT], _type=StatsModifier.TYPE_MULTIPLICATIVE, functions=[ls_fn], formula=[ls_fo]))
        # lunar guidance
        lg_fn = lambda char, **context: [0, 0.08, 0.16, 0.25][char.talents.get(DruidTalents.LUNAR_GUIDANCE)] * char.get_stat(Stats.INTELLECT)
        lg_talent = "#Talents.{}#".format(DruidTalents.LUNAR_GUIDANCE[0])
        lg_fo = "(CHOOSE({talent}+1; 0; 8; 16; 25) * #Stats.{intel}# / 100)".format(talent=lg_talent, intel=Stats.INTELLECT)
        buffs.append(StatsModifier(name=DruidTalents.LUNAR_GUIDANCE[0] + "_spell", stats=[Stats.SPELL_DAMAGE], _type=StatsModifier.TYPE_ADDITIVE, functions=[lg_fn], formula=[lg_fo]))
        buffs.append(StatsModifier(name=DruidTalents.LUNAR_GUIDANCE[0] + "_healing", stats=[Stats.BONUS_HEALING], _type=StatsModifier.TYPE_ADDITIVE, functions=[lg_fn], formula=[lg_fo]))
        # dreamstate
        ds_fn = lambda char, **context: [0, 0.04, 0.07, 0.1][char.talents.get(DruidTalents.DREAMSTATE)] * char.get_stat(Stats.INTELLECT)
        ds_talent = "#Talents.{}#".format(DruidTalents.DREAMSTATE[0])
        ds_fo = "(CHOOSE({talent}+1; 0; 4; 7; 10) * #Stats.{intel}# / 100)".format(talent=ds_talent, intel=Stats.INTELLECT)
        buffs.append(StatsModifier(name=DruidTalents.DREAMSTATE[0], stats=[Stats.MP5], _type=StatsModifier.TYPE_ADDITIVE, functions=[ds_fn], formula=[ds_fo]))
        # nurturing instinct
        ni_fn = lambda char, **context: 0.5 * char.talents.get(DruidTalents.NURTURING_INSTINCT) * char.get_stat(Stats.AGILITY)
        ni_talent = "#Talents.{}#".format(DruidTalents.NURTURING_INSTINCT[0])
        ni_fo = "({talent} * 0.5 * #Stats.{agi}#)".format(talent=ni_talent, agi=Stats.AGILITY)
        buffs.append(StatsModifier(name=DruidTalents.NURTURING_INSTINCT[0], stats=[Stats.BONUS_HEALING], _type=StatsModifier.TYPE_ADDITIVE, functions=[ni_fn], formula=[ni_fo]))
        return StatsModifierArray(buffs)

    @property
    def spell_buff_array(self):
        buffs = list()
        ts_fn = lambda char, **context: (1 - 0.02 * char.talents.get(DruidTalents.TRANQUIL_SPIRIT))
        ts_fo = "(1 - 0.02 * #Talents.{}#)".format(DruidTalents.TRANQUIL_SPIRIT[0])
        buffs.append(StatsModifier(name=DruidTalents.TRANQUIL_SPIRIT,
                                   stats=[("tranquility", HealParts.MANA_COST), ("healing_touch", HealParts.MANA_COST)],
                                   functions=[ts_fn, ts_fn], formula=[ts_fo, ts_fo],
                                   _type=StatsModifier.TYPE_MULTIPLICATIVE))
        mg_fn = lambda char, **context: (1 - 0.03 * char.talents.get(DruidTalents.MOONGLOW))
        mg_fo = "(1 - 0.03 * #Talents.{}#)".format(DruidTalents.MOONGLOW[0])
        buffs.extend([
            StatsModifier(name=DruidTalents.MOONGLOW,
                          stats=[(spell, HealParts.MANA_COST)],
                          functions=[mg_fn], formula=[mg_fo],
                          _type=StatsModifier.TYPE_MULTIPLICATIVE)
            for spell in ["regrowth", "healing_touch", "rejuvenation"]
        ])
        return StatsModifierArray(buffs)
