import { useEffect } from 'react'
import './QuestOfferModal.css'

// Branching quests expose an `outcomes` array; non-branching use the
// flat `objectives` + `rewards` fields. Both paths render here.
export default function QuestOfferModal({ open, offer, onAccept, onAcceptOutcome, onDecline, onClose }) {
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open || !offer) return null

  const isBranching = Array.isArray(offer.outcomes) && offer.outcomes.length > 0

  return (
    <div className="quest-offer-backdrop" onClick={onClose}>
      <div className="quest-offer-modal" onClick={e => e.stopPropagation()}>
        <div className="quest-offer-header">
          <span className="cinzel quest-offer-eyebrow">QUEST OFFERED</span>
          <button className="quest-offer-close" onClick={onClose} title="Not now">✕</button>
        </div>

        <div className="quest-offer-body">
          <div className="quest-offer-title cinzel">{offer.title}</div>
          <div className="quest-offer-giver">
            from <span className="quest-offer-giver-name">{offer.giver}</span>
          </div>

          <p className="quest-offer-desc">{offer.description}</p>

          {isBranching ? (
            <div className="quest-offer-section">
              <div className="quest-offer-label cinzel">CHOOSE YOUR PATH</div>
              <div className="quest-offer-outcomes">
                {offer.outcomes.map((o) => (
                  <button
                    key={o.key}
                    className="quest-offer-outcome"
                    onClick={() => onAcceptOutcome && onAcceptOutcome(o.key)}
                  >
                    <div className="quest-offer-outcome-label cinzel">{o.label}</div>
                    {o.description && (
                      <div className="quest-offer-outcome-desc">{o.description}</div>
                    )}
                    {o.objectives?.length > 0 && (
                      <ul className="quest-offer-outcome-objectives">
                        {o.objectives.map((ob, i) => (
                          <li key={i}>
                            {ob.desc}{ob.qty > 1 && <span className="quest-offer-qty"> ({ob.qty})</span>}
                          </li>
                        ))}
                      </ul>
                    )}
                    {o.rewards?.length > 0 && (
                      <div className="quest-offer-outcome-rewards">
                        {o.rewards.map((r, i) => (
                          <span key={i} className="quest-offer-reward-chip">{r}</span>
                        ))}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {offer.objectives?.length > 0 && (
                <div className="quest-offer-section">
                  <div className="quest-offer-label cinzel">OBJECTIVES</div>
                  <ul className="quest-offer-list">
                    {offer.objectives.map((o, i) => (
                      <li key={i}>{o.desc} {o.qty > 1 && <span className="quest-offer-qty">({o.qty})</span>}</li>
                    ))}
                  </ul>
                </div>
              )}

              {offer.rewards?.length > 0 && (
                <div className="quest-offer-section">
                  <div className="quest-offer-label cinzel">REWARD</div>
                  <div className="quest-offer-rewards">
                    {offer.rewards.map((r, i) => (
                      <span key={i} className="quest-offer-reward-chip">{r}</span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="quest-offer-actions">
          <button className="quest-offer-btn quest-offer-decline" onClick={onDecline}>
            Not now
          </button>
          {!isBranching && (
            <button className="quest-offer-btn quest-offer-accept" onClick={onAccept}>
              Accept
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
