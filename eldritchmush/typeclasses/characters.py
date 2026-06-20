"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia import DefaultCharacter
from world.available_commands import push_available_commands
from world.events import emit_to
from world.character_stats import push_character_stats


def _push_combat_encounter_prompt(character):
    """Fire `combat_encounter_prompt` OOB event if the room has hostiles.

    Lets the web client surface an opt-in modal so a player who walks
    into a boss room (e.g. the nethermancer's sanctum) isn't shoved
    into a fight by the next click. Skipped while the player is
    already in combat — they're already committed.
    """
    if not character.location:
        return
    if character.db.in_combat:
        return
    if (character.db.body or 0) <= 0:
        return
    hostiles = []
    for obj in character.location.contents:
        if obj is character:
            continue
        if not obj.attributes.get("is_aggressive", default=False):
            continue
        if (obj.db.body or 0) <= 0:
            continue
        tier = obj.attributes.get("tier", default=0) or 0
        hostiles.append({
            "name": obj.key,
            "dbref": getattr(obj, "dbref", ""),
            "desc": (obj.db.desc or "")[:200],
            # boss when explicitly flagged OR a high-tier (T3+) bestiary mob
            "isBoss": bool(obj.attributes.get("boss_encounter", default=False))
                      or tier >= 3,
            # bestiary fields → the web client's framed portrait + threat tier
            # (art_key resolves via frontend/src/data/antagonists.js)
            "artKey": obj.attributes.get("art_key", default="") or "",
            "tier": tier,
        })
    if not hostiles:
        return
    emit_to(character, "combat_encounter_prompt", {
        "room": character.location.key,
        "hostiles": hostiles,
    })


class Character(DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    def at_object_creation(self):
        "This is called when object is first created, only."
        # Entries for general stats
        self.db.tracking = 0
        self.db.perception = 0
        self.db.master_of_arms = 0
        self.db.sniper = 0
        self.db.armor = 0
        self.db.armor_specialist = 0
        self.db.tough = 0
        self.db.total_tough = 0
        self.db.body = 3
        self.db.total_body = 3
        self.db.av = 0
        self.db.resilience = 0
        self.db.influential = 0
        self.db.espionage = 0

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Crafting attributes
        self.db.blacksmith = 0
        self.db.artificer = 0
        self.db.bowyer = 0
        self.db.gunsmith = 0
        self.db.alchemist = 0
        self.db.last_repair = 0

        # Entries for healing
        self.db.stabilize = 0
        self.db.medicine = 0
        self.db.battlefieldmedicine = 0
        self.db.chirurgeon = 0

        # Entries for skill proficencies
        self.db.gunner = 0
        self.db.archer = 0
        self.db.shields = 0
        self.db.melee_weapons = 0
        self.db.armor_proficiency = 0

        # Entries for status
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3
        self.db.fear = False
        self.db.disease = False
        self.db.poison = False
        self.db.paralyze = False
        self.db.sleep = False
        

        # Entries for combat
        self.db.melee = 0
        self.db.resist = 0
        self.db.total_resist = 0
        self.db.disarm = 0
        self.db.total_disarm = 0
        self.db.cleave = 0
        self.db.total_cleave = 0
        self.db.sunder = 0
        self.db.total_sunder = 0
        self.db.stun = 0
        self.db.total_stun = 0
        self.db.stagger = 0
        self.db.total_stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.twohanded = 0
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.is_aggressive = False
        self.db.skip_turn = False
        self.db.is_staggered = False

        # Gender identity — male / female / non-binary. Defaults to
        # "unset"; players choose during chargen via `setgender` and
        # can change later. Used by NPC LLM prompts for correct
        # pronoun choice and by any future romance/encounter mechanics.
        self.db.gender = "unset"

        # Char slots for equipping items
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.hand_slot = []
        self.db.foot_slot = []
        self.db.clothing_slot = []
        self.db.cloak_slot = []
        self.db.kit_slot = []
        self.db.arrow_slot = []
        self.db.bullet_slot = []

        # Entries for knights
        self.db.battlefieldcommander = 0
        self.db.rally = 0
        self.db.indomitable = 0

        # Entries for following
        self.db.isLeading = False
        self.db.leader = []
        self.db.isFollowing = False
        self.db.followers = []

        # Entries for economy
        self.db.iron_ingots = 0
        self.db.refined_wood = 0
        self.db.leather = 0
        self.db.cloth = 0
        self.db.gold = 0
        self.db.silver = 0
        self.db.copper = 0
        self.db.arrows = 0

        # Alchemy reagent inventory: {reagent_name: quantity}
        self.db.reagents = {}

        # Known alchemy recipes: set of prototype keys (e.g. {"BLADE_OIL"})
        self.db.known_recipes = set()

        # Faction reputation: {faction_name: int_delta}
        # Adjusted by branching quest outcomes. No thresholds are enforced yet;
        # Event 2+ quests will key off these values for gated content.
        self.db.faction_rep = {
            "crown": 0,
            "cirque": 0,
            "rangers": 0,
            "crows": 0,
            "outlaws": 0,
            "outsider": 0,
        }

        # Per-NPC personal reputation: {npc_key_lower: {"rep": int,
        #   "memories": [tag_str, ...], "last_interacted": iso_ts}}
        # Driven by quest outcomes (npc_rep_deltas / npc_memories on an
        # outcome dict). Consumed by AI NPC system prompt, the `rep`
        # command, and eventually merchant pricing + aggression flips.
        self.db.npc_rep = {}


    def return_appearance(self, looker):
        """
        The return from this method is what
        looker sees when looking at this object.
        """
        text = super().return_appearance(looker)
        # None-safe vitals: uninitialized stats (old Merchant rows,
        # pre-vitals objects) read as HEALTHY, not unconscious — prod's
        # blacksmith spent weeks "succumbed to his injuries" because
        # his body stat was never set.
        body = self.db.body
        total = self.db.total_body
        bleed = self.db.bleed_points
        initialized = body is not None and bleed is not None

        isBleeding = initialized and not body and bleed
        isDying = initialized and not body and not bleed
        isWounded = (initialized and total
                     and 0 < body < total)

        # Return
        if isBleeding:
            return text + f"\n{self.key} |025is bleeding profusely from multiple, serious wounds.|n"

        elif isDying:
            return text + f"\n{self.key} |025has succumbed to their injuries and is now unconscious.|n"

        elif isWounded:
            if body >= total - 1:
                return text + (f"\n{self.key} |025bears fresh wounds — "
                               f"favoring them, but on their feet.|n")
            return text + (f"\n{self.key} |025is badly hurt: bandaged "
                           f"rough, moving carefully, clearly in need "
                           f"of a healer.|n")

        else:
            return text

    def reset_stats(self):
        self.db.resist = self.db.total_resist
        self.db.disarm = self.db.total_disarm
        self.db.cleave = self.db.total_cleave
        self.db.sunder = self.db.total_sunder
        self.db.stun = self.db.total_stun
        self.db.stagger = self.db.total_stagger
        self.db.tough = self.db.total_tough

    # Changed for AI room response
    def at_after_move(self, source_location):
        """
        Default is to look around after a move
        Note:  This has been moved to room.at_object_receive
        """
        #self.execute_cmd('look')

        if (self.db.isLeading):
            for char in self.db.followers:
                if not char.db.in_combat and char.db.body > 0:
                    char.move_to(self.location)
                else:
                    char.db.isFollowing = False
                    char.db.leader = []
                    self.db.followers.remove(char)
                    tempList = list(self.db.followers)
                    if (len(tempList) == 0):
                        self.db.isLeading = False
                    self.msg("|540"+ char.key + " is no longer following you.|n")
                    char.msg("|540You are no longer following " + self.key + "|n")

        # If a follower performed a move away from the leader, they will be removed from the followers array and will
        # no longer be following the leader.
        if (self.db.isFollowing):

            leaderInRoom = self.search(self.db.leader)

            if not leaderInRoom:
                # Try removing them from the target's followers array.
                leader = self.search(self.db.leader, global_search=True)

                try:
                    leader.db.followers.remove(self)
                    tempList = list(leader.db.followers)
                    if (len(tempList) == 0):
                        leader.db.isLeading = False
                    self.msg("|540You are no longer following " + leader.key + "|n")
                    leader.msg("|540"+ self.key + " is no longer following you.|n")
                except ValueError:
                    self.msg("|540You are no longer following " + leader.key + "|n")

                self.db.isFollowing = False
                self.db.leader = []

        # Push updated available commands to the web UI sidebar after every move.
        push_available_commands(self)

        # Quest offers are no longer auto-fired on room entry — they
        # fire when the player ASKS the NPC about something (see
        # commands/ai_dialogue.py). Auto-popping the modal as soon
        # as you walk in felt overbearing and broke immersion.

        # Combat encounter opt-in: if the room contains hostile NPCs
        # and the player isn't already engaged, surface a prompt so
        # they aren't forced into an accidental fight (e.g. walking
        # past the nethermancer while looking for a quest-giver).
        try:
            _push_combat_encounter_prompt(self)
        except Exception as exc:
            print(f"[combat_prompt] failed: {exc!r}", flush=True)

        # Seal Altar visual state — if this room has the Wardstone
        # Hall's altar, push the rune-puzzle state so the modal
        # populates as the player walks in.
        try:
            for obj in (self.location.contents if self.location else []):
                if obj.attributes.get("is_seal_altar", default=False):
                    from commands.seal_altar import emit_altar_state
                    emit_altar_state(obj, character=self)
                    break
        except Exception as exc:
            print(f"[seal_altar] enter emit failed: {exc!r}", flush=True)

    def at_post_puppet(self, **kwargs):
        """Called when a player puppets this character (login / reconnect)."""
        super().at_post_puppet(**kwargs)
        # Push sidebar commands immediately so the UI is populated on connect.
        push_available_commands(self)
        # Tell the UI whether this account is admin/superuser
        try:
            account = self.account
            is_admin = bool(account and (account.is_superuser or account.check_permstring("Admin") or account.check_permstring("Builder")))
        except Exception:
            is_admin = False
        emit_to(self, "account_info", {
            "character": self.key,
            "is_admin": is_admin,
        })
        # Push character vitals so the sidebar panel populates on login.
        try:
            push_character_stats(self)
        except Exception:
            pass

    def at_post_unpuppet(self, account=None, session=None, **kwargs):
        """Called when the account leaves this character (logout/disconnect).

        Tavyl cards are session-scoped props — they represent your hand
        at a live table, not a durable inventory item — so we clear them
        here. If the character was mid-game at a dealer, the dealer's
        tavyl_table state still lives on the NPC and will re-materialize
        the hand next time the player sits.
        """
        try:
            for item in list(self.contents):
                if item.typeclass_path == "typeclasses.objects.TavylCard":
                    item.delete()
        except Exception:
            pass
        # Leave any combat loop BEFORE super() stows us at location=None.
        # A disconnected combatant left in the loop used to freeze the
        # whole fight: turn handoff crashed on our null location, and
        # NPCs kept targeting a character who wasn't there.
        try:
            location = self.location
            loop_list = location.db.combat_loop if location else None
            if loop_list and self in loop_list:
                had_turn = bool(self.db.combat_turn)
                my_index = loop_list.index(self)
                loop_list.remove(self)
                self.db.in_combat = 0
                self.db.combat_turn = 1
                location.msg_contents(
                    f"|025{self.key} slips from the fight as their "
                    f"presence fades from the world.|n")
                if len(loop_list) <= 1:
                    # Fight's over — release the last combatant.
                    for char in list(loop_list):
                        char.db.combat_turn = 1
                        char.db.in_combat = 0
                    loop_list.clear()
                    location.msg_contents(
                        f"|430Combat is now over for the {location}.|n")
                elif had_turn:
                    # Hand the turn on by advancing from the combatant
                    # BEFORE our old slot — cleanup() then lands on
                    # whoever was next after us and drives NPC turns.
                    from world.combat_loop import CombatLoop
                    prev_char = loop_list[(my_index - 1) % len(loop_list)]
                    CombatLoop(prev_char).cleanup()
        except Exception as exc:
            print(f"[characters] unpuppet combat-leave err: {exc!r}",
                  flush=True)
        super().at_post_unpuppet(account=account, session=session, **kwargs)
