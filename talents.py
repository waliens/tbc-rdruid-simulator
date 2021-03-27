
class Talents(object):
    NATURALIST = ("naturalist", 5)
    GIFT_OF_NATURE = ("gift_of_nature", 5)
    TRANQUILITY_SPIRIT = ("tranquil_spirit", 5)
    IMPROVED_REJUVENATION = ("improved_rejuvenation", 3)
    EMPOWERED_REJUVENATION = ("empowered_rejuvenation", 5)
    LIVING_SPIRIT = ("living_spirit", 3)
    EMPOWERED_TOUCH = ("empowered_touch", 2)
    IMPROVED_REGROWTH = ("improved_regrowth", 5)
    INTENSITY = ("intensity", 3)
    TREE_OF_LIFE = ("tree_of_life", 1)
    LUNAR_GUIDANCE = ("lunar_guidance", 3)
    DREAMSTATE = ("dreamstate", 3)

    def __init__(self, talents):
        self._talents = {
            t: min(t[1], talents.get(t[0], 0))
            for t in Talents.all()
        }

    def get(self, talent):
        return self._talents.get(talent, 0)

    @staticmethod
    def all():
        return [Talents.NATURALIST, Talents.GIFT_OF_NATURE, Talents.TRANQUILITY_SPIRIT,
                Talents.IMPROVED_REJUVENATION, Talents.EMPOWERED_REJUVENATION, Talents.LIVING_SPIRIT,
                Talents.EMPOWERED_TOUCH, Talents.IMPROVED_REGROWTH, Talents.INTENSITY, Talents.TREE_OF_LIFE,
                Talents.DREAMSTATE, Talents.LUNAR_GUIDANCE]

    def __len__(self):
        return len(self.all())