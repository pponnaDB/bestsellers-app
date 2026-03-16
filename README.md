# Databricks React App Demo
## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Build & Deploy Pipeline](#build--deploy-pipeline)
3. [Runtime Stack](#runtime-stack)
4. [API Endpoints](#api-endpoints)
5. [Frontend SPA Routing](#frontend-spa-routing)
6. [Auth & Permissions Chain](#auth--permissions-chain)
7. [Key Design Decisions](#key-design-decisions)
8. [File Structure](#file-structure)
9. [New Workspace Deployment Prerequisites](#new-workspace-deployment-prerequisites)
10. [Deployment Sequence](#deployment-sequence)

---

## Architecture Overview

The Amazon Best Seller Products app is a **single-page application (SPA)** deployed as a **Databricks App**. It consists of a React 18 frontend (built with Vite) and a Flask backend, both served from a single Python process. The app queries product data from a Unity Catalog managed table via the Databricks SDK's Statement Execution API.

---

## Build & Deploy Pipeline

A setup notebook generates **8 source files** into a workspace directory. On deployment, the Databricks Apps platform:

1. Detects `package.json` → runs `npm install` + `npm run build` (Vite compiles React + Recharts into `dist/`)
2. Detects `requirements.txt` → runs `pip install flask databricks-sdk`
3. Reads `app.yaml` → starts `python app.py` on **port 8000**

---

## Runtime Stack

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend | React 18 + Vite + Recharts | SPA with 3 tabs, served as static files from `dist/` |
| Backend | Flask (`app.py`) | REST API + static file server on port 8000 |
| Data Access | Databricks SDK `execute_statement()` | SQL via SQL Warehouse (50s timeout) |
| Data Source | `pp_demo.datasets.amazon_best_seller_products` | Unity Catalog managed table (25 columns) |
| Auth | Databricks App Service Principal | Auto-created, requires explicit grants |

---

## API Endpoints

The Flask backend exposes **7 REST endpoints**:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/products?page=&per_page=&category=` | GET | Paginated products (2 SQL calls: COUNT + SELECT with OFFSET) |
| `/api/categories` | GET | Distinct category values for filter dropdown |
| `/api/brands` | GET | All distinct brand names |
| `/api/brands-with-prices` | GET | Brands with valid parseable INITIAL_PRICE and FINAL_PRICE |
| `/api/products/by-brand?brand=` | GET | Products filtered by brand name |
| `/api/analysis?brand=` | GET | Per-product initial vs final price (REGEXP_REPLACE to parse string prices) |
| `/api/analysis/insights` | GET | 5 SQL queries in one call: top discounted, avg price by brand, price distribution, availability breakdown, top rated |

---

## Frontend SPA Routing

The app uses **state-based tab switching** (no router library). Three independent React components manage their own fetch lifecycles:

### 📦 Products Tab
- Paginated table (10 products per page) with Prev/Next navigation
- Category filter dropdown (names truncated to 50 characters, full name on hover)
- Displays title, brand, final price, and availability badge

### 🏷️ Brands Tab
- Brand dropdown selector (defaults to "Amazon Essentials" on load)
- Card grid layout showing each product's title, price, category, and availability

### 📊 Analysis Tab
- **Price Comparison chart** — Grouped bar chart (Initial Price vs Final Price), filterable by brand
- **Top 10 Biggest Savings** — Horizontal bar chart of products with largest price drops
- **Average Price by Brand (Top 15)** — Horizontal bar chart
- **Price Distribution** — Color-coded bar chart by price range ($0-25, $25-50, etc.)
- **Availability Breakdown** — Pie chart with percentage labels
- **Top Rated Products (10+ Reviews)** — Dual-axis bar chart (Rating + Review count)

The Analysis tab fires 3 fetches on mount: `brands-with-prices`, `insights` (global data), and the main chart data (filtered by brand).

---

## Auth & Permissions Chain

```
Databricks App
  └── Service Principal (auto-created, e.g., "app-xxxxx <app-name>")
        ├── CAN_USE on SQL Warehouse (configured as app resource)
        ├── USE CATALOG on pp_demo
        ├── USE SCHEMA on pp_demo.datasets
        └── SELECT on pp_demo.datasets.amazon_best_seller_products
```

The `WorkspaceClient()` in `app.py` authenticates automatically using the app's service principal credentials. The warehouse ID is injected via the `DATABRICKS_WAREHOUSE_ID` environment variable in `app.yaml`.

---

## Key Design Decisions

- **Category display**: Truncated to 50 characters (full breadcrumb path available on hover via `title` attribute)
- **INITIAL_PRICE parsing**: Column is STRING type — parsed server-side with `REGEXP_REPLACE('[^0-9.]+', '')` before casting to DOUBLE
- **Insights endpoint**: Batches 5 SQL queries sequentially in one API call to minimize browser round-trips
- **Pagination**: Server-side with `LIMIT/OFFSET` and a separate `COUNT(DISTINCT)` query for total
- **SQL injection mitigation**: `safe_sql_string()` escapes single quotes
- **Statement execution**: `wait_timeout="50s"` (max allowed by the API)
- **Single-process Flask**: No async workers; suitable for demo/internal use

---

## File Structure

```
amazon-products-app/
├── app.yaml              # App config (start command + env vars)
├── app.py                # Flask backend (7 API endpoints + static serving)
├── requirements.txt      # Python: flask==3.1.1, databricks-sdk==0.44.0
├── package.json          # Node: react, react-dom, recharts, vite
├── vite.config.js        # Vite build config with dev proxy
├── index.html            # Vite entry HTML
└── src/
    ├── main.jsx          # React entry point
    ├── App.jsx           # 3 tab components + main App shell
    └── App.css           # Full SPA styles (nav, tables, cards, charts, widgets)
```

---

## New Workspace Deployment Prerequisites

This section covers everything needed to deploy this app on a **new Databricks workspace in a different AWS account**, assuming the table `pp_demo.datasets.amazon_best_seller_products` already exists.

### 1. Workspace Features

| Requirement | Detail |
| --- | --- |
| Databricks Apps enabled | Must be enabled at workspace level (Premium or Enterprise tier) |
| Unity Catalog enabled | Workspace must be attached to a UC metastore |
| Serverless compute | Required for Databricks Apps runtime |

### 2. Compute — SQL Warehouse

| Requirement | Detail |
| --- | --- |
| SQL Warehouse provisioned | Serverless or Pro recommended; Classic works but Serverless is faster for cold starts |
| Warehouse ID | Copy the ID and update the `app.yaml` cell — replace the existing warehouse ID |
| Auto-stop | Recommend ≤ 10 min for cost control |

### 3. Unity Catalog — Data Access

| Requirement | Detail |
| --- | --- |
| Catalog `pp_demo` | Must exist in the target metastore |
| Schema `pp_demo.datasets` | Must exist under the catalog |
| Table `pp_demo.datasets.amazon_best_seller_products` | Must exist with the same 25-column schema (TITLE, BRAND, FINAL_PRICE, INITIAL_PRICE, RATING, REVIEWS_COUNT, CATEGORIES, AVAILABILITY, CURRENCY, etc.) |

### 4. Databricks App & Service Principal

| Requirement | Detail |
| --- | --- |
| Create the App | Compute → Apps → Create App; set source path to the generated folder |
| SQL Warehouse resource | In the app config, add the warehouse as a resource with **CAN_USE** permission |
| Service principal (auto-created) | Databricks creates one automatically (e.g., `app-xxxxx <app-name>`) |
| `GRANT USE CATALOG ON CATALOG pp_demo` | Grant to the app's service principal |
| `GRANT USE SCHEMA ON SCHEMA pp_demo.datasets` | Grant to the app's service principal |
| `GRANT SELECT ON TABLE pp_demo.datasets.amazon_best_seller_products` | Grant to the app's service principal |

> **Important**: All three grants are required — missing any one will cause silent API failures.

### 5. Network & Security

| Requirement | Detail |
| --- | --- |
| Outbound HTTPS (443) | The app container must reach the workspace control plane (Databricks SDK uses workspace URL) |
| No VPN/IP allowlist conflicts | If the workspace has an IP access list, the app's internal IPs are within the control plane — typically no issue |
| Private Link (if applicable) | If the workspace uses AWS PrivateLink, ensure the Apps compute plane can route to the workspace API endpoint |
| No public internet needed at runtime | The app only talks to the Databricks workspace API (npm/PyPI calls happen only during build) |

### 6. IAM — Cloud Provider (AWS)

| Requirement | Detail |
| --- | --- |
| Databricks workspace IAM role | Must permit Apps service (no extra AWS IAM configuration for standard deployments) |
| S3 access for UC | The metastore's managed storage location must be accessible (standard UC setup) |
| No custom STS/VPC endpoint restrictions | If the VPC has restrictive endpoints, ensure `*.databricks.com` and the workspace API are reachable |

### 7. Code Changes Before Deployment

| File / Cell | Change |
| --- | --- |
| Cell 2 — `BASE_DIR` | Update the workspace path to the new user's home directory |
| Cell 3 — `app.yaml` | Replace the warehouse ID with the new workspace's SQL warehouse ID |
| Cell 11 — `app.py` `TABLE` constant | Already set to `pp_demo.datasets.amazon_best_seller_products` — no change needed if table name matches |

### 8. Quotas & Limits to Verify

| Limit | Default |
| --- | --- |
| Max apps per workspace | 10 (can be increased via support ticket; FE shared workspaces have 50) |
| Statement execution timeout | Max 50s per query (hard API limit) |
| SQL warehouse concurrency | Ensure enough capacity for 5+ concurrent queries (the insights endpoint fires 5 sequential queries) |

---

## Deployment Sequence

1. **Clone or copy** the setup notebook to the new workspace
2. **Update** `BASE_DIR` (cell 2) to the new user's workspace path
3. **Update** `app.yaml` (cell 3) with the new SQL warehouse ID
4. **Run all cells** (1–12) to generate the app files
5. **Create the app** in Compute → Apps; set the source path to the generated folder
6. **Attach the SQL Warehouse** as a resource with CAN_USE permission
7. **Note the auto-created service principal** name from the app's resource page
8. **Run the 3 GRANT statements**:
   ```sql
   GRANT USE CATALOG ON CATALOG pp_demo TO `<service-principal-name>`;
   GRANT USE SCHEMA ON SCHEMA pp_demo.datasets TO `<service-principal-name>`;
   GRANT SELECT ON TABLE pp_demo.datasets.amazon_best_seller_products TO `<service-principal-name>`;
   ```
9. **Deploy** — the platform handles `npm install`, `vite build`, `pip install`, and `python app.py`
10. **Verify** at the generated app URL

