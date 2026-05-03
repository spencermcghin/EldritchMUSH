import { useEffect, useState } from 'react'
import './NpcDialoguePanel.css'

/**
 * NpcDialoguePanel — RPG-style center-screen dialogue modal.
 *
 * Two state sources can drive this open:
 *   1. `dialogue` prop — set when an `npc_dialogue` OOB event arrives
 *      after an AI reply (the canonical case).
 *   2. `pendingDialogue` prop — set synchronously the moment the
 *      player sends `ask <npc> = <topic>` so the modal pops with a
 *      "... considering your words ..." placeholder and the player
 *      gets immediate visual feedback even before the AI replies.
 *
 * When the real reply lands, `dialogue.ts` ticks and we replace
 * `current` with it. The "Ask about" topic chips work both for the
 * real reply (uses dialogue.topics) and the pending state (uses the
 * topics from the previous reply, kept in `current`).
 */
export default function NpcDialoguePanel({ dialogue, pendingDialogue, sendCommand }) {
  const [visible, setVisible] = useState(false)
  const [current, setCurrent] = useState(null)

  // Real reply arrives → swap in the AI response.
  useEffect(() => {
    if (!dialogue || !dialogue.ts) return
    setCurrent(dialogue)
    setVisible(true)
  }, [dialogue?.ts])

  // Player sends an ask → pop with a "thinking" placeholder so the
  // click feels responsive. Carry over previous topics if we have any.
  useEffect(() => {
    if (!pendingDialogue || !pendingDialogue.ts) return
    setCurrent((prev) => ({
      channel: pendingDialogue.channel || 'ask',
      npc: pendingDialogue.npc || (prev && prev.npc) || '',
      npcDbref: pendingDialogue.npcDbref || '',
      npcDesc: (prev && prev.npcDesc) || '',
      question: pendingDialogue.question || '',
      reply: '*considers your words*',
      topics: (prev && prev.topics) || [],
      pending: true,
    }))
    setVisible(true)
  }, [pendingDialogue?.ts])

  useEffect(() => {
    if (!visible) return
    const onKey = (e) => { if (e.key === 'Escape') setVisible(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [visible])

  if (!current) return null

  const askTopic = (topic) => {
    if (!sendCommand) return
    sendCommand(`ask ${current.npc} = ${topic}`)
    // keep panel open so the reply arrives and replaces `current`
  }

  return (
    <>
      {visible && (
        <div className="npc-dialogue-backdrop" onClick={() => setVisible(false)} />
      )}
      <div className={`npc-dialogue-panel ${visible ? 'npc-dialogue-panel-in' : 'npc-dialogue-panel-out'}`}>
        <div className="npc-dialogue-header">
          <span className="cinzel npc-dialogue-eyebrow">
            {current.channel === 'whisper' ? 'WHISPERED' :
             current.channel === 'say' ? 'OVERHEARD' : 'CONVERSATION'}
          </span>
          <button
            className="npc-dialogue-close"
            onClick={() => setVisible(false)}
            title="Close"
          >
            ✕
          </button>
        </div>
        <div className="npc-dialogue-body">
          <div className="npc-dialogue-name cinzel">{current.npc}</div>
          {current.question && (
            <div className="npc-dialogue-question">
              <span className="npc-dialogue-label">You asked:</span>
              <span className="npc-dialogue-question-text">
                {' '}“{current.question}”
              </span>
            </div>
          )}
          <div className="npc-dialogue-reply">“{current.reply}”</div>

          {current.topics?.length > 0 && (
            <div className="npc-dialogue-topics">
              <div className="npc-dialogue-topics-label cinzel">ASK ABOUT</div>
              <div className="npc-dialogue-topics-row">
                {current.topics.map((t, i) => (
                  <button
                    key={i}
                    className="npc-dialogue-topic-chip"
                    onClick={() => askTopic(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
