"""Compat shim — quest content now lives in world/quests/.

Quest definitions were split into per-event modules
(world/quests/event1_walkins.py etc.) on 2026-06-09. Every
existing `from world.quest_data import QUESTS` keeps working.
Add new quests to the appropriate event module, or create a
new module and register it in world/quests/__init__.py.
"""
from world.quests import QUESTS  # noqa: F401
