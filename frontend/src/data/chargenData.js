// ── Chargen Data Layer ──
// All archetype definitions, skill definitions, CP costs, MUD command mappings,
// and art file mappings for the Character Creation Wizard.

// ── Art Mapping ──
// Images are ink wash PNGs in /art/ named by Google Drive file ID.
// Many are duplicates at different sizes — we pick one per subject.
export const ART = {
  blacksmith:    '/art/1Wzg9sTSQJO77OpQryhZlD7hVImOcL1WQ.png',  // smith with hammer + anvil
  apothecary:    '/art/16W6pA1TJz2Cbs83pKNjbQ8vBzbTuW5ga.png',   // hooded figure with potions/scales
  soldier:       '/art/1b6WFdXSL3Gl4YRzNo7d77kWGlDPunWdN.png',   // armored fighter with shield + arrows
  scholar:       '/art/1VOOV6u376nIvHg0TuyvMo791WvbSFIUt.png',   // robed reader with books + candles
  merchant:      '/art/1d3T5XpuEeNX0W-eMuG0jxxX77uHS5W8K.png',   // jolly merchant tossing coins
  urchin:        '/art/1k0Us9F9sSwLIN9f7kLNwyvJZ3aoXXlBB.png',   // hooded figure with dagger in shadows
  farmer:        '/art/1Ondss_mfX4vIm5m7pPlp2DSBjVoOK8SK.png',   // stout figure with pitchfork
  miner:         '/art/1slUbLpAe3qQvqVKcopmL2KrYxbiCxgFG.png',   // miners with pickaxe in crystal cave
  herbalist:     '/art/1KkKd59dO5msLKTyUdDDoIWxjOz0Ro3Qy.png',  // seated woman with herbs + bowl
  feller:        '/art/18u6D36nbsvxkctDEtak0Otkp_T9n8j3J.png',   // figure chopping at tree stump
  hunter:        '/art/1tFZ8Ul5jcYBZQaNeoCHCdYZAt2hyPKVA.png',   // bearded man with rifle + satchel
  resurrectionist: '/art/1lTdFP7HY2vzoYS0lllORsyEVvLObkOUt.png', // sinister figure with shovel + coffin
  physician:     '/art/162-TTHJ7FcWUtAEzxviswRv6SuE7KVQF.png',  // robed healer with caduceus snakes
  brigand:       '/art/1o9ve4NdLN52boXbK-NdHsOf5atjuIQxJ.png',   // fencer/duelist figure
  artificer:     '/art/12xnFNi5yj0iC9Nv6J9T8Q4wZHqPvbLhO.png',  // tinkerer with goggles + tools
  bowyer:        '/art/12exi3JyAnfO2T_MIpNQRU-FyDihVB2-G.png',   // commonfolk by tree (woodworker)
  gunsmith:      '/art/1ZQs1BhCd2a3wIEK5TFf-DZA8mozFvlYo.png',  // alchemist with smoke + potions
  commonfolk:    '/art/1rgX7ty0AlZMSpTsfG44-UIm2DZfy4C2l.png',   // simple person by tree
  courtier:      '/art/1gJ4wAF05OZPFyku3qL6qDcxLYz_kfQjR.png',  // two figures whispering
  gentry:        '/art/1IXOQbJMFYyOHNW-L9esK1oV8hOHYpSsB.png',  // noblewoman in elegant dress
  // Advanced archetypes
  auron:         '/art/1r7Y4b-aGhgeXmG0LhslJ1lwQ-QsucrcZ.png',  // radiant priest with sun symbol
  cirque:        '/art/1kqL_JlVqK2QRuQBB690J_PXqSpQ5RBrF.png',  // acrobat in hoop
  knight:        '/art/1b6WFdXSL3Gl4YRzNo7d77kWGlDPunWdN.png',  // armored fighter (reuse soldier)
  magister:      '/art/1VOOV6u376nIvHg0TuyvMo791WvbSFIUt.png',   // scholar with books (reuse)
  noble:         '/art/1IXOQbJMFYyOHNW-L9esK1oV8hOHYpSsB.png',  // noblewoman (reuse gentry)
  veteran:       '/art/1tFZ8Ul5jcYBZQaNeoCHCdYZAt2hyPKVA.png',   // grizzled hunter (reuse)
  vigil:         '/art/1k0Us9F9sSwLIN9f7kLNwyvJZ3aoXXlBB.png',   // shadowed figure (reuse urchin)
}

// ── MUD Command Map ──
// Maps skill keys to the MUD set* command names
export const SKILL_COMMANDS = {
  tracking:             'settracking',
  perception:           'setperception',
  blacksmith:           'setblacksmith',
  artificer:            'setartificer',
  gunsmith:             'setgunsmith',
  bowyer:               'setbowyer',
  alchemist:            'setalchemist',
  masterOfArms:         'setmasterofarms',
  tough:                'settough',
  armorSpecialist:      'setarmorspecialist',
  vigil:                'setvigil',
  resilience:           'setresilience',
  resist:               'setresist',
  disarm:               'setdisarm',
  cleave:               'setcleave',
  stun:                 'setstun',
  sunder:               'setsunder',
  stagger:              'setstagger',
  gunner:               'setgunner',
  archer:               'setarcher',
  shields:              'setshields',
  meleeWeapons:         'setmeleeweapons',
  armorProficiency:     'setarmorproficiency',
  stabilize:            'setstabilize',
  medicine:             'setmedicine',
  battlefieldMedicine:  'setmedic',
  chirurgeon:           'setchirurgeon',
  battlefieldCommander: 'setbattlefieldcommander',
  rally:                'setrally',
  indomitable:          'setindomitable',
}

// ── Skill Definitions ──
// Each skill: key, display name, category, max level, CP cost per level, description
export const SKILL_CATEGORIES = [
  {
    key: 'martial',
    name: 'Martial',
    skills: [
      { key: 'meleeWeapons',    name: '1-Hand Weapons', max: 3, desc: 'Use small/medium weapons. Grants Stun (1), Stagger (2), Disarm (3) calls.' },
      { key: 'archer',          name: 'Archer',         max: 3, desc: 'Use bows. Arrows bypass AV/Tough. Grants Stun (1), Stagger (2), Disarm (3).' },
      { key: 'gunner',          name: 'Gunner',         max: 3, desc: 'Use firearms. Bullets bypass AV/Tough, target goes to Dying. Stagger (2), Disarm (3).' },
      { key: 'shields',         name: 'Shields',        max: 3, desc: 'Use shields to block. Grants Stun (2), Resist (3) calls.' },
      { key: 'masterOfArms',    name: 'Master of Arms', max: 3, desc: '+1 use of any active martial call per refresh, per level. Enables dual wielding.' },
      { key: 'tough',           name: 'Tough',          max: 3, desc: '+1 natural Armor Value per level. Stacks with worn armor.' },
      { key: 'armorProficiency', name: 'Armor Prof.',   max: 3, desc: 'Wear armor. Higher levels unlock heavier armor at full AV.' },
      { key: 'armorSpecialist', name: 'Combat Agility', max: 3, desc: '+1 AV on light/medium armor per level.' },
      { key: 'resilience',      name: 'Resilience',     max: 3, desc: 'Add minutes to Bleeding duration before Dying (+1/+3/+5 min).' },
    ],
  },
  {
    key: 'techniques',
    name: 'Combat Techniques',
    skills: [
      { key: 'resist',  name: 'Resist',  max: 3, desc: 'Negate any active martial call and its damage.' },
      { key: 'disarm',  name: 'Disarm',  max: 3, desc: 'Force target to drop their weapon.' },
      { key: 'cleave',  name: 'Cleave',  max: 3, desc: 'Strike goes through armor AV (not shields).' },
      { key: 'stun',    name: 'Stun',    max: 3, desc: 'Target dazed for 3 seconds. Must hit the back.' },
      { key: 'sunder',  name: 'Sunder',  max: 3, desc: 'Damage target\'s weapon or shield.' },
      { key: 'stagger', name: 'Stagger', max: 3, desc: 'Target steps back 2 steps, cannot defend.' },
    ],
  },
  {
    key: 'healing',
    name: 'Healing',
    skills: [
      { key: 'stabilize',          name: 'Stabilize',     max: 3, desc: 'Halt bleeding and restore to Wounded condition.' },
      { key: 'medicine',           name: 'Medicine',      max: 3, desc: 'Heal wounded characters. Higher levels reduce healing time.' },
      { key: 'battlefieldMedicine', name: 'Battlefield Med', max: 1, desc: 'Emergency healing on the battlefield.' },
      { key: 'chirurgeon',         name: 'Chirurgeon',    max: 1, desc: 'Advanced surgical healing ability.' },
    ],
  },
  {
    key: 'crafting',
    name: 'Crafting',
    skills: [
      { key: 'blacksmith', name: 'Blacksmith', max: 3, desc: 'Forge weapons and armor. Repair at a Forge for free.' },
      { key: 'artificer',  name: 'Artificer',  max: 3, desc: 'Craft goods and equipment at an Artificer\'s Bench.' },
      { key: 'bowyer',     name: 'Bowyer',     max: 3, desc: 'Craft bows and arrows. Requires Artificer 1.' },
      { key: 'gunsmith',   name: 'Gunsmith',   max: 3, desc: 'Craft firearms. Requires Artificer 1 + Blacksmith 1.' },
      { key: 'alchemist',  name: 'Alchemist',  max: 3, desc: 'Brew potions and substances at an Alchemy Lab.' },
    ],
  },
  {
    key: 'support',
    name: 'Support',
    skills: [
      { key: 'tracking',   name: 'Tracking',   max: 3, desc: 'Follow trails and tracks. Higher levels reveal more.' },
      { key: 'perception',  name: 'Perception',  max: 3, desc: 'Perceive hidden details, traps, and secrets.' },
    ],
  },
  {
    key: 'knight',
    name: 'Knight Abilities',
    skills: [
      { key: 'battlefieldCommander', name: 'Commander',  max: 3, desc: 'Command and coordinate allies in battle.' },
      { key: 'rally',               name: 'Rally',      max: 3, desc: 'Rally allies for morale boost.' },
      { key: 'indomitable',         name: 'Indomitable', max: 3, desc: 'Iron resolve. Adds to Armor Value calculation.' },
    ],
  },
  {
    key: 'archetype',
    name: 'Archetype',
    skills: [
      { key: 'vigil', name: 'Vigil', max: 3, desc: 'Enhanced attack die in place of standard Master of Arms roll.' },
    ],
  },
]

// Helper: get CP cost for a skill at a given level (level 1 = 1 CP, level 2+ = 2 CP each)
export function skillCpCost(fromLevel, toLevel) {
  let cost = 0
  for (let l = fromLevel + 1; l <= toLevel; l++) {
    cost += l === 1 ? 1 : 2
  }
  return cost
}

// ── Basic Archetypes ──
export const BASIC_ARCHETYPES = [
  // 1 CP tier
  {
    key: 'commonfolk', name: 'Commonfolk', cpCost: 1, tier: 1,
    desc: 'A humble soul with no particular specialty. Versatile but unremarkable.',
    flavor: 'You are no one special. That is your greatest strength.',
    startingGear: '10 resources (choose), 10 silver dragons',
    grantedSkills: {},
  },
  {
    key: 'farmer', name: 'Farmer', cpCost: 1, tier: 1,
    desc: 'A tiller of the land. Cloth and textiles are your trade.',
    flavor: 'The earth remembers those who tend it.',
    startingGear: '10 Cloth',
    grantedSkills: {},
  },
  {
    key: 'feller', name: 'Feller', cpCost: 1, tier: 1,
    desc: 'A woodcutter by trade, strong-armed and patient.',
    flavor: 'Every great beam began as a stubborn trunk.',
    startingGear: '10 Refined Wood',
    grantedSkills: {},
  },
  {
    key: 'herbalist', name: 'Herbalist', cpCost: 1, tier: 1,
    desc: 'A gatherer of roots, leaves, and remedies from the wild.',
    flavor: 'The forest provides, if you know where to look.',
    startingGear: '10 Common Herbs',
    grantedSkills: {},
  },
  {
    key: 'hunter', name: 'Hunter', cpCost: 1, tier: 1,
    desc: 'A tracker and trapper. Leather and furs sustain you.',
    flavor: 'The prey does not choose the hunter.',
    startingGear: '10 Leather or Bow + Arrows',
    grantedSkills: {},
  },
  {
    key: 'miner', name: 'Miner', cpCost: 1, tier: 1,
    desc: 'Delver of the deep places. Iron is your lifeblood.',
    flavor: 'In the dark below, fortunes and graves are dug alike.',
    startingGear: '10 Iron Ingots',
    grantedSkills: {},
  },
  {
    key: 'resurrectionist', name: 'Resurrectionist', cpCost: 1, tier: 1,
    desc: 'A dealer in secrets, influence, and things best left buried.',
    flavor: 'The dead have much to offer — if you know the price.',
    startingGear: '2 Influence',
    grantedSkills: {},
  },
  {
    key: 'urchin', name: 'Urchin', cpCost: 1, tier: 1,
    desc: 'Street-smart and resourceful. Espionage or lockpicking come naturally.',
    flavor: 'Nobody sees you. That is exactly as you wish it.',
    startingGear: '2 Influence (Espionage) or Lockpicking Kit',
    grantedSkills: {},
  },
  // 2 CP tier
  {
    key: 'brigand', name: 'Brigand', cpCost: 2, tier: 2,
    desc: 'A sellsword, outlaw, or wandering blade-for-hire.',
    flavor: 'Honor buys nothing. Steel opens every door.',
    startingGear: 'Weapon + 10 silver dragons',
    grantedSkills: { meleeWeapons: 1 },
  },
  {
    key: 'merchant', name: 'Merchant', cpCost: 2, tier: 2,
    desc: 'A trader of goods, with an eye for profit and supply.',
    flavor: 'Every exchange is a negotiation. Every negotiation, a battle.',
    startingGear: '20 silver dragons',
    grantedSkills: {},
  },
  {
    key: 'physician', name: 'Physician', cpCost: 2, tier: 2,
    desc: 'Trained in the healing arts. Medicine and diagnosis are your tools.',
    flavor: 'Where others see suffering, you see a puzzle.',
    startingGear: 'Chirurgeon\'s Kit, 10 silver dragons',
    grantedSkills: { medicine: 1 },
  },
  {
    key: 'scholar', name: 'Scholar', cpCost: 2, tier: 2,
    desc: 'A learned mind with access to lore and academic knowledge.',
    flavor: 'The truth is always written somewhere.',
    startingGear: '5 silver dragons',
    grantedSkills: {},
  },
  {
    key: 'soldier', name: 'Soldier', cpCost: 2, tier: 2,
    desc: 'Trained for war. Weapons, armor, and the shield wall are yours.',
    flavor: 'You were forged in the fires of service.',
    startingGear: '25 silver dragons (20 on gear)',
    grantedSkills: { meleeWeapons: 1, shields: 1 },
  },
  {
    key: 'courtier', name: 'Courtier', cpCost: 2, tier: 2,
    desc: 'A creature of the court. Influence and espionage are your currency.',
    flavor: 'In the halls of power, a whisper carries farther than a sword.',
    startingGear: 'None (granted by a Noble)',
    grantedSkills: {},
  },
  {
    key: 'gentry', name: 'Gentry', cpCost: 2, tier: 2,
    desc: 'Born to minor nobility. Education and coin are your birthright.',
    flavor: 'Blood tells. So does silver.',
    startingGear: '30 silver dragons',
    grantedSkills: {},
  },
  // 4 CP tier
  {
    key: 'apothecary', name: 'Apothecary', cpCost: 4, tier: 3,
    desc: 'Master of potions, poisons, and alchemical craft.',
    flavor: 'Between remedy and ruin lies a single drop.',
    startingGear: 'Apothecary Kit + 2 schematics + resources',
    grantedSkills: { alchemist: 1 },
  },
  {
    key: 'artificer', name: 'Artificer', cpCost: 4, tier: 3,
    desc: 'Inventor, tinkerer, and crafter of cunning devices.',
    flavor: 'Where others see junk, you see components.',
    startingGear: 'Artificer Kit + 2 schematics + resources',
    grantedSkills: { artificer: 1 },
  },
  {
    key: 'blacksmithArchetype', name: 'Blacksmith', cpCost: 4, tier: 3,
    desc: 'Master of the forge. Weapons, armor, and repairs are your domain.',
    flavor: 'Iron bends to your will. So too shall the world.',
    startingGear: 'Blacksmith Kit + 4 schematics + resources',
    grantedSkills: { blacksmith: 1 },
  },
  {
    key: 'bowyerArchetype', name: 'Bowyer', cpCost: 4, tier: 3,
    desc: 'Crafter of bows, arrows, and ranged implements.',
    flavor: 'The arrow knows no allegiance but the archer\'s aim.',
    startingGear: 'Bowyer Kit + 2 schematics + resources',
    grantedSkills: { artificer: 1, bowyer: 1 },
  },
  {
    key: 'gunsmithArchetype', name: 'Gunsmith', cpCost: 4, tier: 3,
    desc: 'Forger of firearms. Black powder and precision are your art.',
    flavor: 'Thunder in your hands, and lightning at your command.',
    startingGear: 'Gunsmith Kit + 2 schematics + resources',
    grantedSkills: { artificer: 1, gunsmith: 1 },
  },
]

// ── Advanced Archetypes ──
export const ADVANCED_ARCHETYPES = [
  {
    key: 'veteran', name: 'Veteran', cpCost: 1,
    desc: 'A battle-hardened survivor. Starts at Rank 1 with broad experience.',
    flavor: 'You have already survived what would break lesser souls.',
    prereqs: null, // any basic archetype
    prereqText: 'Any basic archetype',
  },
  {
    key: 'auron', name: 'Auron', cpCost: 3,
    desc: 'Priest of the faith. Bless allies and bolster the faithful.',
    flavor: 'The light does not ask permission to shine.',
    prereqs: null,
    prereqText: 'Any except Courtier/Gentry',
    excludes: ['courtier', 'gentry'],
  },
  {
    key: 'cirque', name: 'Cirque', cpCost: 3,
    desc: 'Thief, acrobat, and shadow merchant. The underworld is your stage.',
    flavor: 'The crowd watches the show. You watch their pockets.',
    prereqs: null,
    prereqText: 'Any except Courtier/Gentry',
    excludes: ['courtier', 'gentry'],
  },
  {
    key: 'knight', name: 'Knight', cpCost: 3,
    desc: 'Healer-warrior of the battlefield. Medicine under fire is your calling.',
    flavor: 'You carry the banner so others may rise.',
    prereqs: ['gentry', 'physician', 'soldier', 'courtier'],
    prereqText: 'Requires: Gentry, Physician, Soldier, or Courtier',
  },
  {
    key: 'magister', name: 'Magister', cpCost: 3,
    desc: 'Scholar of the Apotheca. Alchemy, lore, and the arcane arts.',
    flavor: 'Knowledge is the only power that cannot be taken by force.',
    prereqs: ['scholar', 'apothecary', 'physician', 'gentry', 'courtier'],
    prereqText: 'Requires: Scholar, Apothecary, Physician, Gentry, or Courtier',
  },
  {
    key: 'vigil', name: 'Vigil', cpCost: 3,
    desc: 'Spymaster and justicar. Espionage, investigation, and the Wylding Hand.',
    flavor: 'Justice is patient. You are not.',
    prereqs: ['courtier', 'gentry'],
    prereqText: 'Requires: Courtier or Gentry',
  },
  {
    key: 'noble', name: 'Noble', cpCost: 6,
    desc: 'Born to rule. Command retainers, levy taxes, and shape the realm.',
    flavor: 'The crown is heavy. You were born to bear it.',
    prereqs: ['courtier', 'gentry'],
    prereqText: 'Requires: Courtier or Gentry only',
  },
]

// Helper: check if an advanced archetype is available given a basic selection
export function isAdvancedAvailable(advanced, basicKey) {
  if (!basicKey) return false
  if (advanced.excludes && advanced.excludes.includes(basicKey)) return false
  if (advanced.prereqs && !advanced.prereqs.includes(basicKey)) return false
  return true
}

// Helper: get art path for an archetype key
export function getArt(key) {
  // Handle archetype keys that differ from art keys
  const artKey = key.replace('Archetype', '')
  return ART[artKey] || ART.commonfolk
}

// ── Step labels ──
export const STEPS = ['Welcome', 'Basic Archetype', 'Advanced Archetype', 'Skills', 'Review']
