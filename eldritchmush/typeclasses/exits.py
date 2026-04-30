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
            "dest_key": "Tamris Harbor — The Broken Pier",
            "arrival": (
                "|cThe stars are not the stars you knew.|n\n\n"
                "The deck pitches under your feet — the |wdoomed captain|n's "
                "last words still in your ear: \"Burn the seal. Burn the "
                "hold. Whatever you do, do not let them open it.\" "
                "Wood splinters. Saltwater floods the hull. Then black, "
                "then mist, then a long sound like a great bell tolled "
                "underwater.\n\n"
                "You wake on a beach of grey shingle. The wreck still "
                "bleeds timber into the tide. The smell of brine and "
                "rot is thick on the wind. Tamris Harbor lies above the "
                "tideline, lamps already lit against the fog."
            ),
        },
        "walkin_cirque": {
            "dest_key": "The Mystvale Marketplace",
            "arrival": (
                "|cThe caravan rolls onward through the fog.|n\n\n"
                "|wYan|n strums a slow tune at the head of the wagon. The "
                "|wRingmaster|n smokes in the painted door of his coach, "
                "watching the road behind. |wEldreth|n's seat in the "
                "fortune-teller's wagon is empty — the lamp guttering, "
                "the curtains pulled back. Nobody saw her step out. "
                "Nobody heard the wheels stop.\n\n"
                "The mist parts. The lights of Mystvale's marketplace "
                "rise out of the dusk. Hawkers, horse-traders, the "
                "smell of charcoal and roast fowl. The Cirque circles "
                "for camp. The Ringmaster's eyes find yours — and "
                "ask, without asking, what you saw."
            ),
        },
        "walkin_noble": {
            "dest_key": "The Old Road — South",
            "arrival": (
                "|cThe carriage rocks across the rutted road.|n\n\n"
                "Hooves thunder behind. \"|rBANDITS!|n\" — the driver's "
                "shout — then a crossbow bolt punches through the "
                "lacquered door. You leap clear into wet leaves, the "
                "|wsealed letter|n a hot weight in your sleeve. The "
                "noble's retinue scatters. Steel sings somewhere in "
                "the trees. The mist thins.\n\n"
                "The Old Road south of Mystvale opens before you, "
                "quiet now, the bandits regrouping somewhere in the "
                "pines. The letter is still sealed. You can feel the "
                "wax under your thumb. The decision is yours."
            ),
        },
        "walkin_scout": {
            "dest_key": "The Old Road — South",
            "arrival": (
                "|cYou cut through pine shadow alone.|n\n\n"
                "Hours of mist, then more mist. A felled raven, neck "
                "broken neat. Then another. Then a |wwaymark|n cut into "
                "the bark of a black pine — three intersecting lines "
                "and a dot. Crow sign. Fresh.\n\n"
                "The Old Road south of Mystvale curls ahead, its mile-"
                "stones half-buried in moss. You can hear the gates "
                "of Mystvale, distantly, north. The waymark is still "
                "behind you, waiting to be reported — or sold."
            ),
        },
        "walkin_chain_gang": {
            "dest_key": "The Mystvale Marketplace",
            "arrival": (
                "|cThe chains, the road, the screaming silence of the Mists.|n\n\n"
                "Whatever you did at the Mistwall — bloody, quiet, legal, "
                "or damning — it is behind you now. The cart-wheels "
                "rumble. A jailer's whistle goes silent in the fog. "
                "Somewhere a fellow prisoner sobs, then doesn't.\n\n"
                "Mystvale's marketplace opens around you, indifferent. "
                "Stalls, shouting, the smell of bread. Nobody is looking "
                "for you here. Not yet."
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
