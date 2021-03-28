
class Talents(object):
    NATURALIST = ("naturalist", 5, "restoration")
    GIFT_OF_NATURE = ("gift_of_nature", 5, "restoration")
    TRANQUILITY_SPIRIT = ("tranquil_spirit", 5, "restoration")
    IMPROVED_REJUVENATION = ("improved_rejuvenation", 3, "restoration")
    EMPOWERED_REJUVENATION = ("empowered_rejuvenation", 5, "restoration")
    LIVING_SPIRIT = ("living_spirit", 3, "restoration")
    EMPOWERED_TOUCH = ("empowered_touch", 2, "restoration")
    IMPROVED_REGROWTH = ("improved_regrowth", 5, "restoration")
    INTENSITY = ("intensity", 3, "restoration")
    TREE_OF_LIFE = ("tree_of_life", 1, "restoration")
    LUNAR_GUIDANCE = ("lunar_guidance", 3, "balance")
    DREAMSTATE = ("dreamstate", 3, "balance")

    def __init__(self, talents, name=""):
        self._name = name
        self._talents = {
            t: min(t[1], talents.get(t[0], 0))
            for t in Talents.all()
        }

    def get(self, talent):
        return self._talents.get(talent, 0)

    @property
    def name(self):
        return self._name

    @staticmethod
    def all():
        return [Talents.NATURALIST, Talents.GIFT_OF_NATURE, Talents.TRANQUILITY_SPIRIT,
                Talents.IMPROVED_REJUVENATION, Talents.EMPOWERED_REJUVENATION, Talents.LIVING_SPIRIT,
                Talents.EMPOWERED_TOUCH, Talents.IMPROVED_REGROWTH, Talents.INTENSITY, Talents.TREE_OF_LIFE,
                Talents.DREAMSTATE, Talents.LUNAR_GUIDANCE]

    def __len__(self):
        return len(self.all())