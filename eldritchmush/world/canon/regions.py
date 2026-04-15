"""Regional canon — the geography, climate, and character of Arnesse."""
from world.canon import ENTRIES, CanonEntry as _E

ENTRIES.extend([
    _E(
        title="Region: The Sovereignlands",
        text=(
            "The Sovereignlands are the core territories under the Crown's "
            "direct rule, where royal authority is strongest. They contain "
            "the major cities and population centers, the seat of royal "
            "power, and the most powerful houses sworn directly to the "
            "throne. Royal garrisons are visible everywhere, and the "
            "King's justice is swift here."
        ),
        regions={"region:sovereignlands", "sovereignlands"},
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
