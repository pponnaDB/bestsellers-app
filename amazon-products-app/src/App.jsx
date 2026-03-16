import { useState, useEffect, useRef, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'

const COLORS = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899']
const truncate = (s, n) => s && s.length > n ? s.slice(0, n) + '...' : s

/* ───────────────── Products Tab ───────────────── */
function ProductsTab() {
  const [products, setProducts] = useState([])
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [availability, setAvailability] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const perPage = 10
  const debounceRef = useRef(null)

  // Debounce search input
  const handleSearch = useCallback((value) => {
    setSearchInput(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setSearchQuery(value)
      setPage(1)
    }, 400)
  }, [])

  useEffect(() => {
    setLoading(true); setError(null)
    const params = new URLSearchParams({ page, per_page: perPage })
    if (searchQuery) params.set('search', searchQuery)
    if (availability) params.set('availability', availability)
    fetch(`/api/products?${params}`)
      .then(r => { if (!r.ok) return r.json().then(d => { throw new Error(d.error || r.status) }); return r.json() })
      .then(data => { setProducts(Array.isArray(data.products) ? data.products : []); setTotal(data.total || 0); setLoading(false) })
      .catch(e => { setError(e.message); setProducts([]); setLoading(false) })
  }, [searchQuery, availability, page])

  useEffect(() => { setPage(1) }, [availability])

  const totalPages = Math.max(1, Math.ceil(total / perPage))
  const fmtPrice = (p, c) => {
    if (p == null) return 'N/A'
    const s = c === 'USD' ? '$' : c === 'EUR' ? '\u20ac' : c === 'GBP' ? '\u00a3' : (c || '$')
    return `${s}${Number(p).toLocaleString()}`
  }
  const avCls = a => {
    if (!a) return 'av-unknown'
    const l = a.toLowerCase()
    return l.includes('in stock') ? 'av-in' : (l.includes('out') || l.includes('unavail')) ? 'av-out' : 'av-ltd'
  }

  return (
    <div>
      <div className="controls">
        <div className="search-box">
          <span className="search-icon"></span>
          <input
            type="text"
            placeholder="Search products..."
            value={searchInput}
            onChange={e => handleSearch(e.target.value)}
            className="search-input"
          />
          {searchInput && (
            <button className="search-clear" onClick={() => { setSearchInput(''); setSearchQuery(''); setPage(1) }}>\u2715</button>
          )}
        </div>
        <div className="toggle-group">
          <button className={`toggle-btn ${availability === '' ? 'active' : ''}`} onClick={() => setAvailability('')}>All</button>
          <button className={`toggle-btn in-stock ${availability === 'in_stock' ? 'active' : ''}`} onClick={() => setAvailability('in_stock')}>In Stock</button>
          <button className={`toggle-btn out-stock ${availability === 'out_of_stock' ? 'active' : ''}`} onClick={() => setAvailability('out_of_stock')}>Out of Stock</button>
        </div>
        <span className="product-count">{total} products</span>
      </div>
      {error && <div className="error-msg">{error}</div>}
      {loading ? (
        <div className="loading"><div className="spinner" /><p>Loading...</p></div>
      ) : (
        <>
          <div className="table-wrap">
            <table className="ptable">
              <thead><tr><th>Title</th><th>Price</th><th>Availability</th></tr></thead>
              <tbody>
                {products.length === 0
                  ? <tr><td colSpan="3" className="no-data">No products found</td></tr>
                  : products.map((p, i) => (
                    <tr key={i}>
                      <td className="title-cell">{p.TITLE || 'N/A'}</td>
                      <td className="price-cell">{fmtPrice(p.FINAL_PRICE, p.CURRENCY)}</td>
                      <td><span className={`av-badge ${avCls(p.AVAILABILITY)}`}>{p.AVAILABILITY || 'Unknown'}</span></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>&laquo; Prev</button>
            <span className="page-info">Page {page} of {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next &raquo;</button>
          </div>
        </>
      )}
    </div>
  )
}

/* ───────────────── Brands Tab ───────────────── */
function BrandsTab() {
  const [brands, setBrands] = useState([])
  const [selectedBrand, setSelectedBrand] = useState('Amazon Essentials')
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/brands')
      .then(r => { if (!r.ok) throw new Error(`API ${r.status}`); return r.json() })
      .then(d => { if (Array.isArray(d)) setBrands(d) })
      .catch(e => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selectedBrand) { setProducts([]); return }
    setLoading(true); setError(null)
    fetch(`/api/products/by-brand?brand=${encodeURIComponent(selectedBrand)}`)
      .then(r => { if (!r.ok) return r.json().then(d => { throw new Error(d.error || r.status) }); return r.json() })
      .then(d => { setProducts(Array.isArray(d) ? d : []); setLoading(false) })
      .catch(e => { setError(e.message); setProducts([]); setLoading(false) })
  }, [selectedBrand])

  return (
    <div>
      <div className="controls">
        <div className="filter-group">
          <label>Brand:</label>
          <select value={selectedBrand} onChange={e => setSelectedBrand(e.target.value)}>
            <option value="">Select a Brand</option>
            {brands.map((b, i) => <option key={i} value={b}>{b}</option>)}
          </select>
        </div>
        {selectedBrand && <span className="product-count">{products.length} products</span>}
      </div>
      {error && <div className="error-msg">{error}</div>}
      {!selectedBrand ? (
        <div className="empty-state">Select a brand to see its products</div>
      ) : loading ? (
        <div className="loading"><div className="spinner" /><p>Loading...</p></div>
      ) : (
        <div className="brand-grid">
          {products.length === 0 ? (
            <div className="empty-state">No products found for this brand</div>
          ) : products.map((p, i) => (
            <div key={i} className="brand-card">
              <div className="card-title">{p.TITLE || 'N/A'}</div>
              <div className="card-meta">
                <span className="card-price">{p.FINAL_PRICE != null ? `$${Number(p.FINAL_PRICE).toLocaleString()}` : 'N/A'}</span>
                {p.CATEGORIES && <span className="card-cat">{truncate(p.CATEGORIES, 35)}</span>}
              </div>
              <span className={`av-badge ${p.AVAILABILITY && p.AVAILABILITY.toLowerCase().includes('in stock') ? 'av-in' : 'av-out'}`}>
                {p.AVAILABILITY || 'Unknown'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ───────────────── Analysis Tab ───────────────── */
function AnalysisTab() {
  const [brands, setBrands] = useState([])
  const [selectedBrand, setSelectedBrand] = useState('')
  const [chartData, setChartData] = useState([])
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(false)
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/brands-with-prices')
      .then(r => { if (!r.ok) throw new Error(`API ${r.status}`); return r.json() })
      .then(d => { if (Array.isArray(d)) setBrands(d) })
      .catch(e => setError(e.message))
  }, [])

  useEffect(() => {
    setInsightsLoading(true)
    fetch('/api/analysis/insights')
      .then(r => { if (!r.ok) return r.json().then(d => { throw new Error(d.error || r.status) }); return r.json() })
      .then(d => { setInsights(d); setInsightsLoading(false) })
      .catch(e => { setError(e.message); setInsightsLoading(false) })
  }, [])

  useEffect(() => {
    setLoading(true); setError(null)
    const url = selectedBrand ? `/api/analysis?brand=${encodeURIComponent(selectedBrand)}` : '/api/analysis'
    fetch(url)
      .then(r => { if (!r.ok) return r.json().then(d => { throw new Error(d.error || r.status) }); return r.json() })
      .then(d => {
        const parsed = (Array.isArray(d) ? d : []).map(r => ({
          name: truncate(r.TITLE || '', 25),
          'Initial Price': Number(r.INITIAL_PRICE) || 0,
          'Final Price': Number(r.FINAL_PRICE) || 0,
        }))
        setChartData(parsed); setLoading(false)
      })
      .catch(e => { setError(e.message); setChartData([]); setLoading(false) })
  }, [selectedBrand])

  const renderPieLabel = ({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`

  return (
    <div>
      <div className="widget-card full-width">
        <div className="widget-header">
          <h3>\ud83d\udcb0 Price Comparison: Initial vs Final</h3>
          <div className="filter-group compact">
            <label>Brand:</label>
            <select value={selectedBrand} onChange={e => setSelectedBrand(e.target.value)}>
              <option value="">All Brands</option>
              {brands.map((b, i) => <option key={i} value={b}>{b}</option>)}
            </select>
          </div>
        </div>
        {error && <div className="error-msg">{error}</div>}
        {loading ? (
          <div className="loading"><div className="spinner" /><p>Loading chart...</p></div>
        ) : chartData.length === 0 ? (
          <div className="empty-state">No price data available</div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" interval={0} tick={{ fontSize: 10 }} height={100} />
              <YAxis tick={{ fontSize: 12 }} label={{ value: 'Price ($)', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={v => `$${Number(v).toLocaleString()}`} />
              <Legend />
              <Bar dataKey="Initial Price" fill="#94a3b8" radius={[4,4,0,0]} />
              <Bar dataKey="Final Price" fill="#3b82f6" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {insightsLoading ? (
        <div className="loading"><div className="spinner" /><p>Loading insights...</p></div>
      ) : insights && (
        <div className="widget-grid">
          <div className="widget-card">
            <h3>\ud83c\udff7\ufe0f Top 10 Biggest Savings</h3>
            {insights.topDiscounted && insights.topDiscounted.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={insights.topDiscounted.map(r => ({
                  name: truncate(r.TITLE || '', 20), Savings: Number(r.SAVINGS) || 0,
                }))} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" width={130} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={v => `$${Number(v).toLocaleString()}`} />
                  <Bar dataKey="Savings" fill="#10b981" radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="empty-state">No discount data</div>}
          </div>

          <div className="widget-card">
            <h3>\ud83c\udfe2 Average Price by Brand (Top 15)</h3>
            {insights.avgByBrand && insights.avgByBrand.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={insights.avgByBrand.map(r => ({
                  name: truncate(r.BRAND || '', 15), 'Avg Price': Number(r.AVG_PRICE) || 0,
                }))} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={v => `$${Number(v).toLocaleString()}`} />
                  <Bar dataKey="Avg Price" fill="#8b5cf6" radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="empty-state">No brand data</div>}
          </div>

          <div className="widget-card">
            <h3>\ud83d\udcca Price Distribution</h3>
            {insights.priceDistribution && insights.priceDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={insights.priceDistribution.map(r => ({
                  range: r.PRICE_RANGE, Products: Number(r.CNT) || 0,
                }))} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="Products" radius={[4,4,0,0]}>
                    {(insights.priceDistribution || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="empty-state">No price data</div>}
          </div>

          <div className="widget-card">
            <h3>\u2705 Availability Breakdown</h3>
            {insights.availability && insights.availability.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={insights.availability.map(r => ({ name: r.STATUS, value: Number(r.CNT) || 0 }))}
                    cx="50%" cy="50%" outerRadius={100} dataKey="value" label={renderPieLabel} labelLine={false}>
                    {insights.availability.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip /><Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : <div className="empty-state">No availability data</div>}
          </div>

          <div className="widget-card full-width">
            <h3>\u2b50 Top Rated Products (10+ Reviews)</h3>
            {insights.topRated && insights.topRated.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={insights.topRated.map(r => ({
                  name: truncate(r.TITLE || '', 25),
                  Rating: Number(r.RATING) || 0, Reviews: Number(r.REVIEWS) || 0,
                }))} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" interval={0} tick={{ fontSize: 10 }} height={100} />
                  <YAxis yAxisId="left" domain={[0, 5]} tick={{ fontSize: 12 }} label={{ value: 'Rating', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} label={{ value: 'Reviews', angle: 90, position: 'insideRight' }} />
                  <Tooltip /><Legend />
                  <Bar yAxisId="left" dataKey="Rating" fill="#f59e0b" radius={[4,4,0,0]} />
                  <Bar yAxisId="right" dataKey="Reviews" fill="#3b82f6" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="empty-state">No rating data</div>}
          </div>
        </div>
      )}
    </div>
  )
}

/* ───────────────── Main App ───────────────── */
function App() {
  const [activeTab, setActiveTab] = useState('products')
  const tabs = [
    { id: 'products', label: 'Products' },
    { id: 'brands',   label: 'Brands' },
    { id: 'analysis', label: 'Analysis' },
  ]
  return (
    <div className="app">
      <header className="header">
        <h1>Amazon Best Seller Products</h1>
        <p className="subtitle">Browse, explore brands, and analyze pricing</p>
      </header>
      <nav className="nav-tabs">
        {tabs.map(t => (
          <button key={t.id} className={`nav-tab ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}>{t.label}</button>
        ))}
      </nav>
      <main className="content">
        {activeTab === 'products' && <ProductsTab />}
        {activeTab === 'brands' && <BrandsTab />}
        {activeTab === 'analysis' && <AnalysisTab />}
      </main>
    </div>
  )
}

export default App
