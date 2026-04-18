"""
Heal command — pay a chirurgeon NPC to restore your health.

Usage:
  heal                  — get healed by the chirurgeon in the room (costs 5 silver)

Requires a healer NPC (db.is_healer = True) in the same room.
Restores body, bleed_points, and death_points to full.
"""
from evennia import Command


class CmdHeal(Command):
    """
    Visit a healer to restore your health.

    Usage:
      heal

    A chirurgeon in the room will tend your wounds for 5 silver.
    Restores body, bleed points, and death points to full, and
    clears status effects (weakness, poison, disease).
    """
    key = "tend"
    aliases = ["rest", "tend wounds", "visit healer"]
    locks = "cmd:all()"
    help_category = "General"

    COST = 5  # silver

    def func(self):
        caller = self.caller
        if not caller.location:
            caller.msg("You can't do that here.")
            return

        # Find a healer NPC in the room
        healer = None
        for obj in caller.location.contents:
            if obj.attributes.get("is_healer", default=False):
                healer = obj
                break
        if not healer:
            caller.msg("|400There is no healer here.|n")
            return

        # Check if already at full health
        body = caller.db.body or 0
        total_body = caller.db.total_body or 3
        bleed = caller.db.bleed_points
        total_bleed = 3
        death = caller.db.death_points
        total_death = 3
        if (body >= total_body and bleed >= total_bleed
                and death >= total_death):
            caller.msg(
                f"|c{healer.key}|n looks you over and nods. "
                f'"You\'re in fine shape. Save your coin."'
            )
            return

        # Check if in combat
        if caller.db.in_combat:
            caller.msg("|400You can't visit the healer while in combat.|n")
            return

        # Check silver
        purse = caller.db.silver or 0
        if purse < self.COST:
            caller.msg(
                f"|c{healer.key}|n says, \"I'd treat you for "
                f"nothing if I could, but herbs cost silver. "
                f"Come back with {self.COST} silver.\""
            )
            return

        # Pay and heal
        caller.db.silver = purse - self.COST
        caller.db.body = total_body
        caller.db.bleed_points = total_bleed
        caller.db.death_points = total_death
        # Clear status effects
        caller.db.weakness = 0
        caller.db.poison = False
        caller.db.disease = False
        caller.db.fear = False

        # Restore limbs
        caller.db.right_arm = 1
        caller.db.left_arm = 1
        caller.db.right_leg = 1
        caller.db.left_leg = 1
        caller.db.torso = 1

        caller.location.msg_contents(
            f"|c{healer.key}|n tends to |g{caller.key}|n's wounds "
            f"with practiced hands, binding, salving, and murmuring "
            f"old remedies. After a few minutes, {caller.key} "
            f"rises restored."
        )
        caller.msg(
            f"|gYou feel whole again. "
            f"|w(-{self.COST} silver)|n"
        )

        # Push updated stats to the frontend
        try:
            from world.character_stats import push_character_stats
            push_character_stats(caller)
        except Exception:
            pass
