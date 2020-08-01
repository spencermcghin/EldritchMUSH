
def healingHandler(caller, target):
    if 1 <= target.db.body <= 3:
        # Return message to area and caller
        if target == caller:
            # Check to see if caller would go over 1 body with application of skill.
            if (caller.db.body + 1) > 3:
                # If so set body to 1
                caller.db.body = 3
                caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
            else:
                # If not over 1, add points to total
                caller.location.msg_contents(f"|230{caller} pulls bandages and ointments from their bag, and starts to mend their wounds.|n\n|540{caller} heals |n|0201|n |540body point per round as long as their work remains uninterrupted.|n")
                caller.db.body += 1
                caller.msg(f"|540Your new body value is:|n {caller.db.body}|n")

        elif target != caller:
            if (target.db.body + 1) > 3:
                # If so set body to 1
                target.db.body = 3
                caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
            else:
                # If not over 1, add points to total
                target.location.msg_contents(f"|230{caller.key} comes to {target.key}'s rescue, healing {target.key} for|n |0201|n |230body point.|n")
                target.db.body += 1
                target.msg(f"|540Your new body value is:|n {target.db.body}|n")

    elif target.db.body <= 0:
        caller.location.msg_contents(f"|230{caller.key} comes to {target.key}'s rescue, though they are too fargone.\n{target.key} may require the aid of more sophisticated healing techniques.|n")
