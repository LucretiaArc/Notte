import discord
import data
import query.types as types
import typing


def get_adventurer_skill(adv: data.Adventurer, slot: types.SkillSlot):
    if slot == types.SkillSlot.SKILL_1 and adv.skill_1:
        return adv.skill_1.get_embed()
    elif slot == types.SkillSlot.SKILL_2 and adv.skill_2:
        return adv.skill_2.get_embed()

    return f"I don't know what that adventurer's skill {slot.value} is!"


def get_dragon_skill(d: data.Dragon, flag = types.FlagSkill):
    if d.skill:
        return d.skill.get_embed()

    return "I don't know what that dragon's skill is!"


def get_tierless_weapon(rarity: types.Rarity, weapon_type: data.WeaponType):
    return get_weapon_helper(rarity.value, None, weapon_type, None)


def get_t1_weapon(rarity: types.Rarity, tier: types.Tier, weapon_type: data.WeaponType):
    if tier.value > 1:
        return "I can't figure out which weapon you want exactly, give me an element to work with!"

    return get_weapon_helper(rarity.value, tier.value, weapon_type, None)


def get_t2_t3_weapon(rarity: types.Rarity, tier: types.Tier, weapon_type: data.WeaponType, element: data.Element):
    if tier.value == 1:
        return None

    return get_weapon_helper(rarity.value, tier.value, weapon_type, element)


def get_weapon_helper(rarity: int, tier: typing.Optional[int], weapon_type: data.WeaponType, element: typing.Optional[data.Element]):
    repo = data.Weapon.get_all()

    for w in repo.values():
        if w.availability == "Core" and w.rarity == rarity and w.tier == tier and w.weapon_type == weapon_type:
            if tier == 2:
                for w_child in w.crafted_to:
                    if w_child.element == element:
                        return w.get_embed()
            elif w.element == element:
                return w.get_embed()

    return "I'm not sure a weapon like that exists."
