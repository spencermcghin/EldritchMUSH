"""Commoner perspective canon — what NON-NOBLES from each protectorate know
and feel about their region. Drawn from the Generalist (commoner-perspective)
packets in the Drive's Generalist/ARCHIVE folder.

The Final regional packets are .gdoc Google Doc pointers and unreadable
from disk; the ARCHIVE packets are the most current readable source.
"""
from world.canon import ENTRIES, CanonEntry as _E

ENTRIES.extend([
    # =====================================================================
    # HEARTHLANDS — what a Blayne commoner believes
    # =====================================================================
    _E(
        title="Hearthlands Commoner: Faith and Fields",
        text=(
            "In the Hearthlands, the day starts with bell and prayer. The "
            "common folk tend their crops and livestock, their lives bound "
            "tightly to the wheel of seasons and the will of the Aurorym "
            "faith. Most are content with their lot — simple folk who know "
            "little beyond their village bounds — but they harbor deep "
            "suspicion of strangers and often jump to conclusions about a "
            "traveler's intentions. They fear the encroaching darkness in "
            "the woods and whisper about things that skulk beneath the "
            "hag stones at night. Their faith is comfort; they cling to "
            "it fiercely, believing the Aurorym protects them if they "
            "remain faithful."
        ),
        regions={"region:hearthlands", "hearthlands"},
        houses={"house:blayne"},
    ),
    _E(
        title="Hearthlands Commoner: The Weight of Piety",
        text=(
            "To be a Hearthlands laborer is to know obligation. Tithes go "
            "to the chantry, taxes to the Crown, and what remains must "
            "feed mouth and belly. The common folk accept this as the "
            "natural order — nobles rule, knights protect, aurons guide, "
            "peasants work. What troubles them more is the question of "
            "faith itself: are they devout enough? Will the Hallowed look "
            "favorably on them when their time comes? They pray, make "
            "offerings, teach their children the old stories — hoping "
            "devotion alone will be enough."
        ),
        regions={"region:hearthlands", "hearthlands"},
        houses={"house:blayne"},
    ),
    _E(
        title="Hearthlands Commoner: Old Ways Beneath the Faith",
        text=(
            "The Hearthlands are rife with folk belief and superstition "
            "alongside formal piety. Wise women brew remedies in cottage "
            "gardens, children are warned against certain woods after "
            "dark, and protective charms hang in doorways against ill "
            "intent. The chantry frowns on such practices, but the common "
            "folk know the old ways offer protection the Aurorym alone "
            "cannot guarantee. They speak in hushed tones of the Eaters "
            "of the Dead, of witches who walk at night, and of treasures "
            "hidden beneath the hag stones — knowledge dangerous to speak "
            "aloud."
        ),
        regions={"region:hearthlands", "hearthlands"},
        houses={"house:blayne"},
    ),

    # =====================================================================
    # DUSKLANDS — what a Richter commoner believes
    # =====================================================================
    _E(
        title="Dusklands Commoner: Living in Shadow",
        text=(
            "A Dusklands villager knows the land is cursed, even if the "
            "nobles say otherwise. The mountains loom dark, the forests "
            "whisper with ancient malice, the people make their living in "
            "the shadow of ruins left by older, stranger powers. They are "
            "accustomed to hardship — cold winters, thin harvests, the "
            "ever-present threat of things that move in darkness. Their "
            "faith in the Aurorym is mixed with older, rawer fears; they "
            "make offerings to the spirits of the land as much as to the "
            "Hallowed, hoping to stay on the good side of forces they do "
            "not fully understand."
        ),
        regions={"region:dusklands", "dusklands"},
        houses={"house:richter"},
    ),
    _E(
        title="Dusklands Commoner: Craft and Caution",
        text=(
            "Dusklands common folk are skilled in the practical arts of "
            "survival — smithing, hunting, trapping, and the careful "
            "husbandry of stubborn land. They are proud of their work and "
            "their ingenuity, but cautious. Strangers are viewed with "
            "suspicion, and those who speak too freely about the ruins or "
            "the old magics are quietly discouraged. The Dusklands have "
            "learned that curiosity can be fatal, and that some questions "
            "are better left unasked. Yet within their own communities, "
            "there is a fierce loyalty and a dark humor that helps them "
            "endure."
        ),
        regions={"region:dusklands", "dusklands"},
        houses={"house:richter"},
    ),
    _E(
        title="Dusklands Commoner: Aurorym and the Old Powers",
        text=(
            "The people of the Dusklands struggle with their faith in ways "
            "other protectorates do not. The Aurorym is their religion, "
            "and they follow it outwardly, but the old powers in the "
            "mountains and forests feel more immediate and more dangerous. "
            "Some fear the Hallowed have abandoned them to their harsh "
            "fate; others believe the Aurorym faith is the only thing "
            "standing between them and absolute darkness. Either way, "
            "they live with constant awareness that whatever shares the "
            "land with them is not necessarily friendly."
        ),
        regions={"region:dusklands", "dusklands"},
        houses={"house:richter"},
    ),

    # =====================================================================
    # NORTHERN MARCHES — what an Innis commoner believes
    # =====================================================================
    _E(
        title="Northern Marches Commoner: Warriors and Woodcraft",
        text=(
            "The people of the Northern Marches differ from southern cousins "
            "in obvious and subtle ways. They are raised from childhood to "
            "be capable with blade and bow, to understand woodcraft and "
            "animal husbandry, to move silently through forest. But they "
            "are not savage — they are disciplined, ordered, deeply bound "
            "by tradition and custom. The common folk understand their "
            "place in a warrior society and take pride in it. They work "
            "hard, fight when called upon, and believe that honor and "
            "loyalty matter more than gold or comfort."
        ),
        regions={"region:northern-marches", "northern_marches"},
        houses={"house:innis"},
    ),
    _E(
        title="Northern Marches Commoner: The Forest's Gift and Price",
        text=(
            "Life in the Thornwood and the borderlands requires constant "
            "vigilance. The forests are beautiful but dangerous, full of "
            "both bounty and threat. A Marcher child learns early how to "
            "move through the trees, how to read the land, how to "
            "distinguish the useful from the deadly. They respect the "
            "forest as both provider and predator, and understand that "
            "to live there is to accept risk. Their superstitions run "
            "deep — they believe in spirits of wood and water, in the "
            "intelligence of ancient trees, and in the importance of "
            "maintaining balance with the wild world."
        ),
        regions={"region:northern-marches", "northern_marches"},
        houses={"house:innis"},
    ),
    _E(
        title="Northern Marches Commoner: Distant Nobles, Close Bonds",
        text=(
            "The common folk of the Northern Marches rarely see their "
            "nobles, and they do not expect much from them. The nobility "
            "is distant and occupied with border wars and political "
            "maneuvering, so the villages and holds govern themselves "
            "through tradition and consensus. This creates strong "
            "community among commoners — neighbors are the people they "
            "rely on for survival, and bonds of kinship and obligation "
            "run deep. They view outsiders with caution and maintain "
            "fierce pride in their own ways, shaped by centuries of living "
            "on the edge of the known world."
        ),
        regions={"region:northern-marches", "northern_marches"},
        houses={"house:innis"},
    ),

    # =====================================================================
    # MIDLANDS — what a Corveaux commoner believes
    # =====================================================================
    _E(
        title="Midlands Commoner: Trade and Tradition",
        text=(
            "The Midlands are the beating heart of commerce and craft in "
            "Arnesse, and the common folk take pride in their work and "
            "their goods. Whether farmer, smith, weaver, or merchant, a "
            "Midlander believes their labor has value and that a fair "
            "price is a matter of honor. They are competitive — proud of "
            "their skills, eager to show that their work is superior. Yet "
            "they are also bound by strong social tradition and believe "
            "deeply in fairness, justice, and equity. They trust in the "
            "Aurorym faith, but they trust equally in their own ability "
            "to shape destiny through hard work and clever dealing."
        ),
        regions={"region:midlands", "midlands"},
        houses={"house:corveaux"},
    ),
    _E(
        title="Midlands Commoner: Order and Law",
        text=(
            "The common folk of the Midlands believe that law and order "
            "are necessary for civilization to flourish. They expect their "
            "rulers to maintain justice and protect property, and that "
            "those who break the law should be punished swiftly and fairly. "
            "Crime is rare in Midlands towns and villages because social "
            "pressure against wrongdoing is immense — most people know "
            "transgression brings shame not only on themselves but on "
            "their families. This deep belief in virtue and proper conduct "
            "sometimes makes Midlands justice appear harsh, but it is "
            "rooted in genuine conviction that strict law alone keeps "
            "the peace."
        ),
        regions={"region:midlands", "midlands"},
        houses={"house:corveaux"},
    ),
    _E(
        title="Midlands Commoner: Freedom and Responsibility",
        text=(
            "A Midlander values personal freedom highly — the freedom to "
            "work hard, to make their own choices, to improve their lot "
            "through talent and effort. But this freedom comes with "
            "responsibility: to support the community, to obey the law, "
            "to treat others with justice. They are skeptical of those "
            "who would impose their will by force or deception, and they "
            "believe true power comes from the respect and consent of "
            "one's peers. The Midlands culture is more egalitarian than "
            "many other regions, though it is not without its inequalities "
            "and tensions."
        ),
        regions={"region:midlands", "midlands"},
        houses={"house:corveaux"},
    ),

    # =====================================================================
    # ROURKE COAST / THREE SEAS — sea-folk commoner perspective
    # =====================================================================
    _E(
        title="Three Seas Commoner: Salt and Survival",
        text=(
            "The people of the Three Seas are shaped by the ocean as surely "
            "as clay is shaped by the potter's hands. Whether sailor, "
            "fisher, dock worker, or merchant, the sea is the center of "
            "their lives. They know its moods — calm and generous one "
            "day, violent and deadly the next. They are accustomed to "
            "danger, to loss, to the constant awareness that the sea is "
            "indifferent to human plans and desires. They are superstitious "
            "about the water and the ships that float upon it, making "
            "offerings to ancient spirits and following traditions passed "
            "down through countless generations. To them, the sea is both "
            "home and master."
        ),
        regions={"region:rourke-coast", "region:three-seas", "three_seas", "rourke_coast"},
        houses={"house:rourke"},
    ),
    _E(
        title="Three Seas Commoner: Harbor Tales and Wide-World Cynicism",
        text=(
            "The ports and harbors of the Three Seas are hives of activity "
            "and rumor. News travels fast in these crowded, chaotic places "
            "— merchant gossip, tavern tales, stories brought by sailors "
            "from distant lands. A Three Seas commoner is worldly in a "
            "way that most people in other regions are not. They have "
            "heard stories of strange lands, of unusual peoples, of "
            "wonders and horrors that exist beyond the known world. This "
            "exposure to a wider world makes them both more confident and "
            "more cynical; they trust less in absolutes and more in the "
            "evidence of their own eyes and ears."
        ),
        regions={"region:rourke-coast", "region:three-seas", "three_seas", "rourke_coast"},
        houses={"house:rourke"},
    ),
    _E(
        title="Three Seas Commoner: Gold and Guile",
        text=(
            "In the Three Seas, wealth matters more than birth, and "
            "reputation matters more than title. A clever person with no "
            "family name can rise to prominence through wit, hard work, "
            "and good fortune. This creates a culture of ambition and "
            "hustle, where common folk view themselves as having agency "
            "in their own destinies. The downside: the Three Seas are "
            "also home to more crime, more deception, and more violence "
            "than many regions. Trust is earned through demonstrated "
            "reliability, not assumed by kinship or station. Survival "
            "depends on knowing when to trust and when to suspect "
            "treachery."
        ),
        regions={"region:rourke-coast", "region:three-seas", "three_seas", "rourke_coast"},
        houses={"house:rourke"},
    ),

    # =====================================================================
    # SOVEREIGNLANDS commoner — Bannon homeland
    # =====================================================================
    _E(
        title="Sovereignlands Commoner: Crown-Bound and Hardy",
        text=(
            "Sovereignlanders bear the weight of being closest to the "
            "Crown — every decree from Highcourt is felt first here, every "
            "tax collected with the King's swift authority. The folk are "
            "stoic and disciplined; their work is hard, their winters "
            "brutal. They fear most the wolves and what walks the deep "
            "Kingswood at night. Loyalty to House Bannon runs in the "
            "blood; even the bitter complain of the Crown only over a "
            "third cup of ale. The succession crisis worries them deeply: "
            "they have seen what happens when kings die without heirs."
        ),
        regions={"region:sovereignlands", "sovereignlands"},
        houses={"house:bannon"},
    ),

    # =====================================================================
    # EVERFROST commoner — Hale homeland
    # =====================================================================
    _E(
        title="Everfrost Commoner: Endure or Die",
        text=(
            "Everfrost folk grow up understanding two things above all "
            "others: the cold will kill you if you let it, and your "
            "neighbors are the only thing standing between you and that "
            "death. The community is small, tight, and unsentimental. "
            "Old folk are revered for surviving; the young train alongside "
            "their elders in survival skills, hunting, and basic combat. "
            "Folk songs are mournful and slow, suited to long dark "
            "evenings. The Aurorym faith reaches Everfrost but is mixed "
            "with older bear-spirit and ice-lore traditions; the chantries "
            "stand quiet through the long polar nights."
        ),
        regions={"region:everfrost", "everfrost"},
        houses={"house:hale"},
    ),

    # =====================================================================
    # TARKATH commoner — Aragon territories
    # =====================================================================
    _E(
        title="Tarkath Commoner: Old Names, Quiet Pride",
        text=(
            "Tarkathi commoners carry an ancient pride in their lineage "
            "even when they have no land or wealth. Family names matter; "
            "the Heset/Blood/Deed naming customs of the south are honored "
            "even by farmers. They are skeptical of Ardan ways and slow "
            "to trust outsiders. The old language and old festivals are "
            "kept alive in folk-song and household ritual. Tarkathi pride "
            "in Aragon's place among the Houses runs warmer than the "
            "Aragons themselves perhaps deserve — though privately the "
            "folk grumble that other Houses look down on them, and they "
            "remember every slight."
        ),
        regions={"region:tarkath", "tarkath"},
        houses={"house:aragon"},
    ),
])
