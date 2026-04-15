"""Faction canon entries — Aurorym, Apotheca, Cirque, Vigil, etc.

Each entry is appended to world.canon.ENTRIES. NPCs whose canon_tags
overlap with an entry's tags will receive that entry in their LLM
system prompt.
"""
from world.canon import ENTRIES, CanonEntry as _E

# ---------------------------------------------------------------------------
# AURORYM — drawn from the Book of Magnus + faction packet
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="Aurorym: The Faith of the New Dawn",
        text=(
            "The Aurorym is the dominant faith of Arnesse, founded by Magnus, "
            "whose teachings are recorded in the Book of Magnus (divided into "
            "Chapters and Runes). Aurons preach in plain speech, citing "
            "Chapter and Rune as proof. Where older faiths bowed to dead gods, "
            "the Aurorym teaches that 'the gods are dead and obsolete' "
            "(Ch. IV Rune I) — mankind looks to no external power, only to "
            "the spark within. The Aurorym calls itself the Coming Dawn."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="Aurorym: The Animus and Ascension",
        text=(
            "Every person carries the ANIMUS — the breath of life given in "
            "Elder days. The animus is fed by virtue and starved by vice "
            "(Ch. I Runes III-V). Through deeds, the animus may grow strong "
            "enough to transcend the mortal coil and become HALLOWED, also "
            "called PARAGONS — exemplars whose lives echo across the world. "
            "Magnus warned: 'seek not the Resurrectionist' (Ch. VII Rune III); "
            "the Hallowed are an article of FAITH for most Aurorym."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="Aurorym: Hierarchy and Ranks",
        text=(
            "The Aurorym hierarchy: Patriarchs and Matriarchs (the highest), "
            "then Lectors, then Curates, then Aurons (preachers), then "
            "Kindling novices (entry rank 'Spark'). Living Saints — those "
            "Hallowed who walk the world — outrank all. Aurons may travel "
            "and preach freely; Curates lead Chantries; Lectors interpret "
            "doctrine; Patriarchs and Matriarchs convene at Highcourt and the "
            "Argent Synod."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="Aurorym: The Lamp and the Eschaton",
        text=(
            "Two doctrines define daily Aurorym practice. The LAMP — 'the "
            "world is a dark place, and so we carry a lamp; our own light is "
            "not diminished by sharing it' (Ch. III Rune III). And the "
            "ESCHATON (Ch. IX) — the prophesied end-battle, signs of which "
            "include the moon turning as blood, the Four Chains breaking, "
            "and the Heralds of Oblivion (Betrayer, Corruptor, Devourer, "
            "Destroyer) arising under the King of Nothing. The Day of Mist "
            "is widely interpreted as the first sign."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="Aurorym: The New Dawn and the Godslayers",
        text=(
            "The NEW DAWN is the Aurorym-backed coalition of holy warriors "
            "who have entered the Annwyn to fight what the Eschaton brings. "
            "It is held in genuine reverence. The GODSLAYERS, by contrast, "
            "are a splinter movement funded by House Hardinger of the "
            "Richter line — armed zealots who hold violence as faith. Most "
            "Aurorym dissenters cite Ch. XIII Rune III against them: 'false "
            "prophets clothed in the countenance of the faithful, speaking "
            "words of honey that do not nourish.'"
        ),
        factions={"aurorym"},
    ),
])

# ---------------------------------------------------------------------------
# APOTHECA — from the Apotheca faction packet
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="Apotheca: Ancient Origins and Founding",
        text=(
            "The Apotheca is one of the oldest organizations in Arnesse, said "
            "to predate even the Great Houses. Born from an order of scholars "
            "and blood mages of Tarkath, the Apotheca's legacy is soaked in "
            "both ink and blood. They have served as tutors, chirurgeons, and "
            "advisors to nobility for centuries — saving countless lives "
            "through chirurgery in an age when no real medicine existed."
        ),
        factions={"apotheca"},
    ),
    _E(
        title="Apotheca: The Pursuit of Knowledge",
        text=(
            "The Apotheca's driving essence is the relentless pursuit of "
            "knowledge, no matter the cost. Masters possess an insatiable "
            "desire to understand the world, and the order jealously guards "
            "its ancient lore from outsiders. A Magister knows much but "
            "shares it only when convinced it benefits themselves, the order, "
            "or the world. Understanding, they hold, is not for everyone."
        ),
        factions={"apotheca"},
    ),
    _E(
        title="Apotheca: Ranks and Hierarchy",
        text=(
            "The Apotheca's rigid hierarchy of ranks: Novitiate, Magister, "
            "Keeper, Preceptor, Archmagister, and Grand Magister. The Grand "
            "Magister leads from the Apotheon and chairs the Inner Council. "
            "Advancement requires both mastery of one's discipline and the "
            "approval of senior ranks — though political maneuvering "
            "increasingly influences selections."
        ),
        factions={"apotheca"},
    ),
    _E(
        title="Apotheca: The Apotheon and the Ashen Tower",
        text=(
            "Second only to High Keep, the APOTHEON looms over Highcourt as "
            "the order's headquarters, housing the largest repository of "
            "scrolls and tomes in all Arnesse and the renowned Argent Academy. "
            "Deep within the Thornwood lies GALDORLEOTH, the Garden Tower, "
            "where forbidden lore from the Eldritch Cataclysm is preserved. "
            "The ASHEN TOWER in Tarkath remains the order's spiritual heart "
            "and houses the mysterious Cranarium beneath it."
        ),
        factions={"apotheca"},
    ),
    _E(
        title="Apotheca: Celibacy and Discretion",
        text=(
            "The Apotheca enforces strict celibacy on those of the order. "
            "Vows broken face death, usually by poison. Discretion is "
            "paramount; masters who speak carelessly of order secrets are "
            "quickly silenced. This culture of secrecy has caused friction "
            "with the rising Aurorym faith, which preaches openness."
        ),
        factions={"apotheca"},
    ),
    _E(
        title="Apotheca: Disciplines and the Apotheceum",
        text=(
            "The Apotheceum at Highcourt comprises Colleges of Metaphysics, "
            "Theologians, Naturalists, Engineering, Law and Logic, and "
            "Anatomy. The Colleges are administered by Keepers and taught by "
            "Magisters and Preceptors. Study is rigorous and often deadly; "
            "the College of Anatomy in particular trains dissectors who "
            "travel the kingdom mending wounds with skill that borders on "
            "miraculous."
        ),
        factions={"apotheca"},
    ),
    _E(
        title="Apotheca: Sub-Orders and Hidden Chapterhouses",
        text=(
            "Within the Apotheca exist several specialized orders: the "
            "ASHENVALE ACQUISITIONS track magical items and relics; the "
            "MAIMED ONES seek to cure afflictions; the NUX VOMICA master "
            "poisons; and the GRIMSCRIBES pursue lore through long "
            "expeditions beyond the towers. The most mysterious is "
            "CHAPTERHOUSE 7, which is said only to preserve the order's "
            "hidden vaults — its membership itself a secret."
        ),
        factions={"apotheca"},
    ),
    _E(
        title="Apotheca: Magic, Lore, and the Old Wards",
        text=(
            "The Apotheca has long served as guardians of magical knowledge "
            "and written lore from the Eldritch Age. For centuries they have "
            "worked to restrict magical practice and seal sorcery under lock "
            "and key, fearing misuse. Some senior masters now believe magic "
            "will return to the world, and have spent the last three "
            "centuries quietly preparing for that moment."
        ),
        factions={"apotheca"},
    ),
    _E(
        title="Apotheca: The Aurorym Crisis",
        text=(
            "Under the Bannon kings the Apotheca faces its sharpest crisis "
            "in centuries: the Aurorym faith rises and questions the order's "
            "neutrality and ancient practices. Some Magisters have converted; "
            "rumor says an Aurorym Archmagister now sits the Inner Council "
            "seeking to make conversion mandatory. The brotherhood is "
            "divided over whether to preserve the ancient essence or adapt "
            "to survive."
        ),
        factions={"apotheca"},
    ),
])

# ---------------------------------------------------------------------------
# CIRQUE — from the Cirque faction packet
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="Cirque: Origin and Monopoly",
        text=(
            "The Cirque is the crafting and merchant guild of Arnesse, "
            "granted absolute monopoly over craft and trade by the Crown in "
            "the Age of Kings. What began as separate independent guilds in "
            "the free cities has consolidated — particularly after the Great "
            "War — into a single unified body with major guildhalls in ten "
            "cities and minor ones in many more."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: Hierarchy and Ranks",
        text=(
            "The Cirque hierarchy runs Trooper, Journeyman, Tradesman, "
            "Master, and Ringmaster. Each established troupe governs its own "
            "region and enforces the guild's monopoly for the benefit of "
            "both the organization and itself. The RINGMASTER holds the "
            "highest rank, responsible for a broad area and all its "
            "guildhalls. The PROPHET is the Ringmaster of Orn — strongest "
            "and most respected of all."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: Privilege and the Carnie Code",
        text=(
            "Privilege is the coin paid to the Cirque by a tradesman to work "
            "within the guild's sphere — in exchange for placement at "
            "markets and protection at and away from market. Without "
            "Privilege, a tradesman cannot legally craft or sell. The CARNIE "
            "CODE governs internal conduct; violations are resolved in the "
            "RING OF BLOOD — a duel where honor is decided by blade, both "
            "combatants cutting their hands and vowing not to leave the "
            "circle until one is dead."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: The Nagas",
        text=(
            "The NAGAS are the personal mercenary company retained by the "
            "Cirque, identified by their serpent sigil — a dagger entwined "
            "by a snake. Broken into groups called NESTS stationed across "
            "Arnesse, they wear dark armor and serpent-motif clothing. "
            "Nagas are drawn exclusively from the lower classes; even noble "
            "blood is rarely allowed permanent service in the company."
        ),
        factions={"cirque", "nagas"},
    ),
    _E(
        title="Cirque: The Golden Hall in Orn",
        text=(
            "The Free City of Orn rests on the southwestern coast and houses "
            "the GOLDEN HALL — the Cirque's headquarters of solid sandstone, "
            "its great hall lined in pure gold. The Hall dominates the WHEEL "
            "OF GOLD where Orn's commerce flows. All Privilege paid anywhere "
            "in Arnesse is ultimately funneled to Orn and to the Prophet."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: The Major Troupes",
        text=(
            "The Cirque operates through territorial troupes. The JACKALS "
            "control Orn's streets; the KRAITS govern Talesein; the IRON "
            "BLOODS rule Ember; the HIGH STREET KINGS dominate King's "
            "Crossing; the DEATH JESTERS operate from Scyld; and the TEN "
            "KNIVES and LORDS hold Highcourt. Each troupe specializes — "
            "street control, craftsmanship, intelligence — and they are "
            "rivals as often as allies."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: Trade Roads and Postal Network",
        text=(
            "The Cirque maintains the major overland trade roads: the DRAGON "
            "ROAD from Orn to Talesein through desolate terrain, guarded by "
            "the CRIMSON CORTEGE caravan; the ASHEN ROAD within a single "
            "Protectorate; the GOLDEN ROAD between Talesein and King's "
            "Crossing; and the DUSK ROAD from Ember to Scyld. The Cirque "
            "also runs the realm's only reliable postal courier service — "
            "letters delivered via troupe outposts for a fee."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: Carnie Cant",
        text=(
            "Over the years the Cirque has developed its own jargon — CARNIE "
            "CANT — born from the days when it was still a performance "
            "group. Cant words distinguish guild members from outsiders and "
            "let members discuss illicit or sensitive matters openly. Some "
            "terms have leaked into common speech, but the deeper Cant "
            "remains opaque to non-Cirque ears."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: Political Neutrality",
        text=(
            "The Cirque is a guild first, reluctant to involve itself in "
            "political affairs unless they threaten guild interests. It "
            "maintains strict non-interference between noble houses and bars "
            "those of noble blood from joining the inner ranks — keeping the "
            "guild's loyalties to itself, not to any house. This neutrality "
            "is what has let the Cirque work for nearly every power in "
            "Arnesse without losing its license."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: The Underwriter (public story)",
        text=(
            "The UNDERWRITER is a figure of legend who arranges unusual "
            "contracts — a courier route no one else will run, an item lost "
            "to the mists, a debt called in across borders. Sealed letters "
            "left at the Broken Oar in Gateway reach her, somehow. Most "
            "folk assume she is Cirque-affiliated; that is the public story. "
            "Her bargains are famous for being precisely fulfilled — and "
            "unusually steep in their final price. Speak of her quietly."
        ),
        factions={"cirque"},
    ),
    _E(
        title="Cirque: Houses and the Aurorym Tension",
        text=(
            "The Cirque maintains complex house relationships: deep dealings "
            "with House Richter, merchant vessels for Rourke trade, "
            "Privilege agreements with Aragon and Bannon, the Midlands trade "
            "for Corveaux, and tense relations with Innis and Rourke. The "
            "rising Aurorym faith strains the Cirque internally — some "
            "guildhalls have converted, and the faith openly questions the "
            "morality of the Black Market and the Menagerie. Ideological "
            "fracture is growing."
        ),
        factions={"cirque"},
    ),
])

# ---------------------------------------------------------------------------
# THE MISTWALKER COMPACT — Gateway-side public knowledge
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="The Mistwalker Compact",
        text=(
            "The Mistwalker Compact is the guild whose members can navigate "
            "the Mists between Arnesse and the Annwyn. They emerged in the "
            "moons after the Day of Mist; no one knows their origin and the "
            "Compact will not say. Mistwalkers do not teach the way through "
            "the fog; they do not bring people back; they do not judge whom "
            "they take in. Their Crossing Office in Gateway, run by the "
            "Registrar Crane, registers Writs of Safe Conduct. Their saying: "
            "'Once the Annwyn has you, only she can let you go.'"
        ),
        factions={"mistwalker_compact", "mistwalker"},
    ),
    _E(
        title="Mistwalker Compact: Internal Code",
        text=(
            "Within the Compact — only known to its sworn members — the "
            "guild operates by a strict triad: Registrars handle paperwork "
            "and oaths; Guides walk bearers through the mists; Wardens watch "
            "the Mistwall from the Annwyn side. Each Mistwalker chooses "
            "(or is given) a single-word working name: Crane, Soap, Greyveil, "
            "Magpie, Veil. The original names of Mistwalkers are not spoken. "
            "The Compact does not explain why."
        ),
        factions={"mistwalker_compact", "mistwalker"},
        scope="secret",
    ),
])

# ---------------------------------------------------------------------------
# AURORYM — DEEPER LORE (Litanies, Living Saints, sub-orders)
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="Aurorym: The Five Litanies",
        text=(
            "Aurorym practice rests on five Litanies: the Litany of Shelter "
            "(defend the defenseless); the Litany of Flame (root out darkness "
            "and corruption); the Litany of Courage (stand firm against "
            "evil); the Litany of Virtue (purity of heart and uprightness); "
            "and the Litany of Hope (be a beacon in darkness). Together they "
            "guide the faithful's path toward Apotheosis."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="Aurorym: The Living Saints",
        text=(
            "Saint Celestine the Eternal commands the Fervent Order of the "
            "Vellatora since the Age of Kings — her undying immortality "
            "taken as proof of the Hallowed. Saint Decima the Immaculate "
            "Aegis stands behind shield and silence. Saint Casilda the "
            "Dawnbreaker, undefeated in single combat, was champion of "
            "House Blayne — slain by werewolves in the Annwyn and rumored "
            "reborn under the Laurent banner in Mystvale. Saint Sachi the "
            "Pure Prophet wanders Arnesse with a single aspirant."
        ),
        factions={"aurorym", "vellatora"},
    ),
    _E(
        title="Aurorym Sub-Orders: the Hierarchs and Confessors",
        text=(
            "The HIERARCHS, founded under King Giles II, work to standardize "
            "Aurorym doctrine across Arnesse — distinctive marks of rank on "
            "their robes, the Book of Magnus carried as authority. The "
            "CONFESSORS counsel the faithful in their path toward "
            "Apotheosis, embodying the ideals of Saint Orione the Pure. "
            "Both orders have grown in influence under Bannon rule."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="Aurorym Sub-Orders: the Reckoners and Gravekeepers",
        text=(
            "The RECKONERS are the only order permitted the rite of "
            "Glorification, judging disputes among the faithful and arbiting "
            "doctrine — feared as much as respected. They take no patron, "
            "swear celibacy, and accept only auron-rank Curates and above. "
            "The GRAVEKEEPERS make their homes at cemeteries, warding "
            "against the Unhallowed; they pass a grueling examination in "
            "warding lore before they may serve."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="Aurorym Sub-Orders: Purgators and Redeemed",
        text=(
            "The PURGATORS are metaphysical warriors who handle possession, "
            "curses, and corruption — they assess fallen brethren for "
            "salvage or for mercy. Membership marks one as a survivor of "
            "Unhallowed harm. The REDEEMED — sprung from Saint Jamie the "
            "Redeemed — are former oath-breakers and criminals seeking "
            "redemption through martial service, particularly in House "
            "Blayne's military, marked with the Solux tattoo on the forehead."
        ),
        factions={"aurorym"},
    ),
    _E(
        title="The Red Dawn (Aurorym heresy)",
        text=(
            "A decade past, an ex-Curate named Mary founded the RED DAWN — "
            "a radical splinter calling for the violent purging of the "
            "nobility, with their wealth converted to the faithful. The "
            "Reckoners stripped her rank; the Aurorym disavowed the "
            "movement; but Red Dawn cells continue to make bloody purges "
            "of the gentry. They are hunted by both the Aurorym and the "
            "houses."
        ),
        factions={"aurorym"},
    ),
])

# ---------------------------------------------------------------------------
# VELLATORA — Aurorym military arm
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="The Fervent Order of the Vellatora",
        text=(
            "The Vellatora is the martial arm of the Aurorym faith. Unlike "
            "knight orders bound to a single noble house, the Vellatora "
            "answers to the Aurorym hierarchy itself — and ultimately to "
            "Saint Celestine the Eternal. Their training combines blade and "
            "breviary; the sword serves the Litanies. To meet a Vellatora "
            "knight on the field is to meet the faith made steel."
        ),
        factions={"vellatora", "aurorym"},
    ),
    _E(
        title="Vellatora: The Wardall of Exeter",
        text=(
            "In the city of Exeter stands the WARDALL — the tomb and "
            "fortress raised in honor of Saint Cuthbert, fallen defending "
            "innocents in the invasion of King Richard II. Exeter is sacred "
            "ground and the Vellatora's primary chapterhouse. Almost every "
            "resident has martial training; the Magnus Rectorix raises "
            "orphans not strong enough to be Vellatora as aurons instead, "
            "so the city's knights and aurons are often paired from "
            "childhood."
        ),
        factions={"vellatora", "aurorym"},
    ),
    _E(
        title="Vellatora: Knights of the Living Saints",
        text=(
            "Each Vellatora knight aspires to follow the path of one Living "
            "Saint, seeking to match their deeds in battle and virtue. "
            "Personal sigils combine the Dawn Sun with a chosen Saint's "
            "mark: Decima's great shield, Casilda's shattered tower, "
            "Celestine's crossed staff and sword. The Vellatora have stood "
            "with the Aurorym through every doctrinal crisis — and against "
            "the Crown when needed, as in the Witch Purge of King Giles."
        ),
        factions={"vellatora", "aurorym"},
    ),
])

# ---------------------------------------------------------------------------
# THE VIGIL — guild of noble counsel
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="The Vigil: Guild of Noble Counsel",
        text=(
            "The Vigil is a guild of highborns trained to serve as "
            "protectors, advisors, and administrators to Arnesse's nobility. "
            "Founded in 452 AS by Queen Catherine and chartered by the "
            "Throne, it operates through decentralized schools called "
            "SCHOLA, headquartered at Highcourt's Hall of Scales. Vigil "
            "graduates are second only to their lord or lady in their "
            "house's authority."
        ),
        factions={"vigil"},
    ),
    _E(
        title="Vigil: The Tria Principia and the Modulus",
        text=(
            "PROTECTION. WISDOM. JUSTICE. These three principles — the "
            "TRIA PRINCIPIA — are the sacred foundation of the Vigil. From "
            "their first day of study, acolytes learn that if even one of "
            "the three fails, order itself collapses. The MODULUS, or "
            "Scale, is the guild's universal symbol — the balance between "
            "Sentinels and Justicars. Vigil live spartan lives of "
            "discipline, never excess."
        ),
        factions={"vigil"},
    ),
    _E(
        title="Vigil: The Geminus Sacramentum",
        text=(
            "Every Vigil swears the GEMINUS SACRAMENTUM — the Dual Oath. "
            "The first oath binds them to the guild and its Tria Principia "
            "at graduation. The second is a fealty oath to the noble house "
            "they serve, contracted on terms that may be severed if breached "
            "by the lord. The dual oath ensures that no Vigil's loyalty is "
            "ever simple — and that no house may command absolutely."
        ),
        factions={"vigil"},
    ),
    _E(
        title="Vigil: The Wylding Hand and Perfectum Corpus",
        text=(
            "The Vigil train in the PERFECTUM CORPUS — a metaphysical "
            "discipline that produces the WYLDING HAND, a hand-to-hand "
            "combat technique that appears supernatural to the untrained. "
            "Graduates are rumored to shatter weapons with bare hands and "
            "perceive what others miss. This esoteric craft, combined with "
            "the guild's hunger for lost lore, makes the Vigil both "
            "protectors and seekers."
        ),
        factions={"vigil"},
    ),
    _E(
        title="Vigil: The White Ravens and the Missiona Ascensus",
        text=(
            "The youngest order within the Vigil, the WHITE RAVENS were "
            "created under King Giles II to enforce the Morality Laws. "
            "They wear raven-skull necklaces and white-feathered mantles, "
            "and may operate across any house. The older MISSIONA ASCENSUS "
            "— a multi-generational project to track noble bloodlines "
            "carrying potential for the Eldritch — has shaped strategic "
            "marriages for centuries; the Seekers carry on this work."
        ),
        factions={"vigil"},
    ),
    _E(
        title="Vigil: Composition and the Aurorym Tension",
        text=(
            "The Vigil is composed almost exclusively of second, third, "
            "fourth, and fifth children of noble houses — younger siblings "
            "given status without claim to the crown. They stand as the "
            "secular counterpart to the Aurorym faith, demanding evidence "
            "where Aurons demand belief. With House Blayne's rise, rumors "
            "swirl that the Aurorym means to convert the guild and bind its "
            "secular power to the faith. Most Vigil remain wary."
        ),
        factions={"vigil"},
    ),
])

# ---------------------------------------------------------------------------
# THE TWILIGHT EMPIRE — formerly "Grasslands" in the source docs
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="The Twilight Empire: People of the Sun",
        text=(
            "Far to the east of Arnesse rises the TWILIGHT EMPIRE, founded "
            "by nomadic tribes from the northern steppes who united after "
            "centuries of internal strife. The empire's people call "
            "themselves the People of the Sun. Smaller in territory than "
            "Arnesse but possessed of formidable military skill and "
            "discipline, the Empire has thrived for hundreds of years and "
            "begun, under the Great Sun Kaidu, its greatest expansion "
            "westward — establishing trade and conquest across distant "
            "lands."
        ),
        factions={"twilight_empire"},
        regions={"east"},
    ),
    _E(
        title="Twilight Empire: The Five Divisions",
        text=(
            "The Empire is governed through five military and administrative "
            "Divisions: the BEAR, frontline fighters under the strongest "
            "warrior; the WOLF, flanking cavalry and ambush masters; the "
            "EAGLE, elite rangers and assassins answering only to the Great "
            "Sun; the HORSE, scholars and ministers managing the realm; and "
            "the TIGER, the Great Sun's personal imperial guard. Beneath "
            "the order, the children and concubines of the Great Sun fuel "
            "constant rivalries between divisions."
        ),
        factions={"twilight_empire"},
    ),
    _E(
        title="Twilight Empire: The Steppe Way",
        text=(
            "To the People of the Sun, the horse is life — transport, food, "
            "war-mount, and beloved companion from childhood. Disputes are "
            "settled in wrestling and archery contests, traditions of "
            "fairness without blood. Women are the equal of men: educated "
            "in martial arts and governance, holding rank as generals, "
            "ministers, and guardians. The Great Sun is held to be a living "
            "deity walking among his people."
        ),
        factions={"twilight_empire"},
    ),
    _E(
        title="Twilight Empire: The Western Campaign",
        text=(
            "Centuries of struggle in the north gave way to a golden age "
            "of prosperity. When the Empire's first western trade envoys "
            "were rejected and slain, the Great Sun answered with armies. "
            "Through superior tactics they have conquered cities, including "
            "footholds in Arnesse itself — the conquered lands now flourish "
            "with cultural exchange and trade, drawing diverse peoples into "
            "the Great Sun's growing dominion."
        ),
        factions={"twilight_empire"},
    ),
    _E(
        title="Twilight Empire: Festivals and Faith",
        text=(
            "The Empire honors its calendar with grand festivals: the "
            "Annual Wrestling and Archery Tournament where talent is tested "
            "and warriors chosen; the Spring Festival of bonfires and "
            "kinship; the Harvest Festival of feasting and ancestor honor. "
            "Underneath: the universe is balanced between good and evil, "
            "the dead are honored with incense and offerings for their "
            "afterlife journey, and great magic is a gift to be revered "
            "rather than feared."
        ),
        factions={"twilight_empire"},
    ),
])

# ---------------------------------------------------------------------------
# NETHERMANCERS — boss-tier antagonists. Annwyn-scope or admin-only.
# ---------------------------------------------------------------------------
ENTRIES.extend([
    _E(
        title="Nethermancers: The Black Craft (rumor)",
        text=(
            "A name muttered in old soldier-stories and Aurorym warning "
            "sermons. Before the Eldritch Cataclysm, Nethermancers wielded "
            "a perverse high sorcery — said to summon legions of the dead "
            "and wield titanic forces of corruption. The Cataclysm severed "
            "the Eldritch from the world; many believe the Nethermancers "
            "were burned out with it. Some whisper that fragments survived, "
            "hidden in shadow, biding their time."
        ),
        factions={"nethermancy"},
        scope="gateway",
    ),
    _E(
        title="Nethermancers: The Four Paths",
        text=(
            "In ages past, the Nethermancer's craft followed four paths: "
            "SPIRITBINDING, which enslaved the souls of the dead; "
            "FLESHWEAVING, which gave false life to corpses; ELDRITCH "
            "REAVING, which stripped essence from the living; and "
            "BLASPHEMOUS INVENTION, which fused death and Void with arcane "
            "artifice. Each path was a doorway to power beyond mortal "
            "comprehension, and each demanded terrible payment."
        ),
        factions={"nethermancy"},
        scope="annwyn",
    ),
    _E(
        title="Nethermancers: Animus Obliteration",
        text=(
            "The Nethermancer's victims do not pass to the realm of the "
            "dead. Their animus is consumed by the Void itself — no "
            "afterlife, no rest, no memory. They are simply erased, and "
            "their essence becomes fuel for the Nethermancer's craft. Even "
            "the bravest Magister blanches at the thought."
        ),
        factions={"nethermancy"},
        scope="annwyn",
    ),
    _E(
        title="Nethermancers: Modern Survivors",
        text=(
            "The Nethermancer tradition is said not to have died with the "
            "Cataclysm but to have adapted to survive in shadow. Modern "
            "practitioners — masquerading as humble magisters, alchemists, "
            "or common folk — blend fragments of dark magic with alchemy "
            "and artifice. Their goal is no longer dominion by sorcery but "
            "infiltration. Artifacts of metal and bone, indistinguishable "
            "from legitimate arcane wonders, are rumored hidden in the "
            "darkest corners of civilized society. Those who hunt them are "
            "few; those who survive the hunt, fewer still."
        ),
        factions={"nethermancy"},
        scope="annwyn",
    ),
    _E(
        title="Nethermancers: The Forbidden Word",
        text=(
            "Guarded more closely than any other secret of the "
            "Nethermancers is the FORBIDDEN WORD — a language so potent "
            "that to speak it aloud is punishable by death or banishment "
            "in most civilized lands. Its letters are said to hold raw "
            "darkness. Knowledge of the Word unlocks the deepest "
            "mysteries of the craft; few who learn it remain sane."
        ),
        factions={"nethermancy"},
        scope="secret",
    ),
])

