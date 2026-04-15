"""Languages, Holidays, Constellations, Calendar — the cultural fabric of
Arnesse. Drawn from the Master History 2.0, the Calendar Graphic, and
extrapolated from references throughout the faction packets.
"""
from world.canon import ENTRIES, CanonEntry as _E

ENTRIES.extend([
    # =====================================================================
    # LANGUAGES
    # =====================================================================
    _E(
        title="Languages: The Common Tongue",
        text=(
            "The common speech of Arnesse derives from Old Ardan, the "
            "lingua franca of the Sovereignlands and Hearthlands. It is "
            "spoken across the realm by nobility and commoner alike. "
            "Those who can read write in the Ardan script; the unlettered "
            "use mark and seal. Most folk speak only the common tongue."
        ),
    ),
    _E(
        title="Languages: The Eldritch Tongues",
        text=(
            "Four ancient languages persist from the Eldritch Age, each "
            "tied to a school of magical or scholarly discipline. "
            "ELYRIAN — air, wisdom — is favored by Apotheca scholars and "
            "Magisters. ARTYRIAN — passion, war — is spoken by warriors "
            "and battle-priests. TELYRIAN — mysticism, the veil — is "
            "used in arcane ritual. FAYRIAN — trade, commerce — is the "
            "common coin-speech of merchants. Only the learned speak "
            "these tongues fluently; most folk know only scattered words "
            "and ritual phrases."
        ),
    ),
    _E(
        title="Languages: Regional and House Speech",
        text=(
            "The Northern Marches keep alive older Celtic-derived tongues "
            "in folk-speech; House Innis maintains them in prayer and "
            "song. House Bannon uses Welsh-Celtic naming (Giles, Charles, "
            "Eldric, Cyrus). House Richter employs Germanic registers "
            "(Hawken, Volkan, Wilhelm). House Corveaux favors French "
            "patterns (Desmond, Marien, Anne). Tarkathi maintain their "
            "own vowel-shifts in proper names, a mark of ancestral pride. "
            "AEONTACHT (Unity), an Aldran word, is the only universally-"
            "known ancient term across the realm."
        ),
    ),

    # =====================================================================
    # CALENDAR
    # =====================================================================
    _E(
        title="Calendar of Arnesse: Year After Shadowfall",
        text=(
            "Arnesse measures time in years AFTER SHADOWFALL (AS), "
            "beginning with Year 1 AS at the Eldritch Cataclysm centuries "
            "ago. The current year is 767 AS. The calendar is recorded by "
            "the Crown and kept in writs; most common folk count by moon "
            "cycle and season only. The year is divided into TWELVE MOON "
            "CYCLES, each tied to a constellation in the sky. Each cycle "
            "lasts roughly thirty days; the WITCHING HOUR is the deep "
            "night between two days."
        ),
    ),

    # =====================================================================
    # HOLIDAYS
    # =====================================================================
    _E(
        title="Holiday: The Ascension Feast",
        text=(
            "The Ascension Feast celebrates Magnus's becoming the First "
            "Hallowed of the Aurorym faith — a kingdom-wide holy day "
            "marked by feasting, torch-lighting at dusk, and processionals "
            "to Aurorym chantries. Work ceases in towns and villages. The "
            "faithful gather to hear sermons on virtue and sacrifice. In "
            "the Dusklands, some houses still keep older customs: a silent "
            "hour at the Witching Hour, and gifts given to the poor."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="Holiday: The Martyrs' Wake",
        text=(
            "The Martyrs' Wake commemorates the fallen Saints and martyrs "
            "of the Aurorym — held annually on the date of the Battle of "
            "Exeter. Aurorym knights wear black bands; funerary flowers "
            "(white anemone, black iris) are laid at chantry shrines. The "
            "Vellatora fast through the day. At dusk, bells ring in every "
            "chantry. The tradition is ancient, predating Magnus himself."
        ),
        factions={"aurorym", "vellatora"},
    ),
    _E(
        title="Holiday: Harvesttide",
        text=(
            "In the Hearthlands and grain-rich Midlands, Harvesttide marks "
            "the end of the harvest — feasting, ancestor-honor, and "
            "thanksgiving for plenty. Granaries are blessed; loaves are "
            "left at Aurorym shrines as offerings. Bonfires are lit at "
            "dusk. In regions where famine has struck, Harvesttide is a "
            "somber affair: prayers alone, no feast. The custom draws "
            "from older folk-traditions predating the Aurorym faith."
        ),
    ),
    _E(
        title="Holiday: The Yule Silence",
        text=(
            "At the darkest point of the year (the deepest winter moon), "
            "many houses observe a day of silence — no work, no loud "
            "speech, no music. Candles are lit at every window to guide "
            "lost souls. The Aurorym call it 'The Lamp At Its Darkest,' "
            "remembering Magnus's words that even the smallest light "
            "banishes great darkness (Ch. III Rune III). In the Dusklands, "
            "it is called the Vigil Night and is marked instead by "
            "feasting and warmth shared with family."
        ),
    ),
    _E(
        title="Holiday: The First Sowing Festival",
        text=(
            "When the spring planting begins, villages hold festival — "
            "music, games, and blessings over the fields. The Aurorym "
            "Curate walks the furrows speaking prayers of growth. Young "
            "couples are often handfasted at this festival, for spring is "
            "deemed the season of new beginnings. In the Northern Marches, "
            "the custom is older: folk-offerings are left in the soil "
            "for faerie favor."
        ),
    ),
    _E(
        title="Holiday: The King's Reckoning",
        text=(
            "Once per year — on the 1st day of the 1st Moon Cycle — the "
            "King's Reckoning is declared: a day of accounts, legal "
            "proceedings, and mercantile settlement. All debts are called "
            "due; contracts are sealed; the Crown hears grievances. It is "
            "a day of formal dress and careful speech. Since King Giles's "
            "murder and the succession crisis, the Reckoning has been "
            "marked by tension: Houses gather but do not feast together "
            "as once they did."
        ),
    ),

    # =====================================================================
    # CONSTELLATIONS
    # =====================================================================
    _E(
        title="Constellations: The Sky Wheel",
        text=(
            "The Arnesse sky wheel holds twelve major constellations, one "
            "for each moon cycle. Magisters study them for omens; sailors "
            "use them for navigation. The Calendar Graphic shows the "
            "layered rings: the outermost holds the Eldritch tongues "
            "(Fayrian, Artyrian, Telyrian, Elyrian), mapped to the "
            "star-paths and seasons. Which constellation rises at your "
            "birth marks your temperament in folk-lore."
        ),
    ),
    _E(
        title="Constellations: Star-Lore and Omens",
        text=(
            "A blood moon (the moon turning as blood) is counted as an "
            "Eschaton sign by Aurorym theologians (Ch. IX Rune II). "
            "Sailors speak of the 'Turning Star' as a guide through "
            "storm; a falling star is held to foretell a great death. "
            "The Night Spiders — constellations near the Dread Run — are "
            "spoken of only quietly, as few wish to draw notice. The "
            "Navigator's Crown, a tight cluster of five stars, aligns "
            "only once per seventeen years; sailors call this a year of "
            "fortunate voyage."
        ),
    ),
    _E(
        title="Constellations: Birth and Calling",
        text=(
            "Folk-lore holds that the constellation of one's birth shapes "
            "one's nature. Magisters born under the Apotheca's "
            "constellation are said to have sharper mind and longer "
            "memory. Those born under the Warrior's Star are fierce in "
            "battle but slow to counsel. Sailors venerate the Navigator's "
            "Crown. Merchants favor the Trade Star, which rises spring-"
            "ward each year. Priests of the Aurorym look to the constellation "
            "of the First Dawn — under whose watch Magnus is said to have "
            "been born."
        ),
    ),
])
