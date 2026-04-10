// ── Entity Icon Mapping ──
// Picks an appropriate map icon for an NPC, item, or player based on
// keywords in the entity name.

const HOUSES = ['aragon', 'bannon', 'blayne', 'corveaux', 'hale', 'innis', 'richter', 'rourke']

// NPC name → icon path. Keywords are checked in order; first match wins.
const NPC_RULES = [
  { match: ['knight', 'sir ', 'dame'], pick: (name) => pickHouse(name, 'knight') || '/art/map/knight_richter.png' },
  { match: ['ranger', 'tracker', 'hunter'], pick: (name) => pickHouse(name, 'ranger') || '/art/map/ranger.png' },
  { match: ['scout', 'spy', 'rogue'], pick: (name) => pickHouse(name, 'scout') || '/art/map/scout.png' },
  { match: ['spearman', 'soldier', 'guard', 'warrior', 'troop'], pick: (name) => pickHouse(name, 'troop') || '/art/map/threat1.png' },
  { match: ['shieldbearer', 'shield'], pick: () => '/art/map/threat2.png' },
  { match: ['champion', 'lord', 'captain'], pick: () => '/art/map/threatchampion1.png' },
  { match: ['beggar', 'urchin', 'commoner', 'peasant'], pick: () => '/art/map/encounter1.png' },
  { match: ['merchant', 'trader', 'shopkeeper'], pick: () => '/art/map/encounter2.png' },
  { match: ['priest', 'monk', 'auron'], pick: () => '/art/map/hexxen.png' },
  { match: ['witch', 'mage', 'magister', 'apothecary'], pick: () => '/art/map/hexxen.png' },
  { match: ['zombie', 'skeleton', 'undead', 'wraith', 'ghost'], pick: () => '/art/map/threat3.png' },
  { match: ['beast', 'wolf', 'bear', 'monster'], pick: () => '/art/map/threat4.png' },
]

function pickHouse(name, prefix) {
  const lower = name.toLowerCase()
  for (const house of HOUSES) {
    if (lower.includes(house)) {
      return `/art/map/${prefix}_${house}.png`
    }
  }
  return null
}

export function getEntityIcon(name, type) {
  if (!name) return null
  const lower = name.toLowerCase()

  if (type === 'item') {
    // Items use a generic encounter icon for now
    return '/art/map/encounter3.png'
  }

  // NPCs / characters / players
  for (const rule of NPC_RULES) {
    if (rule.match.some(kw => lower.includes(kw))) {
      return rule.pick(name)
    }
  }

  // Default: generic encounter
  return '/art/map/encounter3.png'
}
