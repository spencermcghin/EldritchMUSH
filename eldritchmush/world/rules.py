import random

# messages

def resolve_combat(combat_handler, actiondict):
    """
    This is called by the combat handler
    actiondict is a dictionary with a list of two actions
    for each character:
    {char.id:[(action1, char, target), (action2, char, target)], ...}
    """
    flee = {} # track number of flee commands per character

    for isub in range(2):
        # loop over sub-turns
        messages = []
        for subturn in (sub[isub] for sub in actiondict.values()):
            # for each character, resolve the sub-turn
            action, attack_result, damage, char, target = subturn
            if target:
                target.av = tav
                taction, tattack_result, tdamage, tchar, ttarget = actiondict[target.id][isub]
            if action == "strike":
                if taction == "defend":
                    msg = f"{target} defends the attack."
                    messages.append(msg)
                elif taction == "strike":
                    if tattack_result > char.av:
                        msg = f"{target} strikes at you, for {tdamage}"
                        messages.append(msg)
                elif attack_result < tav:
                    msg = f"|rYou strike deftly at {tchar}, but miss!"
                    messages.append(msg)
                else:
                    msg = f"|gYou strike deftly at {tchar}, inflicting a wound upon them."
                    messages.append(msg)
                    # subtract damage from target body.
                    target.body -= damage
            elif action == "flee":
                if char in flee:
                    flee[char] = 1
                    msg = f"|y{char} disengages from the conflict"
                    messages.append(msg % char)

        # echo results of each subturn
        combat_handler.msg_all("\n".join(messages))

    # at the end of both sub-turns, test if anyone fled
    msg = "%s withdraws from combat."
    for (char, fleevalue) in flee.items():
        if fleevalue == 1:
            combat_handler.msg_all(msg % char)
            combat_handler.remove_character(char)
