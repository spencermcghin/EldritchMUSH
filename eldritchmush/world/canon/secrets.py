"""Secret canon — admin / quest-giver only. Never auto-included for any NPC.

These entries have scope='secret' so they're filtered out by the canon
loader regardless of NPC tags. They exist as reference for staff
running encounters and for any future quest hooks that explicitly
reach into them.
"""
from world.canon import ENTRIES, CanonEntry as _E

ENTRIES.extend([
    _E(
        title="SECRET: The Underwriter's True Nature",
        text=(
            "The UNDERWRITER is Fae. Not Cirque. The 'contract broker' "
            "story is the public face she allows to circulate. Her bargains "
            "are Fae bargains — the price is always something the bearer "
            "would never knowingly sell: a memory, a name, the warmth from "
            "one's hands, a true love's last word, a year of life. Her "
            "contracts always come due, often in unexpected ways. NPCs DO "
            "NOT KNOW THIS. Players DO NOT KNOW THIS until they discover "
            "it through play. This entry exists for staff reference only."
        ),
        scope="secret",
    ),
    _E(
        title="SECRET: Mistwalker Compact Origins",
        text=(
            "The Mistwalker Compact's origin is unknown even to its own "
            "members past the Registrars. They are not native to either "
            "Arnesse or the Annwyn — they emerged with the Day of Mist. "
            "Their ageless stillness, their ability to walk the mists, "
            "their eerie identification with single-word names — all "
            "suggest something neither human nor Fae. Even Crane does not "
            "remember a name before Crane. This is staff-reference only."
        ),
        scope="secret",
    ),
    _E(
        title="SECRET: The Living Saints' Rebirth Mechanism",
        text=(
            "The Living Saints rebirth crisis in Mystvale is connected to "
            "the Tower of Menethil's Rite of Aeons. Every Saint who falls "
            "in the Annwyn returns in a new body within Mystvale's bounds. "
            "Whether this is divine miracle (Aurorym position), Resurrection "
            "Heresy (Magnus's warning Ch. VII Rune III), or something "
            "older and worse (Apotheca suspicion) is unresolved canon. "
            "Casilda the Dawnbreaker's reborn vessel walks Mystvale now."
        ),
        scope="secret",
    ),
    _E(
        title="SECRET: Symeon Bannon's True Allegiance",
        text=(
            "King Giles II's killer, Vigil Symeon Bannon, did not act "
            "alone. He was reached by HARBINGERS — the cult devoted to "
            "returning the Unbound to the world. The Harbingers' role in "
            "the regicide is not yet known to the public; they continue "
            "to operate from within Arnesse's highest ranks. Symeon "
            "himself has vanished. Investigations are quietly ongoing."
        ),
        scope="secret",
    ),
])
