"""
Alchemy Reagents

All reagent data sourced from the EldritchMUSH Apothecary reagent list.
Each entry contains: name, rarity, type, special notes, and description.

Rarities: Common, Uncommon, Rare, Black Market, Loot Drop
Approximate unit costs in copper dragons:
  Common: 10c  |  Uncommon: 11c  |  Rare: 18c
  Black Market: 20c  |  Distilled Spirits: 1c
  Loot Drop special costs: Spirit Essence=100, Werewolf Tallow=80,
    Vampire Blood=100, Essence of the Unhallowed=80, Ghoul Venom=60
"""

REAGENTS = {
    "Asp Venom": {
        "rarity": "Black Market",
        "type": "Poison",
        "notes": "black market",
        "description": (
            "The venom of the asp was famously the method by which the Apotheca Mallory chose "
            "to kill Joela, the woman he pined for, but could not have. Perhaps one of the "
            "gentlest deadly venoms, it induces sleep, then paralysis, and then death."
        ),
    },
    "Basilisk Venom": {
        "rarity": "Black Market",
        "type": "Poison",
        "notes": "black market",
        "description": (
            "The famously toxic venom of the basilisk is an intensely corrosive substance. "
            "If ingested, it causes a sensation of internal burning prior to a hardening of "
            "the soft tissues, and then a rupturing which is almost always fatal."
        ),
    },
    "Black Salt": {
        "rarity": "Common",
        "type": "Curing",
        "notes": "",
        "description": (
            "Black Salt comes from the shores of the Drowned Isle. It is known for its "
            "cleansing properties and prevention of basic infection. It is ubiquitous in "
            "common curatives and is used in public baths."
        ),
    },
    "Celandine": {
        "rarity": "Common",
        "type": "Curing",
        "notes": "conditions such as cancer, digestive tract, liver and gallbladder disorders",
        "description": (
            "A common plant found widely throughout Arnesse. Generally used as a purifier "
            "of the body, and can reduce the effects of drunkenness and poisons. Its quality "
            "tends to be unpredictable, and it must be harvested correctly."
        ),
    },
    "Distilled Spirits": {
        "rarity": "Common",
        "type": "",
        "notes": "Used as base for decoctions",
        "description": "The standard base substance needed to create most any apothecary decoction.",
    },
    "Dragon's Eye": {
        "rarity": "Common",
        "type": "Vigor/Strength",
        "notes": "",
        "description": (
            "A hardy plant named for its curious red and gold buds. Its flowers, when dried "
            "and ingested, are known for giving renewed vigor and strength. Modern apothecaries "
            "believe it dulls the nerves so the user does not realize when they have overexerted."
        ),
    },
    "Gold Lotus": {
        "rarity": "Common",
        "type": "Visions",
        "notes": "",
        "description": (
            "A beautiful aquatic plant. The gold lotus produces a single blossom per plant. "
            "Gifting this blossom is said to bring peace and relief from grieving, as well as "
            "pleasant dreams if drunk in a tea."
        ),
    },
    "Hollyrue": {
        "rarity": "Common",
        "type": "Curing",
        "notes": "",
        "description": (
            "A gently spiked green plant, famously the main ingredient of 'Thieves Vinegar'. "
            "A common belief is that if one carries hollyrue in their pocket while traveling, "
            "they will always return home safely."
        ),
    },
    "Luminesce": {
        "rarity": "Common",
        "type": "Curing",
        "notes": "Glows. Fever reducer and mild pain reliever.",
        "description": (
            "Known for its ability to give off a dim glow under the light of a full moon, "
            "Luminesce is one of a few varieties proven as an effective fever reducer. "
            "It also has some mild pain relieving properties."
        ),
    },
    "Mandrake": {
        "rarity": "Common",
        "type": "Sleep",
        "notes": "hallucinogenic and narcotic alkaloids",
        "description": (
            "The thick, tuber-like root has hallucinogenic and mood-altering properties. "
            "In proper doses, it renders sleep unto those in need of a painful procedure. "
            "It is also the main ingredient in a potent love potion."
        ),
    },
    "Merchant's Leaf": {
        "rarity": "Common",
        "type": "",
        "notes": "mild stimulant",
        "description": (
            "This leaf from the Cilla tree is used predominantly as a mild stimulant, "
            "most notably by tradesman and Cirque members during long trips across the empire. "
            "It is commonly chewed, smoked, or blended into other elixirs."
        ),
    },
    "Orgonnian Grapes": {
        "rarity": "Common",
        "type": "Vision/Sense",
        "notes": "",
        "description": (
            "The orgonnian grape is used for dyes and tinctures. Tinctures from it are often "
            "used to treat films on the eyes of the elderly, and it is said to repair and "
            "sharpen the senses."
        ),
    },
    "Phosphorous": {
        "rarity": "Common",
        "type": "Fortifier",
        "notes": "",
        "description": (
            "A bulbous green plant concentrated on the coasts, resembling a type of land "
            "seaweed. It can be harvested for food as well as a fortifying medicine, "
            "rich in nutrients."
        ),
    },
    "Sayge": {
        "rarity": "Common",
        "type": "Base Component",
        "notes": "Required for Magister's Anamnesis",
        "description": (
            "Sayge is one of the oldest known apothecarial reagents, ubiquitous throughout "
            "the practice. Popular for its use in the Magister's Anamnesis Decoction, "
            "it has the ability to sharpen the mental faculties."
        ),
    },
    "Verbaena": {
        "rarity": "Common",
        "type": "Increase Potency/Poisons",
        "notes": "",
        "description": (
            "Verbaena is known for its ability to increase the potency of those substances "
            "to which it is added. It is used in many apothecarial substances and is "
            "unfortunately all too common in the poison trade."
        ),
    },
    "Willow Root": {
        "rarity": "Common",
        "type": "Fortifier",
        "notes": "generally a pain killer",
        "description": (
            "One must take care when digging up willow root to not take too much or dig "
            "too deeply. Willow root serves as an effective painkiller for toothaches, "
            "ailments of the head, moon pain, and swelling of the feet."
        ),
    },
    "Essence of the Unhallowed": {
        "rarity": "Loot Drop",
        "type": "Nethermancy - Revivicator byproduct",
        "notes": "",
        "description": (
            "Byproduct of the Revivication process, whereby unhallowed essence is extracted "
            "from a befouled corpse or living person."
        ),
    },
    "Ghoul Venom": {
        "rarity": "Loot Drop",
        "type": "Poison",
        "notes": "from ghouls",
        "description": (
            "The bite of a ghoul is supernaturally filthy. Their saliva causes a swift "
            "infection that soon kills their victim. The toxic saliva can be used for good "
            "or ill, as it is a powerful poison, blood thinner, and numbing agent."
        ),
    },
    "Spirit Essence": {
        "rarity": "Loot Drop",
        "type": "Curing",
        "notes": "Glows",
        "description": (
            "Ghosts and spirits leave behind a corporeal substance that defies scientific "
            "description. It is gel-like, but also gaseous and luminescent. It appears to "
            "impart life-giving qualities to potions and remedies."
        ),
    },
    "Vampire Blood": {
        "rarity": "Loot Drop",
        "type": "Fell Decoction",
        "notes": "Used in Fell Decoction Tough, Revitalization Elixir",
        "description": (
            "A dangerous substance to hunt for, vampire blood is reputed to be a font of "
            "youth and life. Applying it to wounds can cause them to knit faster and heal. "
            "Drinking it may cure disease."
        ),
    },
    "Werewolf Tallow": {
        "rarity": "Loot Drop",
        "type": "Curing",
        "notes": "Used in Fell Decoction Tough",
        "description": (
            "The hard, rendered fat of a werewolf. The tallow can be used to cure those "
            "who are in the early stages of Lycanthropy disease. Some make it into special "
            "candles for ritual and summoning."
        ),
    },
    "Black Lotus": {
        "rarity": "Rare",
        "type": "Visions",
        "notes": "Memory Loss",
        "description": (
            "The black lotus is associated with the passage of time and forgetting things "
            "that once caused extreme emotional pain. Small doses may cause an inability to "
            "form new memories; larger doses may cause longer periods of amnesia."
        ),
    },
    "Death's Head Cap": {
        "rarity": "Rare",
        "type": "Poison",
        "notes": "Black Market",
        "description": (
            "This white mushroom looks very similar to some common edible mushrooms. "
            "Consumption can lead to a violently bloody death within hours. Even miniscule "
            "doses are deadly."
        ),
    },
    "Embercap": {
        "rarity": "Rare",
        "type": "Curing",
        "notes": "Black Market",
        "description": (
            "Found on old battlefields, the embercap is primarily a universal antidote. "
            "It tends to cleanse the organs quickly and can be used to effectively flush "
            "out poisons and toxins within the body."
        ),
    },
    "Entheric Oil": {
        "rarity": "Rare",
        "type": "Increase Potency",
        "notes": "",
        "description": (
            "A pale, fatty oil extracted from the viscera of large sea birds. When rendered "
            "and refined, it acquires a subtle medicinal scent. Apothecaries use it as a "
            "carrier for volatile tinctures and to soften hardened salves."
        ),
    },
    "Fulger Powder": {
        "rarity": "Rare",
        "type": "Increase Potency/Poisons",
        "notes": "",
        "description": (
            "A pale yellow crystalline dust formed where lightning has struck sandy soil. "
            "When mixed with acids, it produces a faint crackling reaction. Historically "
            "employed to quicken the reactions of volatile mixtures. Sensitive to moisture."
        ),
    },
    "Grave Blood": {
        "rarity": "Rare",
        "type": "Curing",
        "notes": "",
        "description": (
            "Blood recovered from marrow flukes — fat worms that infest corpses buried in "
            "wet soil. Dead blood harvested in this way is most often used for potions that "
            "balance the humors and stimulate the appetite of the extremely sick."
        ),
    },
    "Hag's Wort": {
        "rarity": "Rare",
        "type": "Visions",
        "notes": "",
        "description": (
            "The skilled herbalist knows that true Hag's Wort has distinctively woolly, "
            "flowering stems and can grow up to six feet tall. It tends to grow in marshes. "
            "It is a strong hallucinogen granting intense dreams and waking visions."
        ),
    },
    "Lachrymite Resin": {
        "rarity": "Rare",
        "type": "Curing",
        "notes": "",
        "description": (
            "A hardened, amber-like secretion found in the trunks of certain swamp cypresses. "
            "When heated gently, it releases a vapor with mild anesthetic and anti-infection "
            "qualities, prized by apothecaries and field surgeons."
        ),
    },
    "Waste Lilly": {
        "rarity": "Rare",
        "type": "Fell Decoction",
        "notes": "",
        "description": (
            "A beautiful drooping, bell-shaped lily said to grow on the graves of the innocent. "
            "To consume it imbues one with immense strength. However, the weakness that follows "
            "can last for days as the body's resources are consumed."
        ),
    },
    "Amber Lichen": {
        "rarity": "Uncommon",
        "type": "Warding",
        "notes": "",
        "description": (
            "This lichen is unusually prickly and rough. Using this lichen, finely ground, "
            "is often used to ward off enemies, gossip, and harm."
        ),
    },
    "Blood Medallion": {
        "rarity": "Uncommon",
        "type": "Curing",
        "notes": "can be a sedative",
        "description": (
            "The Blood Medallion is named for its deep red hue and circular shape. "
            "It was first used as a mild sedative, but was then discovered to neutralize "
            "some of the negative side effects of other reagents."
        ),
    },
    "Creeper Moss": {
        "rarity": "Uncommon",
        "type": "Lure",
        "notes": "",
        "description": (
            "The moss tends to propagate so quickly that it can kill a copse of trees "
            "within a few years. When harvested, the moss can be burned as fuel, creating "
            "a heavy smoke that smells of amber and sage used to attract various things."
        ),
    },
    "Crypt Moss": {
        "rarity": "Uncommon",
        "type": "Vigor/Strength",
        "notes": "",
        "description": (
            "Crypt moss is so named because of its propensity to grow in graveyards. "
            "It reacts to human skin almost immediately, rendering it inert and blackened. "
            "When consumed, it is associated with an increase in aggression and energy."
        ),
    },
    "Duskland Rose": {
        "rarity": "Uncommon",
        "type": "Lure",
        "notes": "",
        "description": (
            "This wild rose blooms under harsh conditions and opens its petals for only "
            "a few hours at dusk. Its branches and roots are used in weapons against "
            "undead creatures, and the open blooms can repulse vampires."
        ),
    },
    "Ergot Seeds": {
        "rarity": "Uncommon",
        "type": "Vigor/Strength",
        "notes": "",
        "description": (
            "Seeds from a wild grass relative to wheat. Around one in a dozen is dangerously "
            "poisonous; the rest have a pleasant, nutty taste and are a known virility and "
            "fertility enhancer. A skilled alchemist can detect and discard the deadly ones."
        ),
    },
    "Harrowdust": {
        "rarity": "Uncommon",
        "type": "Visions",
        "notes": "",
        "description": (
            "This fine white powder comes from the Dusk Poppy after it has been dried and "
            "ground. In small doses, it can render pleasant, euphoric visions, but frequent "
            "users can become increasingly agitated and aggressive."
        ),
    },
    "Red Lotus": {
        "rarity": "Uncommon",
        "type": "Curing",
        "notes": "minor sleep aid",
        "description": (
            "Another name for it is 'Fire on the Water' because the plant produces a "
            "substance which can literally burn the skin of the hapless harvester. The flower "
            "can assist with frostbite, disease, and bringing a healing sleep to the ill."
        ),
    },
    "Tarkathi Poppy": {
        "rarity": "Uncommon",
        "type": "Visions",
        "notes": "",
        "description": (
            "The tarkathi poppy distorts reality — peeling back the veil between this world "
            "and others. Users report experiencing sounds, sights, and sensations not "
            "previously present. The danger is some users become lost in these visions."
        ),
    },
    "Thornwood Fern": {
        "rarity": "Uncommon",
        "type": "Curing",
        "notes": "",
        "description": (
            "These ferns grow wild in the Thornwood, home of the Innis clans. Their stems "
            "exude a substance that causes virulent infection if entering the bloodstream. "
            "When diluted, this substance makes an effective coagulant on battlefields."
        ),
    },
    "Widow's Petal": {
        "rarity": "Uncommon",
        "type": "Sleep",
        "notes": "Required for Magister's Anamnesis",
        "description": (
            "When distilled to a severe concentration, Widow's Petal makes what is called "
            "'Tears of Lirit'. In small and controlled doses, it is a vital reagent in the "
            "production of the Anamnesis Decoction."
        ),
    },
    "Wintercrown": {
        "rarity": "Uncommon",
        "type": "Curing",
        "notes": "",
        "description": (
            "This late winter and early spring blooming plant features tender green shoots "
            "and delicate white flowers. It has a numbing agent that can make wound treatment "
            "easier, and can strengthen bones and speed healing."
        ),
    },
    "Wraith Orchid": {
        "rarity": "Uncommon",
        "type": "Increase potency",
        "notes": "",
        "description": (
            "These long, fluted, black flowers are known to only grow in the graveyards of "
            "Arnesse. Like salt in a meal, it enhances the effects of other reagents. "
            "The Cirque sometimes add dried Wraith Orchid to their pipes for an extra kick."
        ),
    },
}

# Quick lookup helpers
REAGENT_RARITIES = {name: data["rarity"] for name, data in REAGENTS.items()}
REAGENTS_BY_RARITY = {}
for name, data in REAGENTS.items():
    rarity = data["rarity"]
    REAGENTS_BY_RARITY.setdefault(rarity, []).append(name)
