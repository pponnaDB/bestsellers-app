# Databricks notebook source
# DBTITLE 1,App Overview
# MAGIC %md
# MAGIC # Amazon Best Seller Products — Databricks App Setup
# MAGIC
# MAGIC This notebook generates all files needed to deploy a **Databricks App** with:
# MAGIC - **React frontend** (Vite + React 18) — responsive product table with category filtering
# MAGIC - **Flask backend** — REST API that queries `pp_demo.datasets.amazon_best_seller_products` via the Databricks SDK
# MAGIC
# MAGIC ### App Features
# MAGIC | Feature | Description |
# MAGIC | --- | --- |
# MAGIC | Product listing | Unique list of Title, Brand, Final Price, and Availability |
# MAGIC | Category filter | Dropdown to filter products by category |
# MAGIC | Responsive design | Clean, modern UI with status badges and loading states |
# MAGIC
# MAGIC > **Run all cells below** to generate the app files, then follow the deployment instructions at the bottom.

# COMMAND ----------

# DBTITLE 1,Create app directory structure
import os

BASE_DIR = "/Workspace/Users/praveen.ponna@databricks.com/amazon-products-app"
os.makedirs(os.path.join(BASE_DIR, "src"), exist_ok=True)
print(f"✅ Created directory structure at: {BASE_DIR}")
print(f"   └── src/")

# COMMAND ----------

# DBTITLE 1,Write app.yaml
# App configuration — defines the startup command and environment variables

app_yaml = """command: ["python", "app.py"]
env:
  - name: "DATABRICKS_WAREHOUSE_ID"
    value: "da549382cd8d3509"
"""

with open(os.path.join(BASE_DIR, "app.yaml"), "w") as f:
    f.write(app_yaml)

print("✅ Written: app.yaml")
print(f"   Warehouse ID: da549382cd8d3509")

# COMMAND ----------

# DBTITLE 1,Write requirements.txt
# Python dependencies for the Flask backend

requirements = """flask==3.1.1
databricks-sdk==0.44.0
"""

with open(os.path.join(BASE_DIR, "requirements.txt"), "w") as f:
    f.write(requirements)

print("✅ Written: requirements.txt")

# COMMAND ----------

# DBTITLE 1,Write package.json
import json

package_json = {
    "name": "amazon-products-app",
    "private": True,
    "version": "2.0.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview"
    },
    "dependencies": {
        "react": "^18.3.1",
        "react-dom": "^18.3.1",
        "recharts": "^2.15.3"
    },
    "devDependencies": {
        "@types/react": "^18.3.18",
        "@types/react-dom": "^18.3.5",
        "@vitejs/plugin-react": "^4.3.4",
        "vite": "^6.0.5"
    }
}

with open(os.path.join(BASE_DIR, "package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

print("✅ Written: package.json (added recharts)")

# COMMAND ----------

# DBTITLE 1,Write vite.config.js
vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
"""

with open(os.path.join(BASE_DIR, "vite.config.js"), "w") as f:
    f.write(vite_config)

print("✅ Written: vite.config.js")

# COMMAND ----------

# DBTITLE 1,Write index.html
# Vite entry point HTML file

index_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Amazon Best Sellers</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

with open(os.path.join(BASE_DIR, "index.html"), "w") as f:
    f.write(index_html)

print("✅ Written: index.html")

# COMMAND ----------

# DBTITLE 1,Write src/main.jsx
main_jsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""

with open(os.path.join(BASE_DIR, "src", "main.jsx"), "w") as f:
    f.write(main_jsx)

print("✅ Written: src/main.jsx")

# COMMAND ----------

# DBTITLE 1,Write src/App.jsx
app_jsx = r"""import { useState, useEffect, useRef, useCallback } from 'react'
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
          <span className="search-icon">\ud83d\udd0d</span>
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
    { id: 'products', label: '\ud83d\udce6 Products' },
    { id: 'brands',   label: '\ud83c\udff7\ufe0f Brands' },
    { id: 'analysis', label: '\ud83d\udcca Analysis' },
  ]
  return (
    <div className="app">
      <header className="header">
        <h1>\ud83d\udcda Amazon Best Seller Products</h1>
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
"""

with open(os.path.join(BASE_DIR, "src", "App.jsx"), "w") as f:
    f.write(app_jsx)

print("✅ Written: src/App.jsx (search box, availability toggle, no Brand column)")

# COMMAND ----------

# DBTITLE 1,Write src/App.css
app_css = """* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa; color: #1a1a2e;
}
.app { max-width: 1200px; margin: 0 auto; padding: 2rem; }

/* Header */
.header { margin-bottom: 1.5rem; }
.header h1 { font-size: 1.8rem; color: #1a1a2e; margin-bottom: 0.25rem; }
.subtitle { color: #6b7280; font-size: 0.95rem; }

/* Navigation */
.nav-tabs { display: flex; gap: 0.25rem; margin-bottom: 1.5rem; border-bottom: 2px solid #e2e8f0; }
.nav-tab {
  padding: 0.7rem 1.5rem; border: none; background: none; font-size: 0.95rem;
  font-weight: 500; color: #64748b; cursor: pointer;
  border-bottom: 3px solid transparent; margin-bottom: -2px; transition: all 0.2s;
}
.nav-tab:hover { color: #3b82f6; background: #f0f7ff; }
.nav-tab.active { color: #3b82f6; border-bottom-color: #3b82f6; font-weight: 600; }

/* Controls */
.controls {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1.5rem; padding: 1rem 1.5rem; flex-wrap: wrap; gap: 0.75rem;
  background: white; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.filter-group { display: flex; align-items: center; gap: 0.75rem; }
.filter-group label { font-weight: 600; font-size: 0.9rem; color: #374151; }
.filter-group select {
  padding: 0.5rem 2rem 0.5rem 0.75rem; border: 1px solid #d1d5db;
  border-radius: 6px; font-size: 0.9rem; background: white; cursor: pointer; max-width: 380px;
}
.filter-group select:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.filter-group.compact select { max-width: 250px; }
.product-count { font-size: 0.85rem; color: #6b7280; font-weight: 500; }

/* Search box */
.search-box {
  display: flex; align-items: center; position: relative; flex: 1; max-width: 400px;
}
.search-icon {
  position: absolute; left: 12px; font-size: 1rem; pointer-events: none; z-index: 1;
}
.search-input {
  width: 100%; padding: 0.6rem 2.2rem 0.6rem 2.4rem;
  border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.9rem;
  background: #f8fafc; transition: all 0.2s;
}
.search-input:focus { outline: none; border-color: #3b82f6; background: white; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.search-input::placeholder { color: #9ca3af; }
.search-clear {
  position: absolute; right: 10px; background: none; border: none;
  font-size: 0.9rem; color: #9ca3af; cursor: pointer; padding: 2px 6px; border-radius: 50%;
}
.search-clear:hover { color: #374151; background: #e2e8f0; }

/* Toggle buttons */
.toggle-group { display: flex; gap: 0; border-radius: 8px; overflow: hidden; border: 1px solid #d1d5db; }
.toggle-btn {
  padding: 0.5rem 1rem; border: none; background: white; font-size: 0.85rem;
  font-weight: 500; color: #64748b; cursor: pointer; transition: all 0.15s;
  border-right: 1px solid #d1d5db;
}
.toggle-btn:last-child { border-right: none; }
.toggle-btn:hover { background: #f8fafc; }
.toggle-btn.active { background: #3b82f6; color: white; font-weight: 600; }
.toggle-btn.in-stock.active { background: #059669; }
.toggle-btn.out-stock.active { background: #dc2626; }

/* Error, loading, empty */
.error-msg {
  background: #fef2f2; color: #dc2626; padding: 0.75rem 1rem;
  border-radius: 8px; margin-bottom: 1rem; border: 1px solid #fecaca;
}
.loading { display: flex; flex-direction: column; align-items: center; padding: 3rem; color: #6b7280; }
.spinner {
  width: 36px; height: 36px; border: 3px solid #e5e7eb; border-top-color: #3b82f6;
  border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 1rem;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { text-align: center; padding: 3rem; color: #9ca3af; font-size: 1rem; }

/* Product table */
.table-wrap { background: white; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); overflow: hidden; }
.ptable { width: 100%; border-collapse: collapse; }
.ptable thead { background: #f8fafc; }
.ptable th {
  padding: 0.75rem 1rem; text-align: left; font-weight: 600; font-size: 0.8rem;
  text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; border-bottom: 2px solid #e2e8f0;
}
.ptable td { padding: 0.75rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }
.ptable tbody tr:hover { background: #f8fafc; }
.title-cell { max-width: 500px; font-weight: 500; }
.price-cell { font-weight: 600; color: #059669; white-space: nowrap; }
.no-data { text-align: center; padding: 2rem; color: #9ca3af; }

/* Availability badges */
.av-badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 500; }
.av-in  { background: #ecfdf5; color: #059669; }
.av-out { background: #fef2f2; color: #dc2626; }
.av-ltd { background: #fffbeb; color: #d97706; }
.av-unknown { background: #f3f4f6; color: #6b7280; }

/* Pagination */
.pagination {
  display: flex; justify-content: center; align-items: center; gap: 1rem;
  margin-top: 1.25rem; padding: 0.75rem;
}
.pagination button {
  padding: 0.5rem 1.2rem; border: 1px solid #d1d5db; border-radius: 6px;
  background: white; color: #374151; font-size: 0.85rem; font-weight: 500;
  cursor: pointer; transition: all 0.15s;
}
.pagination button:hover:not(:disabled) { background: #3b82f6; color: white; border-color: #3b82f6; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 0.9rem; color: #64748b; font-weight: 500; }

/* Brand cards */
.brand-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }
.brand-card {
  background: white; border-radius: 10px; padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08); transition: transform 0.15s, box-shadow 0.15s;
}
.brand-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }
.card-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem; line-height: 1.4; }
.card-meta { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
.card-price { font-weight: 700; color: #059669; font-size: 1.05rem; }
.card-cat {
  font-size: 0.75rem; background: #eff6ff; color: #3b82f6;
  padding: 0.2rem 0.6rem; border-radius: 12px;
  max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* Widget grid (Analysis) */
.widget-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.25rem; margin-top: 1.5rem;
}
.widget-card {
  background: white; border-radius: 12px; padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.widget-card.full-width { grid-column: 1 / -1; }
.widget-card h3 { font-size: 0.95rem; color: #1e293b; margin-bottom: 1rem; font-weight: 600; }
.widget-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;
}
.widget-header h3 { margin-bottom: 0; }

/* Responsive */
@media (max-width: 768px) {
  .widget-grid { grid-template-columns: 1fr; }
  .controls { flex-direction: column; gap: 0.75rem; align-items: stretch; }
  .search-box { max-width: 100%; }
  .filter-group select { max-width: 100%; }
  .toggle-group { justify-content: center; }
}
"""

with open(os.path.join(BASE_DIR, "src", "App.css"), "w") as f:
    f.write(app_css)

print("✅ Written: src/App.css (search box + toggle styles)")

# COMMAND ----------

# DBTITLE 1,Write app.py (Flask backend)
app_py = '''import os
import logging
from flask import Flask, jsonify, request, send_from_directory
from databricks.sdk import WorkspaceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="dist", static_url_path="")

WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")
TABLE = "pp_demo.datasets.amazon_best_seller_products"

if not WAREHOUSE_ID or WAREHOUSE_ID == "your-warehouse-id-here":
    logger.warning("DATABRICKS_WAREHOUSE_ID is not configured!")


def execute_sql(statement):
    if not WAREHOUSE_ID or WAREHOUSE_ID == "your-warehouse-id-here":
        raise ValueError("DATABRICKS_WAREHOUSE_ID is not configured.")
    w = WorkspaceClient()
    logger.info(f"SQL: {statement[:200]}")
    response = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID, statement=statement, wait_timeout="50s"
    )
    if response.status and response.status.error:
        raise RuntimeError(f"SQL error: {response.status.error.message}")
    columns = [col.name for col in response.manifest.schema.columns]
    rows = []
    if response.result and response.result.data_array:
        for row in response.result.data_array:
            rows.append(dict(zip(columns, row)))
    return rows


def safe_sql_string(value):
    return value.replace("\'", "\'\'")


# -- Products (paginated, searchable, availability filter) ---------------

@app.route("/api/products")
def get_products():
    try:
        search = request.args.get("search", "").strip()
        availability = request.args.get("availability", "")  # in_stock, out_of_stock, or empty
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 10))))
        offset = (page - 1) * per_page

        conditions = []
        if search:
            conditions.append(f"LOWER(TITLE) LIKE \'%{safe_sql_string(search.lower())}%\'")
        if availability == "in_stock":
            conditions.append("LOWER(AVAILABILITY) LIKE \'%in stock%\'")
        elif availability == "out_of_stock":
            conditions.append("(LOWER(AVAILABILITY) LIKE \'%out of stock%\' OR LOWER(AVAILABILITY) LIKE \'%unavail%\')")

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        count_rows = execute_sql(f"SELECT COUNT(DISTINCT TITLE) AS cnt FROM {TABLE} {where}")
        total = int(count_rows[0]["cnt"]) if count_rows else 0

        query = (
            f"SELECT DISTINCT TITLE, FINAL_PRICE, CURRENCY, AVAILABILITY "
            f"FROM {TABLE} {where} ORDER BY TITLE LIMIT {per_page} OFFSET {offset}"
        )
        return jsonify({"products": execute_sql(query), "total": total, "page": page, "per_page": per_page})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# -- Brands -------------------------------------------------------------

@app.route("/api/brands")
def get_brands():
    try:
        rows = execute_sql(
            f"SELECT DISTINCT BRAND FROM {TABLE} WHERE BRAND IS NOT NULL ORDER BY BRAND"
        )
        return jsonify([r["BRAND"] for r in rows])
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/brands-with-prices")
def get_brands_with_prices():
    try:
        rows = execute_sql(
            f"SELECT DISTINCT BRAND FROM {TABLE} "
            f"WHERE BRAND IS NOT NULL AND FINAL_PRICE IS NOT NULL "
            f"AND INITIAL_PRICE IS NOT NULL "
            f"AND REGEXP_REPLACE(INITIAL_PRICE, \'[^0-9.]+\', \'\') != \'\' "
            f"ORDER BY BRAND"
        )
        return jsonify([r["BRAND"] for r in rows])
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/products/by-brand")
def get_products_by_brand():
    try:
        brand = request.args.get("brand", "")
        if not brand:
            return jsonify({"error": "brand parameter is required"}), 400
        query = (
            f"SELECT DISTINCT TITLE, BRAND, FINAL_PRICE, CURRENCY, "
            f"AVAILABILITY, CATEGORIES FROM {TABLE} "
            f"WHERE BRAND = \'{safe_sql_string(brand)}\' ORDER BY TITLE LIMIT 500"
        )
        return jsonify(execute_sql(query))
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# -- Analysis -----------------------------------------------------------

@app.route("/api/analysis")
def get_analysis():
    try:
        brand = request.args.get("brand", "")
        where = f"WHERE BRAND = \'{safe_sql_string(brand)}\'" if brand else ""
        query = (
            f"SELECT DISTINCT TITLE, "
            f"CAST(REGEXP_REPLACE(INITIAL_PRICE, \'[^0-9.]+\', \'\') AS DOUBLE) AS INITIAL_PRICE, "
            f"CAST(FINAL_PRICE AS DOUBLE) AS FINAL_PRICE "
            f"FROM {TABLE} {where} ORDER BY TITLE LIMIT 50"
        )
        rows = execute_sql(query)
        clean = [r for r in rows if r.get("INITIAL_PRICE") and r.get("FINAL_PRICE")]
        return jsonify(clean)
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analysis/insights")
def get_insights():
    try:
        result = {}

        # 1. Top 10 most discounted
        result["topDiscounted"] = execute_sql(
            f"SELECT DISTINCT TITLE, "
            f"CAST(REGEXP_REPLACE(INITIAL_PRICE, \'[^0-9.]+\', \'\') AS DOUBLE) AS INITIAL_PRICE, "
            f"CAST(FINAL_PRICE AS DOUBLE) AS FINAL_PRICE, "
            f"CAST(REGEXP_REPLACE(INITIAL_PRICE, \'[^0-9.]+\', \'\') AS DOUBLE) - CAST(FINAL_PRICE AS DOUBLE) AS SAVINGS "
            f"FROM {TABLE} "
            f"WHERE INITIAL_PRICE IS NOT NULL AND FINAL_PRICE IS NOT NULL "
            f"AND REGEXP_REPLACE(INITIAL_PRICE, \'[^0-9.]+\', \'\') != \'\' "
            f"AND CAST(REGEXP_REPLACE(INITIAL_PRICE, \'[^0-9.]+\', \'\') AS DOUBLE) > CAST(FINAL_PRICE AS DOUBLE) "
            f"ORDER BY SAVINGS DESC LIMIT 10"
        )

        # 2. Avg price by brand (top 15)
        result["avgByBrand"] = execute_sql(
            f"SELECT BRAND, "
            f"ROUND(AVG(CAST(FINAL_PRICE AS DOUBLE)), 2) AS AVG_PRICE, "
            f"COUNT(DISTINCT TITLE) AS PRODUCT_COUNT "
            f"FROM {TABLE} WHERE BRAND IS NOT NULL AND FINAL_PRICE IS NOT NULL "
            f"GROUP BY BRAND ORDER BY AVG_PRICE DESC LIMIT 15"
        )

        # 3. Price distribution
        result["priceDistribution"] = execute_sql(
            f"SELECT "
            f"CASE "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 25 THEN \'$0-25\' "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 50 THEN \'$25-50\' "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 100 THEN \'$50-100\' "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 250 THEN \'$100-250\' "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 500 THEN \'$250-500\' "
            f"  ELSE \'$500+\' "
            f"END AS PRICE_RANGE, "
            f"COUNT(DISTINCT TITLE) AS CNT "
            f"FROM {TABLE} WHERE FINAL_PRICE IS NOT NULL "
            f"GROUP BY 1 ORDER BY MIN(CAST(FINAL_PRICE AS DOUBLE))"
        )

        # 4. Availability breakdown
        result["availability"] = execute_sql(
            f"SELECT "
            f"CASE "
            f"  WHEN LOWER(AVAILABILITY) LIKE \'%in stock%\' THEN \'In Stock\' "
            f"  WHEN LOWER(AVAILABILITY) LIKE \'%out of stock%\' OR LOWER(AVAILABILITY) LIKE \'%unavail%\' THEN \'Out of Stock\' "
            f"  WHEN AVAILABILITY IS NULL OR AVAILABILITY = \'\' THEN \'Unknown\' "
            f"  ELSE \'Limited\' "
            f"END AS STATUS, "
            f"COUNT(DISTINCT TITLE) AS CNT "
            f"FROM {TABLE} GROUP BY 1"
        )

        # 5. Top rated products
        result["topRated"] = execute_sql(
            f"SELECT DISTINCT TITLE, BRAND, "
            f"CAST(RATING AS DOUBLE) AS RATING, "
            f"CAST(REVIEWS_COUNT AS INT) AS REVIEWS "
            f"FROM {TABLE} "
            f"WHERE RATING IS NOT NULL AND REVIEWS_COUNT IS NOT NULL "
            f"AND CAST(REVIEWS_COUNT AS INT) >= 10 "
            f"ORDER BY RATING DESC, REVIEWS DESC LIMIT 10"
        )

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# -- Static file serving ------------------------------------------------

@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_proxy(path):
    try:
        return send_from_directory(app.static_folder, path)
    except Exception:
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
'''

with open(os.path.join(BASE_DIR, "app.py"), "w") as f:
    f.write(app_py)

print("✅ Written: app.py (search + availability filter on products)")

# COMMAND ----------

# DBTITLE 1,Deployment Instructions
# MAGIC %md
# MAGIC ## Deployment Instructions
# MAGIC
# MAGIC All app files have been generated at:  
# MAGIC `/Workspace/Users/praveen.ponna@databricks.com/amazon-products-app/`
# MAGIC
# MAGIC ### Steps to Deploy
# MAGIC
# MAGIC 1. **Get your SQL Warehouse ID**  
# MAGIC    Go to **SQL Warehouses** in the sidebar → click your warehouse → copy the **ID** from the URL or connection details.
# MAGIC
# MAGIC 2. **Update `app.yaml`**  
# MAGIC    Replace `your-warehouse-id-here` with your actual SQL warehouse ID in the generated `app.yaml` file.
# MAGIC
# MAGIC 3. **Create the Databricks App**  
# MAGIC    * Go to sidebar → **Compute** → **Apps** → **Create App**
# MAGIC    * Name: `amazon-products-app`
# MAGIC    * Source path: `/Workspace/Users/praveen.ponna@databricks.com/amazon-products-app`
# MAGIC
# MAGIC 4. **Add SQL Warehouse Resource**  
# MAGIC    In the app configuration, add a **SQL Warehouse** resource with **Can use** permission.
# MAGIC
# MAGIC 5. **Grant Table Access**  
# MAGIC    Ensure the app's service principal has `SELECT` access to `pp_demo.datasets.amazon_best_seller_products`.
# MAGIC
# MAGIC 6. **Deploy** — Click **Deploy** and wait for the build to complete.
# MAGIC
# MAGIC ### How It Works
# MAGIC * During deployment, Databricks detects `package.json` and runs `npm install` + `npm run build` (Vite builds React into `dist/`)
# MAGIC * Then `pip install -r requirements.txt` installs Flask + Databricks SDK
# MAGIC * Finally, `python app.py` starts the Flask server which serves the React build and API endpoints
# MAGIC
# MAGIC ### File Structure
# MAGIC ```
# MAGIC amazon-products-app/
# MAGIC ├── app.yaml              # App config (start command + env vars)
# MAGIC ├── app.py                # Flask backend (API + static file serving)
# MAGIC ├── requirements.txt      # Python dependencies
# MAGIC ├── package.json          # Node.js dependencies (React + Vite)
# MAGIC ├── vite.config.js        # Vite build configuration
# MAGIC ├── index.html            # Vite entry HTML
# MAGIC └── src/
# MAGIC     ├── main.jsx          # React entry point
# MAGIC     ├── App.jsx           # Main React component (table + filter)
# MAGIC     └── App.css           # Styles
# MAGIC ```