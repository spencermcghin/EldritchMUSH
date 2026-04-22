import { useState, useMemo, useEffect } from 'react'
import './CraftingModal.css'

// Substance type → CSS class for the alchemy sub-filter tags.
const TYPE_CLASSES = {
  apotheca: 'apotheca',
  poison: 'poison',
  drug: 'drug',
}

const ALCHEMY_FILTERS = ['all', 'apotheca', 'poison', 'drug']

const MATERIAL_LABELS = {
  iron_ingots: 'Iron Ingots',
  refined_wood: 'Refined Wood',
  leather: 'Leather',
  cloth: 'Cloth',
}

function prettyMaterial(name) {
  return MATERIAL_LABELS[name] || name
}

export default function CraftingModal({ onClose, sendCommand, craftingData }) {
  const tabs = craftingData?.tabs || []
  const [activeTabId, setActiveTabId] = useState(null)
  const [selectedKey, setSelectedKey] = useState(null)
  const [alchemyFilter, setAlchemyFilter] = useState('all')

  // Keep the active tab valid whenever tabs change. Default to the first
  // tab that has at least one known recipe; fall back to the first tab.
  useEffect(() => {
    if (!tabs.length) {
      setActiveTabId(null)
      return
    }
    const stillValid = tabs.some(t => t.id === activeTabId)
    if (!stillValid) {
      const firstWithRecipes = tabs.find(t => (t.recipes || []).length > 0)
      setActiveTabId((firstWithRecipes || tabs[0]).id)
      setSelectedKey(null)
    }
  }, [tabs, activeTabId])

  if (!craftingData) return null

  const activeTab = tabs.find(t => t.id === activeTabId) || null
  const recipes = activeTab?.recipes || []
  const isAlchemyTab = activeTab?.id === 'apothecary'

  // Group recipes by level (both tabs use this). Alchemy tab also filters
  // by substance type.
  const grouped = useMemo(() => {
    let list = recipes
    if (isAlchemyTab && alchemyFilter !== 'all') {
      list = list.filter(r => (r.substanceType || '').toLowerCase() === alchemyFilter)
    }
    const groups = {}
    for (const r of list) {
      const lvl = r.level == null ? 0 : r.level
      if (!groups[lvl]) groups[lvl] = []
      groups[lvl].push(r)
    }
    for (const k of Object.keys(groups)) {
      groups[k].sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    }
    return groups
  }, [recipes, isAlchemyTab, alchemyFilter])

  const selected = recipes.find(r => r.key === selectedKey) || null

  const handleCraft = () => {
    if (!selected || !selected.canCraft) return
    sendCommand(`__craft_item__ ${selected.key}`)
  }

  const blockedReason = (() => {
    if (!activeTab) return ''
    if (!activeTab.stationPresent) {
      return `No ${activeTab.label} station in this room.`
    }
    if (!activeTab.hasKit) {
      return `No ${activeTab.label} kit equipped (or kit out of uses).`
    }
    return ''
  })()

  return (
    <div className="alchemy-backdrop" onClick={onClose}>
      <div className="alchemy-modal" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="alchemy-header">
          <span className="alchemy-title cinzel">CRAFTING WORKBENCH</span>
          {activeTab && (
            <span className="alchemy-level">LVL {activeTab.skillLevel}</span>
          )}
          <span className="alchemy-subtitle">
            {activeTab
              ? `${recipes.length} recipe${recipes.length !== 1 ? 's' : ''} known`
              : 'No crafting skills'}
          </span>
          <button className="alchemy-close" onClick={onClose} title="Close">&times;</button>
        </div>

        {/* Tab bar */}
        {tabs.length > 0 && (
          <div className="crafting-tabs">
            {tabs.map(tab => {
              const isActive = tab.id === activeTabId
              return (
                <button
                  key={tab.id}
                  className={`crafting-tab${isActive ? ' active' : ''}`}
                  onClick={() => {
                    setActiveTabId(tab.id)
                    setSelectedKey(null)
                  }}
                >
                  <span>{tab.label}</span>
                  <span className="crafting-tab-meta">
                    LVL {tab.skillLevel} · {tab.recipes.length} recipe{tab.recipes.length !== 1 ? 's' : ''}
                  </span>
                  <span className="crafting-tab-status">
                    <span
                      className={`crafting-tab-status-dot ${tab.stationPresent ? 'ok' : 'missing'}`}
                      title={tab.stationPresent ? 'Station in room' : 'No station in room'}
                    />
                    <span
                      className={`crafting-tab-status-dot ${tab.hasKit ? 'ok' : 'missing'}`}
                      title={tab.hasKit ? 'Kit ready' : 'No kit or out of uses'}
                    />
                  </span>
                </button>
              )
            })}
          </div>
        )}

        {blockedReason && (
          <div className="crafting-reason">{blockedReason}</div>
        )}

        {/* Body */}
        <div className="alchemy-body">

          {/* Left panel: recipe list */}
          <div className="alchemy-recipe-list">
            {isAlchemyTab && (
              <div className="alchemy-filter-bar">
                {ALCHEMY_FILTERS.map(f => (
                  <button
                    key={f}
                    className={`alchemy-filter-btn${alchemyFilter === f ? ' active' : ''}`}
                    onClick={() => setAlchemyFilter(f)}
                  >
                    {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                  </button>
                ))}
              </div>
            )}

            <div className="alchemy-recipes-scroll">
              {recipes.length === 0 && (
                <div className="alchemy-detail-empty">
                  {activeTab
                    ? 'No recipes known. Find or buy schematic scrolls.'
                    : 'No crafting skills.'}
                </div>
              )}
              {recipes.length > 0 && Object.keys(grouped).length === 0 && (
                <div className="alchemy-detail-empty">
                  No recipes match this filter.
                </div>
              )}
              {Object.keys(grouped).sort((a, b) => Number(a) - Number(b)).map(lvl => (
                <div key={lvl} className="alchemy-level-group">
                  <div className="alchemy-level-header cinzel">Level {lvl}</div>
                  {grouped[lvl].map(recipe => (
                    <div
                      key={recipe.key}
                      className={
                        'alchemy-recipe-item' +
                        (selectedKey === recipe.key ? ' selected' : '') +
                        (recipe.canCraft ? ' can-brew' : '')
                      }
                      onClick={() => setSelectedKey(recipe.key)}
                    >
                      <div className="alchemy-recipe-indicator" />
                      <span className="alchemy-recipe-name">{recipe.name}</span>
                      {recipe.substanceType && (
                        <span
                          className={`alchemy-recipe-type-tag ${
                            TYPE_CLASSES[(recipe.substanceType || '').toLowerCase()] || ''
                          }`}
                        >
                          {recipe.substanceType}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Right panel: detail */}
          <div className="alchemy-detail">
            {!selected ? (
              <div className="alchemy-detail-empty">
                Select a recipe to view its details.
              </div>
            ) : (
              <>
                <div className="alchemy-detail-content">
                  <div>
                    <div className="alchemy-detail-name cinzel">{selected.name}</div>
                    <div className="alchemy-detail-meta">
                      {selected.substanceType && (
                        <span
                          className={`alchemy-detail-badge ${
                            TYPE_CLASSES[(selected.substanceType || '').toLowerCase()] || ''
                          }`}
                        >
                          {selected.substanceType}
                        </span>
                      )}
                      <span className="alchemy-detail-badge">Level {selected.level}</span>
                      {selected.qtyProduced > 1 && (
                        <span className="alchemy-detail-badge">
                          Produces {selected.qtyProduced}
                        </span>
                      )}
                    </div>
                  </div>

                  {selected.effect && (
                    <div className="alchemy-detail-effect">
                      {selected.effect}
                    </div>
                  )}

                  <div>
                    <div className="alchemy-detail-section-label cinzel">
                      {isAlchemyTab ? 'Required Reagents' : 'Required Materials'}
                    </div>
                    <div className="alchemy-reagent-list">
                      {(selected.materials || []).length === 0 && (
                        <div className="alchemy-detail-empty" style={{ padding: '8px 0' }}>
                          No materials required.
                        </div>
                      )}
                      {(selected.materials || []).map((m, i) => {
                        const hasEnough = m.have >= m.qty
                        return (
                          <div key={i} className="alchemy-reagent-row">
                            <div className={`alchemy-reagent-status ${hasEnough ? 'has-enough' : 'missing'}`} />
                            <span className="alchemy-reagent-name">
                              {isAlchemyTab ? m.name : prettyMaterial(m.name)}
                            </span>
                            <span className="alchemy-reagent-qty">
                              {m.have} / {m.qty}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {selected.qtyProduced > 1 && (
                    <div className="alchemy-detail-yield">
                      Produces {selected.qtyProduced} per craft.
                    </div>
                  )}

                  {activeTab && !activeTab.hasKit && (
                    <div className="alchemy-brew-feedback error">
                      No {activeTab.label} Kit equipped.
                    </div>
                  )}
                  {activeTab && !activeTab.stationPresent && (
                    <div className="alchemy-brew-feedback error">
                      You need a {activeTab.label} station nearby.
                    </div>
                  )}
                  {activeTab && selected.level > activeTab.skillLevel && (
                    <div className="alchemy-brew-feedback error">
                      Requires {activeTab.label} level {selected.level}.
                    </div>
                  )}
                </div>

                <div className="alchemy-brew-bar">
                  <button
                    className="alchemy-brew-btn"
                    disabled={!selected.canCraft}
                    onClick={handleCraft}
                  >
                    {isAlchemyTab ? 'Brew' : activeTab?.id === 'blacksmith' ? 'Forge' : 'Craft'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="alchemy-footer">
          {activeTab && (
            <div className="alchemy-kit-status">
              <div className={`alchemy-kit-dot ${activeTab.hasKit ? 'has-kit' : 'no-kit'}`} />
              <span>{activeTab.hasKit ? 'Kit ready' : 'No kit'}</span>
            </div>
          )}
          <span className="alchemy-reagent-summary">
            {isAlchemyTab
              ? (() => {
                  const reagents = craftingData.reagents || {}
                  const types = Object.keys(reagents).filter(k => reagents[k] > 0).length
                  const total = Object.values(reagents).reduce((s, q) => s + (q > 0 ? q : 0), 0)
                  return `${types} reagent type${types !== 1 ? 's' : ''}, ${total} total`
                })()
              : (() => {
                  const m = craftingData.materials || {}
                  return Object.keys(MATERIAL_LABELS)
                    .map(k => `${MATERIAL_LABELS[k]}: ${m[k] || 0}`)
                    .join(' · ')
                })()
            }
          </span>
        </div>

      </div>
    </div>
  )
}
