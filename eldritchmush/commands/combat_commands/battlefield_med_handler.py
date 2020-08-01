
# Rules set for healing skills
class HealingHandler:

    def __init__(self, caller, target):
        self.caller = caller
        self.target = target


    def resolve_healing(self):
        if 1 <= self.target.db.body <= 3:
            # Return message to area and caller
            if self.target == self.caller:
                # Check to see if caller would go over 1 body with application of skill.
                if (self.caller.db.body + 1) > 3:
                    # If so set body to 1
                    self.caller.db.body = 3
                    self.caller.msg(f"|230{self.target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
                else:
                    # If not over 1, add points to total
                    self.caller.location.msg_contents(f"|230{self.caller} pulls bandages and ointments from their bag, and starts to mend their wounds.|n\n|540{self.caller} heals |n|0201|n |540body point per round as long as their work remains uninterrupted.|n")
                    self.caller.db.body += 1
                    self.caller.msg(f"|540Your new body value is:|n {self.caller.db.body}|n")

            elif self.target != self.caller:
                if (self.target.db.body + 1) > 3:
                    # If so set body to 1
                    self.target.db.body = 3
                    self.caller.msg(f"|230{self.target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
                else:
                    # If not over 1, add points to total
                    self.target.location.msg_contents(f"|230{self.caller.key} comes to {self.target.key}'s rescue, healing {self.target.key} for|n |0201|n |230body point.|n")
                    self.target.db.body += 1
                    self.target.msg(f"|540Your new body value is:|n {self.target.db.body}|n")

        elif self.target.db.body <= 0:
            self.caller.location.msg_contents(f"|230{self.caller.key} comes to {self.target.key}'s rescue, though they are too fargone.\n{self.target.key} may require the aid of more sophisticated healing techniques.|n")
