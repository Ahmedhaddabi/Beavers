import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################
#
# Beaver's Choice Paper Company - multi-agent quoting, inventory and sales system
# Framework: smolagents (ToolCallingAgent with managed agents)
#
# Agents (5 in total, see agent_workflow_diagram.png and reflection_report.md):
#   1. Orchestrator agent     - customer-facing; delegates to the workers and writes the reply
#   2. Inventory agent        - catalog matching, stock checks, supplier lead times, restocking
#   3. Quoting agent          - quote history research and bulk-discount pricing
#   4. Sales agent            - pre-sale financial health check and order finalization
#   5. Business advisor agent - reviews all transactions after the run and recommends changes
#
# Design principle: the LLM agents decide WHAT to do, while the tools hold the business
# rules and the numbers. Agents pass short reference IDs (assessment, quote) between each
# other instead of re-typing quantities and prices, so figures cannot drift between agents.

import json
import math
import re
import sys

from smolagents import OpenAIServerModel, ToolCallingAgent, tool
from smolagents.monitoring import LogLevel


# ---------------------------------------------------------------------------
# 1. Environment, model and business rules
# ---------------------------------------------------------------------------

dotenv.load_dotenv()

OPENAI_API_BASE = "https://openai.vocareum.com/v1"
MODEL_ID = os.getenv("BEAVER_MODEL_ID", "gpt-4o-mini")
AGENT_VERBOSITY = int(os.getenv("AGENT_VERBOSITY", "0"))  # 0 quiet, 1 info, 2 debug

SHEETS_PER_REAM = 500            # reams/boxes are converted to sheets before pricing
SUPPLIER_COST_RATIO = 0.60       # internal only: supplier charges 60% of our list price
MIN_CASH_RESERVE = 2000.0        # internal only: restocking never drops cash below this
REORDER_TARGET_MULTIPLIER = 2    # stocked items are replenished up to 2x their minimum level
FROM_STOCK_DELIVERY_DAYS = 1     # in-stock items reach the customer the next day
DEFAULT_DEADLINE_DAYS = 14       # assumed deadline when a request gives no date
LARGE_ORDER_THRESHOLD = 1000.0   # quotes above this value get a financial health check

# Bulk discount tiers on the total number of units in an order: (minimum units, rate).
# Every order qualifies for at least the base tier, so each quote carries a bulk discount.
BULK_DISCOUNT_TIERS = [
    (10000, 0.15),
    (2000, 0.10),
    (500, 0.05),
    (1, 0.03),
]
MAX_PROMOTIONAL_DISCOUNT_PCT = 3.0  # extra discount the quoting agent may add strategically

CATALOG: Dict[str, Dict] = {item["item_name"]: item for item in paper_supplies}


def build_model() -> OpenAIServerModel:
    """Create the OpenAI-compatible model client that every agent shares."""
    api_key = os.getenv("UDACITY_OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("UDACITY_OPENAI_API_KEY is not set. Add it to your .env file.")
    return OpenAIServerModel(
        model_id=MODEL_ID,
        api_base=OPENAI_API_BASE,
        api_key=api_key,
        temperature=0.0,
    )


# ---------------------------------------------------------------------------
# 2. Shared utilities: progress display, dates, catalog matching, stock lookups
# ---------------------------------------------------------------------------

STAGE_COLORS = {
    "Orchestr": "\033[95m",
    "Inventory": "\033[94m",
    "Quoting": "\033[93m",
    "Sales": "\033[92m",
    "Advisor": "\033[96m",
}


def announce(stage: str, message: str) -> None:
    """Print a one-line progress update so the operator can follow each agent's work."""
    color = STAGE_COLORS.get(stage, "") if sys.stdout.isatty() else ""
    reset = "\033[0m" if color else ""
    print(f"   {color}[{stage:<9}]{reset} {message}", flush=True)


def to_iso_date(value: Union[str, datetime]) -> str:
    """Normalize a date (ISO string, natural-language string or datetime) to YYYY-MM-DD."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    text_value = str(value).strip()
    try:
        return datetime.fromisoformat(text_value[:10]).strftime("%Y-%m-%d")
    except ValueError:
        return pd.to_datetime(text_value).strftime("%Y-%m-%d")


def add_days(iso_date: str, days: int) -> str:
    """Return the ISO date that is `days` days after `iso_date`."""
    return (datetime.fromisoformat(iso_date) + timedelta(days=days)).strftime("%Y-%m-%d")


# Words that identify products the company does not sell at all.
NOT_CARRIED_KEYWORDS = ("balloon", "ticket", "cardboard", "packaging tape", "masking tape")

# Ordered keyword rules mapping customer wording to exact catalog names.
# Each rule is (any of these keywords, all of these keywords, catalog item name).
# More specific rules come first (e.g. "glossy photo paper" must become Photo paper).
CATALOG_MATCH_RULES: List[tuple] = [
    (("washi", "adhesive tape", "decorative tape"), (), "Decorative adhesive tape (washi tape)"),
    (("streamer",), (), "Party streamers"),
    (("napkin",), (), "Paper napkins"),
    (("plate",), (), "Paper plates"),
    (("disposable cup",), (), "Disposable cups"),
    (("cup",), (), "Paper cups"),
    (("table cover", "tablecloth"), (), "Table covers"),
    (("envelope",), (), "Envelopes"),
    (("sticky note", "post-it"), (), "Sticky notes"),
    (("notepad", "note pad"), (), "Notepads"),
    (("invitation card",), (), "Invitation cards"),
    (("flyer", "flier"), (), "Flyers"),
    (("party bag",), (), "Paper party bags"),
    (("name tag", "lanyard"), (), "Name tags with lanyards"),
    (("folder",), (), "Presentation folders"),
    (("100 lb", "100lb"), (), "100 lb cover stock"),
    (("80 lb", "80lb"), (), "80 lb text paper"),
    (("250 gsm", "250gsm"), (), "250 gsm cardstock"),
    (("220 gsm", "220gsm"), ("poster",), "220 gsm poster paper"),
    (("banner",), ("roll",), "Rolls of banner paper (36-inch width)"),
    (("banner",), (), "Banner paper"),
    (("24x36", '24" x 36', "24 x 36", "poster board", "large poster"), (), "Large poster paper (24x36 inches)"),
    (("poster",), (), "Poster paper"),
    (("cardstock", "card stock"), (), "Cardstock"),
    (("photo",), (), "Photo paper"),
    (("glossy", "gloss"), (), "Glossy paper"),
    (("matte",), (), "Matte paper"),
    (("recycled",), (), "Recycled paper"),
    (("eco-friendly", "eco friendly", "environmentally friendly"), (), "Eco-friendly paper"),
    (("kraft",), (), "Kraft paper"),
    (("construction",), (), "Construction paper"),
    (("wrapping",), (), "Wrapping paper"),
    (("glitter",), (), "Glitter paper"),
    (("letterhead",), (), "Letterhead paper"),
    (("legal",), (), "Legal-size paper"),
    (("crepe",), (), "Crepe paper"),
    (("uncoated",), (), "Uncoated paper"),
    (("butcher",), (), "Butcher paper"),
    (("heavyweight", "heavy-weight", "heavy weight"), (), "Heavyweight paper"),
    (("bright-colored", "bright colored"), (), "Bright-colored paper"),
    (("patterned",), (), "Patterned paper"),
    (("decorative paper",), (), "Decorative paper"),
    (("colored", "coloured", "colorful", "colourful", "assorted color"), (), "Colored paper"),
    (("letter-size", "letter size", "letter-sized", "8.5x11", '8.5"x11', "8.5 x 11"), (), "Letter-sized paper"),
    (("a4",), (), "A4 paper"),
    (("copy", "copier", "printer", "printing", "multi-purpose", "plain", "white paper", "bond"), (), "Standard copy paper"),
]


def match_catalog_item(description: str) -> Union[str, None]:
    """
    Map a customer's wording for a product to the exact catalog item name.

    Exact catalog names match first; otherwise ordered keyword rules are applied.
    Returns None when the product is not something the company sells.
    """
    text_lower = (description or "").lower().strip()
    if not text_lower:
        return None
    for catalog_name in CATALOG:
        if catalog_name.lower() == text_lower:
            return catalog_name
    if any(keyword in text_lower for keyword in NOT_CARRIED_KEYWORDS):
        return None
    for any_of, all_of, catalog_name in CATALOG_MATCH_RULES:
        if any(k in text_lower for k in any_of) and all(k in text_lower for k in all_of):
            return catalog_name
    return None


def current_stock(item_name: str, as_of_date: str) -> int:
    """Return the net units on hand for one item as of a date (wraps get_stock_level)."""
    stock_df = get_stock_level(item_name, as_of_date)
    if stock_df.empty:
        return 0
    value = stock_df["current_stock"].iloc[0]
    return int(value) if pd.notna(value) else 0


def min_stock_level(item_name: str) -> int:
    """Return the reorder point for a regularly stocked item, or 0 for special-order items."""
    policy_df = pd.read_sql(
        "SELECT min_stock_level FROM inventory WHERE item_name = :item_name",
        db_engine,
        params={"item_name": item_name},
    )
    return int(policy_df["min_stock_level"].iloc[0]) if not policy_df.empty else 0


def supplier_unit_cost(item_name: str) -> float:
    """Internal supplier cost per unit. Never shown to customers."""
    return CATALOG[item_name]["unit_price"] * SUPPLIER_COST_RATIO


def parse_quantity(raw_quantity) -> int:
    """Convert '10,000', 500.0 or '200' to an integer unit count (0 when unreadable)."""
    try:
        return int(float(str(raw_quantity).replace(",", "").strip()))
    except (TypeError, ValueError):
        return 0


def parse_items_payload(items_json) -> List[Dict]:
    """Accept the requested items either as a JSON string or as an already-parsed list."""
    if isinstance(items_json, list):
        return items_json
    parsed = json.loads(items_json)
    return parsed if isinstance(parsed, list) else [parsed]


# ---------------------------------------------------------------------------
# 3. Order workspace: shared state the tools use to hand work between agents
# ---------------------------------------------------------------------------

class OrderWorkspace:
    """
    In-memory record of the availability assessments, quotes and orders created in a run.

    The inventory agent creates an assessment, the quoting agent prices it into a quote,
    and the sales agent finalizes that quote. Each step refers to the previous one by ID.
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Clear all records (called at the start of each test run)."""
        self.assessments: Dict[str, Dict] = {}
        self.quotes: Dict[str, Dict] = {}
        self.orders: Dict[str, Dict] = {}
        self.purchases: List[Dict] = []
        self.id_counters: Dict[str, int] = {}
        self.current_request_key: Union[str, None] = None

    def next_id(self, prefix: str) -> str:
        """Generate a short sequential reference such as Q-0007."""
        self.id_counters[prefix] = self.id_counters.get(prefix, 0) + 1
        return f"{prefix}-{self.id_counters[prefix]:04d}"

    def ids_for_current_request(self) -> str:
        """Describe the assessment and quote IDs that belong to the request being handled."""
        key = self.current_request_key
        assessment_ids = [a_id for a_id, a in self.assessments.items() if a["request_key"] == key]
        quote_ids = [q_id for q_id, q in self.quotes.items() if q["request_key"] == key]
        return (f"IDs for the current request - assessments: {', '.join(assessment_ids) or 'none yet'}; "
                f"quotes: {', '.join(quote_ids) or 'none yet'}.")

    def outcome_for_request(self, request_key: str) -> Dict:
        """Summarize what happened to one customer request, for test_results.csv."""
        orders = [o for o in self.orders.values() if o["request_key"] == request_key]
        assessments = [a for a in self.assessments.values() if a["request_key"] == request_key]
        latest_assessment = assessments[-1] if assessments else None

        def unavailable_items(assessment):
            if not assessment:
                return ""
            return "; ".join(
                f"{line['description']} ({line['customer_note']})"
                for line in assessment["lines"] if line["status"] == "unavailable"
            )

        if orders:
            order = orders[-1]
            return {
                "order_status": order["status"],
                "fulfilled_items": "; ".join(f"{l['catalog_item']} x{l['quantity']}" for l in order["lines"]),
                "unfulfilled_items": unavailable_items(latest_assessment),
                "order_total": order["total"],
            }
        if latest_assessment and not any(l["status"] != "unavailable" for l in latest_assessment["lines"]):
            status = "rejected"
        elif latest_assessment:
            status = "not_finalized"
        else:
            status = "not_processed"
        return {
            "order_status": status,
            "fulfilled_items": "",
            "unfulfilled_items": unavailable_items(latest_assessment),
            "order_total": 0.0,
        }


WORKSPACE = OrderWorkspace()


# ---------------------------------------------------------------------------
# 4. Business logic used by the tools
# ---------------------------------------------------------------------------

def consolidate_requested_items(requested_items: List[Dict]) -> List[Dict]:
    """
    Resolve each requested line to a catalog item and convert reams/boxes to sheets.
    Lines that resolve to the same catalog item are merged so stock is checked once.
    """
    merged: Dict[str, Dict] = {}
    lines: List[Dict] = []
    for raw in requested_items:
        description = str(raw.get("description") or raw.get("item") or "").strip()
        unit = str(raw.get("unit") or "").lower()
        quantity = parse_quantity(raw.get("quantity"))
        if "ream" in unit or "box" in unit:
            quantity *= SHEETS_PER_REAM
        catalog_item = match_catalog_item(description)

        if catalog_item and catalog_item in merged:
            merged[catalog_item]["quantity"] += quantity
            merged[catalog_item]["description"] += f" + {description}"
            continue

        line = {"description": description, "catalog_item": catalog_item, "quantity": quantity}
        lines.append(line)
        if catalog_item:
            merged[catalog_item] = line
    return lines


def mark_unavailable(line: Dict, customer_note: str, internal_note: str = "") -> None:
    """Flag a line as unavailable with a customer-safe reason and an internal reason."""
    line.update(status="unavailable", customer_note=customer_note,
                internal_note=internal_note or customer_note)


def evaluate_line(line: Dict, request_date: str, deadline: str, budget: Dict) -> None:
    """
    Decide how one line can be supplied before the customer's deadline.

    - In stock: ship from stock; if stock then falls below the reorder point, plan a
      replenishment purchase (does not delay the customer).
    - Short: plan a supplier restock (shortfall plus safety stock, or just the shortfall
      if the larger order would arrive too late) when it arrives in time and is affordable.
    - Otherwise: unavailable, with the reason recorded.
    """
    item_name = line["catalog_item"]
    quantity = line["quantity"]
    earliest_delivery = add_days(request_date, FROM_STOCK_DELIVERY_DAYS)
    line.update(reorder_qty=0, replenish_qty=0, supplier_arrival=None, delivery_date=None,
                on_hand=0, list_price=None, customer_note="", internal_note="")

    if item_name is None:
        mark_unavailable(line, "this is not an item we carry")
        return
    if quantity <= 0:
        mark_unavailable(line, "the requested quantity was unclear")
        return
    if earliest_delivery > deadline:
        mark_unavailable(line, f"the earliest possible delivery is {earliest_delivery}, after your {deadline} deadline")
        return

    on_hand = current_stock(item_name, request_date)
    reorder_point = min_stock_level(item_name)
    unit_cost = supplier_unit_cost(item_name)
    line.update(on_hand=on_hand, list_price=CATALOG[item_name]["unit_price"])

    if on_hand >= quantity:
        line.update(status="in_stock", delivery_date=earliest_delivery,
                    customer_note="available from stock")
        projected = on_hand - quantity
        if reorder_point and projected < reorder_point:
            replenish_qty = reorder_point * REORDER_TARGET_MULTIPLIER - projected
            cost = replenish_qty * unit_cost
            if budget["planned"] + cost <= budget["available"]:
                line["replenish_qty"] = replenish_qty
                budget["planned"] += cost
        return

    shortfall = quantity - on_hand
    safety_stock = reorder_point * REORDER_TARGET_MULTIPLIER
    candidates = list(dict.fromkeys([shortfall + safety_stock, shortfall]))
    late_arrival = None
    for order_qty in candidates:
        arrival = get_supplier_delivery_date(request_date, order_qty)
        customer_date = max(arrival, earliest_delivery)
        if customer_date > deadline:
            late_arrival = arrival
            continue
        cost = order_qty * unit_cost
        if budget["planned"] + cost > budget["available"]:
            continue
        budget["planned"] += cost
        line.update(status="restock_required", reorder_qty=order_qty, supplier_arrival=arrival,
                    delivery_date=customer_date,
                    customer_note=f"sourced from our supplier, arriving {customer_date}")
        return

    if late_arrival:
        stock_phrase = f"only {on_hand:,} are in stock" if on_hand else "it is currently out of stock"
        mark_unavailable(
            line,
            f"{stock_phrase} and restocking the remaining {shortfall:,} would take until "
            f"{late_arrival}, after your {deadline} deadline",
        )
    else:
        mark_unavailable(
            line,
            "we cannot source this volume in time for your order",
            internal_note="restock cost exceeds the cash available above the reserve",
        )


def build_availability_assessment(request_date: str, deadline: str, requested_items: List[Dict]) -> Dict:
    """Run the availability check for every requested line and store the assessment."""
    request_date = to_iso_date(request_date)
    deadline = to_iso_date(deadline) if deadline else add_days(request_date, DEFAULT_DEADLINE_DAYS)
    budget = {"available": get_cash_balance(request_date) - MIN_CASH_RESERVE, "planned": 0.0}

    lines = consolidate_requested_items(requested_items)
    for line in lines:
        evaluate_line(line, request_date, deadline, budget)

    assessment_id = WORKSPACE.next_id("A")
    assessment = {
        "assessment_id": assessment_id,
        "request_key": WORKSPACE.current_request_key,
        "request_date": request_date,
        "deadline": deadline,
        "lines": lines,
        "restock_executed": False,
        # A restock gates delivery of this order; replenishment only restores safety stock.
        "restock_required": any(l["reorder_qty"] for l in lines if l["status"] != "unavailable"),
        "needs_supplier_orders": any(l["reorder_qty"] or l["replenish_qty"]
                                     for l in lines if l["status"] != "unavailable"),
    }
    WORKSPACE.assessments[assessment_id] = assessment
    return assessment


def describe_assessment(assessment: Dict) -> str:
    """Internal summary of an assessment for the other agents."""
    feasible = [l for l in assessment["lines"] if l["status"] != "unavailable"]
    unavailable = [l for l in assessment["lines"] if l["status"] == "unavailable"]
    rows = [
        f"Assessment {assessment['assessment_id']} | request date {assessment['request_date']} | "
        f"customer deadline {assessment['deadline']}",
        "Items we CAN supply:" if feasible else "Items we CAN supply: none",
    ]
    for l in feasible:
        if l["status"] == "in_stock":
            detail = f"in stock ({l['on_hand']:,} on hand), delivery {l['delivery_date']}"
        else:
            detail = (f"needs supplier restock of {l['reorder_qty']:,} units arriving "
                      f"{l['supplier_arrival']}, delivery {l['delivery_date']}")
        rows.append(f" - {l['catalog_item']} x {l['quantity']:,} (requested as '{l['description']}'): {detail}")
    rows.append("Items we CANNOT supply:" if unavailable else "Items we CANNOT supply: none")
    for l in unavailable:
        rows.append(f" - '{l['description']}' x {l['quantity']:,}: {l['customer_note']}")
    if assessment["restock_required"]:
        supplier_note = "yes (restock required before this order can be finalized)"
    elif assessment["needs_supplier_orders"]:
        supplier_note = "yes (safety-stock replenishment only; does not delay this order)"
    else:
        supplier_note = "no"
    rows.append(f"Supplier orders needed: {supplier_note}")
    if feasible:
        rows.append("Next: quote and finalize the items we CAN supply, even if others are unavailable.")
    else:
        rows.append("Recommendation: decline this request politely using the reasons above.")
    return "\n".join(rows)


def check_current_request(record: Union[Dict, None], record_id: str, kind: str) -> Union[str, None]:
    """
    Return an error message when an ID is unknown or belongs to another customer request.
    This stops an agent from re-using an ID from an earlier request by mistake.
    """
    if record is None:
        return f"Unknown {kind} ID {record_id}. {WORKSPACE.ids_for_current_request()}"
    if WORKSPACE.current_request_key and record["request_key"] != WORKSPACE.current_request_key:
        return (f"{record_id} belongs to an earlier customer request, not the current one. "
                f"{WORKSPACE.ids_for_current_request()}")
    return None


def execute_supplier_orders(assessment_id: str) -> str:
    """Record the planned restock and replenishment purchases as stock_orders transactions."""
    assessment = WORKSPACE.assessments.get(assessment_id)
    problem = check_current_request(assessment, assessment_id, "assessment")
    if problem:
        return problem
    if assessment["restock_executed"]:
        return f"Supplier orders for {assessment_id} were already placed."

    order_date = assessment["request_date"]
    placed = []
    for line in assessment["lines"]:
        if line["status"] == "unavailable":
            continue
        for quantity, purpose in ((line["reorder_qty"], "for this order"),
                                  (line["replenish_qty"], "to restore safety stock")):
            if quantity <= 0:
                continue
            cost = round(quantity * supplier_unit_cost(line["catalog_item"]), 2)
            if get_cash_balance(order_date) - cost < MIN_CASH_RESERVE:
                if purpose == "for this order":
                    mark_unavailable(line, "we cannot source this volume in time for your order",
                                     internal_note="cash reserve reached when placing restock")
                continue
            transaction_id = create_transaction(line["catalog_item"], "stock_orders", quantity, cost, order_date)
            WORKSPACE.purchases.append({"assessment_id": assessment_id, "item": line["catalog_item"],
                                        "quantity": quantity, "cost": cost, "purpose": purpose,
                                        "transaction_id": transaction_id})
            placed.append(f" - {line['catalog_item']}: {quantity:,} units {purpose}, arriving "
                          f"{get_supplier_delivery_date(order_date, quantity)}")

    assessment["restock_executed"] = True
    announce("Inventory", f"Placed {len(placed)} supplier order(s) for {assessment_id}")
    if not placed:
        return f"No supplier orders were needed for {assessment_id}."
    return f"Supplier orders placed for {assessment_id}:\n" + "\n".join(placed)


def bulk_discount_rate(total_units: int) -> float:
    """Return the bulk discount rate for an order of `total_units` units."""
    for minimum_units, rate in BULK_DISCOUNT_TIERS:
        if total_units >= minimum_units:
            return rate
    return 0.0


def describe_tier(total_units: int) -> str:
    """Customer-friendly description of the bulk tier an order falls into."""
    if total_units >= 10000:
        return "orders of 10,000+ units"
    if total_units >= 2000:
        return "orders of 2,000-9,999 units"
    if total_units >= 500:
        return "orders of 500-1,999 units"
    return "every order (base loyalty tier)"


def build_quote(assessment_id: str, promotional_discount_pct: float, promotion_reason: str) -> Dict:
    """
    Price the feasible lines of an assessment.

    Pricing = catalog list price x quantity, less a tiered bulk discount on total units,
    less an optional promotional discount (capped), with the total rounded down to the
    whole dollar as a courtesy for orders of $20 or more.
    """
    assessment = WORKSPACE.assessments[assessment_id]
    feasible = [l for l in assessment["lines"] if l["status"] != "unavailable"]
    if not feasible:
        raise ValueError("No items in this assessment can be supplied, so there is nothing to quote.")

    total_units = sum(l["quantity"] for l in feasible)
    subtotal = round(sum(l["quantity"] * l["list_price"] for l in feasible), 2)
    bulk_rate = bulk_discount_rate(total_units)
    promo_pct = max(0.0, min(float(promotional_discount_pct or 0), MAX_PROMOTIONAL_DISCOUNT_PCT))
    combined_rate = bulk_rate + promo_pct / 100
    discounted_total = subtotal * (1 - combined_rate)
    final_total = math.floor(discounted_total) if discounted_total >= 20 else round(discounted_total, 2)

    # Spread the final total across lines in proportion to their list value (for the ledger).
    quoted_lines, allocated = [], 0.0
    for index, line in enumerate(feasible):
        list_total = round(line["quantity"] * line["list_price"], 2)
        if index == len(feasible) - 1:
            line_total = round(final_total - allocated, 2)
        else:
            line_total = round(final_total * list_total / subtotal, 2) if subtotal else 0.0
            allocated += line_total
        quoted_lines.append({**line, "list_total": list_total, "charged_total": line_total})

    quote_id = WORKSPACE.next_id("Q")
    quote = {
        "quote_id": quote_id,
        "assessment_id": assessment_id,
        "request_key": assessment["request_key"],
        "order_date": assessment["request_date"],
        "lines": quoted_lines,
        "total_units": total_units,
        "subtotal": subtotal,
        "bulk_rate": bulk_rate,
        "bulk_amount": round(subtotal * bulk_rate, 2),
        "promo_pct": promo_pct,
        "promo_amount": round(subtotal * promo_pct / 100, 2),
        "promo_reason": promotion_reason.strip(),
        "rounding_amount": round(discounted_total - final_total, 2),
        "total": float(final_total),
        "delivery_date": max(l["delivery_date"] for l in feasible),
        "status": "quoted",
    }
    WORKSPACE.quotes[quote_id] = quote
    return quote


def describe_quote(quote: Dict) -> str:
    """Customer-safe quote text: prices, discounts with reasons, delivery, exclusions."""
    assessment = WORKSPACE.assessments[quote["assessment_id"]]
    rows = [f"Quote {quote['quote_id']} (order date {quote['order_date']})", "Items:"]
    for l in quote["lines"]:
        rows.append(f" - {l['catalog_item']} (requested as '{l['description']}'): "
                    f"{l['quantity']:,} x ${l['list_price']:.2f} = ${l['list_total']:,.2f}")
    rows.append(f"List subtotal: ${quote['subtotal']:,.2f} for {quote['total_units']:,} units")
    rows.append(f"Bulk discount {quote['bulk_rate'] * 100:.0f}% ({describe_tier(quote['total_units'])}): "
                f"-${quote['bulk_amount']:,.2f}")
    if quote["promo_pct"] > 0:
        rows.append(f"Additional discount {quote['promo_pct']:.1f}% ({quote['promo_reason'] or 'promotional offer'}): "
                    f"-${quote['promo_amount']:,.2f}")
    if quote["rounding_amount"] > 0:
        rows.append(f"Courtesy rounding down to a whole dollar: -${quote['rounding_amount']:,.2f}")
    rows.append(f"TOTAL: ${quote['total']:,.2f}")
    rows.append(f"Estimated delivery: {quote['delivery_date']} (deadline {assessment['deadline']})")
    excluded = [l for l in assessment["lines"] if l["status"] == "unavailable"]
    if excluded:
        rows.append("Not included:")
        rows.extend(f" - '{l['description']}': {l['customer_note']}" for l in excluded)
    if quote["total"] > LARGE_ORDER_THRESHOLD:
        rows.append(f"Note for sales: order above ${LARGE_ORDER_THRESHOLD:,.0f}, run a financial health check first.")
    return "\n".join(rows)


def finalize_quote(quote_id: str) -> str:
    """Re-check stock and record one sales transaction per quoted line."""
    quote = WORKSPACE.quotes.get(quote_id)
    problem = check_current_request(quote, quote_id, "quote")
    if problem:
        return problem
    if quote["status"] == "finalized":
        return f"Quote {quote_id} was already finalized."
    assessment = WORKSPACE.assessments[quote["assessment_id"]]
    if assessment["restock_required"] and not assessment["restock_executed"]:
        return (f"NOT FINALIZED: supplier orders for assessment {assessment['assessment_id']} have not "
                f"been placed yet. Ask the inventory agent to place them, then finalize again.")

    order_date = quote["order_date"]
    for line in quote["lines"]:
        if line["status"] == "unavailable":
            return f"NOT FINALIZED: {line['catalog_item']} could not be sourced after quoting."
        on_hand = current_stock(line["catalog_item"], order_date)
        if on_hand < line["quantity"]:
            return (f"NOT FINALIZED: only {on_hand:,} units of {line['catalog_item']} are on hand "
                    f"for an order of {line['quantity']:,}.")

    transaction_ids = [
        create_transaction(line["catalog_item"], "sales", line["quantity"], line["charged_total"], order_date)
        for line in quote["lines"]
    ]
    has_exclusions = any(l["status"] == "unavailable" for l in assessment["lines"])
    order_id = WORKSPACE.next_id("O")
    WORKSPACE.orders[order_id] = {
        "order_id": order_id,
        "quote_id": quote_id,
        "request_key": quote["request_key"],
        "lines": quote["lines"],
        "total": quote["total"],
        "status": "partially_fulfilled" if has_exclusions else "fulfilled",
        "transaction_ids": transaction_ids,
    }
    quote["status"] = "finalized"
    announce("Sales", f"Order {order_id} confirmed: ${quote['total']:,.2f} for {len(transaction_ids)} line(s)")
    return (f"ORDER CONFIRMED: order {order_id} for quote {quote_id}. "
            f"{len(transaction_ids)} item line(s) recorded, total charged ${quote['total']:,.2f}, "
            f"estimated delivery {quote['delivery_date']}.")


# ---------------------------------------------------------------------------
# 5. Tools for the inventory agent
# ---------------------------------------------------------------------------

@tool
def assess_order_availability(request_date: str, delivery_deadline: str, items_json: str) -> str:
    """
    Check whether each requested item can be delivered by the deadline. Matches items to the
    catalog, checks stock, plans supplier restocks within the deadline and cash limits, and
    stores the result under an assessment ID.

    Args:
        request_date: Date the customer made the request, YYYY-MM-DD.
        delivery_deadline: Date the customer needs delivery by, YYYY-MM-DD.
        items_json: JSON list of objects with keys "description" (customer's wording),
            "quantity" (number as stated) and "unit" (e.g. "sheets", "reams", "rolls", "packs").
    """
    try:
        requested_items = parse_items_payload(items_json)
        announce("Inventory", f"Assessing {len(requested_items)} requested line(s), deadline {delivery_deadline}")
        assessment = build_availability_assessment(request_date, delivery_deadline, requested_items)
        return describe_assessment(assessment)
    except (ValueError, json.JSONDecodeError) as exc:
        return f"Could not read the request: {exc}. Send items_json as a JSON list and dates as YYYY-MM-DD."


@tool
def place_supplier_orders(assessment_id: str) -> str:
    """
    Place the supplier restock and safety-stock replenishment orders planned in an
    assessment, recording each as a stock purchase.

    Args:
        assessment_id: The assessment ID returned by assess_order_availability, e.g. "A-0001".
    """
    return execute_supplier_orders(assessment_id.strip())


@tool
def check_stock_level(item_name: str, as_of_date: str) -> str:
    """
    Report the units on hand for one item on a given date.

    Args:
        item_name: Catalog item name or the customer's wording for it.
        as_of_date: Date to check, YYYY-MM-DD.
    """
    catalog_item = match_catalog_item(item_name)
    if catalog_item is None:
        return f"'{item_name}' is not an item we carry."
    stock_df = get_stock_level(catalog_item, to_iso_date(as_of_date))
    on_hand = int(stock_df["current_stock"].fillna(0).iloc[0]) if not stock_df.empty else 0
    return (f"{catalog_item}: {on_hand:,} units on hand as of {to_iso_date(as_of_date)} "
            f"(reorder point {min_stock_level(catalog_item):,}).")


@tool
def get_inventory_snapshot(as_of_date: str) -> str:
    """
    List every item with positive stock on a date and flag items below their reorder point.

    Args:
        as_of_date: Date of the snapshot, YYYY-MM-DD.
    """
    snapshot = get_all_inventory(to_iso_date(as_of_date))
    rows = [f"Inventory as of {to_iso_date(as_of_date)} ({len(snapshot)} items in stock):"]
    for item_name, units in sorted(snapshot.items()):
        reorder_point = min_stock_level(item_name)
        flag = "  <-- below reorder point" if reorder_point and units < reorder_point else ""
        rows.append(f" - {item_name}: {int(units):,}{flag}")
    return "\n".join(rows)


@tool
def lookup_catalog_item(description: str) -> str:
    """
    Find the catalog item and list price that matches a customer's wording.

    Args:
        description: The customer's wording, e.g. "A4 glossy paper" or "heavy cardstock".
    """
    catalog_item = match_catalog_item(description)
    if catalog_item is None:
        return f"No catalog item matches '{description}'; we do not carry it."
    entry = CATALOG[catalog_item]
    return f"'{description}' -> {catalog_item} ({entry['category']}), list price ${entry['unit_price']:.2f} per unit."


@tool
def get_supplier_delivery_estimate(order_date: str, quantity: int) -> str:
    """
    Estimate when a supplier order of a given size would arrive.

    Args:
        order_date: Date the supplier order would be placed, YYYY-MM-DD.
        quantity: Number of units to order.
    """
    arrival = get_supplier_delivery_date(to_iso_date(order_date), int(quantity))
    return f"A supplier order of {int(quantity):,} units placed on {to_iso_date(order_date)} arrives {arrival}."


# ---------------------------------------------------------------------------
# 6. Tools for the quoting agent
# ---------------------------------------------------------------------------

@tool
def search_past_quotes(keywords: str) -> str:
    """
    Search historical quotes for similar requests to calibrate pricing and discounts.

    Args:
        keywords: Comma-separated keywords, e.g. "cardstock, glossy, ceremony".
    """
    terms = [t.strip() for t in keywords.split(",") if t.strip()][:4]
    seen, matches = set(), []
    # search_quote_history combines terms with AND, so search each term separately (OR).
    for term in terms or [""]:
        for record in search_quote_history([term] if term else [], limit=5):
            key = record["original_request"]
            if key in seen or not record["total_amount"] or record["total_amount"] <= 0:
                continue
            seen.add(key)
            matches.append(record)
    announce("Quoting", f"Found {len(matches)} similar past quote(s) for: {', '.join(terms)}")
    if not matches:
        return "No similar past quotes found. Use the standard bulk discount tiers."
    rows = []
    for record in matches[:6]:
        explanation = str(record["quote_explanation"])[:280]
        rows.append(f"- ${record['total_amount']} | {record['order_size']} {record['event_type']} order "
                    f"for a {record['job_type']}: {explanation}")
    return "Similar past quotes (for reference only; amounts may be rounded):\n" + "\n".join(rows)


@tool
def generate_quote(assessment_id: str, promotional_discount_pct: float, promotion_reason: str) -> str:
    """
    Create a priced quote for the items an assessment can supply. Applies the bulk discount
    tier automatically; you may add a promotional discount of 0 to 3 percent.

    Args:
        assessment_id: Assessment ID from the inventory agent, e.g. "A-0001".
        promotional_discount_pct: Extra discount in percent (0 to 3). Use 0 when there is no reason.
        promotion_reason: Short customer-friendly reason for the extra discount, or "" when 0.
    """
    assessment_id = assessment_id.strip()
    problem = check_current_request(WORKSPACE.assessments.get(assessment_id), assessment_id, "assessment")
    if problem:
        return problem
    try:
        quote = build_quote(assessment_id, promotional_discount_pct, promotion_reason or "")
    except ValueError as exc:
        return f"No quote created: {exc}"
    announce("Quoting", f"Quote {quote['quote_id']}: ${quote['total']:,.2f} "
                        f"({quote['bulk_rate'] * 100:.0f}% bulk + {quote['promo_pct']:.1f}% promo)")
    return describe_quote(quote)


# ---------------------------------------------------------------------------
# 7. Tools for the sales agent
# ---------------------------------------------------------------------------

@tool
def check_financial_health(as_of_date: str) -> str:
    """
    Internal health check before a large order: cash, inventory value and top sellers.
    Never share these figures with the customer.

    Args:
        as_of_date: Date of the check, YYYY-MM-DD.
    """
    report = generate_financial_report(to_iso_date(as_of_date))
    cash = get_cash_balance(to_iso_date(as_of_date))
    healthy = cash >= MIN_CASH_RESERVE
    top = ", ".join(p["item_name"] for p in report["top_selling_products"]
                    if isinstance(p["item_name"], str)) or "none yet"
    announce("Sales", f"Financial health check: {'OK' if healthy else 'LOW CASH'}")
    return (f"INTERNAL financial health as of {report['as_of_date']}: cash ${cash:,.2f}, "
            f"inventory value ${report['inventory_value']:,.2f}, total assets ${report['total_assets']:,.2f}. "
            f"Top sellers: {top}. Status: {'healthy, proceed' if healthy else 'cash below reserve, review'}.")


@tool
def finalize_order(quote_id: str) -> str:
    """
    Finalize a quote: verify stock is on hand for every line and record the sales transactions.

    Args:
        quote_id: Quote ID from the quoting agent, e.g. "Q-0002".
    """
    return finalize_quote(quote_id.strip())


# ---------------------------------------------------------------------------
# 8. Tools for the business advisor agent
# ---------------------------------------------------------------------------

@tool
def get_financial_report(as_of_date: str) -> str:
    """
    Full company financial report: cash, inventory value, total assets, low-stock items
    and top-selling products.

    Args:
        as_of_date: Report date, YYYY-MM-DD.
    """
    report = generate_financial_report(to_iso_date(as_of_date))
    low_stock = [
        f"{row['item_name']} ({int(row['stock'])})" for row in report["inventory_summary"]
        if row["stock"] < min_stock_level(row["item_name"])
    ]
    top = "; ".join(f"{p['item_name']} ${p['total_revenue']:,.2f}"
                    for p in report["top_selling_products"] if isinstance(p["item_name"], str))
    return (f"Financial report as of {report['as_of_date']}: cash ${report['cash_balance']:,.2f}, "
            f"inventory value ${report['inventory_value']:,.2f}, total assets ${report['total_assets']:,.2f}.\n"
            f"Top sellers by revenue: {top or 'none'}.\n"
            f"Stocked items below reorder point: {', '.join(low_stock) or 'none'}.")


@tool
def get_sales_activity_summary() -> str:
    """
    Summarize this run's customer requests: outcomes, revenue, supplier spend and the
    items most often requested but not supplied (and why).
    """
    request_keys = list(dict.fromkeys(a["request_key"] for a in WORKSPACE.assessments.values()))
    outcomes = [WORKSPACE.outcome_for_request(key)["order_status"] for key in request_keys]
    status_counts = pd.Series(outcomes).value_counts().to_dict() if outcomes else {}
    revenue = sum(o["total"] for o in WORKSPACE.orders.values())
    spend = sum(p["cost"] for p in WORKSPACE.purchases)
    missed = [l for a in WORKSPACE.assessments.values() for l in a["lines"] if l["status"] == "unavailable"]
    missed_rows = "\n".join(
        f" - {l['catalog_item'] or l['description']} x {l['quantity']:,}: {l['internal_note']}" for l in missed[:15]
    )
    special_orders = sorted({p["item"] for p in WORKSPACE.purchases if min_stock_level(p["item"]) == 0})
    return (f"Requests handled: {len(request_keys)}; outcomes: {status_counts}.\n"
            f"Revenue booked: ${revenue:,.2f}; supplier purchases: ${spend:,.2f}.\n"
            f"Items sourced on demand (not normally stocked): {', '.join(special_orders) or 'none'}.\n"
            f"Lines not supplied ({len(missed)}):\n{missed_rows or ' - none'}")


# ---------------------------------------------------------------------------
# 9. Agent definitions
# ---------------------------------------------------------------------------

INVENTORY_INSTRUCTIONS = """You are the Inventory Agent of Beaver's Choice Paper Company. You own stock levels and supplier purchasing. You never set prices and never record sales.

When asked to assess a customer request:
1. Extract every requested line item. For each item keep the customer's own wording as "description", the number exactly as stated as "quantity", and the unit as stated as "unit" (sheets, reams, rolls, packs, boxes...). Do not convert reams yourself; the tool does it.
2. Find the delivery deadline in the request and convert it to YYYY-MM-DD. Use the request date given in the task, never today's date.
3. Call assess_order_availability ONCE with all items as a JSON list.
4. Your final answer must contain the assessment ID and the tool output copied verbatim.

When asked to place supplier orders for an assessment ID, call place_supplier_orders and return its output verbatim.
For general stock questions use check_stock_level, get_inventory_snapshot, lookup_catalog_item or get_supplier_delivery_estimate."""

QUOTING_INSTRUCTIONS = """You are the Quoting Agent of Beaver's Choice Paper Company. You turn an availability assessment into a competitive, transparent quote.

1. Call search_past_quotes with 2-4 short comma-separated keywords (the main item types and the event type) to see how similar orders were priced.
2. Decide on an optional promotional discount between 0 and 3 percent. Use 0 for most orders. Add it only when there is a clear business reason: 2-3% for schools and non-profits, or 2% for orders of 2,000+ units when similar past quotes show deeper discounts. State that reason.
3. Call generate_quote once with the assessment ID, the promotional percentage and a short customer-friendly reason ("" when 0).
4. Your final answer must contain the quote ID and the quote text copied verbatim.
Never invent or change prices; only generate_quote sets prices."""

SALES_INSTRUCTIONS = """You are the Sales Agent of Beaver's Choice Paper Company. You finalize orders from quotes and record the sales.

1. If the quote total is above $1,000 (or the quote text asks for it), first call check_financial_health with the order date. Keep those figures internal.
2. Call finalize_order with the quote ID.
3. Your final answer must contain the finalize_order output verbatim. If it starts with "NOT FINALIZED", say exactly what is missing so the orchestrator can resolve it."""

ORCHESTRATOR_INSTRUCTIONS = """You are the Orchestrator and the customer-facing sales representative of Beaver's Choice Paper Company. You coordinate your team and then reply to the customer. You never check stock or set prices yourself.

Workflow for each customer request:
1. Ask inventory_agent to assess the request. Give it the full request text, the request date and the delivery deadline.
2. If the assessment says no items can be supplied, skip to step 6. If at least one item can be supplied, continue: partial orders are quoted and finalized for the items we can supply.
3. Ask quoting_agent to generate a quote for the assessment ID. Include the customer context (job, event, order size).
4. If the assessment says "Supplier orders needed: yes", ask inventory_agent to place supplier orders for the assessment ID.
Always pass the exact assessment and quote IDs returned for THIS request; never reuse an ID from an earlier request.
5. Ask sales_agent to finalize the quote ID, telling it the order date and quote total. If it reports NOT FINALIZED because supplier orders are missing, do step 4 and ask sales_agent once more.
6. Give your final answer: the reply to the customer.

Rules for the customer reply:
- Only say an order is confirmed after sales_agent returns ORDER CONFIRMED.
- Open with the outcome: order confirmed, partially confirmed, or unable to fulfil.
- Copy every price, discount, total and delivery date exactly from the quote; never estimate or leave placeholders.
- For confirmed items list each item, quantity, unit price and line amount, then the subtotal, each discount with the reason it applies, the total charged and the estimated delivery date. Include the quote reference.
- For every item we cannot supply, give the reason in plain language and suggest the closest alternative if one is obvious.
- Never reveal internal information: supplier costs, margins, cash or financial figures, restocking plans, assessment IDs, tool or error messages, or the names of internal agents.
- Do not repeat personal details about the customer. Sign off as "Beaver's Choice Paper Company Sales Team"."""

ADVISOR_INSTRUCTIONS = """You are the Business Advisor of Beaver's Choice Paper Company. After a batch of customer requests, review the company's performance and recommend concrete operational changes.

1. Call get_sales_activity_summary and get_financial_report (use the date given in the task).
2. Give 3-5 specific, numbered recommendations to increase revenue or efficiency, e.g. which items to start stocking, reorder point changes, pricing or discount adjustments, or lead-time improvements. Tie each one to the evidence you saw."""

# Terms that must never appear in a customer-facing reply.
INTERNAL_TERMS = ("supplier cost", "margin", "cash balance", "assessment id", "assessment a-",
                  "inventory_agent", "quoting_agent", "sales_agent", "traceback", "not finalized")


def customer_reply_is_safe(final_answer, memory, agent=None) -> bool:
    """Final-answer check: block replies that leak internal details or are empty."""
    text_lower = str(final_answer).lower()
    if len(text_lower.strip()) < 40:
        raise ValueError("The customer reply is too short. Write a complete reply.")
    leaked = [term for term in INTERNAL_TERMS if term in text_lower]
    if leaked:
        raise ValueError(f"The customer reply mentions internal details ({', '.join(leaked)}). Rewrite it without them.")
    return True


def format_money_variants(amount: float) -> List[str]:
    """Ways a total may be written in a reply, e.g. 1,087.00 / 1087.00 / 1,087."""
    variants = [f"{amount:,.2f}", f"{amount:.2f}"]
    if float(amount).is_integer():
        variants += [f"{int(amount):,}", f"{int(amount)}"]
    return variants


def workflow_is_complete(final_answer, memory, agent=None) -> bool:
    """
    Final-answer check: the orchestrator may only reply once the workflow matches the reply.

    - an assessment must exist for the current request;
    - if any item can be supplied, a quote must exist and the order must be finalized;
    - the reply must state the exact quoted total and contain no placeholder prices.
    """
    text_value = str(final_answer)
    if re.search(r"\$[A-Z]\b|\bTBD\b", text_value):
        raise ValueError("The reply contains placeholder prices. Use the exact figures from the quote.")

    key = WORKSPACE.current_request_key
    assessments = [a for a in WORKSPACE.assessments.values() if a["request_key"] == key]
    if not assessments:
        raise ValueError("No availability assessment exists for this request. Ask inventory_agent to assess it.")
    latest = assessments[-1]
    if not any(l["status"] != "unavailable" for l in latest["lines"]):
        return True  # nothing can be supplied: a polite decline is the correct outcome

    quotes = [q for q in WORKSPACE.quotes.values() if q["assessment_id"] == latest["assessment_id"]]
    if not quotes:
        raise ValueError(f"Assessment {latest['assessment_id']} has items we CAN supply but no quote yet. "
                         f"Ask quoting_agent to generate a quote for {latest['assessment_id']}, then finalize it.")
    quote = quotes[-1]
    if quote["status"] != "finalized":
        restock_step = ""
        if latest["restock_required"] and not latest["restock_executed"]:
            restock_step = f"first ask inventory_agent to place supplier orders for {latest['assessment_id']}, then "
        raise ValueError(f"Quote {quote['quote_id']} is not finalized, so the order is not recorded yet: "
                         f"{restock_step}ask sales_agent to finalize {quote['quote_id']}.")
    if not any(variant in text_value for variant in format_money_variants(quote["total"])):
        raise ValueError(f"The reply must state the total charged exactly as quoted: ${quote['total']:,.2f}.")
    return True


def build_agent_team(model: OpenAIServerModel) -> Dict[str, ToolCallingAgent]:
    """Create the four request-handling agents plus the business advisor."""
    log_level = LogLevel(min(max(AGENT_VERBOSITY, -1), 2))

    inventory_agent = ToolCallingAgent(
        tools=[assess_order_availability, place_supplier_orders, check_stock_level,
               get_inventory_snapshot, lookup_catalog_item, get_supplier_delivery_estimate],
        model=model,
        name="inventory_agent",
        description=("Inventory specialist. Give it a customer request with the request date to get an "
                     "availability assessment (assessment ID), or an assessment ID to place supplier orders. "
                     "Also answers stock questions."),
        instructions=INVENTORY_INSTRUCTIONS,
        max_steps=5,
        verbosity_level=log_level,
    )
    quoting_agent = ToolCallingAgent(
        tools=[search_past_quotes, generate_quote],
        model=model,
        name="quoting_agent",
        description=("Pricing specialist. Give it an assessment ID plus customer context; it returns a quote "
                     "ID and an itemized quote with bulk discounts."),
        instructions=QUOTING_INSTRUCTIONS,
        max_steps=5,
        verbosity_level=log_level,
    )
    sales_agent = ToolCallingAgent(
        tools=[check_financial_health, finalize_order],
        model=model,
        name="sales_agent",
        description=("Sales specialist. Give it a quote ID, the order date and the quote total; it finalizes "
                     "the order and records the sale."),
        instructions=SALES_INSTRUCTIONS,
        max_steps=4,
        verbosity_level=log_level,
    )
    orchestrator = ToolCallingAgent(
        tools=[],
        model=model,
        managed_agents=[inventory_agent, quoting_agent, sales_agent],
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        final_answer_checks=[customer_reply_is_safe, workflow_is_complete],
        max_steps=12,
        verbosity_level=log_level,
    )
    business_advisor = ToolCallingAgent(
        tools=[get_sales_activity_summary, get_financial_report],
        model=model,
        name="business_advisor",
        instructions=ADVISOR_INSTRUCTIONS,
        max_steps=4,
        verbosity_level=log_level,
    )
    return {
        "orchestrator": orchestrator,
        "inventory": inventory_agent,
        "quoting": quoting_agent,
        "sales": sales_agent,
        "advisor": business_advisor,
    }


FALLBACK_REPLY = ("Thank you for your request. We were unable to complete your quote automatically just now. "
                  "A member of our sales team will follow up shortly with pricing and availability.\n"
                  "Beaver's Choice Paper Company Sales Team")


def compose_reply_from_records(request_key: str) -> str:
    """
    Safety net: build the customer reply directly from the recorded quote/order when the
    orchestrator could not produce a valid reply (e.g. it ran out of steps).
    """
    orders = [o for o in WORKSPACE.orders.values() if o["request_key"] == request_key]
    assessments = [a for a in WORKSPACE.assessments.values() if a["request_key"] == request_key]
    if orders:
        quote_text = describe_quote(WORKSPACE.quotes[orders[-1]["quote_id"]])
        quote_lines = [line for line in quote_text.splitlines() if not line.startswith("Note for sales")]
        return ("Your order is confirmed. Here are the details:\n" + "\n".join(quote_lines)
                + "\nBeaver's Choice Paper Company Sales Team")
    if assessments and not any(l["status"] != "unavailable" for l in assessments[-1]["lines"]):
        reasons = "\n".join(f" - {l['description']}: {l['customer_note']}" for l in assessments[-1]["lines"])
        return ("Thank you for your request. Unfortunately we are unable to fulfil it:\n" + reasons
                + "\nBeaver's Choice Paper Company Sales Team")
    return FALLBACK_REPLY


def handle_customer_request(orchestrator: ToolCallingAgent, request_key: str, request_with_date: str,
                            customer_context: str) -> str:
    """Send one customer request through the orchestrator and return the customer reply."""
    WORKSPACE.current_request_key = request_key
    task = (f"New customer request.\nCustomer context: {customer_context}\n"
            f"Request:\n\"\"\"\n{request_with_date}\n\"\"\"")
    announce("Orchestr", "Delegating request to the team")
    try:
        reply = str(orchestrator.run(task, reset=True)).strip()
        customer_reply_is_safe(reply, None)
        workflow_is_complete(reply, None)
        return reply
    except Exception as exc:  # keep the batch running; the customer never sees the error
        announce("Orchestr", f"Using the recorded quote/order for the reply ({type(exc).__name__})")
        return compose_reply_from_records(request_key)


def run_business_review(advisor: ToolCallingAgent, as_of_date: str) -> str:
    """Ask the business advisor to review the run and save its recommendations."""
    announce("Advisor", "Reviewing all transactions from this run")
    try:
        advice = str(advisor.run(f"Review the business as of {as_of_date} and recommend improvements.",
                                 reset=True))
    except Exception as exc:
        advice = f"Business review unavailable ({type(exc).__name__})."
    with open("business_advisor_report.txt", "w", encoding="utf-8") as report_file:
        report_file.write(advice + "\n")
    return advice


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():

    print("Initializing Database...")
    init_database(db_engine)
    WORKSPACE.reset()
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    agent_team = build_agent_team(build_model())
    orchestrator = agent_team["orchestrator"]

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        request_key = f"request-{idx + 1}"
        customer_context = f"{row['job']} organizing a {row['event']} ({row['need_size']} order)"
        response = handle_customer_request(orchestrator, request_key, request_with_date, customer_context)
        outcome = WORKSPACE.outcome_for_request(request_key)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Outcome: {outcome['order_status']}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
                "order_status": outcome["order_status"],
                "order_total": outcome["order_total"],
                "fulfilled_items": outcome["fulfilled_items"],
                "unfulfilled_items": outcome["unfulfilled_items"],
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)

    # Business advisor review of the whole run (saved to business_advisor_report.txt)
    advice = run_business_review(agent_team["advisor"], final_date)
    print("\n===== BUSINESS ADVISOR RECOMMENDATIONS =====")
    print(advice)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()