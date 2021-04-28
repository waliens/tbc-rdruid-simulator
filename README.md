# TBC Resto Druid Simulator

A simulator and spreadsheet generator for Resto Druid HoT rotations on WoW TBC.

Given a set of healing spells assignments (e.g. keeping lifebloom up on tank 1, keeping rejuv up on target 2...), 
this tools generates a near-optimal rotation for maximizing player activity and HoT up-time on different targets. 
Based on those rotations, the tools generate a bunch of statistics such as HPS, HPM, time to OOM... that can be used
to compare different setups.

### Ideas for future developments

1. Fix all formula based on feedback from PTR 
2. Generate more fancy reports
3. Integration with seventyupgrades/wowtbc.gg to generate rotations and stats from characters

## Install

The tool is a Python script, so Python needs to be installed from [Python](https://www.python.org/downloads/) or [Anaconda](https://www.anaconda.com/products/individual#Downloads)
 
Then:

- download the code as a zip file [here](https://github.com/waliens/tbc-rdruid-simulator/archive/refs/heads/main.zip) or using Git: `git clone https://github.com/waliens/tbc-rdruid-simulator.git`
- open a command line interface and move into the folder downloaded
- install python dependencies from the `requirements.txt` file: `pip install -r requirements.txt`

You are now up and running. 

## How to use

1. Setup a configuration file (see `tbc_phase1_config.json`). You need to define:
 - one or more healing spells rotations 
 - one or more character profiles to evaluate (character stats & talents)
2. Launch the python `main.py` file passing the config file ```python main.py -f config.json -o ./files```.
3. Analyze the produced data:
 - inspect generated timeline for rotations
 - inspect generated spreadsheets (by importing them on google sheet)

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
  "description": "Keeping all hots rolling on one target, with filler.",
  "assignments": [
    { "spell": "lifebloom", "allow_fade": false, "target": "tank" },
    { "spell": "rejuvenation", "target": "tank" },
    { "spell": "regrowth", "target": "tank" }
  ],
  "buffs": {
    "tank": ["amplify_magic", "tree_of_life_healing"]
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

Currently supported buffs are:

* `"gift_of_the_wild"`: +12 all stats
* `"gift_of_the_wild_tal"`: +16 all stats
* `"divine_spirit"`: +50 spirit
* `"divine_spirit_tal"`: +50 spirit and 10% spirit converted to bonus healing
* `"arcane_intellect"`: +40 intellect
* `"benediction_of_king"`: +10% all stats
* `"benediction_of_wisdom"`: +41 mp5
* `"benediction_of_wisdom_tal"`: +49 mp5
* `"mana_spring_totem"`: +50mp5 
* `"mana_tide_totem"`: +24% mana
* `"wrath_of_air_totem"`: +101 bh and 101 spell damage
* `"totem_of_wrath"`: +3% crit
* `"moonkin_aura"`: +5% crit
* `"mark_of_bite"`: +5% all stats
* `"elixir_of_draenic_wisdom"`: +30 spirit and intellect
* `"elixir_of_major_mageblood"`: +16 mp5
* `"elixir_of_healing_power"`: +50 bh
* `"elixir_of_mastery"`: +15 all stats
* `"golden_fish_sticks"`: +44 bh and +20 spirit
* `"tree_of_life_mana"`: -20% mana cost for HoTs
* `"atiesh_druid"`: +11 mp5
* `"atiesh_priest"`: +64 bh
* `"atiesh_mage"`: +28 crit rating
* `"atiesh_lock"`: +33 sp
* `"super_mana_pot_rota"`: +100 mp5 (on cd)
* `"demonic_rune_rota"`: +50mp5 (on cd)

Target buffs:
    
* `"dampen_magic"`: -120 sp and -240 bh 
* `"amplify_magic"`: +120 sp and +240bh
* `"tree_of_life_healing"` +25% of druid's spirit converted to bh 
    
### Talents

Talents points as a JSON dictionary:

```json
{
  "name": "deep_resto",
  "points": {
    "naturalist": 0,
    "gift_of_nature": 5,
    "tranquil_spirit": 5,
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

Currently supported druid talents: 
 
* `"naturalist"`
* `"gift_of_nature"`
* `"tranquil_spirit"`
* `"improved_rejuvenation"`
* `"empowered_rejuvenation"`
* `"living_spirit"`
* `"empowered_touch"`
* `"improved_regrowth"`
* `"intensity"`
* `"tree_of_life"`
* `"lunar_guidance"`
* `"dreamstate"`
* `"nurturing_instinct"`

### Character profiles

For generating stats about a rotation, the simulator needs to know stats of one or several characters.  

```json
{
  "name": "gear_set_name",
  "description": "A gear set",
  "level": 70,
  "bonuses": [
    "idol_of_the_emerald_queen"
  ],
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
  },
  "gems": [
    {"name": "a_name", "slots": ["meta", "red"], "bonus": [{"stat": "intellect", "value": 4}]},
  ]
}
```

Bonuses corresponds to gear or set bonuses that are not counted directly into stats (spell specific bonus, on use).

Currently supported bonuses are:

* `"idol_of_the_emerald_queen"`: +88 bh on lifebloom ticks
* `"idol_of_rejuvenation"`: +50 bh for overall rejuv
* `"harolds_rejuvenating_broach"`: +86 bh for overall rejuv
* `"gladiators_idol_of_tenacity"`: +87 bh for lifebloom direct heal 
* `"merciless_gladiators_idol_of_tenacity"`: + 105bh for lifebllom direct heal
* `"vengeful_gladiators_idol_of_tenacity"`: + 116bh for lifebllom direct heal
* `"brutal_gladiators_idol_of_tenacity"`: + 131bh for lifebllom direct heal
* `"idol_of_the_raven_goddess"`: adds 44 bh on tree of life healing bonus
* `"idol_of_the_avian_heart"`: +136 bh for healing touch
* `"t5_nordrassil_raiment_4p"`: +150 bh for lifebllom direct heal
* `"primal_mooncloth_3p"`: +5% regen while not casting active when casting
* `"whitemend_2p"`: 5% of intellect converted into bh
* `"t2_stormrage_raiment_3p"`: +20 mp5
* `"darkmoon_card_blue_dragon"`: see [notes](#blue-dragon-card)
* `"lower_city_prayer_book"`: +14mp5 (on cd, assumes 8 casts on 15sec)
* `"t5_nordrassil_raiment_2p"`: +6sec for regrowth (+ 2ticks) 
* `"t3_dreamwalker_raiment_4p"`: -3% mana cost for healing spells
* `"t2_stormrage_raiment_5p"`: reduce regrowth cast time by 0.2sec
* `"t2_stormrage_raiment_8p"`: +3 sec for rejuv (+1 tick)
* `"t6_thunderheart_raiment_4p"`: +10% healing on healing touch
* `"idol_of_budding_life"`: -36 mana for casting rejuv
* `"idol_of_the_crescent_goddess"`: -65 mana for casting regrowth

In the future, I hope to be able to generate such information from websites such as seventyupgrades. 

### Gems policy

Gem slots are defined per character profile. How to fill them is specified as a gem policy. This policy will define
how to fill the gem slots.

```json
{
  "gems_policy": [
    {"policy":"stack_healing", "heroic": true, "jewelcrafting": false},
    {"policy":"match_slots", "heroic": true, "jewelcrafting": false}
  ]
}
```

Two policies are currently available:

* `stack_healing`: stack largest available gems to maximize bonus healing (ignoring slot colors if necessary)
* `match_slots`: matching slot colors while picking gems maximizing bonus healing

One can also specify if gems from heroic or jewelcrafting should be considered for filling the slots. 


## Notes

### Blue dragon card

The effect the blue dragon card is simulated as follows. `a` is the probability that the card is active at a 
mana regen tick. To be active means that the card has procced at least once in the last 15sec. Maximum number of casts
in a 15sec period without haste is 9, but we will assume 8 (to account for healer imperfections, latency, etc.). 
Using a binomial distribution (at least 1 proc among 8 casts, with probability to proc at a given cast being equal to 
`p=0.02`), we get `a = 0.1389000853`. Now given `R`, the regen while not casting (per tick), 
and `c`, the portion of regen while not casting currently converted into regen while casting, we have `r` the
regen gained from the card on average:

```
r = R * a * (1 - c) 
```

