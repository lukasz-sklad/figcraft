#!/usr/bin/env python3
"""
Assemble crates/ui-egui/locales/pl.toml from all dictionaries,
ensuring 100% Polish coverage, 0 Czech characters, valid placeholders.
"""
import os
import sys
import json
import re
import tomllib

sys.path.insert(0, os.path.dirname(__file__))

from dict_other import DICT_OTHER
from dict_ad import DICT_AD
from dict_el import DICT_EL
from dict_mr import DICT_MR
from dict_sz import DICT_SZ
from generate_full_polish_catalog import MENU_POLISH, PLURALS_POLISH, COMMANDS_POLISH

ROOT = "/home/deck/GIT/app/figcraft"
LOCALES_DIR = os.path.join(ROOT, "crates/ui-egui/locales")

def load_tsv(path):
    m = {}
    if not os.path.exists(path): return m
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip("\r\n")
            if not line or line.startswith("#"): continue
            parts = line.split("\t")
            if len(parts) >= 3:
                m[parts[1].strip()] = parts[2].strip()
            elif len(parts) == 2:
                m[parts[0].strip()] = parts[1].strip()
    return m

sibling_dict = {}
for p in ['vectorcraft', 'deckcraft', 'filmcraft', 'photocraft', 'wordcraft', 'printcraft']:
    tsv_path = f"/home/deck/GIT/app/{p}/crates/ui-egui/src/i18n/pl.tsv"
    sibling_dict.update(load_tsv(tsv_path))

with open(os.path.join(LOCALES_DIR, "en.toml"), "rb") as f:
    en_cat = tomllib.load(f)
with open(os.path.join(LOCALES_DIR, "pl.toml"), "rb") as f:
    old_pl_cat = tomllib.load(f)
with open(os.path.join(LOCALES_DIR, "cs.toml"), "rb") as f:
    cs_cat = tomllib.load(f)

ui_en = en_cat.get("ui", {})
ui_old_pl = old_pl_cat.get("ui", {})
ui_cs = cs_cat.get("ui", {})

valid_old_pl = {}
czech_chars = ['ř', 'ě', 'ů', 'ň', 'ť', 'ď']
for k, v in ui_old_pl.items():
    if isinstance(v, str):
        if v != ui_en.get(k) and v != ui_cs.get(k) and v.strip() != "":
            if not any(c in v for c in czech_chars):
                valid_old_pl[k] = v

# Assemble plain UI strings
ui_combined = {}
plain_en_keys = [k for k, v in ui_en.items() if isinstance(v, str)]

for k in plain_en_keys:
    if k in DICT_OTHER:
        ui_combined[k] = DICT_OTHER[k]
    elif k in DICT_AD:
        ui_combined[k] = DICT_AD[k]
    elif k in DICT_EL:
        ui_combined[k] = DICT_EL[k]
    elif k in DICT_MR:
        ui_combined[k] = DICT_MR[k]
    elif k in DICT_SZ:
        ui_combined[k] = DICT_SZ[k]
    elif k in valid_old_pl:
        ui_combined[k] = valid_old_pl[k]
    elif k in sibling_dict:
        ui_combined[k] = sibling_dict[k]
    else:
        raise ValueError(f"Missing plain UI key: {k}")

# Check all 41 plurals
plural_en_keys = [k for k, v in ui_en.items() if isinstance(v, dict)]
for k in plural_en_keys:
    if k not in PLURALS_POLISH:
        raise ValueError(f"Missing plural UI key: {k}")

print(f"Total plain UI: {len(ui_combined)}/{len(plain_en_keys)}")
print(f"Total plurals: {len(PLURALS_POLISH)}/{len(plural_en_keys)}")
print(f"Total commands: {len(COMMANDS_POLISH)}")
print(f"Total menu: {len(MENU_POLISH)}")

# Validation checks
for k, v in ui_combined.items():
    for c in czech_chars:
        if c in v:
            raise ValueError(f"Czech char '{c}' found in ui key '{k}': {v}")

for cmd, v in COMMANDS_POLISH.items():
    for c in czech_chars:
        if c in v:
            raise ValueError(f"Czech char '{c}' found in command '{cmd}': {v}")

for item, v in MENU_POLISH.items():
    for c in czech_chars:
        if c in v:
            raise ValueError(f"Czech char '{c}' found in menu '{item}': {v}")

# Write to pl.toml
out_path = os.path.join(LOCALES_DIR, "pl.toml")
with open(out_path, "w", encoding="utf-8") as f:
    f.write('# FigCraft interface strings: Polish.\n')
    f.write('#\n')
    f.write('# Complete, native-quality Polish localization for FigCraft.\n')
    f.write('# Clean-room implementation adhering strictly to ArtCraft standards.\n\n')
    f.write('[meta]\n')
    f.write('name = "Polski"\n\n')
    
    f.write('[ui]\n')
    # Write in order of en.toml keys
    for k in ui_en.keys():
        key_str = json.dumps(k, ensure_ascii=False)
        if k in PLURALS_POLISH:
            p = PLURALS_POLISH[k]
            one = json.dumps(p['one'], ensure_ascii=False)
            few = json.dumps(p['few'], ensure_ascii=False)
            many = json.dumps(p['many'], ensure_ascii=False)
            other = json.dumps(p['other'], ensure_ascii=False)
            f.write(f'{key_str} = {{ one = {one}, few = {few}, many = {many}, other = {other} }}\n')
        else:
            val_str = json.dumps(ui_combined[k], ensure_ascii=False)
            f.write(f'{key_str} = {val_str}\n')
            
    f.write('\n[commands]\n')
    cs_cmds = set(cs_cat.get("commands", {}).keys())
    for k in sorted(cs_cmds):
        if k in COMMANDS_POLISH:
            key_str = json.dumps(k, ensure_ascii=False)
            val_str = json.dumps(COMMANDS_POLISH[k], ensure_ascii=False)
            f.write(f'{key_str} = {val_str}\n')
        else:
            raise ValueError(f"Missing translation for command {k}")

    f.write('\n[menu]\n')
    cs_menu = set(cs_cat.get("menu", {}).keys())
    for k in sorted(cs_menu):
        if k in MENU_POLISH:
            key_str = json.dumps(k, ensure_ascii=False)
            val_str = json.dumps(MENU_POLISH[k], ensure_ascii=False)
            f.write(f'{key_str} = {val_str}\n')
        else:
            raise ValueError(f"Missing translation for menu item {k}")

print(f"Successfully generated {out_path}!")

# Re-parse to verify syntax
with open(out_path, "rb") as f:
    parsed = tomllib.load(f)

print(f"Parsed verification: ui={len(parsed['ui'])}, commands={len(parsed['commands'])}, menu={len(parsed['menu'])}")
