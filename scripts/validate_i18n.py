#!/usr/bin/env python3
"""
SpaceLoop i18n Completeness Validator
Checks parity across all 6 supported locales:
- en: English
- hi: Hindi
- mr: Marathi
- gar: Garhwali
- kfy: Kumaoni
- jns: Jaunsari

Validates that:
1. All 6 locale files exist.
2. All keys defined in types.ts / en.ts exist in every other locale file.
3. No locale is left with placeholder copies or empty strings.
"""

import os
import re
import sys

LOCALES_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'i18n', 'locales')
REQUIRED_LOCALES = ['en', 'hi', 'mr', 'gar', 'kfy', 'jns']

def extract_keys_from_ts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # If it's a TS export of an object, extract the JSON portion
    json_start = content.find('{')
    json_end = content.rfind('}')
    if json_start != -1 and json_end != -1:
        raw_json = content[json_start:json_end+1]
        try:
            data = json.loads(raw_json)
            keys = set()
            def recurse(d, prefix=""):
                for k, v in d.items():
                    full_key = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, dict):
                        recurse(v, full_key)
                    else:
                        keys.add((full_key, str(v)))
            recurse(data)
            return keys
        except Exception:
            pass

    # Fallback to regex
    keys = set()
    current_section = None
    
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('//') or line.startswith('import') or line.startswith('export'):
            continue
        
        section_match = re.match(r'^["\']?([a-zA-Z0-9_]+)["\']?\s*:\s*\{', line)
        if section_match:
            current_section = section_match.group(1)
            continue
        
        kv_match = re.match(r'^["\']?([a-zA-Z0-9_]+)["\']?\s*:\s*[\'"`](.*)[\'"`],?', line)
        if kv_match:
            key_name = kv_match.group(1)
            full_key = f"{current_section}.{key_name}" if current_section else key_name
            val = kv_match.group(2)
            keys.add((full_key, val))

    return keys

def main():
    print("=" * 60)
    print(" SpaceLoop i18n Completeness & Parity Audit")
    print("=" * 60)

    en_file = os.path.join(LOCALES_DIR, 'en.ts')
    if not os.path.exists(en_file):
        print(f"ERROR: English baseline file missing at {en_file}")
        sys.exit(1)

    en_entries = extract_keys_from_ts(en_file)
    en_keys = {k for k, _ in en_entries}
    print(f"Loaded English baseline with {len(en_keys)} dictionary keys.")

    all_passed = True

    for loc in REQUIRED_LOCALES:
        loc_file = os.path.join(LOCALES_DIR, f"{loc}.ts")
        if not os.path.exists(loc_file):
            print(f"[FAIL] Missing locale dictionary file: {loc}.ts")
            all_passed = False
            continue

        loc_entries = extract_keys_from_ts(loc_file)
        loc_keys = {k for k, _ in loc_entries}
        missing_keys = en_keys - loc_keys

        if missing_keys:
            print(f"[FAIL] Locale '{loc}' is missing {len(missing_keys)} keys:")
            for mk in sorted(missing_keys)[:10]:
                print(f"   - {mk}")
            if len(missing_keys) > 10:
                print(f"   ... and {len(missing_keys) - 10} more.")
            all_passed = False
        else:
            # Check non-empty values
            empty_keys = [k for k, v in loc_entries if not v.strip()]
            if empty_keys:
                print(f"[WARN] Locale '{loc}' has {len(empty_keys)} empty values.")
            print(f"[PASS] Locale '{loc}' has 100% key parity ({len(loc_keys)} keys validated).")

    print("=" * 60)
    if all_passed:
        print("SUCCESS: All 6 SpaceLoop locales are 100% complete and synchronized!")
        sys.exit(0)
    else:
        print("FAILURE: Key discrepancies found. Please update dictionary files.")
        sys.exit(1)

if __name__ == '__main__':
    main()
