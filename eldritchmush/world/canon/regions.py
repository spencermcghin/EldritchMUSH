"""Regional canon — the protectorates of Arnesse: geography, climate,
people, settlements, daily life, and cultural temperament. Drawn from
the Houses faction packets so any common-folk NPC can speak of their
home region with authority.
"""
from world.canon import ENTRIES, CanonEntry as _E

ENTRIES.extend([
    # =====================================================================
    # SOVEREIGNLANDS — House Bannon (royal protectorate)
    # =====================================================================
    _E(
        title="The Sovereignlands: Wolf-Haunted North",
        text=(
            "The Sovereignlands stretch across Arnesse's northernmost reach "
            "— ancient forests dense with shadow, long winters that bury "
            "settlements in snow, and folk hardened by them. Kingswood "
            "Forest dominates the interior; those who claim kinship with "
            "wolves are common. The land breeds loyalty bone-deep, honor "
            "as currency, and the subtle Bannon madness that touches most "
            "of noble descent. When someone vanishes here, folk say they "
            "were 'fed to the pack.'"
        ),
        regions={"region:sovereignlands", "sovereignlands"},
        houses={"house:bannon"},
    ),
    _E(
        title="Sovereignlands: Two Rivers and Hollowmere",
        text=(
            "Where the Sovereignlands soften, two great waterways converge "
            "in the TWO RIVERS protectorate — fertile farmland between, "
            "merchant boats moving daily, river-spirits respected with "
            "cautious offerings each spring thaw. Westward lies HOLLOWMERE, "
            "a desolate lakeland whose dark waters are said to hold ill "
            "fortune; folk live on the edges, never the heart, and quiet "
            "things are sometimes set adrift to appease what dwells beneath."
        ),
        regions={"region:two-rivers", "region:hollowmere", "two_rivers", "hollowmere"},
        houses={"house:bannon"},
    ),
    _E(
        title="Sovereignlands: Common Folk and the Wolf-Touch",
        text=(
            "Sovereignlanders rise before dawn for plots wrested from forest "
            "or moor; food runs scarce in winter despite careful storage. "
            "Community is tight by necessity, and craftwork fills the long "
            "evenings around hearth fires. The Bannon madness — the "
            "'touch of the wolf' — is not hidden but woven into life: "
            "parents speak of it carefully to children, and communities have "
            "old ways of managing those who succumb. Wolves are revered; "
            "hunting them is forbidden by royal decree."
        ),
        regions={"region:sovereignlands", "sovereignlands"},
        houses={"house:bannon"},
    ),
    _E(
        title="Region: The Hearthlands",
        text=(
            "The Hearthlands are warm, settled territories named for hearth "
            "and home — farmland, villages, established communities of "
            "common folk, artisans, and minor nobility. Patron house: "
            "Blayne. Aurorym Chantries dot the landscape; Saint Casilda "
            "the Dawnbreaker walked these roads in life. The Hearthlands "
            "are the backbone of the realm — serfs, freemen, merchants."
        ),
        regions={"region:hearthlands", "hearthlands"},
        houses={"house:blayne"},
    ),
    _E(
        title="Region: The Dusklands",
        text=(
            "The Dusklands are shadowed territories where darkness falls "
            "earlier and lingers longer. Forests block the sun; landscapes "
            "feel perpetually twilit. Patron house: Richter, with cadet "
            "Hardinger commanding the Deephold. Cities: Ember, Noctuary. "
            "The region has long sheltered practitioners of shadow magic "
            "and hides what other regions would burn."
        ),
        regions={"region:dusklands", "dusklands"},
        houses={"house:richter"},
    ),
    _E(
        title="Region: The Northern Marches",
        text=(
            "The Northern Marches are forested upland territories of "
            "western Arnesse, ancestral lands of HOUSE INNIS. Cold winters, "
            "stubborn farmland, hedge-witches in the deep woods. Lune is "
            "a notable town. The border conflict with the Dusklander "
            "vassals of House Richter has been simmering for years and "
            "fills the Last Walk columns with prisoners."
        ),
        regions={"region:northern_marches", "northern_marches", "marches"},
        houses={"house:innis"},
    ),
    _E(
        title="Region: The Midlands",
        text=(
            "The Midlands are the bountiful central heartlands — fertile, "
            "ideal for agriculture and great cities. Centered on KING'S "
            "CROSSING under House Corveaux. The Midlands fed the ancient "
            "Escalon Empire and remain the economic heart of Arnesse. "
            "Inland trade caravans converge here; Cirque presence is "
            "heavy."
        ),
        regions={"region:midlands", "midlands"},
        houses={"house:corveaux"},
    ),
    _E(
        title="Region: The Everfrost",
        text=(
            "The Everfrost is the northernmost reaches — frozen, sparsely "
            "settled, named for lands locked in perpetual winter. Patron "
            "house: Hale, with cadet Coldhill in the high country. "
            "Settlements like Grimfrost cling to defensible sites; the "
            "Get of Ursin walk the wood-edges. Few venture into the "
            "deepest Everfrost; much remains unmapped and dangerous."
        ),
        regions={"region:everfrost", "everfrost"},
        houses={"house:hale"},
    ),
    _E(
        title="Region: The Thornwood",
        text=(
            "The Thornwood is a vast forest region on the eastern edge of "
            "the Hearthlands, worked by logging crews and laborers — both "
            "Freemen and contracted. Ancient trees provide wealth and "
            "danger; the work is bloody. Lady Bríet of House Innis has "
            "been known to defend Thornwood timber rights with lethal "
            "force. Lydiard sits on the southern edge."
        ),
        regions={"region:thornwood", "thornwood"},
    ),
    _E(
        title="Region: Tarkath",
        text=(
            "TARKATH lies along the southern wastes, settled by the Tarkan "
            "people who maintain a culture distinct from the Ardan north. "
            "The TALIESIN city — the Golden City — rises here. The "
            "Apotheca's Ashen Tower stands in Tarkath, ancient and feared. "
            "Tarkathi are independent, often fiercely so; their warriors "
            "(Heset/Blood/Deed-named under Aragon's older traditions) hold "
            "ancestral pride in their lineage."
        ),
        regions={"region:tarkath", "tarkath"},
        houses={"house:aragon"},
    ),
    _E(
        title="Region: The Worldspine Mountains",
        text=(
            "The WORLDSPINE MOUNTAINS form the great spine of peaks "
            "running through Arnesse, dividing regions and creating "
            "natural fortifications. Treacherous heights, valuable "
            "minerals, dangerous creatures, harsh weather. Several "
            "strategic passes connect the Hearthlands to the Dusklands; "
            "control of those passes is bloodily contested in every war."
        ),
        regions={"region:worldspine", "worldspine"},
    ),
    _E(
        title="Region: The Deephold",
        text=(
            "The DEEPHOLD is the underground realm — vast subterranean "
            "caverns, stone halls, hidden communities beneath the "
            "Worldspine and Dusklands. Home to peoples adapted to "
            "darkness, with their own cultures and governance. House "
            "Richter rules its Dusklander surface holdings from there. "
            "Trade between surface and depths is limited; rumor places "
            "older powers in the deepest reaches."
        ),
        regions={"region:deephold", "deephold"},
        houses={"house:richter"},
    ),
    _E(
        title="Region: Breakwater Bay & the Western Coast",
        text=(
            "BREAKWATER BAY is the great coastal region of western Arnesse, "
            "where the Nyssian seaborn people made their home in the "
            "western islands. Rocky shores, treacherous waters, naval "
            "tradition. The bay fronts the WALL OF MIST — the Annwyn's "
            "edge. Rourke ships call here; pirates patrol the Skeleton "
            "Shoals and the Silent Shores. ARKHAM ISLAND is a name spoken "
            "carefully."
        ),
        regions={"region:breakwater", "breakwater_bay", "western_coast"},
    ),
    _E(
        title="Region: The Vale of Shadows",
        text=(
            "The VALE OF SHADOWS is the haunted river-vale on the western "
            "Arnesse coast. Rocky terrain, shadow-filled valleys, an air "
            "of danger. The DREAD RUN flows through it — a river-barge "
            "route used by Cirque caravans bound for Gateway. Few travel "
            "the Vale without purpose; superstitious peasants speak of "
            "things that move in the bog-fog. Gateway sits on its western "
            "edge."
        ),
        regions={"region:vale", "vale_of_shadows", "vale"},
    ),
    _E(
        title="Region: The Annwyn (across the Mists)",
        text=(
            "The ANNWYN — the Otherworld discovered after the Day of Mist "
            "— lies beyond the wall of fog at western Arnesse's edge. "
            "Ancient ruins, contested settlements, supernatural threats. "
            "Settlements: MYSTVALE (Laurent, central hub), IRONHAVEN "
            "(Richter, southwest coast), ARCTON (Corveaux, eastern sea), "
            "CARRAN (Laurent + Bannon garrison), HARROWGATE (Hale/Coldhill, "
            "far north), GOLDLEAF (Innis, hidden), MOONFALL (Aragon, "
            "hidden), and the ruined port of TAMRIS far southwest."
        ),
        regions={"region:annwyn", "annwyn"},
        scope="annwyn",
    ),
    _E(
        title="Region: The Annwyn (rumored)",
        text=(
            "The ANNWYN — the Otherworld beyond the Mists — is known to "
            "Gateway folk only as a name. Travelers speak of ancient "
            "ruins, named settlements (Mystvale, Carran, Ironhaven, "
            "Arcton, Harrowgate are the most-said), riches and dangers. "
            "Most who cross do not return; the ones who do come back "
            "speak in fragments, or refuse to speak at all. The Mistwalker "
            "Compact runs the only paid passage."
        ),
        regions={"region:annwyn", "annwyn"},
        scope="gateway",
    ),
    _E(
        title="Free City of Orn",
        text=(
            "The FREE CITY OF ORN sits on the southwestern coast — a "
            "mercantile city-state outside any Protectorate's direct "
            "rule. Headquarters of the Cirque guild via the GOLDEN HALL. "
            "All Cirque Privilege flows here. The Wheel of Gold is its "
            "great market; the Prophet, Ringmaster of Orn, holds the "
            "first chair of the Cirque hierarchy."
        ),
        regions={"region:orn", "orn", "free_city"},
        factions={"cirque"},
    ),
    _E(
        title="Highcourt: Seat of the Crown",
        text=(
            "HIGHCOURT is the royal capital of Arnesse, seat of House "
            "Bannon and the Aurorym Patriarchy. Notable: the FIVE TOWERS "
            "and the Knights of the Five Towers (royal guard); the "
            "APOTHEON (Apotheca headquarters); HALL OF SCALES (Vigil "
            "headquarters). The royal court runs intrigue thicker than "
            "anywhere in the realm; the city is home to the highest "
            "Cirque troupe (the Ten Knives and Lords)."
        ),
        regions={"region:highcourt", "highcourt"},
        houses={"house:bannon"},
    ),
])


# =====================================================================
# HEARTHLANDS — House Blayne (eastern reaches, dragon-haunted)
# =====================================================================
ENTRIES.extend([
    _E(
        title="The Hearthlands: Dragon Country and Pious Folk",
        text=(
            "The Hearthlands stretch across central-east Arnesse — rolling "
            "farmland giving way to rugged mountain wilderness as one "
            "travels east. House Blayne rules from RIVER'S END and BEGGAR'S "
            "KEEP. The eastern reaches are dragon country: not the great "
            "wyrms of legend, but lesser draconic creatures encountered "
            "often enough to shape the people. The Aurorym faith runs "
            "deepest here — the Vellatora's chapterhouse stands at EXETER, "
            "and the Magnus Rectorix raises orphans as aurons alongside "
            "the knights they will pair with for life."
        ),
        regions={"region:hearthlands", "hearthlands"},
        houses={"house:blayne"},
    ),
    _E(
        title="Hearthlands: Common Folk and Daily Survival",
        text=(
            "Hearthlander peasants live shaped by community cooperation "
            "and constant frontier awareness. Villages are often separated "
            "by long stretches of wild country; a family must grow and "
            "preserve enough food for winter while remaining ready for "
            "wyrm or wolf. The folk develop quiet, determined courage — "
            "not the bold bravery of warriors, but resilience that comes "
            "from knowing any day may bring disaster. Tales of dragonslayers "
            "and Aurorym Saints fill tavern evenings; altars to local "
            "heroes stand at most crossroads."
        ),
        regions={"region:hearthlands", "hearthlands"},
        houses={"house:blayne"},
    ),
    _E(
        title="Hearthlands: Exeter, City of Shrines",
        text=(
            "EXETER is the spiritual and martial heart of the Hearthlands. "
            "The WARDALL — the tomb-fortress of Saint Cuthbert who fell "
            "defending innocents in the invasion of King Richard II — "
            "stands at the city's center. Almost every resident has martial "
            "training; aurons and Vellatora knights walk the streets in "
            "equal number; bells ring for the canonical hours. Festivals "
            "of the Aurorym calendar (Ascension Feast, Martyrs' Wake) draw "
            "pilgrims from across Arnesse."
        ),
        regions={"region:hearthlands", "region:exeter", "hearthlands", "exeter"},
        houses={"house:blayne"},
        factions={"aurorym", "vellatora"},
    ),
])


# =====================================================================
# DUSKLANDS / DURISLANDS — House Richter (Iron Lords, archipelago trade)
# =====================================================================
ENTRIES.extend([
    _E(
        title="The Dusklands: Iron, Salt, and Strict Order",
        text=(
            "The Dusklands extend from the Deephold's mountain reaches "
            "south and west into the DURISLANDS — a scattered archipelago "
            "of islands connected by treacherous sea routes. House Richter "
            "rules with iron hand: strict trade regulation, swift justice, "
            "the IRON GUARD enforcing peace at every port. Climate alternates "
            "between sultry summers and temperate winters; hurricanes "
            "shape every settlement's architecture. Trade flows constantly "
            "through Richter ports, bringing both wealth and dangerous "
            "ideas the House works tirelessly to contain."
        ),
        regions={"region:dusklands", "region:durislands", "dusklands", "durislands"},
        houses={"house:richter"},
    ),
    _E(
        title="Dusklands: Grindfrost, the Powder-Keg Port",
        text=(
            "GRINDFROST is the Durislands' bustling main trading port — "
            "merchants from a dozen nations haggling in the markets, the "
            "smell of spices and tar in the air, languages from distant "
            "lands on every street corner. Cosmopolitan compared to most "
            "of Arnesse, but the Richter family's iron grip on taxation "
            "is unbroken; merchants who overstep are dealt with swiftly. "
            "Wealthy trader-houses live in tall narrow town-houses; the "
            "dock-folk live in tenements above the warehouses where they "
            "labor."
        ),
        regions={"region:durislands", "region:grindfrost", "grindfrost"},
        houses={"house:richter"},
    ),
    _E(
        title="Dusklands: Common Folk and the Spice Routes",
        text=(
            "Richter common folk are divided by their proximity to trade. "
            "Merchant servants and skilled tradesfolk occupy a higher rung; "
            "dock workers and casual laborers below them live precariously "
            "at wages set by House-licensed guilds. All are heavily taxed; "
            "all know that speaking against Richter policy is unwise. Yet "
            "the cuisine — pepper, cinnamon, foreign preserves, strange "
            "fruits scavenged from trader's scraps — is the richest in "
            "Arnesse, and ambition runs high. A clever dock-worker may "
            "become a warehouse manager; from there, a stall."
        ),
        regions={"region:dusklands", "region:durislands", "dusklands", "durislands"},
        houses={"house:richter"},
    ),
    _E(
        title="Dusklands: The Deephold and Inland Mining",
        text=(
            "Inland from the Durislands, the DEEPHOLD lies — vast "
            "subterranean caverns and stone halls beneath the Worldspine "
            "mountains. The Richter line proper holds it; mining fuels "
            "the IRON GUARD's armament and the realm's blacksmith trade. "
            "Folk adapted to darkness live their whole lives in lamp-lit "
            "halls; trade with the surface is limited and prized. Older "
            "powers are said to dwell in the deepest reaches; Hardinger "
            "miners speak of these only over strong drink."
        ),
        regions={"region:deephold", "region:dusklands", "deephold", "dusklands"},
        houses={"house:richter", "house:hardinger"},
    ),
])


# =====================================================================
# MIDLANDS — House Corveaux (commerce, scholarship, tournaments)
# =====================================================================
ENTRIES.extend([
    _E(
        title="The Midlands: Commerce and Martial Excellence",
        text=(
            "The Midlands roll across central Arnesse in gentle hills and "
            "fertile river valleys, the kingdom's commercial spine. KING'S "
            "CROSSING is the great city — neither as harsh as the north "
            "nor as lush as the south, the Midlands strike a balance that "
            "lets merchant-houses and farming communities flourish side "
            "by side. House Corveaux rules through a complex patchwork of "
            "vassal High Houses, each with castles, garrisons, and local "
            "customs. Tournaments are held frequently — drawing fighters "
            "from across the realm to compete for glory and prize money."
        ),
        regions={"region:midlands", "midlands"},
        houses={"house:corveaux"},
    ),
    _E(
        title="Midlands: Fair Lady Vale",
        text=(
            "FAIR LADY VALE is the Midlands' jewel — a river valley of "
            "vineyards, meadows, and the graceful castle that looks down "
            "from a commanding height. Wines and grains from the vale fetch "
            "high prices in distant markets. Beneath the pastoral beauty "
            "lies darker history: the vale changed hands by betrayal and "
            "marriage alliance, and old grudges between Corveaux and other "
            "Houses still simmer. The folk are more refined than their "
            "harder-living counterparts elsewhere; courtesy and courtliness "
            "mask ruthlessness in matters of honor."
        ),
        regions={"region:midlands", "region:fair-lady-vale", "fair_lady_vale"},
        houses={"house:corveaux"},
    ),
    _E(
        title="Midlands: Common Folk and the Path of Ambition",
        text=(
            "The Midlanders entertain dreams of advancement that would be "
            "unthinkable in more rigidly stratified regions. A young person "
            "of talent may rise from peasant origins to minor knighthood "
            "through tournament valor; markets and taverns buzz with gossip "
            "about who is rising and who has fallen. Loyalty is "
            "transactional — merchants and artisans are free folk who move "
            "between masters in search of better terms — but once an oath "
            "is sworn, Midlanders honor it with strict adherence. The "
            "Midlands runs on contracts, not blood-bonds."
        ),
        regions={"region:midlands", "midlands"},
        houses={"house:corveaux"},
    ),
])


# =====================================================================
# NORTHERN MARCHES — House Innis (border, vigilance, ranger tradition)
# =====================================================================
ENTRIES.extend([
    _E(
        title="The Northern Marches: Borderland of Constant Watch",
        text=(
            "The Northern Marches form Arnesse's northwestern border — "
            "dramatic mountain country, deep river valleys cut sharp, "
            "stretches of open moor alternating with ancient forest. House "
            "Innis rules from BRIDG'T and maintains old pacts with the "
            "woods. The folk are necessarily martial — many serve as "
            "soldiers, scouts, or rangers alongside their ordinary trades. "
            "The relationship between Innis and the common folk is direct: "
            "the folk depend utterly on Innis leadership and military "
            "strength for protection, and that creates a tight bond — and "
            "an undertone of bitter resignation."
        ),
        regions={"region:northern-marches", "northern_marches", "marches"},
        houses={"house:innis"},
    ),
    _E(
        title="Northern Marches: Fortress Towns and Rangers",
        text=(
            "Major settlements are built defensively — high walls, strong "
            "gatekeeps, streets laid for maximum defender advantage if the "
            "outer wall breaks. Children learn to recognize weapons, armor, "
            "and the signs of enemy approach as essential education. A "
            "significant portion of able-bodied folk serve as scouts, "
            "rangers, or light cavalry, developing intimate knowledge of "
            "the wild lands beyond the settlements — passages and secret "
            "routes the Richter have not mapped and will not. The ranger "
            "tradition is celebrated in story; many young folk aspire to it."
        ),
        regions={"region:northern-marches", "northern_marches"},
        houses={"house:innis"},
    ),
    _E(
        title="Northern Marches: Common Folk and the Border War",
        text=(
            "Vigilance is the Marcher way of life, born of generations on "
            "the contested frontier with the Dusklander vassals of Richter. "
            "Families maintain emergency supplies and safe places; "
            "settlements have organized systems for rapid assembly and "
            "mutual defense. Yet the folk are not joyless — they take "
            "pleasure where they find it and celebrate firmly, knowing "
            "peace can end without warning. The bitterness over the Border "
            "War — and the prisoner-columns sent through Gateway on the "
            "Last Walk — runs deep in every Marcher household."
        ),
        regions={"region:northern-marches", "northern_marches"},
        houses={"house:innis"},
    ),
])


# =====================================================================
# EVERFROST — House Hale (eternal winter, hard-forged folk)
# =====================================================================
ENTRIES.extend([
    _E(
        title="The Everfrost: Realm of Eternal Winter",
        text=(
            "The Everfrost spreads across Arnesse's far north — bitter "
            "cold that permits no softness, winter lasting nine months, "
            "summer a brief precious window that never melts the ancient "
            "ice beneath. The land is beautiful in a severe way: towering "
            "snow-crowned mountains, ice-bound valleys, skies that burn "
            "with strange colors during the long polar nights. Every "
            "tool, settlement, and custom exists because it enables "
            "survival. The folk are tough, pragmatic, possessed of "
            "strength both physical and spiritual. They regard those from "
            "softer lands with a mixture of pity and contempt."
        ),
        regions={"region:everfrost", "everfrost"},
        houses={"house:hale"},
    ),
    _E(
        title="Everfrost: GRIMFROST and the Northern Settlements",
        text=(
            "GRIMFROST FORTRESS anchors the Hale presence — a stronghold "
            "built into living rock, hearths kept burning around the year. "
            "Smaller settlements (Husklif, Fairlund) cling to defensible "
            "sites along the snow-line. House Coldhill rules at HARROWGATE "
            "in the Annwyn, but the homeland is Hale's: longhouses of dark "
            "pine and iron banding, hides of Great Bears as wall trophies, "
            "the GET OF URSIN sworn to Coldhill walking woods edge with "
            "ritual scars on both forearms."
        ),
        regions={"region:everfrost", "everfrost"},
        houses={"house:hale", "house:coldhill"},
    ),
    _E(
        title="Everfrost: Common Folk and Winter's Discipline",
        text=(
            "The peasantry's annual cycle is shaped entirely by the "
            "seasons. In autumn they work frantically to harvest and "
            "preserve every calorie; in winter they huddle in settlements "
            "and labor at crafts and maintenance, venturing out only when "
            "necessary. The folk possess profound knowledge of ice and "
            "snow — the signs of avalanche and crevasse, the building of "
            "structures that can withstand months of severe weather. "
            "Survival itself is a victory; those who live long lives in "
            "the Everfrost are revered. Combat skill is integrated into "
            "daily survival, not treated as separate; Hale warriors are "
            "respected — feared — throughout Arnesse."
        ),
        regions={"region:everfrost", "everfrost"},
        houses={"house:hale"},
    ),
])


# =====================================================================
# TARKATH — House Aragon (south, Tor cities, ancient pride)
# =====================================================================
ENTRIES.extend([
    _E(
        title="Tarkath: The Southern Reaches and Ancient Pride",
        text=(
            "Tarkath sprawls across the southern reaches of Arnesse — a "
            "land of greater warmth and more abundant resources than the "
            "north, yet shaped by proximity to dragon-haunted wilds and the "
            "legendary draconic creatures that may still survive in hidden "
            "places. The TOR CITIES rise on ancient sites — TOR OMAN at "
            "the base of the Ashen Tower; TOR SIRAT under cool grey light; "
            "TOR OBOLUS with its old standing stones; DRAGONSPIRE at the "
            "southern coast. The land permits longer growing seasons and "
            "diverse populations. Aragon culture is proud, ambitious, and "
            "carries Iberian-Romance naming traditions and Heset/Blood/Deed "
            "ancestral name-systems."
        ),
        regions={"region:tarkath", "tarkath"},
        houses={"house:aragon"},
    ),
    _E(
        title="Tarkath: Taliesin, the Golden City",
        text=(
            "TALIESIN — the Golden City — rises in northern Tarkath, "
            "centuries of Aragon and Apotheca patronage shining from its "
            "yellowed-stone walls and gilt-roofed towers. The Apotheca's "
            "ASHEN TOWER stands here, ancient and feared, with the "
            "Cranarium beneath. Magisters, scholars, and traveling sages "
            "fill the lower wards; the upper wards belong to Aragon court "
            "and the Ascended Lyna. Tarkathi independence is fierce; they "
            "guard their distinct culture against Ardan domination."
        ),
        regions={"region:tarkath", "region:taliesin", "taliesin"},
        houses={"house:aragon"},
        factions={"apotheca"},
    ),
    _E(
        title="Tarkath: Common Folk and Quiet Aspiration",
        text=(
            "Away from the Tor cities, Tarkathi common folk live somewhat "
            "less shaped by martial concerns and more oriented toward "
            "agricultural production and local craft. Smaller communities "
            "maintain strong traditions of self-governance and local "
            "loyalty; folk songs, crafts, and cooking vary markedly village "
            "to village. The folk harbor a particular frustration — Aragon "
            "is respected but not feared, perceived as somewhat less than "
            "the greatest of Houses — that breeds pragmatic, understated "
            "loyalty, never fervent."
        ),
        regions={"region:tarkath", "tarkath"},
        houses={"house:aragon"},
    ),
])


# =====================================================================
# ROURKE COASTAL DOMAIN — House Rourke (sea lords, High Armada)
# =====================================================================
ENTRIES.extend([
    _E(
        title="Rourke's Coastal Domain: The Sea is Lifeblood",
        text=(
            "House Rourke rules a kingdom that extends from the coastline "
            "deep into fertile valleys and mountain passes, but the true "
            "heart of Rourke power is the sea. SCYLD is the seat. Coastal "
            "landscape is dramatic — high cliffs alternating with protected "
            "harbors, sheltering islands, vast stretches of rocky shore "
            "where fishing villages cling. Climate is temperate; the sea "
            "moderates extremes. Sailors, fishermen, merchants, and traders "
            "form Rourke society's backbone; those who cannot navigate or "
            "trade hold lower social status."
        ),
        regions={"region:rourke-coast", "rourke_coast", "scyld"},
        houses={"house:rourke"},
    ),
    _E(
        title="Rourke: The High Armada",
        text=(
            "The HIGH ARMADA is one of the great accumulations of military "
            "and merchant vessels in Arnesse, a fleet so vast it rivals "
            "some Houses in actual power. The Armada provides Rourke's "
            "naval defense AND the strength to dominate trade routes and "
            "impose Rourke's will on distant shores. Lord Tybold Rourke "
            "captains the SEA WRAITH, the flagship; Lady Eleanor Stormwall "
            "is one of its legendary masters. A position aboard a High "
            "Armada vessel is one of the most prestigious paths to "
            "advancement available to a common-born sailor."
        ),
        regions={"region:rourke-coast", "rourke_coast"},
        houses={"house:rourke"},
    ),
    _E(
        title="Rourke: Common Folk, Salt-Spray, and Distant Trade",
        text=(
            "Coastal common folk live lives bound to the sea — fishing "
            "families maintaining generations of knowledge about local "
            "waters, seasonal patterns, and the methods for harvesting the "
            "sea's bounty. Winter storms take boats and lives with cruel "
            "regularity; drowning is a common death. Yet the work provides "
            "independence and dignity unknown elsewhere. In port cities, "
            "the harbor folk live in a cosmopolitan environment shaped by "
            "trade — stevedores haggling sailors, food vendors selling "
            "exotic dishes, young folk dreaming of joining ships and "
            "sailing to distant lands."
        ),
        regions={"region:rourke-coast", "rourke_coast"},
        houses={"house:rourke"},
    ),
])
