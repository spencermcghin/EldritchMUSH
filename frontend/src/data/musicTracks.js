// Music track manifest. Files served as static assets from /public/audio.
//
// "The Forsaken Gate" plays as the title-screen theme on the LoginScreen.
// Once the player logs in, the in-game playlist alternates tracks from
// both albums so neither dominates. Both albums are royalty-free / paid
// licenses owned by the project.

export const ALBUMS = {
  stoneharrow: {
    key: 'stoneharrow',
    artist: 'Mountain Realm',
    title: 'Stoneharrow',
  },
  heathens: {
    key: 'heathens',
    artist: 'Swordlender',
    title: 'Where Heathens Roam',
  },
}

const STONEHARROW = [
  ['01-a-broken-man-stands-tall', 'A Broken Man Stands Tall'],
  ['02-village-in-the-mist', 'Village in the Mist'],
  ['03-i-will-craft-you-a-sword-to-slay-gods', 'I Will Craft You A Sword To Slay Gods'],
  ['04-banner-held-high', 'Banner Held High'],
  ['05-the-wall-of-rusted-nails', 'The Wall Of Rusted Nails'],
  ['06-a-warm-dream-by-cold-ashes', 'A Warm Dream By Cold Ashes'],
  ['07-ruins-in-decay', 'Ruins In Decay'],
  ['08-clawing-hands-beneath-the-soil', 'Clawing Hands Beneath The Soil'],
  ['09-fallen-gods', 'Fallen Gods'],
  ['10-shield-of-spring', 'Shield Of Spring'],
  ['11-awakening', 'Awakening'],
].map(([slug, title]) => ({
  id: `stoneharrow/${slug}`,
  src: `/audio/stoneharrow/${slug}.mp3`,
  title,
  album: ALBUMS.stoneharrow,
}))

const HEATHENS = [
  ['01-a-warm-hearth', 'A Warm Hearth'],
  ['02-northbound', 'Northbound'],
  ['03-the-forsaken-gate', 'The Forsaken Gate'],
  ['04-burial-rites', 'Burial Rites'],
  ['05-ancient-mountain', 'Ancient Mountain'],
  ['06-sheltered-among-ruins', 'Sheltered Among Ruins'],
  ['07-dawn-comes-early', 'Dawn Comes Early'],
  ['08-caverns-of-the-old-gods', 'Caverns of the Old Gods'],
  ['09-fires-of-freya', 'Fires of Freya'],
  ['10-spirit-of-the-north', 'Spirit of the North'],
  ['11-mists-among-the-greenwood', 'Mists Among the Greenwood'],
  ['12-descent', 'Descent'],
  ['13-a-hearth-beyond-the-horizon', 'A Hearth Beyond the Horizon'],
].map(([slug, title]) => ({
  id: `heathens/${slug}`,
  src: `/audio/heathens/${slug}.mp3`,
  title,
  album: ALBUMS.heathens,
}))

// Title-screen theme — looped on LoginScreen / pre-puppet.
const TITLE_TRACK_ID = 'heathens/03-the-forsaken-gate'
export const TITLE_TRACK = HEATHENS.find(t => t.id === TITLE_TRACK_ID)

// In-game playlist excludes the title track so it stays distinctive.
const remainingHeathens = HEATHENS.filter(t => t.id !== TITLE_TRACK_ID)

function interleave(a, b) {
  const out = []
  const max = Math.max(a.length, b.length)
  for (let i = 0; i < max; i++) {
    if (i < a.length) out.push(a[i])
    if (i < b.length) out.push(b[i])
  }
  return out
}

// In-game playlist: alternating tracks from both albums (Stoneharrow
// first, then Heathens, repeating). 11 + 12 = 23 tracks.
export const GAME_PLAYLIST = interleave(STONEHARROW, remainingHeathens)

// All tracks combined (used by the toggle UI's "now playing" picker).
export const ALL_TRACKS = [TITLE_TRACK, ...STONEHARROW, ...remainingHeathens]
