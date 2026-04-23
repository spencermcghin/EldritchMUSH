import { useEffect, useState } from 'react'
import './NpcDialoguePanel.css'

// Slide-in side panel showing the last NPC reply + topic chips.
// Dismisses on Escape, click-outside, or the user sending any command.
// Topic chips fire `ask <npc> <topic>` via sendCommand.
export default function NpcDialoguePanel({ dialogue, sendCommand }) {
  const [visible, setVisible] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!dialogue || !dialogue.ts) return
    setCurrent(dialogue)
    setVisible(true)
  }, [dialogue?.ts])

  useEffect(() => {
    if (!visible) return
    const onKey = (e) => { if (e.key === 'Escape') setVisible(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [visible])

  if (!current) return null

  const askTopic = (topic) => {
    if (!sendCommand) return
    sendCommand(`ask ${current.npc} ${topic}`)
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
