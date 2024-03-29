from buffs import Buff, ALL_STATS_BUFFS
from character import Stats, BuffedCharacter
from spell import HealingSpell, Lifebloom, HEALING_TOUCH, REJUVENATION, REGROWTH, LIFEBLOOM, TRANQUILITY
from statsmodifiers import StatsModifierArray
from talents import DruidTalents
from util import bisect_right, sort_by, apply_crit, argmin


def robust_zipstar(*arrays, tuple_size=2):
    if len(arrays) == 0:
        return [() for i in range(tuple_size)]
    return zip(*arrays)


class SingleAssignment(object):
    """single target and single spell assigment"""
    def __init__(self, spell, target, allow_fade=True, fade_at_stacks=1, spell_queue=False):
        self._target = target
        self._spell = spell
        self._allow_fade = allow_fade
        self._fade_at_stacks = fade_at_stacks  # nb of stacks before allowing fade
        self._spell_queue = spell_queue

    @property
    def spell_queue(self):
        return self._spell_queue

    @property
    def target(self):
        return self._target

    @property
    def spell(self):
        return self._spell

    @property
    def allow_fade(self):
        return self._allow_fade

    @property
    def fade_at_stacks(self):
        return self._fade_at_stacks

    @property
    def identifier(self):
        return self.spell.identifier, self.target

    def __str__(self):
        return self.spell.identifier + "-" + self.target

    @staticmethod
    def from_dict(**kwargs):
        return SingleAssignment(
            spell=get_spell_from_assign(kwargs),
            target=kwargs["target"],
            allow_fade=kwargs.get("allow_fade", True),
            fade_at_stacks=kwargs.get("fade_at_stacks", 1),
            spell_queue=kwargs.get("spell_queue", False)
        )


class FillerAssignment(SingleAssignment):
    def __init__(self, assignment, target_suffix):
        super().__init__(assignment.spell, assignment.target,
                         allow_fade=assignment.allow_fade,
                         fade_at_stacks=assignment.fade_at_stacks)
        self._base_assignment = assignment
        self._target_suffix = target_suffix

    @property
    def target(self):
        return self._base_assignment.target + self._target_suffix


def get_spell_from_assign(assign):
    all_spells = {
        "healing_touch": HEALING_TOUCH,
        "rejuvenation": REJUVENATION,
        "regrowth": REGROWTH,
        "lifebloom": LIFEBLOOM,
        "tranquility": TRANQUILITY
    }
    if assign["spell"] in all_spells:
        spells = all_spells[assign["spell"]]
        return spells[assign.get("rank", len(spells)) - 1]
    else:
        raise ValueError("unknown spell '{}'".format(assign["spell"]))


class Assignments(object):
    def __init__(self, assignments, name="", description="", filler=None, target_buffs=None):
        self._description = description
        self._assignments = assignments
        self._name = name
        if filler is not None and ("allow_fade" in filler or "fade_at_stacks" in filler):
            raise ValueError("filler description does not allow fields 'allow_fade' and 'fade_at_stacks'")
        self._filler = SingleAssignment.from_dict(**filler) if filler is not None else filler
        self._target_buffs = {} if target_buffs is None else target_buffs

    def __len__(self):
        return len(self._assignments)

    def __iter__(self):
        return iter(self._assignments)

    @property
    def filler(self):
        return self._filler

    @property
    def has_filler(self):
        return self._filler is not None

    @property
    def name(self):
        return self._name

    def buffs(self, target):
        modifiers = list()
        if target in self._target_buffs:
            modifiers = [ALL_STATS_BUFFS[n] for n in self._target_buffs[target]]
        return StatsModifierArray(modifiers)

    @staticmethod
    def from_dict(data):
        return Assignments(
            [SingleAssignment.from_dict(**assign) for assign in data["assignments"]],
            name=data["name"],
            description=data["description"],
            filler={"target": "_filler", **data.get("filler")} if "filler" in data else None,
            target_buffs=data.get("buffs")
        )

    @property
    def spell_queued(self):
        """Returns assignments that have a spell-queue requirement (excluding filler)"""
        return [a for a in self._assignments if a.spell_queue]


class Event(object):
    def __init__(self, start, duration=0, stacks=1):
        self._start = start
        self._duration = duration
        self._stacks = stacks

    @property
    def stacks(self):
        return self._stacks

    @stacks.setter
    def stacks(self, new_stacks):
        self._stacks = new_stacks

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self.start + self.duration

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, new_duration):
        self._duration = new_duration

    def __repr__(self):
        return "{}(start={},end={},duration={})".format(type(self), self.start, self.end, self.duration)


class SpellEvent(Event):
    def __init__(self, start, spell, stacks=1):
        super().__init__(start=start, duration=spell.base_duration, stacks=stacks)
        self._spell = spell

    @property
    def spell(self):
        return self._spell

    @staticmethod
    def from_spell(spell, start):
        return SpellEvent(start, spell, stacks=1)

    def _on_use_active_at_cast(self, on_use=None):
        if on_use is None:
            return []
        return [on_use_timeline.event_at(self.start)
                for on_use_timeline in on_use if on_use_timeline.is_up_at(self.start)]

    @classmethod
    def _on_use_buffed_characters(cls, character, active_at_cast_on_use_events):
        # hot's capture the buffs when cast, ticks after the end of on use duration also benefit from the effect
        # -> no filtering
        return BuffedCharacter(
            character,
            spell_buffs=StatsModifierArray([b for event in active_at_cast_on_use_events for b in event.item.spell_effects.buffs]),
            stats_buffs=StatsModifierArray([b for event in active_at_cast_on_use_events for b in event.item.stats_effects.buffs]))

    @classmethod
    def _get_hot_first_tick_with_cadence(cls, start, period, cadence=None):
        if cadence is None:
            return start + period
        duration_between = int(start - cadence)
        first = cadence + duration_between * period
        if first <= start:
            first += period
        return first

    def _hot_with_on_use(self, character, start, end, on_use=None, prev_tick_cadence=None):
        active_at_cast = self._on_use_active_at_cast(on_use=on_use)
        ticks = list()
        max_ticks = self.spell.n_ticks(character)
        period = self.spell.tick_period(character)
        n_ticks = 0
        t = self._get_hot_first_tick_with_cadence(self.start, period, cadence=prev_tick_cadence)
        while t <= end and t <= self.end and n_ticks < max_ticks:
            if t >= start:
                character_at_tick = self._on_use_buffed_characters(character, active_at_cast)
                if self.spell.type == HealingSpell.TYPE_HOT:
                    tick = self.spell.get_healing(character_at_tick)
                elif self.spell.type == HealingSpell.TYPE_HYBRID:
                    _, tick = self.spell.get_healing(character_at_tick)
                else:
                    raise ValueError("non hot spell cannot be applied on_use with hots")
                ticks.append((t, tick * self.stacks))
            t += period
            n_ticks += 1

        return ticks

    def _direct_with_on_use(self, character, on_use=None):
        active_at_cast = self._on_use_active_at_cast(on_use=on_use)
        character_at_tick = self._on_use_buffed_characters(character, active_at_cast)
        if self.spell.type == HealingSpell.TYPE_DIRECT:
            direct = self.spell.get_healing(character_at_tick)
        elif self.spell.type == HealingSpell.TYPE_HYBRID:
            direct, _ = self.spell.get_healing(character_at_tick)
        else:
            raise ValueError("non hot spell cannot be applied on_use with hots")
        return direct

    def get_heals(self, start, end, character, on_use=None, prev_tick_cadence=None):
        # TODO spell duration and max_stacks are not applying any on use effects
        timestamps, heals, string_heals = list(), list(), list()
        if self.spell.type == HealingSpell.TYPE_HOT:
            tick_str = "#{spell}.hot_tick#".format(spell=self.spell.identifier)
            t, h = robust_zipstar(*self._hot_with_on_use(character, start, end, on_use=on_use, prev_tick_cadence=prev_tick_cadence))
            timestamps.extend(t)
            heals.extend(h)
            string_heals.extend([tick_str] * len(t))
        elif self.spell.type == HealingSpell.TYPE_DIRECT:
            timestamps.append(self.start)
            _avg = self._direct_with_on_use(character, on_use=on_use)
            heals.append(apply_crit(_avg, character.get_stat(Stats.SPELL_CRIT)))
            string_heals.append("#{spell}.avg_direct_heal#".format(spell=self.spell.identifier))
        elif self.spell.type == HealingSpell.TYPE_HYBRID:
            if (self.spell.direct_first and self.start >= start) or (not self.spell.direct_first and start + self.spell.duration(character) <= end and self.spell.duration(character) <= self.duration):
                timestamps.append(self.start if self.spell.direct_first else self.end)
                direct_avg = self._direct_with_on_use(character, on_use=on_use)
                with_crit = apply_crit(direct_avg, character.get_stat(Stats.SPELL_CRIT))
                heals.append(direct_avg if isinstance(self.spell, Lifebloom) else with_crit)
                string_heals.append("#{spell}.avg_direct_heal#".format(spell=self.spell.identifier))
            tick_str = "#{spell}.hot_tick{tick}#".format(spell=self.spell.identifier, tick="" if self.spell.max_stacks(character) == 1 else self.stacks)
            t, h = robust_zipstar(*self._hot_with_on_use(character, start, end, on_use=on_use, prev_tick_cadence=prev_tick_cadence))
            timestamps.extend(t)
            heals.extend(h)
            string_heals.extend([tick_str] * len(t))

        tuple_array = [(t, h, s) for t, h, s in zip(timestamps, heals, string_heals) if start <= t <= end]
        if len(tuple_array) == 0:
            return [], [], []
        return tuple(zip(*tuple_array))

    def __repr__(self):
        return "SpellEvent(start={}, duration={}, end={}, stacks={})".format(self.start, self.duration, self.end, self.stacks)


class BusyEvent(Event):
    def __init__(self, start, duration):
        super().__init__(start, duration)


class OnUseEvent(Event):
    def __init__(self, start, duration, item):
        super().__init__(start, duration)
        self._item = item

    @property
    def item(self):
        return self._item


class Timeline(object):
    def __init__(self, name):
        self._name = name
        self._events = list()

    def __repr__(self):
        return "Timeline<{}>()".format(self._name)

    def __len__(self):
        return len(self._events)

    def __iter__(self):
        return iter(self._events)

    def __getitem__(self, item):
        return self._events[item]

    def add_spell_event(self, start, spell):
        event = SpellEvent.from_spell(spell, start)
        if len(self) > 0:  # any spell in the pipeline
            prev_event = self._events[-1]
            if prev_event.spell.identifier != spell.identifier:
                raise ValueError("cannot store different spells in a timeline")
            if prev_event.end > start:
                prev_event.duration -= (prev_event.end - start)
                event.stacks = min(prev_event.stacks + 1, spell.base_max_stacks)
        self._events.append(event)

    def add_busy_event(self, start, duration):
        self._events.append(BusyEvent(start, duration=duration))

    def add_on_use_event(self, event: OnUseEvent):
        self._events.append(event)

    @property
    def duration(self):
        if len(self._events) == 0:
            return 0
        else:
            return self._events[-1].end - self._events[0].start

    @property
    def start(self):
        return self._events[0].start if len(self) > 0 else 0

    @property
    def end(self):
        return self._events[-1].end if len(self) > 0 else 0

    def _index_event_before(self, at):
        return bisect_right(self._events, at, key=lambda event: event.start)

    def event_at(self, at):
        index = self._index_event_before(at)
        if index == 0:
            return None
        event = self._events[index - 1]
        return event if (event.start <= at <= event.end) else None

    def event_before(self, at):
        index = self._index_event_before(at)
        if index == 0:
            return None
        event = self._events[index - 1]
        return event if event.start <= at else None

    def events_starting_after(self, at, n=-1):
        index = self._index_event_before(at)
        while index < len(self) and self._events[index].start < at:
            index += 1
        if n == -1:
            return self._events[index:]
        else:
            return self._events[index:index + n]

    @property
    def name(self):
        return self._name

    def uptime(self, start=0, end=None):
        if end is None:
            end = self.end
        events = [e for e in self._events if start <= e.start <= end or start <= e.end <= end]
        uptime = sum([e.duration for e in self._events], 0)
        if len(events) > 0 and events[0].start < start:
            uptime -= start - events[0].start
        if len(events) > 0 and end is not None and events[-1].end > end:
            uptime -= events[-1].end - end
        return uptime

    def is_up_at(self, at):
        event = self.event_at(at)
        return event is not None

    def remaining_uptime(self, at):
        event = self.event_at(at)
        return (event.end - at) if event is not None else 0

    def total_time(self):
        """time between 0 and last self end's time"""
        if len(self) == 0:
            return 0
        else:
            return self._events[-1].end

    def stats(self, character, start=0, end=None, on_use=None):
        if end is None:
            end = start if len(self) == 0 else self._events[-1].end
        filtered = [e for e in self._events
                    if isinstance(e, SpellEvent) and (start <= e.start <= end or start <= e.end <= end)]

        timestamps = list()
        heals = list()
        string_heals = list()

        prev_tick_cadence = None
        for event in filtered:
            if isinstance(event, SpellEvent) and event.spell.name == "lifebloom" and (prev_tick_cadence is None or event.stacks == 1):
                prev_tick_cadence = event.start
            t, h, s = event.get_heals(start, end, character, on_use=on_use, prev_tick_cadence=prev_tick_cadence)
            if isinstance(event, SpellEvent) and event.spell.name == "lifebloom" and len(t) == event.spell.n_ticks(character):
                # does tick reset ? seven ticks = reset
                prev_tick_cadence = None
            timestamps.extend(t)
            heals.extend(h)
            string_heals.extend(s)

        timestamps, heals, string_heals = sort_by(timestamps, heals, string_heals, f=(lambda t, h, s: start <= t <= end))
        mana_ticks = [e.start for e in filtered]
        mana_costs = [e.spell.mana_cost(character) for e in filtered]
        string_mana = ["#{spell}.mana_cost#".format(spell=e.spell.identifier) for e in filtered]

        return {
            "uptime": self.uptime(start=start, end=end),
            "start": start,
            "end": end,
            "duration": end - start,
            "mana_costs": mana_costs,
            "mana_ticks": mana_ticks,
            "string_mana": string_mana,
            "total_mana": sum(mana_costs),
            "heals": heals,
            "string_heals": string_heals,
            "timestamps": timestamps,
            "total_heal": sum(heals)
        }


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text  # or whatever


class Rotation(object):
    def __init__(self, assignments):
        self._assignments = assignments
        self._reset_state()

    def _reset_state(self):
        self._timelines = {assignment.identifier: Timeline(str(assignment)) for assignment in self._assignments}
        self._gcd_timeline = Timeline("gcd")
        self._cast_timeline = Timeline("cast")
        self._uptime_timeline = Timeline("uptime")
        self._filler_target_suffixes = list()
        self._rotation_assigments = list()

    def _get_regen_per_tick(self, character):
        mp5 = character.get_stat(Stats.MP5)
        regen = character.get_stat(Stats.REGEN_5SR)
        in_5sr = 2 * mp5 / 5
        out_5sr = 2 * (mp5 + regen) / 5
        return in_5sr, out_5sr

    def optimal_rotation(self, character, fight_duration=120, reaction=0.01, eps=1e-6, opt_for_ticks=False):
        self._reset_state()
        gcd = character.get_stat(Stats.GCD)
        current_time = 0
        mana = character.get_stat(Stats.MANA)
        last_mana_tick = 2
        while (fight_duration < 0 and mana > 0) or current_time < fight_duration:
            wait, assignment = self._action_at(current_time + eps, gcd, character, reaction=reaction, opt_for_ticks=opt_for_ticks)
            if wait < 0:
                start_time = current_time + eps
                cast_time = assignment.spell.cast_time(character)
                self._gcd_timeline.add_busy_event(start_time, gcd)
                self._cast_timeline.add_busy_event(start_time, cast_time)
                self._uptime_timeline.add_busy_event(start_time, max(gcd, cast_time))
                self._timelines[assignment.identifier].add_spell_event(start_time + cast_time, assignment.spell)
                self._rotation_assigments.append(assignment)
                current_time += max(gcd, cast_time) + eps
                mana -= assignment.spell.mana_cost(character)
            else:
                current_time += wait

            # evaluate regen
            ticks, mana_gained = self._regen_ticks(character, start=last_mana_tick, end=current_time + eps)
            if len(ticks) > 0:
                last_mana_tick = ticks[-1]
                mana += sum(mana_gained)

    @property
    def duration(self):
        return self.end - self.start

    @property
    def start(self):
        return min([t.start for t in self._timelines.values()])

    @property
    def end(self):
        return max([t.end for t in self._timelines.values()])

    @property
    def gcd_timeline(self):
        return self._gcd_timeline

    @property
    def cast_timeline(self):
        return self._cast_timeline

    @property
    def filler_targets(self):
        return ["{}{}".format(self._assignments.filler.target, s) for s in self._filler_target_suffixes]

    def timeline_by_assignment(self, assigment):
        return self._timelines[assigment.identifier]

    @property
    def timelines(self):
        timelines = [(a, self._timelines[a.identifier]) for a in self._assignments]
        for filler_suffix in self._filler_target_suffixes:
            f_assign = FillerAssignment(self.assignments.filler, filler_suffix)
            timelines.append((f_assign, self._timelines[f_assign.identifier]))
        return timelines

    @property
    def assignments(self):
        return self._assignments

    def _action_at(self, current_time, gcd, character, reaction=0.01, opt_for_ticks=False):
        """(wait_duration|-1, assigment|None)"""
        lookahead = 9999  # to store the time before a higher priority hot must be reapplied
        wait = 9999
        for assignment in self._assignments:
            # current cast time/gcd prevent from later applying/casting a higher priority spell
            cast_time = assignment.spell.cast_time(character)
            if max(gcd, cast_time) >= lookahead:
                continue

            # current spell not up, so cast !
            timeline = self._timelines[assignment.identifier]
            if not timeline.is_up_at(current_time):
                return -1, assignment

            # spell is up (can only be a HoT), cast time does not prevent higher priority spell to be
            # cast in the future
            spell_event = timeline.event_at(current_time)
            remaining_time = timeline.remaining_uptime(current_time)
            period = assignment.spell.base_tick_period
            if assignment.allow_fade and spell_event.stacks == assignment.fade_at_stacks:
                # cast right after last tick (t_cast + duration - period + reaction), or wait so that casting time
                # results in landing the heal right after the last tick
                if cast_time > remaining_time:
                    return -1, assignment
                else:
                    wait = min(wait, remaining_time - cast_time + reaction)
            # for sure needs refresh but might be worth
            elif (opt_for_ticks and remaining_time <= 2 * reaction) or (not opt_for_ticks and remaining_time <= period):
                return -1, assignment
            else:
                lookahead = min(lookahead, remaining_time - cast_time - reaction)
                wait = min(wait, remaining_time - cast_time + reaction - (period if not opt_for_ticks else 0))

        # check if any spell should be spell-queued
        spell_queued = self._assignments.spell_queued
        if len(spell_queued) > 0:
            min_assign, min_time = None, 0
            for assignment in spell_queued:
                timeline = self._timelines[assignment.identifier]
                if len(timeline) == 0 or timeline[-1].end < current_time:
                    continue
                remaining = timeline[-1].end - current_time
                if min_assign is None or min_time > remaining:
                    min_time = remaining
                    min_assign = assignment
            # if not true, means that a higher priority spell should have been applied
            assert min_assign is not None
            return -1, min_assign

        # wait for the lookahead, or take filler action
        return self._check_filler(current_time, wait, lookahead, character, reaction=reaction)

    def _check_filler(self, current_time, wait, lookahead, character, reaction=0.01):
        """attempt to use wait time to"""
        if not self._assignments.has_filler:
            return wait, None

        filler = self._assignments.filler
        cast_time = filler.spell.cast_time(character)
        downtime = max(character.get_stat(Stats.GCD), cast_time)
        if downtime > lookahead:
            return wait, None

        for target_suffix in self._filler_target_suffixes:
            filler_assignment = FillerAssignment(filler, target_suffix)
            if self._timelines[filler_assignment.identifier].is_up_at(current_time + reaction):
                continue
            return -1, filler_assignment

        new_suffix = "_" + str(len(self._filler_target_suffixes))
        filler_assignment = FillerAssignment(filler, new_suffix)
        self._filler_target_suffixes.append(new_suffix)
        self._timelines[filler_assignment.identifier] = Timeline(str(filler_assignment))
        return -1, filler_assignment

    def stats(self, character, start=0, end=None, on_use=None):
        if end is None:
            end = self.end
        stats = dict()
        stats["timelines"] = dict()
        stats["targets"] = dict()

        targets = {t[1] for t in self._timelines}

        id2assign = {a.identifier: a for a in self._assignments}
        for identifier, timeline in self._timelines.items():
            if identifier not in id2assign:
                comp_character = character
            else:
                comp_character = BuffedCharacter(character, stats_buffs=self._assignments.buffs(id2assign[identifier].target))
            stats["timelines"][timeline.name] = timeline.stats(comp_character, start=start, end=end, on_use=on_use)
            self._per_unit_stats(stats["timelines"][timeline.name], character)

        stats.update(**self._merge_timeline_stats(*stats["timelines"].values()))
        self._per_unit_stats(stats, character, start=start, end=end)
        stats["uptime"] = self._uptime_timeline.uptime(start=start, end=end)
        stats["gcd"] = {
            "used": len(self._gcd_timeline),
            "wasted": len(self._wasted_gcd(character, start=start, end=end))
        }

        for target in targets:
            target_timelines = [stats["timelines"][t.name]
                                for (_, tl_target), t in self._timelines.items()
                                if tl_target == target]
            stats["targets"][target] = self._merge_timeline_stats(*target_timelines)
            self._per_unit_stats(stats["targets"][target], character)

        return stats

    def _regen_ticks(self, character, start=0, end=None):
        if end is None:
            end = self.end
        t = start - (start % 2)
        in_5sr, out_5sr = self._get_regen_per_tick(character)
        ticks, mana = list(), list()
        while t < end:
            before = self._cast_timeline.event_before(t)
            ticks.append(t)
            if before is None or t - before.end > 5:
                mana.append(out_5sr)
            else:
                mana.append(in_5sr)
            t += 2
        return ticks, mana

    def _per_unit_stats(self, stats, character, start=0, end=None):
        duration = stats["duration"]
        stats["hps"] = stats["total_heal"] / duration
        stats["mps"] = stats["total_mana"] / duration
        stats["hpm"] = stats["total_heal"] / stats["total_mana"] if stats["total_mana"] else 0
        stats["mana_regen_ticks"], stats["mana_regen_gained"] = self._regen_ticks(character, start=start, end=end)
        stats["time2oom"] = character.get_stat(Stats.MANA) / ((sum(stats["mana_costs"]) / duration) - (sum(stats["mana_regen_gained"]) / duration))

    def _wasted_gcd(self, character, start=0, end=None):
        if end is None:
            end = self._uptime_timeline.end
        uptime_events = [e for e in self._uptime_timeline if start <= e.start <= end or start <= e.end <= end]
        i = 0
        gcd = character.get_stat(Stats.GCD)
        wasted_gcds = []
        if start < uptime_events[0].start:
            downtime = uptime_events[0].start - start
            wasted = downtime // gcd
            wasted_gcds.extend([start + i * gcd for i in range(int(wasted))])
        while i < len(uptime_events) - 1:
            curr = uptime_events[i]
            _next = uptime_events[i+1]
            downtime = _next.start - curr.end
            wasted = downtime // gcd
            wasted_gcds.extend([curr.end + i * gcd for i in range(int(wasted))])
            i += 1
        if end > uptime_events[-1].end:
            downtime = end - uptime_events[-1].end
            wasted = downtime // gcd
            wasted_gcds.extend([start + i * gcd for i in range(int(wasted))])

        return wasted_gcds

    @classmethod
    def _merge_timeline_stats(cls, *timeline_stats):
        stats = dict()
        stats["start"] = min([t["start"] for t in timeline_stats])
        stats["end"] = min([t["end"] for t in timeline_stats])
        stats["duration"] = stats["end"] - stats["start"]

        mana_ticks, mana_costs, heals, timestamps, string_heals, string_mana = [list() for _ in range(6)]

        for timeline_stat in timeline_stats:
            mana_ticks.extend(timeline_stat["mana_ticks"])
            mana_costs.extend(timeline_stat["mana_costs"])
            heals.extend(timeline_stat["heals"])
            string_heals.extend(timeline_stat["string_heals"])
            string_mana.extend(timeline_stat["string_mana"])
            timestamps.extend(timeline_stat["timestamps"])

        mana_ticks, mana_costs, string_mana = sort_by(mana_ticks, mana_costs, string_mana)
        timestamps, heals, string_heals = sort_by(timestamps, heals, string_heals)
        stats.update(**{
            "mana_ticks": mana_ticks,
            "mana_costs": mana_costs,
            "string_mana": string_mana,
            "mana": sum(mana_costs),
            "heals": heals,
            "string_heals": string_heals,
            "timestamps": timestamps,
            "total_mana": sum(mana_costs),
            "total_heal": sum(heals)
        })
        return stats


def make_on_use_timelines(duration, items, cast_timeline):
    timelines = list()
    for item in items:
        timeline = Timeline(item.name)
        t = 0
        while t <= duration:
            # resolve on use
            if item.stacks == 0:
                timeline.add_on_use_event(OnUseEvent(t, min(t + item.duration, duration) - t, item))
            else:
                current_stacks = item.stacks
                remaining_events = cast_timeline.events_starting_after(t)
                current_event_idx = 0
                actual_duration = 0
                while current_stacks > 0 and current_event_idx < len(remaining_events) \
                        and remaining_events[current_event_idx].end - t < item.duration:
                    current_stacks -= 1
                    current_event = remaining_events[current_event_idx]
                    actual_duration += current_event.end - (t + actual_duration)
                    # if there is a cast and other events, check if following event benefits also of the stack
                    if remaining_events[current_event_idx].duration > 0 and current_event_idx + 1 < len(remaining_events):
                        next_event = remaining_events[current_event_idx + 1]
                        if next_event.end - current_event.end < 1e-3:
                            current_event_idx += 1
                            actual_duration += next_event.end - (t + actual_duration)
                    actual_duration += 1e-6  # to avoid weird equality issues
                    current_event_idx += 1
                timeline.add_on_use_event(OnUseEvent(t, min(t + actual_duration, duration) - t, item))
            t += item.cooldown
        timelines.append(timeline)
    return timelines

