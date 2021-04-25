# TBC Resto Druid Simulator

A simulator and spreadsheet generator for Resto Druid HoT rotations on WoW TBC.

Given a set of healing spells assignments (e.g. keeping lifebloom up on tank 1, keeping rejuv up on target 2...), 
this tools generates a near-optimal rotation for maximizing player activity and HoT up-time on different targets. 
Based on those rotations, the tools generate a bunch of statistics such as HPS, HPM, time to OOM... that can be used
to compare different setups.

## Install

The tool is a Python script, so Python needs to be installed from [Python](https://www.python.org/downloads/) or [Anaconda](https://www.anaconda.com/products/individual#Downloads)
 
Then:

- download the code as a zip file [here](https://github.com/waliens/tbc-rdruid-simulator/archive/refs/heads/main.zip) or using Git: `git clone https://github.com/waliens/tbc-rdruid-simulator.git`
- open a command line interface and move into the folder downloaded
- install python dependencies from the `requirements.txt` file: `pip install -r requirements.txt`

You are now up and running. 

## How to use

1. Setup a configuration file (see `example_config.json`). You need to define:
 - one or more healing spells rotations 
 - one or more character profiles to evaluate (character stats & talents)
2. Launch the python `main.py` file passing the config file ```python main.py -f config.json -o ./files```.
3. Analyze the produced data:
 - inspect generated timeline for rotations
 - inspect generated spreadsheets (by importing them on google)

### Command line interface

Command line parameters:

- `-c/--config`: the filepath to the configuration file
- `-o/--out_folder`: the output folder where the tool should write output files (spreadsheets, pngs, json)
- `-g/--graphs`: if specified, the tool generates graph timelines of the generated rotations
- `-s/--spreadsheets`: if specified, generates spreadsheets presenting the results
 
## Documentation

The simulator will generate healing rotations for combinations of character stats, talents, buffs and healing 
assignments. Therefore, you have to provide at least one of each element in a JSON format (see full example in file
`example_config.json`).

###

### Healing assignments

A set of prioritized healing assignments such as:

```json
{
  "name": "single_target_rotation",
  "description": "Keeping all hots rolling on one target, no filler.",
  "assignments": [
    { "spell": "lifebloom", "allow_fade": false, "target": "tank" },
    { "spell": "rejuvenation", "target": "tank" },
    { "spell": "regrowth", "target": "tank" }
  ],
  "buffs": {
    "tank": ["amplify_magic", "dampen_magic", "tree_of_life_healing"]
  },
  "filler": { "spell": "rejuvenation" }
}
```

As explained in the description, this rotation is just keeping all our available HoTs running on one target 
(called `tank`). The `lifebloom` assignment being the first, it has the highest priority. The simulator will therefore 
make  sure it always up and that it will not fade/bloom (see `"allow_fade": false`). The `rejuvenation` comes second 
and is allowed to fade. By default, max spell rank is used if not specified (but can be specified with a `"rank": 1` 
field). This simulation will not add any other heal other than the one specified in the rotation. This means that when
all assigments are satisfied the simulator will just wait until an assignment needs to be satisfied again. 

One can also specify by-target buffs using the `buffs` field. One can also specify a spell to use as filler (see 
`filler` field). The tool will attempt to cast the filler spell when all other assignments are satisfied. 

The tool can also produce timeline graphs based on the auto-generated rotations. For example, for the
rotation above:

![example_rotation](https://github.com/waliens/tbc-rdruid-simulator/raw/main/images/example_graph.png)

### Buffs

A list of active buffs to evaluate as a JSON array of buff name. 

Currently supported buffs are: `"gift_of_the_wild", "arcane_intellect", "benediction_of_king", "benediction_of_wisdom", "benediction_of_wisdom_tal", "mana_tide_totem", "mana_tide_totem_tal", "wrath_of_air_totem", "totem_of_wrath", "moonkin_aura", "mark_of_bite", "elixir_of_draenic_wisdom", "elixir_of_major_mageblood", "elixir_of_healing_power", "elixir_of_mastery", "golden_fish_sticks", "tree_of_life_mana", "atiesh_druid", "atiesh_priest", "atiesh_mage", "atiesh_lock"`

### Talents

Talents points as a JSON dictionary:

```json
{
  "name": "deep_resto",
  "points": {
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
 
The `name` is the spec name and `points` contains the points dictionary mapping talent name with the number of assigned
points. 

Currently supported druid talents: `"naturalist", "gift_of_nature", "tranquil_spirit", "improved_rejuvenation", "empowered_rejuvenation", "living_spirit", "empowered_touch", "improved_regrowth", "intensity", "tree_of_life", "lunar_guidance", "dreamstate"`
  
### Character profiles

For generating stats about a rotation, the simulator needs to know stats of one or several characters.  

```json
{
  "name": "classic_gear",
  "description": "Level 70 with naxxramas gear and standard talents",
  "level": 70,
  "stats": {
    "intellect": 395,
    "strength": 77,
    "spirit": 312,
    "stamina": 324,
    "agility": 79,
    "spell_haste_rating": 0,
    "spell_crit_rating": 0,
    "mp5": 70,
    "spell_damage": 409,
    "bonus_healing": 1263
  }
}
```

In the future, I hope to be able to generate such information from websites such as seventyupgrades. 

## Ideas for future developments

1. Fix all formula based on feedback from PTR 
2. Integrate gear bonuses, spell-specific bonus effects and buffs
3. Generate more fancy reports
4. Integration with seventyupgrades/wowtbc.gg to generate rotations and stats from characters

