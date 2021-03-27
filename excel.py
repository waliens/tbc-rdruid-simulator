import os
import re
from abc import abstractmethod
from collections import defaultdict

from xlsxwriter import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell

from buff import BUFFS
from character import Stats, Character
from spell import HealingSpell, HEALING_TOUCH, REJUVENATION, REGROWTH, LIFEBLOOM, TRANQUILITY
from talents import Talents


def sheet_cell_ref(sheet, row, col):
    return "'" + sheet.name + "'!" + xl_rowcol_to_cell(row, col, row_abs=True, col_abs=True)


def parse_formula(formula, cell_map):
    pattern = re.compile(r"#([a-zA-Z_0-9 -]+)\.([a-zA-Z_0-9 -]+)#")
    array = []
    start = 0
    for match in pattern.finditer(formula):
        mstart, mend = match.regs[0][0], match.regs[-1][1]
        array.append(formula[start:mstart])
        array.append(cell_map[(match.group(1), match.group(2))])
        start = mend + 1
    array.append(formula[start:])
    return "".join(array)


class ThematicSheet(object):
    def __init__(self, workbook, sheet, cell_map, offset=(0, 0)):
        self._sheet_name = sheet.name
        self._worksheet = sheet
        self._workbook = workbook
        self._cell_map = cell_map
        self._offset = offset

    @classmethod
    def create_from_sheet(cls, workbook, sheet, cell_map, *args, **kwargs):
        return cls(workbook, sheet, cell_map, *args, **kwargs)

    @classmethod
    def create_new_sheet(cls, workbook, sheet_name, cell_map, *args, **kwargs):
        return cls(workbook, workbook.add_worksheet(name=sheet_name), cell_map, *args, **kwargs)

    @property
    def offset(self):
        return self._offset

    @property
    def offset_row(self):
        return self._offset[0]

    @property
    def offset_col(self):
        return self._offset[1]

    @property
    @abstractmethod
    def n_cols(self):
        pass

    @property
    @abstractmethod
    def n_rows(self):
        pass

    @property
    def sheet_name(self):
        return self._sheet_name

    @property
    def workbook(self):
        return self._workbook

    @property
    def worksheet(self):
        return self._worksheet

    @property
    def cell_map(self):
        return self._cell_map

    def human_readable(self, s):
        return s.replace("_", " ").capitalize()

    @abstractmethod
    def write_sheet(self):
        pass

    def write_cell(self, row, col, val, formula=False):
        (self.worksheet.write if not formula else self.worksheet.write_formula)(row, col, val)
        return col

    def write_cell_and_map(self, row, col, val, cm_group, cm_key, formula=False):
        self.cell_map[(cm_group, cm_key)] = sheet_cell_ref(self.worksheet, row, col)
        return self.write_cell(row, col, val, formula=formula)


class CharacterSheetGenerator(ThematicSheet):
    def __init__(self, workbook, sheet, cell_map, character, descr="", offset=(0, 0)):
        super().__init__(workbook, sheet, cell_map, offset=offset)
        self._character = character
        self._description = descr

        talent_img_base_url = "https://legacy-wow.com/talentcalcs/tbc/shared/global/talents/druid/images/restoration"
        self._talents_url = {
            talent_name: "{}/{}.jpg".format(talent_img_base_url, talent_name.replace("_", ""))
            for talent_name, _ in Talents.all()
        }

    @property
    def all_stats(self):
        return list(Stats.primary()) + list(Stats.secondary()) + list(Stats.computed())

    def write_talents(self):
        first_row, first_col = self.offset
        first_col += 4
        self.worksheet.merge_range(first_row, first_col, first_row, first_col + 5, 'Talents')
        self.worksheet.merge_range(first_row + 1, first_col, first_row + 1, first_col + 2, 'Name')
        col = self.write_cell(first_row + 1, first_col + 3, "Value")
        self.write_cell(first_row + 1, col + 1, "Max")

        for i, talent in enumerate(Talents.all()):
            col = self.write_cell(first_row + i + 2, first_col, self.human_readable(talent[0]))
            col = self.write_cell(first_row + i + 2, col + 2, "IMAGE(\"{}\")".format(self._talents_url[talent[0]]), formula=True)
            col = self.write_cell_and_map(first_row + i + 2, col + 1, self._character.talents.get(talent[0]),
                                          cm_group="Talents", cm_key=talent[0])
            self.write_cell(first_row + i + 2, col + 1, talent[1])

    def _write_stat_row(self, row, col, stat):
        col = self.write_cell(row, col, self.human_readable(stat))
        base_formula = parse_formula(self._character.get_base_excel_formula(stat), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, base_formula, "Stats", Stats.base(stat), formula=True)
        buff_formula = parse_formula(self._character.get_buffed_excel_formula(stat), self.cell_map)
        self.write_cell_and_map(row, col + 1, buff_formula, "Stats", stat, formula=True)
        return row + 1, col

    def write_character(self):
        first_row, first_col = self.offset
        if len(self._description) > 0:
            self.write_cell(first_row, first_col, "Descr.")
            self.write_cell(first_row, first_col + 1, self._description)
            first_row += 1

        self.worksheet.merge_range(first_row, first_col, first_row, first_col + 1, "Level")
        self.write_cell_and_map(first_row, first_col + 2, self._character.level, cm_group="Character", cm_key="level")
        self.worksheet.merge_range(first_row + 1, first_col, first_row + 1, first_col + 1, "Tree aura on target")
        self.write_cell_and_map(first_row + 1, first_col + 2, 1, "Target", "tree_of_life")
        self.worksheet.merge_range(first_row + 2, first_col, first_row + 2, first_col + 2, 'Primary')
        self.write_cell(first_row + 3, first_col, "Stat")
        self.write_cell(first_row + 3, first_col + 1, "Base")
        self.write_cell(first_row + 3, first_col + 2, "Buffed")

        row = first_row + 4
        for stat in Stats.primary():
            row, _ = self._write_stat_row(row, first_col, stat)

        self.worksheet.merge_range(row, first_col, row, first_col + 2, 'Secondary')
        self.write_cell(row + 1, first_col, "Stat")
        self.write_cell(row + 1, first_col + 1, "Base")
        self.write_cell(row + 1, first_col + 2, "Buffed")
        row += 2

        for stat in Stats.secondary():
            row, _ = self._write_stat_row(row, first_col, stat)

        self.worksheet.merge_range(row, first_col, row, first_col + 1, 'Others')
        self.write_cell(row + 1, first_col, "Stat")
        self.write_cell(row + 1, first_col + 1, "Base")
        self.write_cell(row + 1, first_col + 2, "Buffed")
        row += 2

        for i, stat in enumerate(Stats.computed()):
            row, _ = self._write_stat_row(row, first_col, stat)

    def write_buffs(self):
        first_row, first_col = self.offset
        first_col += 10
        self.worksheet.merge_range(first_row, first_col, first_row, first_col + 1, 'Buffs')
        self.write_cell(first_row + 1, first_col, "Name")
        self.write_cell(first_row + 1, first_col + 3, "Active")

        row = first_row + 2
        for name, buff in BUFFS.items():
            col = self.write_cell(row, first_col, self.human_readable(name))
            self.write_cell_and_map(row, col + 3, int(self._character.buffs.has_buff(name)), "Buff", name)
            row += 1

    def write_sheet(self):
        self.write_buffs()
        self.write_talents()
        self.write_character()

    @property
    def n_cols(self):
        return 11

    @property
    def n_rows(self):
        return max(
            len(self._character.talents) + (1 if len(self._description) > 0 else 0),
            7 + len(self.all_stats),
            2 + len(BUFFS)) + 1


class SpellSheetGenerator(ThematicSheet):
    def __init__(self, workbook, sheet, cell_map, spell_ranks, offset=(0, 0)):
        super().__init__(workbook, sheet, cell_map, offset=offset)
        self._spells = spell_ranks

    @abstractmethod
    def write_spell_header(self):
        pass

    @abstractmethod
    def write_spell(self, row, spell):
        pass

    @abstractmethod
    def write_table_from_bh(self):
        pass

    def write_sheet(self):
        self.write_spell_header()
        for i, spell in enumerate(self._spells):
            self.write_spell(self.offset_row + 2 + i, spell)
        # self.write_table_from_bh()

    @property
    def n_rows(self):
        return 2 + len(self._spells)


class HealingTouchSheetGenerator(SpellSheetGenerator):
    def write_spell(self, row, spell):
        col = self.write_cell_and_map(row, self.offset_col, spell.rank, spell.identifier, "rank")
        col = self.write_cell_and_map(row, col + 1, spell.level, spell.identifier, "level")
        col = self.write_cell_and_map(row, col + 1, spell.mana_cost, spell.identifier, "base_mana_cost")
        self.cell_map[(spell.identifier, "mana_cost")] = self.cell_map[(spell.identifier, "base_mana_cost")]
        col = self.write_cell_and_map(row, col + 1, spell.cast_time, spell.identifier, "base_cast_time")
        col = self.write_cell_and_map(row, col + 1, spell.min_heal, spell.identifier, "base_min_heal")
        col = self.write_cell_and_map(row, col + 1, spell.max_heal, spell.identifier, "base_max_heal")
        col = self.write_cell_and_map(row, col + 1, parse_formula(
            spell.coef_excel_formula, self.cell_map), spell.identifier, "coef", formula=True)
        cast_time = parse_formula("(#{}.base_cast_time# - #Talents.{}# * 0.1) / (1 + #Stats.{}#)".format(
            spell.identifier, Talents.NATURALIST[0], Stats.SPELL_HASTE), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, cast_time, spell.identifier, "cast_time", formula=True)
        formula_min, formula_max = spell.excel_formula
        col = self.write_cell_and_map(row, col + 1, parse_formula(formula_min, self.cell_map),
                                      spell.identifier, "min_heal", formula=True)
        col = self.write_cell_and_map(row, col + 1, parse_formula(formula_max, self.cell_map),
                                      spell.identifier, "max_heal", formula=True)
        avg_heal = parse_formula("(1 + #Stats.{crit}# / 2) * (#{spell}.min_heal# + #{spell}.max_heal#) / 2".format(
            crit=Stats.SPELL_CRIT, spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, avg_heal, spell.identifier, "avg_heal", formula=True)
        hps = parse_formula("(#{spell}.avg_heal# / MAX(#Stats.{gcd}#; #{spell}.cast_time#))".format(gcd=Stats.GCD, spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hps, spell.identifier, "hps", formula=True)
        hpm = parse_formula("(#{spell}.avg_heal# / #{spell}.mana_cost#)".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hpm, spell.identifier, "hpm", formula=True)
        mps = parse_formula("(#{spell}.mana_cost# / MAX(#Stats.{gcd}#; #{spell}.cast_time#))".format(gcd=Stats.GCD, spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, mps, spell.identifier, "mps", formula=True)
        return col

    def write_spell_header(self):
        first_row, first_col = self.offset
        subtitle_row = first_row + 1
        col = self.write_cell(subtitle_row, first_col, "rank")
        col = self.write_cell(subtitle_row, col + 1, "level")
        col = self.write_cell(subtitle_row, col + 1, "mana")
        col = self.write_cell(subtitle_row, col + 1, "base cast time")
        col = self.write_cell(subtitle_row, col + 1, "min")
        col = self.write_cell(subtitle_row, col + 1, "max")
        col = self.write_cell(subtitle_row, col + 1, "coef")
        self.worksheet.merge_range(first_row, first_col, first_row, col, "Base data (healing touch)")
        second_col = col + 1
        col = self.write_cell(subtitle_row, second_col, "cast time")
        col = self.write_cell(subtitle_row, col + 1, "min")
        col = self.write_cell(subtitle_row, col + 1, "max")
        col = self.write_cell(subtitle_row, col + 1, "avg (w. crit)")
        col = self.write_cell(subtitle_row, col + 1, "hps")
        col = self.write_cell(subtitle_row, col + 1, "hpm")
        col = self.write_cell(subtitle_row, col + 1, "mps")
        self.worksheet.merge_range(first_row, second_col, first_row, col, "Effective healing")
        return col

    def write_table_from_bh(self):
        first_row = self.offset_row + len(self._spells) + 3
        first_col = self.offset_col

        self.write_cell(first_row, first_col, "Bonus heal")
        for j, spell in enumerate(self._spells):
            self.write_cell(first_row, first_col + j + 1, "Rank " + str(spell.rank))

        for i, bh in enumerate(range(0, 3001, 100)):
            self.write_cell(first_row + i + 1, first_col, str(bh))

        for j, spell in enumerate(self._spells):
            formula_min, formula_max = spell.excel_formula
            for i, bh in enumerate(range(0, 3001, 100)):
                row = first_row + i + 1
                col = first_col + j + 1
                min_formula = formula_min.replace("#Stats.{}#".format(Stats.BONUS_HEALING), xl_rowcol_to_cell(row, first_col, col_abs=True))
                max_formula = formula_max.replace("#Stats.{}#".format(Stats.BONUS_HEALING), xl_rowcol_to_cell(row, first_col, col_abs=True))
                formula = "(1 + #Stats.{crit}# / 2) * ({min} + {max}) / 2".format(
                    crit=Stats.SPELL_CRIT, min=min_formula, max=max_formula, spell=spell.identifier)
                self.write_cell(row, col, parse_formula(formula, self.cell_map), formula=True)

    @property
    def n_cols(self):
        return 14


class RejuvenationSheetGenerator(SpellSheetGenerator):
    def write_spell(self, row, spell):
        col = self.write_cell_and_map(row, self.offset_col, spell.rank, spell.identifier, "rank")
        col = self.write_cell_and_map(row, col + 1, spell.level, spell.identifier, "level")
        col = self.write_cell_and_map(row, col + 1, spell.mana_cost, spell.identifier, "base_mana_cost")
        col = self.write_cell_and_map(row, col + 1, spell.duration, spell.identifier, "base_hot_duration")
        col = self.write_cell_and_map(row, col + 1, spell.hot_heal / spell.ticks, spell.identifier, "base_hot_tick")
        col = self.write_cell_and_map(row, col + 1, spell.hot_heal, spell.identifier, "base_hot_total")
        col = self.write_cell_and_map(row, col + 1, parse_formula(spell.coef_excel_formula, self.cell_map),
                                      spell.identifier, "coef", formula=True)
        mana_cost = parse_formula("MAX(0; #{spell}.base_mana_cost# - 20 * #Talents.{tree}#)".format(
                                  spell=spell.identifier, tree=Talents.TREE_OF_LIFE[0]), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, mana_cost, spell.identifier, "mana_cost", formula=True)
        col = self.write_cell_and_map(row, col + 1, parse_formula(spell.excel_formula, self.cell_map),
                                      spell.identifier, "hot_tick", formula=True)
        hot_tick = parse_formula("(#{spell}.hot_tick# * {ticks})".format(spell=spell.identifier, ticks=spell.ticks), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hot_tick, spell.identifier, "hot_total", formula=True)
        hps = parse_formula("(#{spell}.hot_total# / #{spell}.base_hot_duration#)".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hps, spell.identifier, "hps", formula=True)
        hpm = parse_formula("(#{spell}.hot_total# / #{spell}.mana_cost#)".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hpm, spell.identifier, "hpm", formula=True)
        mps = parse_formula("(#{spell}.mana_cost# / #{spell}.base_hot_duration#)".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, mps, spell.identifier, "mps", formula=True)
        return col

    def write_spell_header(self):
        first_row, first_col = self.offset
        subtitle_row = first_row + 1
        col = self.write_cell(subtitle_row, first_col, "rank")
        col = self.write_cell(subtitle_row, col + 1, "level")
        col = self.write_cell(subtitle_row, col + 1, "mana")
        col = self.write_cell(subtitle_row, col + 1, "duration")
        col = self.write_cell(subtitle_row, col + 1, "tick")
        col = self.write_cell(subtitle_row, col + 1, "total")
        col = self.write_cell(subtitle_row, col + 1, "coef")
        self.worksheet.merge_range(first_row, first_col, first_row, col, "Base data (rejuvenation)")
        second_col = col + 1
        col = self.write_cell(subtitle_row, col + 1, "mana_cost")
        col = self.write_cell(subtitle_row, col + 1, "tick")
        col = self.write_cell(subtitle_row, col + 1, "total")
        col = self.write_cell(subtitle_row, col + 1, "hps")
        col = self.write_cell(subtitle_row, col + 1, "hpm")
        col = self.write_cell(subtitle_row, col + 1, "mps")
        self.worksheet.merge_range(first_row, second_col, first_row, col, "Effective healing")
        return col

    def write_table_from_bh(self):
        pass

    @property
    def n_cols(self):
        return 13


class RegrowthSheetGenerator(SpellSheetGenerator):
    def write_spell(self, row, spell):
        col = self.write_cell_and_map(row, self.offset_col, spell.rank, spell.identifier, "rank")
        col = self.write_cell_and_map(row, col + 1, spell.level, spell.identifier, "level")
        col = self.write_cell_and_map(row, col + 1, spell.mana_cost, spell.identifier, "base_mana_cost")
        col = self.write_cell_and_map(row, col + 1, spell.cast_time, spell.identifier, "base_cast_time")
        col = self.write_cell_and_map(row, col + 1, spell.duration, spell.identifier, "base_hot_duration")
        col = self.write_cell_and_map(row, col + 1, spell.min_direct_heal, spell.identifier, "base_min_direct_heal")
        col = self.write_cell_and_map(row, col + 1, spell.max_direct_heal, spell.identifier, "base_max_direct_heal")
        col = self.write_cell_and_map(row, col + 1, spell.hot_heal, spell.identifier, "base_hot_total")
        col = self.write_cell_and_map(row, col + 1, spell.hot_heal / spell.ticks, spell.identifier, "base_hot_tick")
        coef_direct, coef_hot = spell.coef_excel_formula
        col = self.write_cell_and_map(row, col + 1, parse_formula(coef_direct, self.cell_map), cm_group=spell.identifier, cm_key="direct_coef", formula=True)
        col = self.write_cell_and_map(row, col + 1, parse_formula(coef_hot, self.cell_map), cm_group=spell.identifier, cm_key="hot_coef", formula=True)
        mana_cost = parse_formula("MAX(0; #{spell}.base_mana_cost# - 20 * #Talents.{tree}#)".format(spell=spell.identifier, tree=Talents.TREE_OF_LIFE[0]), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, mana_cost, spell.identifier, "mana_cost", formula=True)
        direct_min, direct_max, hot_tick = spell.excel_formula
        col = self.write_cell_and_map(row, col + 1, parse_formula(direct_min, self.cell_map), spell.identifier, "min_heal", formula=True)
        col = self.write_cell_and_map(row, col + 1, parse_formula(direct_max, self.cell_map), spell.identifier, "max_heal", formula=True)
        avg_heal = parse_formula("(1 + #Stats.{crit}# / 2) * (#{spell}.min_heal# + #{spell}.max_heal#) / 2".format(crit=Stats.SPELL_CRIT, spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, avg_heal, spell.identifier, "avg_heal", formula=True)
        col = self.write_cell_and_map(row, col + 1, parse_formula(hot_tick, self.cell_map), spell.identifier, "hot_tick", formula=True)
        hot_tick = parse_formula("(#{spell}.hot_tick# * {ticks})".format(spell=spell.identifier, ticks=spell.ticks), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hot_tick, spell.identifier, "hot_total", formula=True)
        hps = parse_formula("(#{spell}.avg_heal# + #{spell}.hot_total#) / #{spell}.base_hot_duration#".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hps, spell.identifier, "hps", formula=True)
        hpm = parse_formula("(#{spell}.avg_heal# + #{spell}.hot_total#) / #{spell}.mana_cost#".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hpm, spell.identifier, "hpm", formula=True)
        mps = parse_formula("#{spell}.mana_cost# / #{spell}.base_hot_duration#".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, mps, spell.identifier, "mps", formula=True)
        return col

    def write_spell_header(self):
        first_row, first_col = self.offset
        subtitle_row = first_row + 1
        col = self.write_cell(subtitle_row, first_col, "rank")
        col = self.write_cell(subtitle_row, col + 1, "level")
        col = self.write_cell(subtitle_row, col + 1, "mana")
        col = self.write_cell(subtitle_row, col + 1, "cast time")
        col = self.write_cell(subtitle_row, col + 1, "duration")
        col = self.write_cell(subtitle_row, col + 1, "direct min")
        col = self.write_cell(subtitle_row, col + 1, "direct max")
        col = self.write_cell(subtitle_row, col + 1, "hot total")
        col = self.write_cell(subtitle_row, col + 1, "hot tick")
        col = self.write_cell(subtitle_row, col + 1, "coef direct")
        col = self.write_cell(subtitle_row, col + 1, "coef hot")
        self.worksheet.merge_range(first_row, first_col, first_row, col, "Base data (regrowth)")
        second_col = col + 1
        col = self.write_cell(subtitle_row, col + 1, "mana_cost")
        col = self.write_cell(subtitle_row, col + 1, "min")
        col = self.write_cell(subtitle_row, col + 1, "max")
        col = self.write_cell(subtitle_row, col + 1, "avg (w. crit)")
        col = self.write_cell(subtitle_row, col + 1, "tick")
        col = self.write_cell(subtitle_row, col + 1, "total")
        col = self.write_cell(subtitle_row, col + 1, "hps")
        col = self.write_cell(subtitle_row, col + 1, "hpm")
        col = self.write_cell(subtitle_row, col + 1, "mps")
        self.worksheet.merge_range(first_row, second_col, first_row, col, "Effective healing")
        return col

    def write_table_from_bh(self):
        pass

    @property
    def n_cols(self):
        return 20


class LifebloomSheetGenerator(SpellSheetGenerator):
    def write_spell(self, row, spell):
        col = self.write_cell_and_map(row, self.offset_col, spell.rank, spell.identifier, "rank")
        col = self.write_cell_and_map(row, col + 1, spell.level, spell.identifier, "level")
        col = self.write_cell_and_map(row, col + 1, spell.mana_cost, spell.identifier, "base_mana_cost")
        col = self.write_cell_and_map(row, col + 1, spell.duration, spell.identifier, "base_hot_duration")
        col = self.write_cell_and_map(row, col + 1, spell.direct_heal, spell.identifier, "base_direct_heal")
        col = self.write_cell_and_map(row, col + 1, spell.hot_heal, spell.identifier, "base_hot_total")
        col = self.write_cell_and_map(row, col + 1, spell.hot_heal / spell.ticks, spell.identifier, "base_hot_tick")
        coef_direct, coef_hot = spell.coef_excel_formula
        col = self.write_cell_and_map(row, col + 1, parse_formula(coef_direct, self.cell_map),
                                      cm_group=spell.identifier, cm_key="direct_coef", formula=True)
        col = self.write_cell_and_map(row, col + 1, parse_formula(coef_hot, self.cell_map),
                                      cm_group=spell.identifier, cm_key="hot_coef", formula=True)
        mana_cost = parse_formula("MAX(0; #{spell}.base_mana_cost# - 20 * #Talents.{tree}#)".format(spell=spell.identifier, tree=Talents.TREE_OF_LIFE[0]), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, mana_cost, spell.identifier, "mana_cost", formula=True)
        direct_heal, _, hot_heal = spell.excel_formula
        avg_heal = parse_formula("(1 + #Stats.{crit}# / 2) * {direct}".format(crit=Stats.SPELL_CRIT, direct=direct_heal), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, avg_heal, spell.identifier, "avg_direct_heal", formula=True)
        hot_heal = parse_formula(hot_heal, self.cell_map)
        col = self.write_cell_and_map(row, col + 1, parse_formula(hot_heal, self.cell_map), spell.identifier, "hot_tick1", formula=True)
        hot_tick2 = parse_formula("(#{spell}.hot_tick1# * 2)".format(spell=spell.identifier), cell_map=self.cell_map)
        hot_tick3 = parse_formula("(#{spell}.hot_tick1# * 3)".format(spell=spell.identifier), cell_map=self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hot_tick2, spell.identifier, "hot_tick2", formula=True)
        col = self.write_cell_and_map(row, col + 1, hot_tick3, spell.identifier, "hot_tick3", formula=True)
        hot_total = parse_formula("(#{spell}.hot_tick1# * {ticks})".format(spell=spell.identifier, ticks=spell.ticks), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hot_total, spell.identifier, "hot_total1", formula=True)
        hot_total2 = parse_formula("(#{spell}.hot_total1# * 2)".format(spell=spell.identifier), cell_map=self.cell_map)
        hot_total3 = parse_formula("(#{spell}.hot_total1# * 3)".format(spell=spell.identifier), cell_map=self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hot_total2, spell.identifier, "hot_total2", formula=True)
        col = self.write_cell_and_map(row, col + 1, hot_total3, spell.identifier, "hot_total3", formula=True)
        return col

    def write_spell_header(self):
        first_row, first_col = self.offset
        subtitle_row = first_row + 1
        col = self.write_cell(subtitle_row, first_col, "rank")
        col = self.write_cell(subtitle_row, col + 1, "level")
        col = self.write_cell(subtitle_row, col + 1, "mana")
        col = self.write_cell(subtitle_row, col + 1, "duration")
        col = self.write_cell(subtitle_row, col + 1, "bloom")
        col = self.write_cell(subtitle_row, col + 1, "hot total")
        col = self.write_cell(subtitle_row, col + 1, "hot tick")
        col = self.write_cell(subtitle_row, col + 1, "coef direct")
        col = self.write_cell(subtitle_row, col + 1, "coef hot")
        self.worksheet.merge_range(first_row, first_col, first_row, col, "Base data (lifebloom)")
        second_col = col + 1
        col = self.write_cell(subtitle_row, col + 1, "mana_cost")
        col = self.write_cell(subtitle_row, col + 1, "direct (w. crit)")
        col = self.write_cell(subtitle_row, col + 1, "tick 1")
        col = self.write_cell(subtitle_row, col + 1, "tick 2")
        col = self.write_cell(subtitle_row, col + 1, "tick 3")
        col = self.write_cell(subtitle_row, col + 1, "total 1")
        col = self.write_cell(subtitle_row, col + 1, "total 2")
        col = self.write_cell(subtitle_row, col + 1, "total 3")
        self.worksheet.merge_range(first_row, second_col, first_row, col, "Effective healing")
        return col

    def write_table_from_bh(self):
        pass

    @property
    def n_cols(self):
        return 17


class TranquilitySheetGenerator(SpellSheetGenerator):
    def write_spell(self, row, spell):
        col = self.write_cell_and_map(row, self.offset_col, spell.rank, spell.identifier, "rank")
        col = self.write_cell_and_map(row, col + 1, spell.level, spell.identifier, "level")
        col = self.write_cell_and_map(row, col + 1, spell.mana_cost, spell.identifier, "base_mana_cost")
        col = self.write_cell_and_map(row, col + 1, spell.duration, spell.identifier, "base_hot_duration")
        col = self.write_cell_and_map(row, col + 1, spell.hot_heal / spell.ticks, spell.identifier, "base_hot_tick")
        col = self.write_cell_and_map(row, col + 1, spell.hot_heal, spell.identifier, "base_hot_total")
        col = self.write_cell_and_map(row, col + 1, parse_formula(spell.coef_excel_formula, self.cell_map),
                                      spell.identifier, "coef", formula=True)
        mana_cost = parse_formula("MAX(0; #{spell}.base_mana_cost# - 20 * #Talents.{tree}#)".format(
                                  spell=spell.identifier, tree=Talents.TREE_OF_LIFE[0]), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, mana_cost, spell.identifier, "mana_cost", formula=True)
        col = self.write_cell_and_map(row, col + 1, parse_formula(spell.excel_formula, self.cell_map),
                                      spell.identifier, "hot_tick", formula=True)
        hot_total = parse_formula("(#{spell}.hot_tick# * {ticks})".format(spell=spell.identifier, ticks=spell.ticks), self.cell_map)
        hot_total5 = parse_formula("(#{spell}.hot_tick# * {ticks} * 5)".format(spell=spell.identifier, ticks=spell.ticks), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hot_total, spell.identifier, "hot_total", formula=True)
        col = self.write_cell_and_map(row, col + 1, hot_total5, spell.identifier, "hot_total5", formula=True)
        hps = parse_formula("(#{spell}.hot_total# / #{spell}.base_hot_duration#)".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hps, spell.identifier, "hps", formula=True)
        hpm = parse_formula("(#{spell}.hot_total# / #{spell}.mana_cost#)".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, hpm, spell.identifier, "hpm", formula=True)
        mps = parse_formula("(#{spell}.mana_cost# / #{spell}.base_hot_duration#)".format(spell=spell.identifier), self.cell_map)
        col = self.write_cell_and_map(row, col + 1, mps, spell.identifier, "mps", formula=True)
        return col

    def write_spell_header(self):
        first_row, first_col = self.offset
        subtitle_row = first_row + 1
        col = self.write_cell(subtitle_row, first_col, "rank")
        col = self.write_cell(subtitle_row, col + 1, "level")
        col = self.write_cell(subtitle_row, col + 1, "mana")
        col = self.write_cell(subtitle_row, col + 1, "duration")
        col = self.write_cell(subtitle_row, col + 1, "tick")
        col = self.write_cell(subtitle_row, col + 1, "total")
        col = self.write_cell(subtitle_row, col + 1, "coef")
        self.worksheet.merge_range(first_row, first_col, first_row, col, "Base data (tranquility)")
        second_col = col + 1
        col = self.write_cell(subtitle_row, col + 1, "mana_cost")
        col = self.write_cell(subtitle_row, col + 1, "tick")
        col = self.write_cell(subtitle_row, col + 1, "total")
        col = self.write_cell(subtitle_row, col + 1, "total 5")
        col = self.write_cell(subtitle_row, col + 1, "hps")
        col = self.write_cell(subtitle_row, col + 1, "hpm")
        col = self.write_cell(subtitle_row, col + 1, "mps")
        self.worksheet.merge_range(first_row, second_col, first_row, col, "Effective healing")
        return col

    def write_table_from_bh(self):
        pass

    @property
    def n_cols(self):
        return 14


class AssigmentsSheet(ThematicSheet):
    def __init__(self, workbook, sheet, cell_map, assigments, description="", offset=(0, 0)):
        super().__init__(workbook, sheet, cell_map, offset=offset)
        self._assigments = assigments
        self._description = description

    @property
    def n_cols(self):
        return 2

    @property
    def n_rows(self):
        return 2 + len(self._assigments)

    def write_sheet(self):
        row, col = self.offset
        self.worksheet.merge_range(row, col, row, col + 1, "Healing assignment")
        self.write_cell(row + 1, col, "Desc.:")
        self.write_cell(row + 1, col + 1, self._description)
        self.write_cell(row + 2, col, "Prio.")
        self.write_cell(row + 2, col + 1, "Assigment")
        for i, assigment in enumerate(self._assigments):
            descriptor = [
                self.human_readable(assigment.spell.name),
                "rank={}".format(assigment.spell.rank),
            ]
            if assigment.spell.type in {HealingSpell.TYPE_HYBRID, HealingSpell.TYPE_HOT}:
                descriptor.append("allow_fade={}".format(assigment.allow_fade))
                if assigment.spell.max_stacks > 1 and assigment.allow_fade:
                    descriptor.append("max_stacks={}".format(assigment.fade_at_stacks))
            self.write_cell(row + i + 3, col, i + 1)
            self.write_cell(row + i + 3, col + 1, ", ".join(descriptor))


class ComparisonSummarySheet(ThematicSheet):
    def __init__(self, workbook, sheet, cell_map, combinations, cell_maps, offset=(0, 0)):
        super().__init__(workbook, sheet, cell_map, offset)
        self._combinations = {(c[0], c[3]): c for c in combinations}
        self._c_names = list({c[0] for c in combinations})
        self._r_names = list({c[3] for c in combinations})
        self._all_cell_maps = cell_maps

    @property
    def n_cols(self):
        return len(self._c_names) + 1

    @property
    def n_rows(self):
        return len(self._r_names) + 1

    def write_sheet(self):
        first_row, first_col = self._offset
        for i, r_name in enumerate(self._r_names):
            self.write_cell(first_row + 1 + i, first_col, r_name)
        for j, c_name in enumerate(self._c_names):
            self.write_cell(first_row, first_col + j + 1, c_name)
            for i, r_name in enumerate(self._r_names):
                merged_name = "{}_{}".format(c_name, r_name)
                _, character, _, _, assigments, _, stats = self._combinations[(c_name, r_name)]
                formula = ComparisonSummarySheet.to_formula(stats["string_heals"])
                formula = "{} / {}".format(formula, stats["duration"])
                parsed = parse_formula(formula, cell_map=self._all_cell_maps[merged_name])
                self.write_cell(first_row + 1 + i, first_col + 1 + j, parsed, formula=True)

    @staticmethod
    def to_formula(heals):
        heal_dict = defaultdict(lambda: 0)
        for heal_tokken in heals:
            heal_dict[heal_tokken] += 1
        return "(" + "+".join([
            "({mult} * ({form}))".format(mult=mult, form=form)
            for form, mult in heal_dict.items()
        ]) + ")"


def write_spell_charac_sheet(workbook, name, character, offset=(0, 0)):
    cell_map = dict()

    charac_sheet = CharacterSheetGenerator.create_new_sheet(workbook, name, cell_map, character, offset=offset)
    charac_sheet.write_sheet()

    spell_sheets = [
        (HealingTouchSheetGenerator, HEALING_TOUCH),
        (RejuvenationSheetGenerator, REJUVENATION),
        (RegrowthSheetGenerator, REGROWTH),
        (LifebloomSheetGenerator, LIFEBLOOM),
        (TranquilitySheetGenerator, TRANQUILITY)
    ]

    row = offset[0]
    prev_sheet = charac_sheet
    for cls, spells in spell_sheets:
        row += prev_sheet.n_rows + 2
        spell_sheet = cls.create_from_sheet(workbook, charac_sheet.worksheet, cell_map, spells, offset=(row, offset[1]))
        spell_sheet.write_sheet()
        prev_sheet = spell_sheet

    return cell_map


def write_spells_wb(character, name, outfolder):
    wb = Workbook(os.path.join(outfolder, "character_{}.xlsx".format(name)))
    write_spell_charac_sheet(wb, name, character)
    wb.close()


def write_compare_setups_wb(configs, outfolder):
    wb = Workbook(os.path.join(outfolder, "compare.xlsx"))
    cell_maps = defaultdict(lambda: dict())
    for c_name, character, c_descr, r_name, assigments, r_descr, stats in configs:
        merged_name = "{}_{}".format(c_name, r_name)
        sheet = wb.add_worksheet(name=merged_name[:31])
        cell_map = cell_maps[merged_name]
        char_part = CharacterSheetGenerator.create_from_sheet(wb, sheet, cell_map, character, c_descr, offset=(0, 0))
        assi_part = AssigmentsSheet.create_from_sheet(wb, sheet, cell_map, assigments, r_descr, offset=(0, char_part.n_cols + 1))
        spells_start_row = max(char_part.offset_row + char_part.n_rows + 1, assi_part.offset_row + assi_part.n_rows + 1)
        htou_part = HealingTouchSheetGenerator.create_from_sheet(wb, sheet, cell_map, HEALING_TOUCH, offset=(spells_start_row, 0))
        reju_part = RejuvenationSheetGenerator.create_from_sheet(wb, sheet, cell_map, REJUVENATION, offset=(htou_part.offset_row + htou_part.n_rows + 1, 0))
        regr_part = RegrowthSheetGenerator.create_from_sheet(wb, sheet, cell_map, REGROWTH, offset=(reju_part.offset_row + reju_part.n_rows + 1, 0))
        lblo_part = LifebloomSheetGenerator.create_from_sheet(wb, sheet, cell_map, LIFEBLOOM, offset=(regr_part.offset_row + regr_part.n_rows + 1, 0))

        for s in [char_part, assi_part, htou_part, reju_part, regr_part, lblo_part]:
            s.write_sheet()

    comp = ComparisonSummarySheet.create_new_sheet(wb, "summary", dict(), configs, cell_maps)
    comp.write_sheet()
    wb.close()
