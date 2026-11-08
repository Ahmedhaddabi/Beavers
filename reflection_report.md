# Reflection Report – Beaver's Choice Paper Company Multi-Agent System

Files referenced in this report:

- `agent_workflow_diagram.png` / `agent_workflow_diagram.svg` – the agent workflow diagram (source: `agent_workflow_diagram.dot`)
- `project_starter.py` – implementation (smolagents)
- `test_results.csv` – results of the full run over `quote_requests_sample.csv` (20 requests)
- `business_advisor_report.txt` – recommendations written by the Business Advisor agent after the run

---

## 1. Explanation of the agent workflow diagram

The system uses **smolagents** and has **five agents** (the project maximum). Each agent has a single, non-overlapping responsibility, and every business rule or number lives inside a tool, not in the LLM.

| Agent | Responsibility | Tools (purpose) | Starter helpers used |
|---|---|---|---|
| **1. Orchestrator** (manager `ToolCallingAgent`) | Customer-facing. Decides the order of delegation and writes the final reply. Never checks stock or sets prices. | none – it manages the three worker agents | – |
| **2. Inventory Agent** | Catalog matching, stock checks, supplier lead times, restocking | `assess_order_availability` (per-line availability + restock plan → assessment ID), `place_supplier_orders` (record restock purchases), `check_stock_level`, `get_inventory_snapshot`, `lookup_catalog_item`, `get_supplier_delivery_estimate` | `get_stock_level`, `get_all_inventory`, `get_supplier_delivery_date`, `get_cash_balance`, `create_transaction` |
| **3. Quoting Agent** | Pricing using quote history and bulk-discount tiers | `search_past_quotes` (similar historical quotes), `generate_quote` (itemised quote → quote ID) | `search_quote_history` |
| **4. Sales Agent** | Pre-sale financial check and order finalisation | `check_financial_health` (internal cash check for orders > $1,000), `finalize_order` (verify stock, record sale) | `generate_financial_report`, `get_cash_balance`, `create_transaction`, `get_stock_level` |
| **5. Business Advisor Agent** | Runs once after the batch; reviews all transactions and recommends changes | `get_sales_activity_summary`, `get_financial_report` | `generate_financial_report` |

All seven required helper functions are used by at least one tool.

**Orchestration flow (solid arrows in the diagram):**

1. The customer request (text, request date, customer context) goes to the Orchestrator.
2. Orchestrator → Inventory Agent: *assess request*. The Inventory Agent extracts the line items and deadline and returns an **assessment ID** with a status per line: *in stock*, *restock in time*, or *unavailable* (not carried, or the supplier cannot deliver before the deadline).
3. If at least one item can be supplied, Orchestrator → Quoting Agent: *quote request* with the assessment ID. The Quoting Agent checks past quotes, decides whether a 0–3 % promotional discount is justified (and states why), and returns a **quote ID**.
4. If the assessment needs supplier orders, Orchestrator → Inventory Agent: *place supplier orders*.
5. Orchestrator → Sales Agent: *finalize* with the quote ID. The Sales Agent runs a financial health check for large orders, then returns **ORDER CONFIRMED** or **NOT FINALIZED** with the reason.
6. The Orchestrator writes the customer reply. Two final-answer checks (`customer_reply_is_safe`, `workflow_is_complete`) reject replies that leak internal data, contain placeholder prices, or claim a confirmation that was not recorded.
7. After all requests, the Business Advisor reviews the run and writes `business_advisor_report.txt`.

**Why this architecture (decision-making):**

- **Orchestrator–worker pattern.** One agent owns the conversation and the sequence; workers own their domain. This mirrors a real sales team and keeps each agent's prompt short and focused.
- **Agents decide *what* to do; tools hold the rules and numbers.** Prices, discount tiers, lead times and cash limits are computed in Python, so the LLM cannot invent or miscalculate figures.
- **Reference IDs instead of re-typed numbers.** Agents pass assessment and quote IDs, so quantities and prices cannot drift between agents.
- **Tool assignment by ownership.** Only the Inventory Agent can buy stock, only the Quoting Agent can price, only the Sales Agent can record a sale. This prevents overlapping responsibilities.
- **Guardrails at the output.** Final-answer checks and a fallback reply built from recorded data keep customer messages accurate and safe even if the LLM misbehaves.

---

## 2. Evaluation results (from `test_results.csv`)

The full sample of **20 requests** (01–17 April 2025) was processed end to end.

**Summary of outcomes**

| Outcome | Requests | Share |
|---|---|---|
| Fulfilled (all items) | 10 | 50 % |
| Partially fulfilled | 9 | 45 % |
| Rejected (nothing could be supplied in time) | 1 (request 15) | 5 % |
| **Total booked revenue** | **$12,219.40** | 19 of 20 requests produced a sale |

| Line items | Count |
|---|---|
| Line items fulfilled | 41 |
| Line items not fulfilled | 19 |
| – not carried (balloons, A3 paper, cardboard, tickets) | 4 |
| – could not be restocked before the customer's deadline | 15 |

**Financial state over the run**

| | After request 1 (01 Apr) | After request 20 (17 Apr) | Change |
|---|---|---|---|
| Cash balance | $45,122.70 | $49,112.55 | +$3,989.85 |
| Inventory value | $4,875.30 | $4,216.55 | −$658.75 |

The cash balance moved after every request that produced a sale (only rejected request 15 left it unchanged), and every request received a reply with either a confirmed order or a clear reason.

**Detailed summary of orders**

| Req | Date | Status | Total | Fulfilled items | Not fulfilled (reason) |
|---|---|---|---|---|---|
| 1 | 04-01 | fulfilled | $63.00 | Glossy 200, Cardstock 100, Colored 100 | – |
| 2 | 04-03 | partial | $133.00 | Poster paper 500, Party streamers 300 | balloons (not carried) |
| 3 | 04-04 | partial | $8,715.00 | A4 10,000, Standard copy 250,000 | A3 paper (not carried) |
| 4 | 04-05 | fulfilled | $81.00 | Cardstock 500, A4 250 | – |
| 5 | 04-05 | fulfilled | $125.00 | Colored 500, Cardstock 300, Washi tape 200 | – |
| 6 | 04-06 | fulfilled | $71.00 | Construction 500, Copy 300, Cardstock 200 | – |
| 7 | 04-07 | fulfilled | $536.00 | Glossy 500, Matte 1,000, Large poster 300, Cardstock 200 | – |
| 8 | 04-07 | fulfilled | $633.00 | Glossy 500, Matte 1,000, Colored 2,000, Recycled 3,000 | – |
| 9 | 04-07 | fulfilled | $31.00 | A4 200, Glossy 100, Envelopes 50 | – |
| 10 | 04-08 | fulfilled | $137.00 | Glossy 500, Cardstock 300 | – |
| 11 | 04-08 | fulfilled | $146.00 | Glossy 500, Matte 300 | – |
| 12 | 04-08 | fulfilled | $49.00 | Cardstock 200, Copy 500, Napkins 100 | – |
| 13 | 04-08 | partial | $28.00 | Cardstock 200 | A4 (270 in stock, restock after deadline) |
| 14 | 04-09 | partial | $69.00 | Cardstock 500 | A4, poster paper (restock after deadline) |
| 15 | 04-12 | rejected | $0.00 | – | A4, colored paper (restock after deadline); cardboard (not carried) |
| 16 | 04-13 | partial | $97.00 | Large poster 100 | A4, construction paper (restock after deadline) |
| 17 | 04-14 | partial | $47.00 | Paper plates 500 | A4, colored paper, napkins, cups (restock after deadline) |
| 18 | 04-14 | partial | $19.40 | Colored 200 | cardstock, copy paper (restock after deadline) |
| 19 | 04-15 | partial | $139.00 | Cardstock 1,000 | glossy, matte (restock after deadline) |
| 20 | 04-17 | partial | $1,100.00 | Flyers 5,000, Poster paper 2,000 | tickets (not carried) |

**Strengths shown by the evaluation**

1. **Reliable end-to-end handling.** All 20 requests completed with no crash and no customer-visible error; 19 of 20 generated revenue.
2. **Correct partial fulfilment.** In 9 requests the system sold what it could and explained the rest, instead of rejecting the whole order. Request 3 alone booked $8,715.00 despite one unavailable item.
3. **Deadline-aware restocking.** The Inventory Agent compared supplier lead times with each customer deadline and only promised items it could deliver (e.g. request 3: 250,000 sheets restocked and delivered by 11 April).
4. **Accurate, explainable pricing.** Every quote showed list prices, the bulk-discount tier, any promotional discount with its reason (e.g. 2 % for the school board in request 3), and the exact total. The `workflow_is_complete` check guarantees the total in the reply matches the recorded sale.
5. **Safe customer replies.** No reply contained supplier costs, margins, cash figures, internal IDs or agent names; unavailable items always had a plain-language reason.

**Weaknesses found**

- **Stock-outs repeat.** A4 paper stayed at 270 sheets from 8 April onward and caused lost line items in requests 13, 14, 15, 16 and 17. Replenishment only happens when an item is *sold*, so a lost order never triggers a reorder.
- **Lead time beats short deadlines.** 15 of the 19 unfulfilled lines were items we *do* sell but could not restock before the deadline.
- **Inconsistent product matching.** "A3 paper" was treated as not carried in request 3, but "A3 colored paper" in request 15 was matched to Colored paper.
- **No customer choice on partial orders.** Partial orders were confirmed automatically; the customer was not offered a later delivery date or substitute for the missing items.

---

## 3. Suggestions for further improvement

**Suggestion 1 – Proactive, demand-based replenishment (fixes the repeated stock-outs).**
*Evidence:* A4 paper was requested in 5 consecutive requests (13–17) and lost every time, and inventory value fell by $658.75 over the run.
*Change:* After every request – including rejected or partial ones – record the *unmet demand* per item and let the Inventory Agent reorder any item whose stock plus incoming orders is below its reorder point. Reorder points should be recalculated from recent demand and supplier lead time (e.g. average daily demand × lead time + safety stock) instead of the fixed random `min_stock_level`. This would have restocked A4 after request 13 and likely converted several of the 15 deadline-related losses into sales.

**Suggestion 2 – Offer alternatives and back-orders instead of silently dropping items (customer choice + more revenue).**
*Evidence:* 9 of 20 orders were only partially fulfilled, and request 15 was fully rejected, even though most missing items were products we carry.
*Change:* Add a step where the Orchestrator presents options for each unavailable line: (a) a later delivery date for the full order, (b) a substitute in stock (e.g. Letter-sized or Standard copy paper for A4, Cardstock for cardboard signage), or (c) proceed with the partial order. A substitute lookup tool for the Inventory Agent would rank in-stock items by similarity and price.

**Suggestion 3 – Improve product matching for size and variant words.**
*Evidence:* "A3 paper" and "A3 colored paper" were handled differently.
*Change:* Parse size, colour and finish as separate attributes before matching, and send low-confidence matches back to the customer as a clarification question instead of guessing.

---

## 4. Trade-offs and scaling

- **Simplicity vs. flexibility.** Putting rules in deterministic tools made the system accurate and easy to test, but each new rule needs code, not just a prompt change.
- **Sequential orchestration.** One request at a time keeps the database consistent and easy to audit; a production version handling many concurrent requests would need transaction locking or a queue.
- **Cost and latency.** Each request uses 4–6 LLM calls. With more agents or tools, cost grows linearly; caching quote-history searches and using a smaller model for the workers would keep this manageable.
