import { useState, useEffect, useCallback } from 'react'
import './ShopModal.css'

function BuyCard({ item, onBuy, playerSilver, buying }) {
  const canAfford = playerSilver >= item.price
  return (
    <div className={`shop-item-card ${canAfford ? '' : 'cant-afford'}`}>
      <div className="shop-item-info">
        <span className="shop-item-name">{item.name}</span>
        {item.desc && <span className="shop-item-desc">{item.desc}</span>}
        <div className="shop-item-stats">
          {item.damage > 0 && <span className="shop-stat">DMG {item.damage}</span>}
          {item.materialValue > 0 && <span className="shop-stat">AV +{item.materialValue}</span>}
          {item.type && <span className="shop-stat">{item.type}</span>}
        </div>
      </div>
      <div className="shop-item-price">
        <span className="shop-price-amount">{item.price}</span>
        <span className="shop-price-label">silver</span>
      </div>
      <button
        className="shop-action-btn buy"
        onClick={() => onBuy(item.name)}
        disabled={!canAfford || buying}
        title={canAfford ? `Buy for ${item.price} silver` : 'Not enough silver'}
      >
        {buying ? '...' : 'Buy'}
      </button>
    </div>
  )
}

function SellCard({ item, onSell, selling }) {
  return (
    <div className="shop-item-card sell-card">
      <div className="shop-item-info">
        <span className="shop-item-name">{item.name}</span>
        {item.type && <span className="shop-item-type">{item.type}</span>}
      </div>
      <div className="shop-item-price sell-price">
        <span className="shop-price-amount">{item.sellPrice}</span>
        <span className="shop-price-label">silver</span>
      </div>
      <button
        className="shop-action-btn sell"
        onClick={() => onSell(item.name)}
        disabled={item.sellPrice === 0 || selling}
        title={item.sellPrice > 0 ? `Sell for ${item.sellPrice} silver` : 'No value'}
      >
        {selling ? '...' : 'Sell'}
      </button>
    </div>
  )
}

export default function ShopModal({ onClose, sendCommand, shopData }) {
  const [tab, setTab] = useState('buy')
  const [loading, setLoading] = useState(!shopData)
  const [buying, setBuying] = useState(null)
  const [selling, setSelling] = useState(null)

  useEffect(() => {
    sendCommand('__shop_ui__')
  }, [sendCommand])

  useEffect(() => {
    if (shopData) setLoading(false)
  }, [shopData])

  const handleBuy = useCallback((itemName) => {
    const merchant = shopData?.merchants?.[0]
    if (!merchant) return
    setBuying(itemName)
    sendCommand(`__buy__ ${itemName} from ${merchant.name}`)
    setTimeout(() => {
      sendCommand('__shop_ui__')
      setBuying(null)
    }, 800)
  }, [sendCommand, shopData])

  const handleSell = useCallback((itemName) => {
    setSelling(itemName)
    sendCommand(`__sell__ ${itemName}`)
    setTimeout(() => {
      sendCommand('__shop_ui__')
      setSelling(null)
    }, 800)
  }, [sendCommand])

  const merchants = shopData?.merchants || []
  const playerSilver = shopData?.playerSilver || 0
  const sellInventory = shopData?.sellInventory || []
  const merchant = merchants[0]

  return (
    <div className="shop-backdrop" onClick={onClose}>
      <div className="shop-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="shop-header">
          <div className="shop-header-left">
            <span className="cinzel shop-title">
              {merchant ? merchant.name : 'MERCHANT'}
            </span>
            {merchant?.desc && (
              <span className="shop-merchant-desc">{merchant.desc}</span>
            )}
          </div>
          <div className="shop-wallet">
            <span className="shop-wallet-amount">{playerSilver}</span>
            <span className="shop-wallet-label">silver</span>
          </div>
          <button className="shop-close" onClick={onClose}>✕</button>
        </div>

        {/* Tab bar */}
        <div className="shop-tabs">
          <button
            className={`shop-tab ${tab === 'buy' ? 'active' : ''}`}
            onClick={() => setTab('buy')}
          >
            Buy
          </button>
          <button
            className={`shop-tab ${tab === 'sell' ? 'active' : ''}`}
            onClick={() => setTab('sell')}
          >
            Sell
          </button>
        </div>

        {/* Body */}
        <div className="shop-body">
          {loading ? (
            <div className="shop-loading">The merchant appraises their wares...</div>
          ) : tab === 'buy' ? (
            <div className="shop-items">
              {merchant && merchant.items.length > 0 ? (
                merchant.items.map((item, i) => (
                  <BuyCard
                    key={i}
                    item={item}
                    onBuy={handleBuy}
                    playerSilver={playerSilver}
                    buying={buying === item.name}
                  />
                ))
              ) : (
                <div className="shop-empty">No wares available.</div>
              )}
            </div>
          ) : (
            <div className="shop-items">
              {sellInventory.length > 0 ? (
                sellInventory.filter(i => i.sellPrice > 0).map((item, i) => (
                  <SellCard
                    key={i}
                    item={item}
                    onSell={handleSell}
                    selling={selling === item.name}
                  />
                ))
              ) : (
                <div className="shop-empty">You have nothing to sell.</div>
              )}
            </div>
          )}
        </div>

        <div className="shop-footer">
          <span className="cinzel">✦ ─────── ✦ ─────── ✦</span>
        </div>
      </div>
    </div>
  )
}
