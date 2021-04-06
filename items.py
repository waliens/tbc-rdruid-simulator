from spell import HealingSpell
from statistics import Stats
from statsmodifiers import StatsModifier, ConstantStatsModifier, StatsModifierArray


class ItemBonus(object):
    def __init__(self, name, identifier, spell_effects):
        self._name = name
        self._identifier = identifier
        self._effects = spell_effects

    @property
    def effects(self):
        return self._effects


class Gear(object):
    def __init__(self, item_bonuses):
        self._items = item_bonuses
        self._effects = StatsModifierArray([e for item_bonus in self._items for e in item_bonus.effects])

    @property
    def effects(self):
        return self._effects


_items = [
    ('idol_of_the_emerald_queen', 27886, [('lifebloom', HealingSpell.HEAL_TICK, StatsModifier.TYPE_ADDITIVE, "GearBonus", (Stats.BONUS_HEALING, 88))])
]


ITEMS = {
    name: ItemBonus(name, _id, [ConstantStatsModifier("item_{}_{}".format(i, name), _type, [effect], cond_cm_group=cm_group, spell_name=sname, spell_part=starget)
                                for i, (sname, starget, _type, cm_group, effect) in enumerate(modifiers)])
    for name, _id, modifiers in _items
}