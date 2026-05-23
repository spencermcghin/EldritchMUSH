"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
from evennia import DefaultExit


class Exit(DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets default exit locks (to change, use `at_object_creation` instead).
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed and should
                              rebuild the Exit cmdset along with a command matching the name
                              of the Exit object. Conventionally, a kwarg `force_init`
                              should force a rebuild of the cmdset, this is triggered
                              by the `@alias` command when aliases are changed.
     at_failed_traverse() - gives a default error message ("You cannot
                            go there") if exit traversal fails and an
                            attribute `err_traverse` is not defined.

    Relevant hooks to overload (compared to other types of Objects):
        at_traverse(traveller, target_loc) - called to do the actual traversal and calling of the other hooks.
                                            If overloading this, consider using super() to use the default
                                            movement implementation (and hook-calling).
        at_after_traverse(traveller, source_loc) - called by at_traverse just after traversing.
        at_failed_traverse(traveller) - called by at_traverse if traversal failed for some reason. Will
                                        not be called if the attribute `err_traverse` is
                                        defined, in which case that will simply be echoed.
    """

    def at_object_creation(self):
        self.locks.add("traverse:attr(in_combat, 0)")

        return


class WalkInMistsExit(Exit):
    """The one-way crossing through the Mists at the Mistwall.

    Reads the player's active walk-in quest (if any) and routes them
    to a flavored arrival room with a multi-line narrative cutscene
    describing the journey through the Mists from the chosen flavor's
    perspective:

      walkin_ship       → Tamris Harbor (the wreck)
      walkin_cirque     → Mystvale Marketplace (Cirque caravan)
      walkin_noble      → Old Road South (ambush site)
      walkin_scout      → Old Road South (pine shadow)
      walkin_chain_gang → Mystvale Marketplace (escape into the city)

    Players without an active walk-in fall through to the exit's
    configured destination (Mistgate, the generic mist-crossing room).
    """

    # Destination room key + arrival cutscene per walk-in quest key.
    # The destination is looked up at traverse-time so re-runs of
    # populate that move rooms don't break this.
    WALKIN_ROUTES = {
        "walkin_ship": {
            "dest_key": "The Cargo Hold of the Doomed Ship",
            "arrival": (
                "|cThe Mists thicken into the smell of brine and tar.|n\n\n"
                "The mist becomes weight. The weight becomes wood under "
                "your back, a ship's hammock swaying with a sea you "
                "cannot see. A storm hammers the hull from outside. "
                "Distantly, somewhere above, the |wcaptain|n is shouting. "
                "The cabin door has been locked from the other side. "
                "Other passengers are huddled around you — strangers, "
                "all bound for the Annwyn, all trying not to look "
                "afraid. The ship lurches.\n\n"
                "You are not in the Mists anymore. You are on the ship "
                "they were always going to put you on."
            ),
        },
        "walkin_cirque": {
            "dest_key": "The Cirque Camp at the Mistwall",
            "arrival": (
                "|cThe caravan stops at the Mistwall. The guide does not come.|n\n\n"
                "Two days of waiting in painted wagons at the edge of "
                "the fog. The horses are nervous. The food is gone. "
                "Mistwalker Soap, who was supposed to lead the cargo "
                "through, never came. Now |wYan|n, the Cirque's "
                "foreman, stands by four iron-banded crates with a "
                "Cirque-stamped contract rolled in his belt and the "
                "look of a man who has chosen to walk the Tangle "
                "alone if he has to.\n\n"
                "|wThe Cirque needs a courier|n, he says when he sees "
                "you. |wEldreth waits in the Annwyn. Soap doesn't. "
                "Sign the manifest, take the crates, walk with me.|n"
            ),
        },
        "walkin_noble": {
            "dest_key": "Martin's Abandoned Camp",
            "arrival": (
                "|cThe last of the road, the empty camp, the wrong silence.|n\n\n"
                "You travelled the long way overland in noble comfort "
                "until comfort ran out and you walked the rest. |wWil|n, "
                "the Guide's assistant the retinue hired in Gateway, "
                "promised Mistwalker Martin would meet you at the "
                "trail-head. He did not. The camp ahead is set, the "
                "fire is dead, the cook-pot is cold, and the lantern "
                "burned itself out hours ago.\n\n"
                "Wil clears his throat too cheerfully. |wMust have just "
                "stepped away|n, he says. |wLet's see what he left us.|n"
            ),
        },
        "walkin_scout": {
            "dest_key": "Magister Ipwin's Abandoned Camp",
            "arrival": (
                "|cThe Lodge's call, the dim trail, the empty desk.|n\n\n"
                "You answered Magister Ipwin's summons to the Annwyn — "
                "him and his Lodge of the Metaphysical Mind, "
                "promising a once-in-a-lifetime study of the place's "
                "spirit phenomena. The lanterns marking the way "
                "burned violet, and you followed them through the "
                "Mists. They lead here: a scholar's camp, a cold "
                "cooking-fire, an open journal, and no Ipwin.\n\n"
                "|wMagister Vell|n, your Lodge colleague, is already "
                "frowning over a pinned note. |wHe's gone on ahead|n, "
                "she says. |wA discovery. The barrow. The trail's in "
                "the lanterns. We'd better catch him.|n"
            ),
        },
        "walkin_chain_gang": {
            "dest_key": "The Prison Cart at the Mistwall",
            "arrival": (
                "|cChains, a wagon, the long dark road into the fog.|n\n\n"
                "The jailers cuff you and chain you to the man beside "
                "you. Your weapons go into a Laurent-stamped crate that "
                "is carried off into the mist. The wagon-doors open on "
                "blackness and a forest the captain calls the Last Walk. "
                "Beside you, a heavy-shouldered Northman whose wrists "
                "are as raw as yours leans close.\n\n"
                "|wThe name's Ulfric|n, he says. |wYou look like a man "
                "who can hold a blade. Stay near me, friend. The Mists "
                "are about to get interesting.|n"
            ),
        },
    }

    def _active_walkin(self, traversing_object):
        """Return the walk-in quest key the player has accepted, or None."""
        if not hasattr(traversing_object, "db"):
            return None
        quests = traversing_object.db.quests or {}
        for key, state in quests.items():
            if (
                key in self.WALKIN_ROUTES
                and state
                and state.get("status") == "active"
            ):
                return key
        return None

    def at_traverse(self, traversing_object, target_location, **kwargs):
        from evennia.objects.models import ObjectDB

        walkin_key = self._active_walkin(traversing_object)
        if walkin_key:
            route = self.WALKIN_ROUTES[walkin_key]
            target = ObjectDB.objects.filter(db_key=route["dest_key"]).first()
            if target:
                # Show the cutscene narration before the move so the
                # player reads it tagged to their previous location,
                # then arrives in the new room with a fresh `look`.
                traversing_object.msg(route["arrival"])
                return super().at_traverse(traversing_object, target, **kwargs)
        # No active walk-in (or the room lookup failed) — default behavior.
        return super().at_traverse(traversing_object, target_location, **kwargs)


class WalkInJourneyExit(Exit):
    """Exit used inside walk-in transit scenes (the Cargo Hold → Deck →
    Tamris Beach sequence for the Ship walk-in, etc.). When the
    traversing player moves through, any NPC in the source room
    tagged `db.is_walkin_companion = True` follows them through.

    This is what makes companion NPCs (First Mate Nosaj, Yan, etc.)
    feel like they're actually travelling with the player rather than
    being stranded one room behind. The companion sees a quiet
    follow-message; everyone else in the destination room sees them
    arrive.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        source = traversing_object.location
        companions = []
        if source:
            for obj in list(source.contents):
                if obj is traversing_object:
                    continue
                if obj.attributes.get("is_walkin_companion", default=False):
                    companions.append(obj)
        super().at_traverse(traversing_object, target_location, **kwargs)
        # Only drag companions along if the player actually moved.
        if traversing_object.location is target_location:
            for comp in companions:
                try:
                    comp.move_to(target_location, quiet=True)
                    traversing_object.msg(
                        f"|c{comp.key}|n follows you through."
                    )
                except Exception:
                    pass


class QuestGatedExit(Exit):
    """Exit that requires a specific quest to be active or completed.

    Set `db.required_quest` to the quest key (e.g. "rescue_blacksmith").
    Set `db.gate_message` to a custom rejection message (optional).

    Players without the quest active/completed see the exit but can't
    traverse — they get a lore-flavored rejection instead.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        quest_key = self.attributes.get("required_quest", default=None)
        if quest_key and hasattr(traversing_object, "db"):
            # Admins/builders bypass the gate
            account = getattr(traversing_object, "account", None)
            if account and (account.is_superuser or account.check_permstring("Builder")):
                return super().at_traverse(traversing_object, target_location, **kwargs)

            quests = traversing_object.db.quests or {}
            state = quests.get(quest_key)
            if not state or state.get("status") not in ("active", "completed"):
                msg = self.attributes.get("gate_message", default=None)
                if not msg:
                    msg = (
                        "|400The path is unclear and overgrown. You'd need "
                        "a reason — and directions — to push through.|n"
                    )
                traversing_object.msg(msg)
                return
        return super().at_traverse(traversing_object, target_location, **kwargs)
