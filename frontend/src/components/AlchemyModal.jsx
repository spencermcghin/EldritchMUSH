import { useState, useMemo } from 'react'
import './AlchemyModal.css'

const TYPE_CLASSES = {
  apotheca: 'apotheca',
  poison: 'poison',
  drug: 'drug',
}

export default function AlchemyModal({ onClose, sendCommand, alchemyData }) {
  const [selectedKey, setSelectedKey] = useState(null)
  const [filter, setFilter] = useState('all') // 'all' | 'apotheca' | 'poison' | 'drug'

  if (!alchemyData) return null

  const {
    alchemistLevel = 0,
    knownRecipes = [],
    reagents = {},
    hasKit = false,
  } = alchemyData

  // Filter and group recipes by level
  const filtered = useMemo(() => {
    let list = knownRecipes
    if (filter !== 'all') {
      list = list.filter(r => (r.type || '').toLowerCase() === filter)
    }
    // Group by level
    const groups = {}
    for (const recipe of list) {
      const lvl = recipe.level || 1
      if (!groups[lvl]) groups[lvl] = []
      groups[lvl].push(recipe)
    }
    // Sort recipes within each level alphabetically
    for (const lvl of Object.keys(groups)) {
      groups[lvl].sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    }
    return groups
  }, [knownRecipes, filter])

  const selected = knownRecipes.find(r => r.key === selectedKey) || null

  const reagentCount = Object.values(reagents).reduce((sum, qty) => sum + (qty > 0 ? qty : 0), 0)
  const reagentTypes = Object.keys(reagents).filter(k => reagents[k] > 0).length

  const handleBrew = () => {
    if (!selected || !selected.canBrew) return
    sendCommand(`__alchemy_brew__ ${selected.key}`)
  }

  return (
    <div className="alchemy-backdrop" onClick={onClose}>
      <div className="alchemy-modal" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="alchemy-header">
          <span className="alchemy-title cinzel">ALCHEMY WORKBENCH</span>
          <span className="alchemy-level">LVL {alchemistLevel}</span>
          <span className="alchemy-subtitle">
            {knownRecipes.length} recipe{knownRecipes.length !== 1 ? 's' : ''} known
          </span>
          <button className="alchemy-close" onClick={onClose} title="Close">&times;</button>
        </div>

        {/* Body */}
        <div className="alchemy-body">

          {/* Left panel: recipe list */}
          <div className="alchemy-recipe-list">
            <div className="alchemy-filter-bar">
              {['all', 'apotheca', 'poison', 'drug'].map(f => (
                <button
                  key={f}
                  className={`alchemy-filter-btn${filter === f ? ' active' : ''}`}
                  onClick={() => setFilter(f)}
                >
                  {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>

            <div className="alchemy-recipes-scroll">
              {Object.keys(filtered).length === 0 && (
                <div className="alchemy-detail-empty">
                  No recipes match this filter.
                </div>
              )}
              {Object.keys(filtered).sort((a, b) => Number(a) - Number(b)).map(lvl => (
                <div key={lvl} className="alchemy-level-group">
                  <div className="alchemy-level-header cinzel">Level {lvl}</div>
                  {filtered[lvl].map(recipe => (
                    <div
                      key={recipe.key}
                      className={
                        'alchemy-recipe-item' +
                        (selectedKey === recipe.key ? ' selected' : '') +
                        (recipe.canBrew ? ' can-brew' : '')
                      }
                      onClick={() => setSelectedKey(recipe.key)}
                    >
                      <div className="alchemy-recipe-indicator" />
                      <span className="alchemy-recipe-name">{recipe.name}</span>
                      <span className={`alchemy-recipe-type-tag ${TYPE_CLASSES[(recipe.type || '').toLowerCase()] || ''}`}>
                        {recipe.type || '?'}
                      </span>
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
                      <span className={`alchemy-detail-badge ${TYPE_CLASSES[(selected.type || '').toLowerCase()] || ''}`}>
                        {selected.type}
                      </span>
                      <span className="alchemy-detail-badge">Level {selected.level}</span>
                      {selected.qty_produced > 1 && (
                        <span className="alchemy-detail-badge">
                          Produces {selected.qty_produced}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="alchemy-detail-effect">
                    {selected.effect || 'No effect description available.'}
                  </div>

                  <div>
                    <div className="alchemy-detail-section-label cinzel">Required Reagents</div>
                    <div className="alchemy-reagent-list">
                      {(selected.reagents || []).map((r, i) => {
                        const hasEnough = r.have >= r.qty
                        return (
                          <div key={i} className="alchemy-reagent-row">
                            <div className={`alchemy-reagent-status ${hasEnough ? 'has-enough' : 'missing'}`} />
                            <span className="alchemy-reagent-name">{r.name}</span>
                            <span className="alchemy-reagent-qty">
                              {r.have} / {r.qty}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {selected.qty_produced > 1 && (
                    <div className="alchemy-detail-yield">
                      Produces {selected.qty_produced} doses per brew.
                    </div>
                  )}

                  {!hasKit && (
                    <div className="alchemy-brew-feedback error">
                      No Apothecary Kit equipped.
                    </div>
                  )}
                  {selected.level > alchemistLevel && (
                    <div className="alchemy-brew-feedback error">
                      Requires Alchemist level {selected.level}.
                    </div>
                  )}
                </div>

                <div className="alchemy-brew-bar">
                  <button
                    className="alchemy-brew-btn"
                    disabled={!selected.canBrew}
                    onClick={handleBrew}
                  >
                    Brew
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="alchemy-footer">
          <div className="alchemy-kit-status">
            <div className={`alchemy-kit-dot ${hasKit ? 'has-kit' : 'no-kit'}`} />
            <span>{hasKit ? 'Kit ready' : 'No kit'}</span>
          </div>
          <span className="alchemy-reagent-summary">
            {reagentTypes} reagent type{reagentTypes !== 1 ? 's' : ''}, {reagentCount} total
          </span>
        </div>

      </div>
    </div>
  )
}
