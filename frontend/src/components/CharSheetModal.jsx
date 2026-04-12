import { useState, useEffect } from 'react'
import './CharSheetModal.css'

const SKILL_SECTIONS = [
  { key: 'status', title: 'STATUS', type: 'status' },
  { key: 'proficiencies', title: 'PROFICIENCIES' },
  { key: 'activeMartial', title: 'ACTIVE MARTIAL SKILLS' },
  { key: 'passiveMartial', title: 'PASSIVE MARTIAL SKILLS' },
  { key: 'general', title: 'GENERAL SKILLS' },
  { key: 'profession', title: 'PROFESSION SKILLS' },
  { key: 'crafting', title: 'CRAFTING SKILLS' },
  { key: 'resources', title: 'RESOURCES', type: 'resources' },
]

function SkillBar({ level, max = 3 }) {
  return (
    <div className="cs-skill-bar">
      {Array.from({ length: max }, (_, i) => (
        <div key={i} className={`cs-pip ${i < level ? 'filled' : 'empty'}`} />
      ))}
    </div>
  )
}

function StatusSection({ data }) {
  if (!data) return null
  return (
    <div className="cs-status-grid">
      <div className="cs-status-item">
        <span className="cs-status-label">Body</span>
        <span className="cs-status-value">{data.body} / {data.totalBody}</span>
      </div>
      <div className="cs-status-item">
        <span className="cs-status-label">Armor Value</span>
        <span className="cs-status-value">{data.armorValue}</span>
      </div>
      <div className="cs-status-item">
        <span className="cs-status-label">Weapon Bonus</span>
        <span className="cs-status-value">{data.weaponBonus}</span>
      </div>
      <div className="cs-status-item">
        <span className="cs-status-label">R. Hand</span>
        <span className="cs-status-value equip">{data.rightSlot || '---'}</span>
      </div>
      <div className="cs-status-item">
        <span className="cs-status-label">L. Hand</span>
        <span className="cs-status-value equip">{data.leftSlot || '---'}</span>
      </div>
      <div className="cs-status-item">
        <span className="cs-status-label">Armor</span>
        <span className="cs-status-value equip">{data.bodySlot || '---'}</span>
      </div>
    </div>
  )
}

function SkillSection({ title, data, type }) {
  if (!data) return null
  const entries = Object.entries(data)
  if (type === 'status') return <StatusSection data={data} />

  return (
    <div className="cs-section">
      <div className="cs-section-title cinzel">{title}</div>
      <div className="cs-skill-list">
        {entries.map(([name, level]) => (
          <div key={name} className={`cs-skill-row ${level > 0 ? 'has-skill' : 'no-skill'}`}>
            <span className="cs-skill-name">{name}</span>
            {type === 'resources' ? (
              <span className="cs-skill-value">{level}</span>
            ) : (
              <SkillBar level={level} max={Math.max(3, level)} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function CharSheetModal({ onClose, sendCommand, charsheetData }) {
  const [loading, setLoading] = useState(!charsheetData)

  useEffect(() => {
    sendCommand('__charsheet_ui__')
  }, [sendCommand])

  useEffect(() => {
    if (charsheetData) setLoading(false)
  }, [charsheetData])

  const data = charsheetData || {}

  return (
    <div className="cs-modal-backdrop" onClick={onClose}>
      <div className="cs-modal" onClick={e => e.stopPropagation()}>
        <div className="cs-modal-header">
          <span className="cinzel cs-modal-title">
            {data.name ? `${data.name}'s Character Sheet` : 'CHARACTER SHEET'}
          </span>
          <button className="cs-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="cs-modal-body">
          {loading ? (
            <div className="cs-loading">Reading the tome of your deeds...</div>
          ) : (
            SKILL_SECTIONS.map(sec => (
              <SkillSection
                key={sec.key}
                title={sec.title}
                data={data[sec.key]}
                type={sec.type}
              />
            ))
          )}
        </div>

        <div className="cs-modal-footer">
          <span className="cinzel">✦ ─────── ✦ ─────── ✦</span>
        </div>
      </div>
    </div>
  )
}
