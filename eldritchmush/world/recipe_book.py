"""
Known-recipe storage helpers.

`character.db.known_recipes` holds the uppercase prototype keys a character
has learned. Evennia does NOT hand that attribute back as a plain `set` — it
wraps mutable collections in `_SaverSet`, which is a `MutableSet` but *not* a
`set` subclass. Every read site that did:

    known = caller.db.known_recipes
    if not isinstance(known, set):
        known = set()

therefore threw the stored recipes away on every call. `learn` then wrote the
fresh single-entry set back, so learning a second scroll silently destroyed
the first (and its scroll), and `brew` / `recipes` / the alchemy OOB handlers
reported an empty book for every non-superuser.

Go through these helpers rather than touching the attribute directly.
"""


def known_recipes(character):
    """Return the character's learned recipe keys as a plain uppercase set.

    Accepts anything iterable, so `_SaverSet`, `set`, and legacy list values
    all read correctly. Returns an empty set for an unset or unusable value.
    """
    if character is None:
        return set()

    raw = character.attributes.get("known_recipes", default=None)
    if raw is None:
        return set()

    try:
        return {str(key).upper() for key in raw}
    except TypeError:
        # Not iterable (corrupt value) — treat as an empty book rather than
        # raising into a player-facing command.
        return set()


def knows(character, recipe_key):
    """True if the character has learned `recipe_key` (case-insensitive)."""
    if not recipe_key:
        return False
    return str(recipe_key).upper() in known_recipes(character)


def learn(character, recipe_key):
    """Record `recipe_key` as learned.

    Returns True if it was newly added, False if already known. Stores a
    plain set so the attribute round-trips predictably.
    """
    if character is None or not recipe_key:
        return False

    key = str(recipe_key).upper()
    current = known_recipes(character)
    if key in current:
        return False

    current.add(key)
    character.attributes.add("known_recipes", current)
    return True
