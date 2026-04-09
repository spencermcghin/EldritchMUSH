"""
Combat Handler Script

Legacy typeclass referenced by existing database objects.
Provides a minimal stub so Evennia can load these objects without errors.
"""

from evennia import DefaultScript


class CombatHandler(DefaultScript):
    """
    A script that manages a combat instance. Referenced by existing
    objects in the database from an earlier version of the combat system.
    """

    def at_script_creation(self):
        self.key = "combat_handler"
        self.desc = "Handles combat rounds"
        self.persistent = True

    def at_repeat(self):
        pass
