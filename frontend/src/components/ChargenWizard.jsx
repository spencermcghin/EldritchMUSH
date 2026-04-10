import { useReducer, useCallback, useState } from 'react'
import {
  BASIC_ARCHETYPES,
  ADVANCED_ARCHETYPES,
  SKILL_CATEGORIES,
  SKILL_COMMANDS,
  STEPS,
  skillCpCost,
  isAdvancedAvailable,
  getArt,
} from '../data/chargenData'
import './ChargenWizard.css'

// ── Reducer ──

const DEFAULT_CP_TOTAL = 15

const initialState = {
  step: 0,
  cpTotal: DEFAULT_CP_TOTAL,
  basicArchetype: null,
  advancedArchetype: null,
  skills: {},
}

function computeCpSpent(state) {
  const basicCost = state.basicArchetype?.cpCost ?? 0
  const advancedCost = state.advancedArchetype?.cpCost ?? 0
  const granted = getGrantedSkills(state)
  const skillCost = Object.entries(state.skills).reduce((sum, [key, level]) => {
    const grantedLevel = granted[key] || 0
    return sum + skillCpCost(grantedLevel, level)
  }, 0)
  return basicCost + advancedCost + skillCost
}

function getGrantedSkills(state) {
  const granted = {}
  if (state.basicArchetype?.grantedSkills) {
    Object.entries(state.basicArchetype.grantedSkills).forEach(([k, v]) => {
      granted[k] = Math.max(granted[k] || 0, v)
    })
  }
  if (state.advancedArchetype?.grantedSkills) {
    Object.entries(state.advancedArchetype.grantedSkills).forEach(([k, v]) => {
      granted[k] = Math.max(granted[k] || 0, v)
    })
  }
  return granted
}

function reducer(state, action) {
  switch (action.type) {
    case 'SELECT_BASIC':
      return { ...state, basicArchetype: action.payload, advancedArchetype: null, skills: {} }
    case 'SELECT_ADVANCED':
      return { ...state, advancedArchetype: action.payload }
    case 'SKIP_ADVANCED':
      return { ...state, advancedArchetype: null, step: 3 }
    case 'SET_SKILL': {
      const { key, level } = action.payload
      const next = { ...state, skills: { ...state.skills, [key]: level } }
      return next
    }
    case 'UNSET_SKILL': {
      const { key } = action.payload
      const granted = getGrantedSkills(state)
      const minLevel = granted[key] || 0
      const current = state.skills[key] || 0
      const newLevel = Math.max(minLevel, current - 1)
      return { ...state, skills: { ...state.skills, [key]: newLevel } }
    }
    case 'NEXT_STEP':
      return { ...state, step: Math.min(state.step + 1, STEPS.length - 1) }
    case 'PREV_STEP':
      return { ...state, step: Math.max(state.step - 1, 0) }
    case 'RESET':
      return { ...initialState }
    default:
      return state
  }
}

// ── Sub-Components ──

function CpTracker({ spent, total, isAdmin }) {
  if (isAdmin) {
    return (
      <div className="cp-tracker admin-tracker">
        <span className="cp-label admin-label">∞ ADMIN</span>
      </div>
    )
  }
  // Cap pips at 30 to avoid overflow with high CP totals
  const pipCount = Math.min(total, 30)
  const spentRatio = total > 0 ? spent / total : 0
  const spentPips = Math.round(spentRatio * pipCount)
  const remaining = total - spent
  return (
    <div className="cp-tracker">
      <div className="cp-pips">
        {Array.from({ length: pipCount }, (_, i) => (
          <div key={i} className={`cp-pip ${i < spentPips ? 'spent' : 'available'}`} />
        ))}
      </div>
      <span className="cp-label">{remaining} / {total} CP</span>
    </div>
  )
}

function StepIndicator({ current, steps }) {
  return (
    <div className="step-indicator">
      {steps.map((label, i) => (
        <div key={i} className="step-item">
          <div className={`step-dot ${i === current ? 'active' : i < current ? 'completed' : ''}`} />
          <span className={`step-label ${i === current ? 'active' : ''}`}>{label}</span>
        </div>
      ))}
    </div>
  )
}

function WelcomeStep({ onNext }) {
  return (
    <div className="chargen-step welcome-step">
      <div className="welcome-content panel panel-decorated">
        <h1 className="chargen-title">The Threshold</h1>
        <div className="chargen-divider">✦ ─────── ✦ ─────── ✦</div>
        <p className="chargen-flavor">
          You stand at the edge of becoming. Before you stretches the vast tapestry of fate,
          and the threads of your destiny are yours to weave. Choose your path wisely —
          the Kingdom of Arnesse does not suffer the unprepared.
        </p>
        <div className="welcome-rules">
          <h3 className="chargen-label">CHARACTER POINTS</h3>
          <p>You begin with <strong>4 Character Points (CP)</strong> to spend on your archetype and skills.</p>
          <ul>
            <li>Choose a <strong>Basic Archetype</strong> (1-4 CP) — your origin and starting skills</li>
            <li>Optionally choose an <strong>Advanced Archetype</strong> (1-6 CP) — your specialization</li>
            <li>Spend remaining CP on <strong>Skills</strong> — 1 CP for level 1, 2 CP per additional level</li>
          </ul>
        </div>
        <button className="chargen-btn primary" onClick={onNext}>
          Begin Your Journey
        </button>
      </div>
    </div>
  )
}

function ArchetypeCard({ archetype, selected, disabled, onClick }) {
  const art = getArt(archetype.key)
  return (
    <div
      className={`archetype-card panel ${selected ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
      onClick={disabled ? undefined : onClick}
    >
      <div className="archetype-card-art-wrap">
        <img
          src={art}
          alt={archetype.name}
          className="archetype-card-art"
          loading="lazy"
          decoding="async"
        />
        <div className="archetype-card-cost">{archetype.cpCost} CP</div>
        {selected && <div className="archetype-card-check">✦</div>}
      </div>
      <div className="archetype-card-body">
        <h3 className="archetype-card-name">{archetype.name}</h3>
        <p className="archetype-card-flavor">{archetype.flavor}</p>
        <p className="archetype-card-desc">{archetype.desc}</p>
        {archetype.startingGear && (
          <div className="archetype-card-gear">
            <span className="gear-label">Starts with:</span> {archetype.startingGear}
          </div>
        )}
        {archetype.grantedSkills && Object.keys(archetype.grantedSkills).length > 0 && (
          <div className="archetype-card-skills">
            <span className="gear-label">Skills:</span>{' '}
            {Object.entries(archetype.grantedSkills).map(([k, v]) => `${k} ${v}`).join(', ')}
          </div>
        )}
        {archetype.prereqText && (
          <div className="archetype-card-prereq">{archetype.prereqText}</div>
        )}
      </div>
    </div>
  )
}

function BasicArchetypeStep({ state, dispatch, cpRemaining }) {
  const tiers = [
    { label: 'Common Origins', cost: 1, archetypes: BASIC_ARCHETYPES.filter(a => a.tier === 1) },
    { label: 'Trained Paths', cost: 2, archetypes: BASIC_ARCHETYPES.filter(a => a.tier === 2) },
    { label: 'Specialist Callings', cost: 3, archetypes: BASIC_ARCHETYPES.filter(a => a.tier === 3) },
  ]

  return (
    <div className="chargen-step">
      <h2 className="chargen-section-title">Choose Your Path</h2>
      <p className="chargen-section-desc">Select a basic archetype — your origin in the world of Arnesse.</p>
      {tiers.map(tier => (
        <div key={tier.label} className="archetype-tier">
          <h3 className="tier-label">{tier.label} <span className="tier-cost">({tier.archetypes[0]?.cpCost} CP)</span></h3>
          <div className="archetype-grid">
            {tier.archetypes.map(arch => (
              <ArchetypeCard
                key={arch.key}
                archetype={arch}
                selected={state.basicArchetype?.key === arch.key}
                disabled={state.basicArchetype?.key !== arch.key && arch.cpCost > cpRemaining + (state.basicArchetype?.cpCost || 0)}
                onClick={() => dispatch({ type: 'SELECT_BASIC', payload: arch })}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function AdvancedArchetypeStep({ state, dispatch, cpRemaining }) {
  const basicKey = state.basicArchetype?.key
  return (
    <div className="chargen-step">
      <h2 className="chargen-section-title">Specialization</h2>
      <p className="chargen-section-desc">
        Choose an advanced archetype to define your role — or skip to spend all CP on skills.
      </p>
      <div className="archetype-grid">
        {ADVANCED_ARCHETYPES.map(arch => {
          const available = isAdvancedAvailable(arch, basicKey)
          const canAfford = arch.cpCost <= cpRemaining + (state.advancedArchetype?.cpCost || 0)
          const disabled = !available || (!canAfford && state.advancedArchetype?.key !== arch.key)
          return (
            <ArchetypeCard
              key={arch.key}
              archetype={arch}
              selected={state.advancedArchetype?.key === arch.key}
              disabled={disabled}
              onClick={() => dispatch({
                type: 'SELECT_ADVANCED',
                payload: state.advancedArchetype?.key === arch.key ? null : arch,
              })}
            />
          )
        })}
      </div>
      <button
        className="chargen-btn secondary skip-btn"
        onClick={() => dispatch({ type: 'SKIP_ADVANCED' })}
      >
        Skip — Spend All CP on Skills
      </button>
    </div>
  )
}

function SkillPips({ current, max, granted }) {
  return (
    <div className="skill-pips">
      {Array.from({ length: max }, (_, i) => {
        const level = i + 1
        let cls = 'skill-pip empty'
        if (level <= granted) cls = 'skill-pip granted'
        else if (level <= current) cls = 'skill-pip filled'
        return <div key={i} className={cls} />
      })}
    </div>
  )
}

function SkillsStep({ state, dispatch, cpRemaining }) {
  const granted = getGrantedSkills(state)

  return (
    <div className="chargen-step skills-step">
      <h2 className="chargen-section-title">Spend Your Skills</h2>
      <p className="chargen-section-desc">
        Allocate remaining CP to skills. Level 1 costs 1 CP, each additional level costs 2 CP.
      </p>
      <div className="skills-layout">
        <div className="skills-categories">
          {SKILL_CATEGORIES.map(cat => (
            <div key={cat.key} className="skill-category">
              <h3 className="skill-category-name">{cat.name}</h3>
              {cat.skills.map(skill => {
                const currentLevel = state.skills[skill.key] || granted[skill.key] || 0
                const grantedLevel = granted[skill.key] || 0
                const nextCost = currentLevel < skill.max ? skillCpCost(currentLevel, currentLevel + 1) : 0
                const canIncrease = currentLevel < skill.max && nextCost <= cpRemaining
                const canDecrease = currentLevel > grantedLevel

                return (
                  <div key={skill.key} className="skill-row">
                    <div className="skill-info">
                      <span className="skill-name">{skill.name}</span>
                      <SkillPips current={currentLevel} max={skill.max} granted={grantedLevel} />
                    </div>
                    <div className="skill-controls">
                      <button
                        className="skill-btn minus"
                        disabled={!canDecrease}
                        onClick={() => dispatch({ type: 'UNSET_SKILL', payload: { key: skill.key } })}
                      >-</button>
                      <span className="skill-level">{currentLevel}</span>
                      <button
                        className="skill-btn plus"
                        disabled={!canIncrease}
                        onClick={() => dispatch({
                          type: 'SET_SKILL',
                          payload: { key: skill.key, level: currentLevel + 1 },
                        })}
                      >{nextCost > 0 ? `+${nextCost}` : '+'}</button>
                    </div>
                    <p className="skill-desc">{skill.desc}</p>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ReviewStep({ state, sendCommand, onReset }) {
  const granted = getGrantedSkills(state)
  const allSkills = { ...granted }
  Object.entries(state.skills).forEach(([k, v]) => {
    allSkills[k] = Math.max(allSkills[k] || 0, v)
  })

  const [finalizing, setFinalizing] = useState(false)

  const handleFinalize = () => {
    setFinalizing(true)

    // Send all set* commands for the final build
    const cmds = Object.entries(allSkills)
      .filter(([, level]) => level > 0)
      .map(([key, level]) => [SKILL_COMMANDS[key], level])
      .filter(([cmd]) => cmd)

    // Send commands with small delays to avoid flooding
    cmds.forEach(([cmd, level], i) => {
      setTimeout(() => {
        sendCommand(`${cmd} ${level}`)
      }, i * 300)
    })

    // After all skill commands, exit the wizard UI
    // The player can navigate out of chargen room manually via exits
    setTimeout(() => {
      sendCommand('look')
      if (onExit) onExit()
    }, cmds.length * 300 + 500)
  }

  return (
    <div className="chargen-step review-step">
      <h2 className="chargen-section-title">Review Your Character</h2>
      <div className="review-layout">
        <div className="review-card panel panel-decorated">
          {state.basicArchetype && (
            <div className="review-archetype">
              <img
                src={getArt(state.basicArchetype.key)}
                alt={state.basicArchetype.name}
                className="review-art"
                loading="lazy"
              />
              <div className="review-archetype-info">
                <h3>{state.basicArchetype.name}</h3>
                <span className="review-tag basic">Basic Archetype</span>
                <p>{state.basicArchetype.desc}</p>
              </div>
            </div>
          )}
          {state.advancedArchetype && (
            <div className="review-archetype">
              <img
                src={getArt(state.advancedArchetype.key)}
                alt={state.advancedArchetype.name}
                className="review-art"
                loading="lazy"
              />
              <div className="review-archetype-info">
                <h3>{state.advancedArchetype.name}</h3>
                <span className="review-tag advanced">Advanced Archetype</span>
                <p>{state.advancedArchetype.desc}</p>
              </div>
            </div>
          )}
        </div>
        <div className="review-skills panel">
          <h3 className="chargen-label">SKILLS</h3>
          {SKILL_CATEGORIES.map(cat => {
            const catSkills = cat.skills.filter(s => (allSkills[s.key] || 0) > 0)
            if (catSkills.length === 0) return null
            return (
              <div key={cat.key} className="review-skill-cat">
                <h4>{cat.name}</h4>
                {catSkills.map(s => (
                  <div key={s.key} className="review-skill-row">
                    <span>{s.name}</span>
                    <SkillPips current={allSkills[s.key]} max={s.max} granted={granted[s.key] || 0} />
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      </div>
      <div className="review-actions">
        <button className="chargen-btn secondary" onClick={onReset} disabled={finalizing}>Start Over</button>
        <button className="chargen-btn primary" onClick={handleFinalize} disabled={finalizing}>
          {finalizing ? 'Applying Skills...' : 'Finalize Character'}
        </button>
      </div>
    </div>
  )
}

// ── Character Sheet View (read-only) ──

function CharacterSheetView({ sendCommand, onExit, onEditMode }) {
  // Show all skill categories with current levels from the MUD
  // User can request charsheet data and view it visually
  return (
    <div className="chargen-step">
      <h2 className="chargen-section-title">Your Character</h2>
      <p className="chargen-section-desc">
        View your current build. To modify skills, enter the Chargen room in-game.
      </p>
      <div className="skills-layout">
        <div className="skills-categories">
          {SKILL_CATEGORIES.map(cat => (
            <div key={cat.key} className="skill-category">
              <h3 className="skill-category-name">{cat.name}</h3>
              {cat.skills.map(skill => (
                <div key={skill.key} className="skill-row">
                  <div className="skill-info">
                    <span className="skill-name">{skill.name}</span>
                    <SkillPips current={0} max={skill.max} granted={0} />
                  </div>
                  <p className="skill-desc">{skill.desc}</p>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="review-actions" style={{ marginTop: 20 }}>
        <button className="chargen-btn secondary" onClick={onExit}>Back to Game</button>
        <button className="chargen-btn primary" onClick={() => sendCommand('charsheet')}>
          Refresh from Server
        </button>
      </div>
    </div>
  )
}

// ── Main Wizard ──

export default function ChargenWizard({ sendCommand, onExit, viewMode, isAdmin }) {
  // Admins get effectively unlimited CP
  const adminCpTotal = 999
  const initialStateAdmin = isAdmin
    ? { ...initialState, cpTotal: adminCpTotal }
    : initialState
  const [state, dispatch] = useReducer(reducer, initialStateAdmin)
  const [isViewMode, setIsViewMode] = useState(viewMode || false)
  const cpSpent = computeCpSpent(state)
  const cpRemaining = state.cpTotal - cpSpent

  const handleNext = useCallback(() => dispatch({ type: 'NEXT_STEP' }), [])
  const handlePrev = useCallback(() => dispatch({ type: 'PREV_STEP' }), [])
  const handleReset = useCallback(() => dispatch({ type: 'RESET' }), [])

  const canAdvance = () => {
    if (state.step === 0) return true
    if (state.step === 1) return state.basicArchetype !== null
    if (state.step === 2) return true
    if (state.step === 3) return true
    return false
  }

  // View mode — show read-only character sheet
  if (isViewMode) {
    return (
      <div className="chargen-wizard">
        <div className="chargen-wizard-header">
          <button className="chargen-btn secondary chargen-back-btn" onClick={onExit}>
            Back to Game
          </button>
          <span className="chargen-label" style={{ flex: 1, textAlign: 'center' }}>CHARACTER SHEET</span>
          <button className="chargen-btn primary chargen-back-btn" onClick={() => setIsViewMode(false)}>
            New Build
          </button>
        </div>
        <div className="chargen-wizard-body">
          <CharacterSheetView sendCommand={sendCommand} onExit={onExit} />
        </div>
      </div>
    )
  }

  // Edit mode — full wizard
  return (
    <div className="chargen-wizard">
      <div className="chargen-wizard-header">
        <button className="chargen-btn secondary chargen-back-btn" onClick={onExit}>
          Back to Game
        </button>
        <StepIndicator current={state.step} steps={STEPS} />
        <CpTracker spent={cpSpent} total={state.cpTotal} isAdmin={isAdmin} />
      </div>
      <div className="chargen-wizard-body">
        {state.step === 0 && <WelcomeStep onNext={handleNext} />}
        {state.step === 1 && (
          <BasicArchetypeStep state={state} dispatch={dispatch} cpRemaining={cpRemaining} />
        )}
        {state.step === 2 && (
          <AdvancedArchetypeStep state={state} dispatch={dispatch} cpRemaining={cpRemaining} />
        )}
        {state.step === 3 && (
          <SkillsStep state={state} dispatch={dispatch} cpRemaining={cpRemaining} />
        )}
        {state.step === 4 && (
          <ReviewStep state={state} sendCommand={sendCommand} onReset={handleReset} />
        )}
      </div>
      {state.step > 0 && state.step < 4 && (
        <div className="chargen-wizard-nav">
          <button className="chargen-btn secondary" onClick={handlePrev}>Back</button>
          <button
            className="chargen-btn primary"
            disabled={!canAdvance()}
            onClick={handleNext}
          >
            {state.step === 3 ? 'Review' : 'Next'}
          </button>
        </div>
      )}
    </div>
  )
}
