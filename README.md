# TBC Resto Druid Simulator

A simulator and spreadsheet generator for Resto Druid HoT rotations on WoW TBC.

Given a set of healing spells assignments (e.g. keeping lifebloom up on tank 1, keeping rejuv up on target 2...), 
this tools generates a near-optimal rotation for maximizing player activity and HoT up-time on different targets. 
Based on those rotations, the tools generate a bunch of statistics such as HPS, HPM, time to OOM... that can be used
to compare different setups.

## Install

See `requirements.txt`.

## How to use

1. Setup a configuration file containing different HoT rotations and characters stats & talents to evaluate (see example `example_config.json`).
2. Launch the python `main.py` file passing the config file ```python main.py -f config.json -o ./files```. 

### Command line interface

## Documentation

Few information about the simulator. 

### Rotation

A rotation is a set of prioritized healing assignments such as:

```json
{
  "name": "single_target_rotation",
  "description": "Keeping all hots rolling on one target, no filler.",
  "assignments": [
    { "spell": "lifebloom", "allow_fade": false, "target": "tank" },
    { "spell": "rejuvenation", "target": "tank" },
    { "spell": "regrowth", "target": "tank" }
  ]
}
```

As explained in the description, this rotation is just keeping all our available HoTs running on one target 
(called `tank`). The `lifebloom` assignment being the first, it has the highest priority. The simulator will therefore 
make  sure it always up and that it will not fade/bloom (see `"allow_fade": false`). The `rejuvenation` comes second 
and is allowed to fade. By default, max spell rank is used if not specified (but can be specified with a `"rank": 1` 
field). This simulation will not add any other heal other than the one specified in the rotation. This means that when
all assigments are satisfied the simulator will just wait until an assignment needs to be satisfied again. 


The tool can also generate timeline graph based on rotations to show the generated rotations. For example, for the
rotation above:



### Character

For generating stats about a rotation, the simulator needs to know stats and talents of one or several characters.  

```json
{
  "name": "classic_gear",
  "description": "Level 70 with naxxramas gear and standard talents",
  "level": 70,
  "tree_form": true,
  "stats": {
    "primary": {
      "intelligence": 395,
      "strength": 77,
      "spirit": 312,
      "stamina": 324,
      "agility": 79
    },
    "secondary": {
      "spell_haste_rating": 0,
      "spell_crit_rating": 0,
      "mp5": 70,
      "spell_damage": 409,
      "bonus_healing": 1263
    }
  },
  "talents": {
    "naturalist": 0,
    "gift_of_nature": 5,
    "tranquility_spirit": 5,
    "improved_rejuvenation": 3,
    "empowered_rejuvenation": 5,
    "living_spirit": 3,
    "empowered_touch": 2,
    "improved_regrowth": 5,
    "intensity": 3,
    "tree_of_life": 1
  }
}
```

In the future, I hope to be able to generate such information from websites such as seventyupgrades. 

## Ideas for future developments

1. Fix all formula based on feedback from PTR 
2. Integrate gear bonuses, spell-specific bonus effects and buffs
3. Generate more fancy reports
4. Integration with seventyupgrades/wowtbc.gg to generate rotations and stats from characters

