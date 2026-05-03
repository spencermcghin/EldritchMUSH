import { useEffect, useRef, useState } from 'react'
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
export default function NpcDialoguePanel({
  dialogue,
  pendingDialogue,
  sendCommand,
  questOffers = [],
  onAcceptOffer,
  onAcceptOfferOutcome,
  onDeclineOffer,
}) {
  const [visible, setVisible] = useState(false)
  const [current, setCurrent] = useState(null)
  const [draft, setDraft] = useState('')
  const inputRef = useRef(null)

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

  // Send the typed question. Keeps the modal open and clears the
  // input; the pending state will pop next render via App.jsx's
  // sendCommand wrapper noticing the `ask <npc> = <q>` pattern.
  const submitDraft = (e) => {
    if (e?.preventDefault) e.preventDefault()
    const text = (draft || '').trim()
    if (!text || !current?.npc || !sendCommand) return
    sendCommand(`ask ${current.npc} = ${text}`)
    setDraft('')
    if (inputRef.current) inputRef.current.focus()
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

          {/* Inline quest-offer block — when this NPC is currently
              offering a quest (server fired a quest_offer event for
              them after the player engaged), surface it inside the
              dialogue modal so the player doesn't have to dismiss
              the conversation to accept. Branching outcomes render
              one accept button per path. */}
          {(() => {
            const npcLower = (current.npc || '').toLowerCase()
            const matching = (questOffers || []).filter(
              (o) => (o.giver || '').toLowerCase() === npcLower
            )
            if (matching.length === 0) return null
            return (
              <div className="npc-dialogue-offers">
                <div className="npc-dialogue-topics-label cinzel">
                  QUEST OFFERED
                </div>
                {matching.map((offer) => (
                  <div key={offer.key} className="npc-dialogue-offer">
                    <div className="npc-dialogue-offer-title">
                      {offer.title}
                    </div>
                    {offer.description && (
                      <div className="npc-dialogue-offer-desc">
                        {offer.description}
                      </div>
                    )}
                    {offer.outcomes?.length > 0 ? (
                      <div className="npc-dialogue-offer-outcomes">
                        {offer.outcomes.map((oc) => (
                          <button
                            key={oc.key}
                            className="npc-dialogue-offer-btn"
                            onClick={() => onAcceptOfferOutcome?.(offer, oc.key)}
                            title={oc.description}
                          >
                            {oc.label || oc.key}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="npc-dialogue-offer-actions">
                        <button
                          className="npc-dialogue-offer-btn primary"
                          onClick={() => onAcceptOffer?.(offer)}
                        >
                          Accept
                        </button>
                      </div>
                    )}
                    {onDeclineOffer && (
                      <button
                        className="npc-dialogue-offer-decline"
                        onClick={() => onDeclineOffer(offer)}
                      >
                        Not now
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )
          })()}

          {/* Continue the conversation in-modal — typed follow-ups go
              straight to `ask <npc> = <text>`. App.jsx's sendCommand
              wrapper sees the ask pattern and pops the pending state,
              so the placeholder reasserts while the AI thinks. */}
          <form className="npc-dialogue-input-form" onSubmit={submitDraft}>
            <input
              ref={inputRef}
              type="text"
              className="npc-dialogue-input"
              placeholder={`Say something to ${current.npc}…`}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              autoFocus
              maxLength={400}
            />
            <button
              type="submit"
              className="npc-dialogue-input-send"
              disabled={!draft.trim()}
              title="Send (Enter)"
            >
              ▶
            </button>
          </form>
        </div>
      </div>
    </>
  )
}
