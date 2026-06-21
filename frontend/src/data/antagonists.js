// ── Antagonist Portraits ──
// Maps an NPC `art_key` (or a name/keyword fallback) to a framed creature
// portrait derived from committed Eldritch source art. Mirrors the
// biomes.js registry pattern: a key -> asset map plus a keyword resolver.
//
// Every portrait under /art/antagonists/ is a framed crop of a single
// Eldritch source illustration from the Drive Bestiary/ folder (or the
// local skull.png plate for the skeletal undead). The raw sources live in
// /art/antagonists/_sources/. See docs/bestiary-build.md for the full
// provenance table. No external/stock/AI art is used.

export const ANTAGONISTS = {
  // ── Lycanthropes ──
  werewolf_alpha: {
    portrait: '/art/antagonists/werewolf_alpha-portrait.png',
    label: 'Werewolf',
    source: 'Bestiary/Werewolf.jpg',
    keywords: ['werewolf', 'dranor', 'alpha', 'lycan', 'wolf'],
  },
  werewolf: {
    portrait: '/art/antagonists/werewolf-portrait.png',
    label: 'Wurdulac',
    source: 'Bestiary/Werewolf.jpg',
    keywords: ['wurdulac', 'lycanthrope', 'beast', 'hound', 'wendigo'],
  },

  // ── Risen Dead (Unhallowed) ──
  wight: {
    portrait: '/art/antagonists/wight-portrait.png',
    label: 'Dread Wight',
    source: 'Bestiary/Wight.jpg',
    keywords: ['wight'],
  },
  revenant: {
    portrait: '/art/antagonists/revenant-portrait.png',
    label: 'Revenant',
    source: 'Bestiary/Revenant.jpg',
    keywords: ['revenant'],
  },
  risen_dead: {
    portrait: '/art/antagonists/risen_dead-portrait.png',
    label: 'The Risen Dead',
    source: 'local skull.png (Bones_.png over Drive 10MB download limit)',
    keywords: ['risen', 'corpse', 'zombie', 'rotting', 'skeleton', 'undead'],
  },
  unhallowed_spawn: {
    portrait: '/art/antagonists/unhallowed_spawn-portrait.png',
    label: 'Spawn of the Unhallowed',
    source: 'local skull.png (Bones_.png over Drive 10MB download limit)',
    keywords: ['unhallowed', 'spawn', 'deathbound', 'thrall'],
  },

  // ── Nethermancers ──
  nethermancer: {
    portrait: '/art/antagonists/nethermancer-portrait.png',
    label: 'Nethermancer Initiate',
    source: 'Bestiary/Nethermancer.jpg',
    keywords: ['nethermancer', 'initiate', 'warlock', 'cultist', 'hexxen', 'occultist'],
  },
  necromancer: {
    portrait: '/art/antagonists/necromancer-portrait.png',
    label: 'Nethermancer Acolyte',
    source: 'Bestiary/Necromancer.jpg',
    keywords: ['necromancer', 'acolyte', 'lich'],
  },
  netherphage: {
    portrait: '/art/antagonists/netherphage-portrait.png',
    label: 'Netherphage',
    source: 'Bestiary/Netherphage_.jpg',
    keywords: ['netherphage', 'necrophage', 'phage', 'horror'],
  },

  // ── Ghouls (Bestiary "Withered_L" plate — gaunt weeping-eyed corpse) ──
  crypt_ghoul: {
    portrait: '/art/antagonists/crypt_ghoul-portrait.png',
    label: 'Crypt Ghoul',
    source: 'Bestiary/Withered_L.jpg',
    keywords: ['crypt ghoul', 'ghoul', 'grave-feeder', 'withered'],
  },
  vodnyk: {
    portrait: '/art/antagonists/vodnyk-portrait.png',
    label: 'Vodnyk',
    source: 'Bestiary/Withered_L.jpg',
    keywords: ['vodnyk', 'vodyanoy'],
  },

  // ── Risen Dead — Mortwight (Bestiary "WightHG" plate, distinct variant) ──
  mortwight: {
    portrait: '/art/antagonists/mortwight-portrait.png',
    label: 'Mortwight',
    source: 'Bestiary/WightHG.png',
    keywords: ['mortwight', 'plague wight'],
  },

  // ── Corrupted Magisters (Bestiary "Witch" plates — corrupted casters) ──
  plaguist: {
    portrait: '/art/antagonists/plaguist-portrait.png',
    label: 'Plaguist',
    source: 'Bestiary/Witch.jpg',
    keywords: ['plaguist', 'corrupted magister', 'plague doctor'],
  },
  pandemist: {
    portrait: '/art/antagonists/pandemist-portrait.png',
    label: 'Pandemist',
    source: 'Bestiary/Witch.jpg',
    keywords: ['pandemist'],
  },
  pestis: {
    portrait: '/art/antagonists/pestis-portrait.png',
    label: 'Pestis',
    source: 'Bestiary/witch_large.jpg',
    keywords: ['pestis', 'apostle of plague', 'witch', 'hag'],
  },
}

// Resolve a portrait for an NPC. Preference order:
//   1. explicit art_key sent by the server (npc.db.art_key)
//   2. keyword match against the displayed name
// Returns the antagonist entry, or null for non-antagonists (PCs, vendors).
export function resolveAntagonist(name, artKey) {
  if (artKey && ANTAGONISTS[artKey]) return ANTAGONISTS[artKey]
  if (!name) return null
  const n = name.toLowerCase()
  for (const entry of Object.values(ANTAGONISTS)) {
    if (entry.keywords.some(k => n.includes(k))) return entry
  }
  return null
}
