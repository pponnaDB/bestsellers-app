import os
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
    return value.replace("'", "''")


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
            conditions.append(f"LOWER(TITLE) LIKE '%{safe_sql_string(search.lower())}%'")
        if availability == "in_stock":
            conditions.append("LOWER(AVAILABILITY) LIKE '%in stock%'")
        elif availability == "out_of_stock":
            conditions.append("(LOWER(AVAILABILITY) LIKE '%out of stock%' OR LOWER(AVAILABILITY) LIKE '%unavail%')")

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
            f"AND REGEXP_REPLACE(INITIAL_PRICE, '[^0-9.]+', '') != '' "
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
            f"WHERE BRAND = '{safe_sql_string(brand)}' ORDER BY TITLE LIMIT 500"
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
        where = f"WHERE BRAND = '{safe_sql_string(brand)}'" if brand else ""
        query = (
            f"SELECT DISTINCT TITLE, "
            f"CAST(REGEXP_REPLACE(INITIAL_PRICE, '[^0-9.]+', '') AS DOUBLE) AS INITIAL_PRICE, "
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
            f"CAST(REGEXP_REPLACE(INITIAL_PRICE, '[^0-9.]+', '') AS DOUBLE) AS INITIAL_PRICE, "
            f"CAST(FINAL_PRICE AS DOUBLE) AS FINAL_PRICE, "
            f"CAST(REGEXP_REPLACE(INITIAL_PRICE, '[^0-9.]+', '') AS DOUBLE) - CAST(FINAL_PRICE AS DOUBLE) AS SAVINGS "
            f"FROM {TABLE} "
            f"WHERE INITIAL_PRICE IS NOT NULL AND FINAL_PRICE IS NOT NULL "
            f"AND REGEXP_REPLACE(INITIAL_PRICE, '[^0-9.]+', '') != '' "
            f"AND CAST(REGEXP_REPLACE(INITIAL_PRICE, '[^0-9.]+', '') AS DOUBLE) > CAST(FINAL_PRICE AS DOUBLE) "
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
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 25 THEN '$0-25' "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 50 THEN '$25-50' "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 100 THEN '$50-100' "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 250 THEN '$100-250' "
            f"  WHEN CAST(FINAL_PRICE AS DOUBLE) < 500 THEN '$250-500' "
            f"  ELSE '$500+' "
            f"END AS PRICE_RANGE, "
            f"COUNT(DISTINCT TITLE) AS CNT "
            f"FROM {TABLE} WHERE FINAL_PRICE IS NOT NULL "
            f"GROUP BY 1 ORDER BY MIN(CAST(FINAL_PRICE AS DOUBLE))"
        )

        # 4. Availability breakdown
        result["availability"] = execute_sql(
            f"SELECT "
            f"CASE "
            f"  WHEN LOWER(AVAILABILITY) LIKE '%in stock%' THEN 'In Stock' "
            f"  WHEN LOWER(AVAILABILITY) LIKE '%out of stock%' OR LOWER(AVAILABILITY) LIKE '%unavail%' THEN 'Out of Stock' "
            f"  WHEN AVAILABILITY IS NULL OR AVAILABILITY = '' THEN 'Unknown' "
            f"  ELSE 'Limited' "
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
