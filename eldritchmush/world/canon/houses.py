"""Great House canon — sigils, seats, lineages, alliances, key figures."""
from world.canon import ENTRIES, CanonEntry as _E

ENTRIES.extend([
    # ---- HOUSE BANNON (royal) ----
    _E(
        title="House Bannon: The Crown",
        text=(
            "House Bannon holds the throne of Arnesse from Castle Cair "
            "Ghalon. The Bannon line claims descent from Giles I, first "
            "king of the unified realm, and the Aurorym blessing has been "
            "central to their legitimacy ever since. Their sigil is the "
            "GOLD TOWER ON A CRIMSON FIELD; their motto, 'For the Realm.' "
            "Royal Welsh-Celtic naming runs in the line — Giles, Charles, "
            "Eldric, Cyrus, Symeon (the traitor)."
        ),
        houses={"house:bannon", "bannon"},
    ),
    _E(
        title="King Giles Bannon II",
        text=(
            "King Giles II inherited the Dragon Throne from his father, "
            "Giles I. A skilled administrator, his reign held Arnesse "
            "through decades of regional strain — until his murder during "
            "the Pendragon Tournament of 766 AS, struck down by his own "
            "Vigil Symeon Bannon. The succession remains contested. The "
            "Queen Aline of House Blayne survives him; her children's "
            "claims are now openly disputed."
        ),
        houses={"house:bannon", "bannon"},
    ),
    _E(
        title="The Bannon Garrison",
        text=(
            "The Bannons keep a hardened garrison tradition — every "
            "third son a knight, every second a man-at-arms. The Annwyn "
            "garrison at Carran under Arch Magistrat Symon Bannon trains "
            "knights for the Crown; Ser Ewan Bannon serves as his "
            "lieutenant. The Bannon gold tower on crimson is sewn to "
            "every halberdier's surcoat in the realm."
        ),
        houses={"house:bannon", "bannon"},
    ),

    # ---- HOUSE RICHTER ----
    _E(
        title="House Richter: Iron Lords of the Dusklands",
        text=(
            "House Richter rules from the DEEPHOLD in the dark stone "
            "reaches of the Dusklands. Smiths and warriors both, the "
            "Richters forge steel and will alike through generations of "
            "hardship. Sigil: the IRON HAMMER on grey (the great hammer "
            "of the smith-warrior; some Richter knights also bear the "
            "iron tower as an alternate device for their hold-keeps). "
            "Motto: 'Cinder and Steel.' Naming register is Germanic — "
            "Hawken, Yelena, Volkan, Wilhelm. Lord Hawken Richter, the "
            "Primmhammer, currently bears the weight of the line."
        ),
        houses={"house:richter", "richter"},
    ),
    _E(
        title="Richter: The Iron Guard",
        text=(
            "The IRON GUARD are the elite warriors of House Richter, clad "
            "in armor unmatched in the realm. Richter soldiers are known "
            "for grim patience, relentless pressure, and willingness to "
            "absorb punishment that would break lesser warriors. Half the "
            "Mistguard's halberdiers wear the iron hammer; Richter holds "
            "Gateway since Corveaux and Innis were driven out."
        ),
        houses={"house:richter", "richter"},
    ),
    _E(
        title="House Hardinger (Richter cadet)",
        text=(
            "House HARDINGER — a Richter cadet — controls the mountain "
            "passes, mining operations, and Annwyn-side garrison at "
            "Ironhaven. Lord Wilhelm Hardinger commands. The Hardingers "
            "are the primary funders of the Godslayer movement, a fact "
            "that has tarnished the Iron Hammer's name among more "
            "circumspect Richter."
        ),
        houses={"house:richter", "house:hardinger", "richter", "hardinger"},
    ),

    # ---- HOUSE CORVEAUX ----
    _E(
        title="House Corveaux: Falcons of the Midlands",
        text=(
            "House Corveaux rules the Midlands from KING'S CROSSING — a "
            "city of commerce, learning, and law. Sigil: the GREY FALCON "
            "on sky blue. Naming runs French — Desmond, Marien, Anne. "
            "Corveaux are scholars and diplomats as much as warriors. "
            "Lord Paragon Desmond Corveaux, ageing, leads from King's "
            "Crossing; his cadet HOUSE FALCONER under Lady Ella holds "
            "ARCTON in the Annwyn."
        ),
        houses={"house:corveaux", "corveaux"},
    ),
    _E(
        title="House Corveaux: Suthwater and the Vermilion Order",
        text=(
            "The Corveaux of SUTHWATER command the castle and surrounding "
            "sea-trade region, served by the VERMILION ORDER of knights. "
            "Lady Jeanne Corveaux rules with shrewd political maneuvering. "
            "Suthwater grows prosperous under her — though some whisper "
            "of morally questionable dealings. The Vermilion knights are "
            "famous for their crimson surcoats."
        ),
        houses={"house:corveaux", "corveaux", "vermilion_order"},
    ),

    # ---- HOUSE LAURENT (Bannon vassal) ----
    _E(
        title="House Laurent: The Antlered Hart",
        text=(
            "HOUSE LAURENT, a Bannon vassal, rules the Annwyn town of "
            "MYSTVALE from STAG HALL — formerly the ancient Castellan "
            "fortress of Maidencourt. Sigil: the antlered HART on deep "
            "green. Naming runs French — Ludmilla (founder), Silas (Lord "
            "Pro Tempore), Julia. The Laurents are the primary Annwyn-"
            "side governing house; they hold the Burgomaster's office, "
            "the town watch, and the Aurorym Chantry's patronage."
        ),
        houses={"house:laurent", "laurent"},
    ),
    _E(
        title="Laurent: The Mystvale Inner Circle",
        text=(
            "Domitille of the Apotheca serves as Burgomaster of Mystvale "
            "for House Laurent — a Magister-trained administrator with "
            "deep Apotheca contacts. Ser Ake Dagson is Sheriff. Walter "
            "Beauchamp serves as Seneschal. Lord Silas Laurent acts as "
            "Pro Tempore for the line. Together they administer the "
            "town's daily life and answer to the Crown via Carran."
        ),
        houses={"house:laurent", "laurent"},
        scope="annwyn",
    ),

    # ---- HOUSE HALE ----
    _E(
        title="House Hale: Wardens of the North",
        text=(
            "HOUSE HALE stands sentinel over the Everfrost and the harsh "
            "northern lands from the WAILING KEEP. Hardened by generations "
            "of conflict with creatures of the wild, the Hales motto: "
            "'Courage is Ours.' Naming runs Norse — Talbot, Oskari, "
            "Thora, Anatea. Lord Talbot Hale heads the line; Lady Emma "
            "Hale is heir."
        ),
        houses={"house:hale", "hale"},
    ),
    _E(
        title="House Coldhill (Hale cadet)",
        text=(
            "HOUSE COLDHILL is the Hale cadet that holds HARROWGATE in "
            "the Annwyn under Lady Thora Coldhill. Their sworn berserker "
            "retinue, the GET OF URSIN, keeps the bear-skull pauldron "
            "and the ritual scarring. Tova of the Get serves as their "
            "captain at the Hall of Bears."
        ),
        houses={"house:hale", "house:coldhill", "hale", "coldhill"},
        scope="annwyn",
    ),

    # ---- HOUSE INNIS ----
    _E(
        title="House Innis: Keepers of the Deep Woods",
        text=(
            "HOUSE INNIS holds the deep forests of the western Northern "
            "Marches from the seat of BRIDG'T. Naming runs Celtic — "
            "Keena, Bodhmall, Branwen. Lady Paragon Iantressa leads; "
            "the line keeps ancient pacts with the woods and its rumored "
            "inhabitants. Their motto: 'Live that you may live.' Their "
            "Annwyn-side hidden settlement is GOLDLEAF; their scouts "
            "wear leaf-green cloaks."
        ),
        houses={"house:innis", "innis"},
    ),
    _E(
        title="Innis: Suspected Crow Funding",
        text=(
            "The Innis are quietly suspected by both Crown and Cirque of "
            "arming the CROWS — the Annwyn-side bandit network whose "
            "ranks include Last Walk survivors. There is no proof, only "
            "patterns: caravan raids that hit Laurent traders harder than "
            "Richter, suspicious gaps in scout patrols where Crow signs "
            "appear. The Innis say nothing."
        ),
        houses={"house:innis", "innis"},
    ),

    # ---- HOUSE ARAGON ----
    _E(
        title="House Aragon: Lords of Dragonspire",
        text=(
            "HOUSE ARAGON claims descent from Tarkath, the first warrior-"
            "king who united the southern lands before the Age of Kings. "
            "Their seat is DRAGONSPIRE, built upon ruins of ancient "
            "glory. Naming runs Iberian-Romance — Lyra, Elenya, Hector, "
            "Vaeros, Danica. Sigil: the CRESCENT MOON on deep blue. "
            "Proud, ambitious, dark-haired, with a complex relationship "
            "to the Bannon Crown."
        ),
        houses={"house:aragon", "aragon"},
    ),
    _E(
        title="Aragon: The Hidden Outpost at Moonfall",
        text=(
            "The Aragons hold a hidden cliff outpost in the Annwyn called "
            "MOONFALL, surrounded by old standing stones. Few know its "
            "location. Heron Aragon serves as watchman. Aragon ships have "
            "been seen on the Ironhaven coast — and Ser Hartwig Richter "
            "refuses to discuss them. Some whisper that Aragon backs the "
            "Oban incursions; Heron, when pressed, is very clear that "
            "Aragon is not directly involved."
        ),
        houses={"house:aragon", "aragon"},
        scope="annwyn",
    ),

    # ---- HOUSE ROURKE ----
    _E(
        title="House Rourke: Masters of the High Armada",
        text=(
            "HOUSE ROURKE rules the coastal reaches from SCYLD with the "
            "HIGH ARMADA of ships, dominating naval trade and warfare in "
            "Arnesse waters. Their sigil: a ship upon rough seas. The "
            "Rourkes are bold, cunning, and not above bending morality "
            "for profit. Lord Paragon Tybold Rourke captains the SEA "
            "WRAITH; Lady Eleanor Stormwall serves as a legendary master "
            "captain."
        ),
        houses={"house:rourke", "rourke"},
    ),

    # ---- HOUSE BLAYNE ----
    _E(
        title="House Blayne: The Aurorym Patron",
        text=(
            "HOUSE BLAYNE holds the HEARTLANDS Protectorate and is the "
            "secular patron of the Aurorym faith. Magnus, the Aurorym's "
            "founder, was of Blayne blood. Naming is Germanic-Italic — "
            "Magnus, Frederick, Aline, Estella. Their colors are orange "
            "and green; their sigil shows a sun and sword crossed. Queen "
            "ALINE of the Bannon Crown is Frederick Blayne's daughter — "
            "her standing in the succession crisis is Blayne's chief "
            "concern."
        ),
        houses={"house:blayne", "blayne"},
    ),
    _E(
        title="Blayne: Saint Casilda and Beggar's Keep",
        text=(
            "Saint CASILDA THE DAWNBREAKER, undefeated in single combat "
            "and patron of House Blayne, was slain by werewolves in the "
            "Annwyn — and rumored reborn beneath the Laurent banner in "
            "Mystvale. Estella Blayne, daughter of Lord William of "
            "BEGGAR'S KEEP in the Hearthlands, is a noted Blayne heir. "
            "Sir Tadeo Blayne serves as a Vellatora knight commander and "
            "represents the house's military-religious tradition."
        ),
        houses={"house:blayne", "blayne"},
    ),

    # ---- MINOR HOUSES ----
    _E(
        title="House Varga: Dusklander Farmers",
        text=(
            "House VARGA holds the southern Dusklands from the Deephold's "
            "shadow, farming the blighted lands and managing underground "
            "ecosystems. Lady Sylvane Varga keeps a careful neutrality "
            "between the Great Houses through diplomacy and agrarian "
            "expertise. Their dealings are often quiet — and never "
            "advertised."
        ),
        houses={"house:varga", "varga"},
    ),
    _E(
        title="House Beil: The Black Keep",
        text=(
            "House BEIL holds the BLACK KEEP and the surrounding shadow "
            "lands of the southern Dusklands. Lord Udaine Beil commands "
            "with fierce dedication — his people skilled in the difficult "
            "work of guarding against the darkness that seeps from the "
            "wild places. Beil is the realm's southern frontier sentinel."
        ),
        houses={"house:beil", "beil"},
    ),
    _E(
        title="House Perryn: The Odda Edani Knights",
        text=(
            "House PERRYN holds Avalon and the surrounding northern plains. "
            "Skilled in mounted warfare, the Perryns founded the ODDA "
            "EDANI — a legendary order of knights still trained at "
            "Perryn castle. Their plains overlook ancient battlegrounds, "
            "and their cavalry is among the realm's finest."
        ),
        houses={"house:perryn", "perryn", "odda_edani"},
    ),
    _E(
        title="House Oban: Recent Aggressors",
        text=(
            "HOUSE OBAN have made repeated military incursions against "
            "Carran and Stag Hall in the past two years, supported (some "
            "whisper) by Aragon. Naming runs Celtic — Niall and others. "
            "The Oban are not yet at open war with the Crown, but every "
            "Bannon and Laurent watch them closely."
        ),
        houses={"house:oban", "oban"},
    ),
    _E(
        title="House Rourke (Pooka traditions)",
        text=(
            "House ROURKE has long associations with the POOKA — Celtic-"
            "Irish guides and spirit-touched scouts native to the Northern "
            "Marches. The Rourke seafaring tradition meets the Pooka's "
            "land-knowledge in mixed retainers; rare, prized, and quietly "
            "resented by stricter Aurorym."
        ),
        houses={"house:rourke", "rourke", "pooka"},
    ),
])
