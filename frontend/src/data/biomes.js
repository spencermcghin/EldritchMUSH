// ── Biome Detection ──
// Maps room names/descriptions to a "biome" type and an associated icon.
// Used by RoomView to render an atmospheric scene banner.

// Each biome: keywords (matched in room name + description),
// icon path, color tint for the room view, label
export const BIOMES = {
  ruins: {
    icon: '/art/map/ruin.png',
    label: 'Ruins',
    tint: 'rgba(120, 60, 60, 0.08)',
    accent: '#a04848',
    keywords: ['ruin', 'ruins', 'burned', 'ash', 'graveyard', 'crypt', 'tomb', 'rest', 'rubble', 'collapsed', 'broken', 'abandoned'],
  },
  threat: {
    icon: '/art/map/threat1.png',
    label: 'Wilds',
    tint: 'rgba(80, 40, 40, 0.1)',
    accent: '#8b0000',
    keywords: ['lair', 'den', 'swamp', 'bog', 'mire', 'wilds', 'darkness', 'haunted', 'cursed'],
  },
  settlement: {
    icon: '/art/map/settlement1.png',
    label: 'Settlement',
    tint: 'rgba(180, 130, 70, 0.06)',
    accent: '#c89a6a',
    keywords: ['village', 'hamlet', 'cabin', 'home', 'house', 'cottage', 'dwelling', 'inn', 'tavern', 'hall', 'rest stop'],
  },
  walledSettlement: {
    icon: '/art/map/walledsettlement1.png',
    label: 'Town',
    tint: 'rgba(160, 140, 90, 0.06)',
    accent: '#c8b46a',
    keywords: ['town', 'city', 'walled', 'gate', 'keep'],
  },
  market: {
    icon: '/art/map/settlement2.png',
    label: 'Market',
    tint: 'rgba(200, 160, 80, 0.07)',
    accent: '#d4af37',
    keywords: ['market', 'marketplace', 'bazaar', 'square', 'plaza', 'maker', "maker's hollow", 'trade'],
  },
  castle: {
    icon: '/art/map/castle1.png',
    label: 'Castle',
    tint: 'rgba(140, 130, 110, 0.06)',
    accent: '#b8a878',
    keywords: ['castle', 'fortress', 'citadel', 'palace', 'spire'],
  },
  tower: {
    icon: '/art/map/tower1.png',
    label: 'Tower',
    tint: 'rgba(120, 110, 100, 0.06)',
    accent: '#9a8a6a',
    keywords: ['tower', 'watchtower', 'belfry', 'lookout', 'rookery'],
  },
  forge: {
    icon: '/art/map/mine1.png',
    label: 'Forge',
    tint: 'rgba(180, 80, 30, 0.08)',
    accent: '#cc4422',
    keywords: ['forge', 'smithy', 'smith', 'workshop', 'anvil', 'foundry', 'ironworks'],
  },
  mine: {
    icon: '/art/map/mine1.png',
    label: 'Mine',
    tint: 'rgba(80, 70, 90, 0.08)',
    accent: '#6a5a8a',
    keywords: ['mine', 'cavern', 'cave', 'tunnel', 'underground', 'depths', 'shaft'],
  },
  quarry: {
    icon: '/art/map/quarry1.png',
    label: 'Quarry',
    tint: 'rgba(120, 110, 100, 0.06)',
    accent: '#9a8a7a',
    keywords: ['quarry', 'pit', 'stones', 'standing stones', 'monolith'],
  },
  farm: {
    icon: '/art/map/farm1.png',
    label: 'Farm',
    tint: 'rgba(60, 130, 60, 0.06)',
    accent: '#6aa86a',
    keywords: ['farm', 'farmstead', 'crop', 'pasture', 'orchard', 'meadow', 'lower field'],
  },
  field: {
    icon: '/art/map/nodefarm1.png',
    label: 'Field',
    tint: 'rgba(80, 130, 60, 0.06)',
    accent: '#7aa86a',
    keywords: ['field', 'clearing', 'glade', 'plain'],
  },
  forest: {
    icon: '/art/map/nodewood1.png',
    label: 'Forest',
    tint: 'rgba(40, 80, 50, 0.08)',
    accent: '#4a8a5a',
    keywords: ['forest', 'wood', 'woods', 'grove', 'thicket', 'copse', 'wilderness', 'annwyn'],
  },
  road: {
    icon: '/art/map/encounter1.png',
    label: 'Road',
    tint: 'rgba(110, 100, 80, 0.05)',
    accent: '#9a8a6a',
    keywords: ['road', 'path', 'trail', 'route', 'crossroads', 'way', 'lane'],
  },
  mill: {
    icon: '/art/map/mill1.png',
    label: 'Mill',
    tint: 'rgba(140, 120, 90, 0.06)',
    accent: '#b89c70',
    keywords: ['mill', 'millhouse', 'windmill', 'watermill'],
  },
  docks: {
    icon: '/art/map/fleet.png',
    label: 'Docks',
    tint: 'rgba(40, 80, 110, 0.08)',
    accent: '#4a78a8',
    keywords: ['dock', 'docks', 'harbor', 'harbour', 'shore', 'pier', 'wharf', 'quay', 'beach'],
  },
  ritual: {
    icon: '/art/map/hexxen.png',
    label: 'Ritual Site',
    tint: 'rgba(120, 50, 130, 0.08)',
    accent: '#9a4aa8',
    keywords: ['altar', 'shrine', 'circle', 'ritual', 'sanctum', 'temple', 'consecrated'],
  },
  carnival: {
    icon: '/art/map/encounter2.png',
    label: 'Carnival',
    tint: 'rgba(180, 70, 130, 0.08)',
    accent: '#c84a8a',
    keywords: ['carnival', 'fair', 'circus', 'puppet', 'funhouse', 'ophidia'],
  },
  default: {
    icon: '/art/map/encounter3.png',
    label: 'Place',
    tint: 'rgba(100, 90, 70, 0.04)',
    accent: '#9a8266',
    keywords: [],
  },
}

// Order matters: more specific biomes checked first
const BIOME_PRIORITY = [
  'ritual', 'carnival', 'docks', 'forge', 'mine', 'quarry', 'mill',
  'castle', 'tower', 'walledSettlement', 'market', 'farm', 'ruins',
  'threat', 'forest', 'field', 'road', 'settlement', 'default',
]

export function detectBiome(roomName, description = '') {
  const haystack = `${roomName} ${description}`.toLowerCase()
  for (const key of BIOME_PRIORITY) {
    const biome = BIOMES[key]
    if (!biome.keywords.length) continue
    for (const kw of biome.keywords) {
      // Match whole word with simple boundary check
      const re = new RegExp(`\\b${kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (re.test(haystack)) {
        return { key, ...biome }
      }
    }
  }
  return { key: 'default', ...BIOMES.default }
}
