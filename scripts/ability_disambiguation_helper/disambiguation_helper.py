import data
import asyncio
import config
import collections
import re


def description_line(generic_name, description):
    description = re.sub(r"\.\s+", ". ", description.replace('"', '\\"'))
    description = re.sub(r" by \d+%", "", description)
    description = re.sub(r"If the user is attuned to [^:]+: ", "", description)
    description = description[0].upper() + description[1:]
    return f'  "{generic_name}": "{description}",'


roman_numerals = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
}

asyncio.get_event_loop().run_until_complete(data.update_repositories())
abilities = {str(e).lower(): e for e in data.Ability.get_all().values()}
generic_ability_map = collections.defaultdict(list)
for name, ab in abilities.items():
    generic_ability_map[ab.generic_name].append(ab)

numeric_ex = re.compile(r"(.+) \+(\d+)%?")
roman_ex = re.compile(r"(.+) ([IVX]+)")

generic_descriptions = config.get_global("ability_disambiguation")
non_matching = []
for gen_name, ab_list in generic_ability_map.items():
    if len(ab_list) > 1:
        if gen_name not in generic_descriptions:
            if any(numeric_ex.match(ab.name) for ab in ab_list):
                ab_max = None
                ab_max_value = 0
                for ab in ab_list:
                    m = numeric_ex.match(ab.name)
                    if m and int(m.group(2)) > ab_max_value:
                        ab_max = ab
                        ab_max_value = int(m.group(2))
                print(description_line(gen_name, ab_max.description))
            elif any(roman_ex.match(ab.name) for ab in ab_list):
                ab_max = None
                ab_max_value = 0
                for ab in ab_list:
                    m = roman_ex.match(ab.name)
                    if m and roman_numerals.get(m.group(2)) and roman_numerals[m.group(2)] > ab_max_value:
                        ab_max = ab
                        ab_max_value = roman_numerals[m.group(2)]
                print(description_line(gen_name, ab_max.description))
            else:
                non_matching.append(gen_name)

for name in non_matching:
    print(f"No matching order definition for generic ability class {name}")
