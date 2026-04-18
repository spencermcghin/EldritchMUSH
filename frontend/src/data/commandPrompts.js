// ── Friendly Command Prompts ──
// Maps MUD commands that require input to user-friendly modal prompts.
// New players don't need to know the syntax — they get a clear question.

/**
 * Each prompt definition:
 * - title: short header shown at top of modal
 * - label: friendly question shown above the input
 * - placeholder: input placeholder text
 * - icon: emoji shown in header
 * - submitLabel: text on the submit button
 * - buildCommand(input, target?): returns the actual MUD command string
 */

export const PROMPTS = {
  say: {
    title: 'Speak',
    label: 'What do you want to say?',
    placeholder: 'Hello, traveler...',
    icon: '💬',
    submitLabel: 'Say it',
    buildCommand: (input) => `say ${input}`,
  },

  emote: {
    title: 'Perform Action',
    label: 'What do you want to do?',
    placeholder: 'waves cheerfully',
    icon: '🎭',
    submitLabel: 'Perform',
    buildCommand: (input) => `emote ${input}`,
  },

  pose: {
    title: 'Strike a Pose',
    label: 'How do you want to pose?',
    placeholder: 'leans against the wall',
    icon: '🎭',
    submitLabel: 'Pose',
    buildCommand: (input) => `pose ${input}`,
  },

  whisper: (targetName) => ({
    title: `Whisper to ${targetName}`,
    label: `What do you want to whisper to ${targetName}?`,
    placeholder: 'A secret message...',
    icon: '🤫',
    submitLabel: 'Whisper',
    buildCommand: (input) => `whisper ${targetName} = ${input}`,
  }),

  tell: (targetName) => ({
    title: `Tell ${targetName}`,
    label: `What do you want to tell ${targetName}?`,
    placeholder: 'Send a private message...',
    icon: '📜',
    submitLabel: 'Send',
    buildCommand: (input) => `tell ${targetName}=${input}`,
  }),

  ask: (targetName) => ({
    title: `Ask ${targetName}`,
    label: `What do you want to ask ${targetName}?`,
    placeholder: 'about your sister, about the Mists...',
    icon: '🗣',
    submitLabel: 'Ask',
    buildCommand: (input) => `ask ${targetName} = ${input}`,
  }),

  look: {
    title: 'Look At',
    label: 'Who or what do you want to look at?',
    placeholder: 'a person, object, or direction',
    icon: '👁',
    submitLabel: 'Look',
    buildCommand: (input) => `look ${input}`,
  },

  examine: {
    title: 'Examine',
    label: 'What do you want to examine closely?',
    placeholder: 'an item or character',
    icon: '🔍',
    submitLabel: 'Examine',
    buildCommand: (input) => `examine ${input}`,
  },

  give: {
    title: 'Give Item',
    label: 'What do you want to give, and to whom?',
    placeholder: 'gold to merchant',
    icon: '🎁',
    submitLabel: 'Give',
    buildCommand: (input) => `give ${input}`,
  },

  get: {
    title: 'Pick Up',
    label: 'What do you want to pick up?',
    placeholder: 'a sword',
    icon: '✋',
    submitLabel: 'Get',
    buildCommand: (input) => `get ${input}`,
  },

  drop: {
    title: 'Drop',
    label: 'What do you want to drop?',
    placeholder: 'an item from your inventory',
    icon: '↓',
    submitLabel: 'Drop',
    buildCommand: (input) => `drop ${input}`,
  },

  brew: {
    title: 'Brew Substance',
    label: 'What substance do you want to brew?',
    placeholder: 'blade oil',
    icon: '⚗',
    submitLabel: 'Brew',
    buildCommand: (input) => `brew ${input}`,
  },

  forge: {
    title: 'Forge Item',
    label: 'What do you want to forge?',
    placeholder: 'iron sword',
    icon: '🔨',
    submitLabel: 'Forge',
    buildCommand: (input) => `forge ${input}`,
  },

  craft: {
    title: 'Craft Item',
    label: 'What do you want to craft?',
    placeholder: 'a recipe name',
    icon: '🛠',
    submitLabel: 'Craft',
    buildCommand: (input) => `craft ${input}`,
  },

  repair: {
    title: 'Repair',
    label: 'What item do you want to repair?',
    placeholder: 'an item from your inventory',
    icon: '🔧',
    submitLabel: 'Repair',
    buildCommand: (input) => `repair ${input}`,
  },

  buy: {
    title: 'Buy',
    label: 'What do you want to buy, and from whom?',
    placeholder: 'sword from merchant',
    icon: '🪙',
    submitLabel: 'Buy',
    buildCommand: (input) => `buy ${input}`,
  },

  sell: {
    title: 'Sell',
    label: 'What do you want to sell, and to whom?',
    placeholder: 'sword to merchant',
    icon: '💰',
    submitLabel: 'Sell',
    buildCommand: (input) => `sell ${input}`,
  },

  help: {
    title: 'Help',
    label: 'What topic do you need help with?',
    placeholder: 'combat, skills, etc.',
    icon: '❓',
    submitLabel: 'Look up',
    buildCommand: (input) => `help ${input}`,
  },
}

// Map command keys (from CommandSidebar) to prompt definitions.
// Returns null if the command doesn't need a prompt.
export function getPromptForCommand(commandKey) {
  return PROMPTS[commandKey] || null
}
