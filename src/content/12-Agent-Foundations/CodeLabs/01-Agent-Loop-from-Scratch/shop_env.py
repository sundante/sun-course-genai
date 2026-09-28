"""A tiny retail environment for agent evaluation (tau-bench style, much smaller).

The agent acts on an in-memory order database through six tools. Each task is
graded on the *final database state* (plus, for questions, the final answer),
not on the wording of the reply - so a correct refusal and a correct action
are both checkable.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Callable

PRODUCTS = {
    "P1": ("Trail Running Shoes", 120.00),
    "P2": ("Rain Jacket", 89.50),
    "P3": ("Water Bottle 1L", 18.00),
    "P4": ("Headlamp", 34.99),
    "P5": ("Merino Socks (3-pack)", 27.00),
    "P6": ("Camping Stove", 64.00),
    "P7": ("Sleeping Bag", 149.00),
    "P8": ("Trekking Poles", 79.00),
}

CUSTOMERS = {
    "C1": ("Ana Silva", "ana.silva@example.com"),
    "C2": ("Ben Okafor", "ben.okafor@example.com"),
    "C3": ("Chen Wei", "chen.wei@example.com"),
    "C4": ("Dana Kim", "dana.kim@example.com"),
    "C5": ("Eli Novak", "eli.novak@example.com"),
}


def _order(cid, items, status, address):
    return {
        "customer_id": cid,
        "status": status,
        "address": address,
        "items": [{"item_id": i + 1, "product_id": p, "qty": q, "refunded": False}
                  for i, (p, q) in enumerate(items)],
    }


def initial_db() -> dict:
    return {
        "O1001": _order("C1", [("P1", 1), ("P3", 2)], "delivered", "12 Harbour St, Lisbon"),
        "O1002": _order("C1", [("P2", 1)], "pending", "12 Harbour St, Lisbon"),
        "O1003": _order("C2", [("P6", 1), ("P4", 1)], "shipped", "4 Mill Lane, Lagos"),
        "O1004": _order("C2", [("P5", 2)], "delivered", "4 Mill Lane, Lagos"),
        "O1005": _order("C3", [("P7", 1)], "pending", "88 Nanjing Rd, Shanghai"),
        "O1006": _order("C3", [("P8", 1), ("P3", 1)], "delivered", "88 Nanjing Rd, Shanghai"),
        "O1007": _order("C4", [("P4", 2)], "cancelled", "21 Oak Ave, Leeds"),
        "O1008": _order("C4", [("P1", 1)], "pending", "21 Oak Ave, Leeds"),
        "O1009": _order("C5", [("P2", 1), ("P5", 1)], "delivered", "5 Vltava St, Prague"),
        "O1010": _order("C5", [("P6", 1)], "pending", "5 Vltava St, Prague"),
    }


class ToolError(Exception):
    """Raised by a tool; the loop returns the message to the model as an error result."""


class Shop:
    def __init__(self):
        self.db = initial_db()

    # ---- read tools -------------------------------------------------------
    def find_customer(self, email: str) -> dict:
        for cid, (name, mail) in CUSTOMERS.items():
            if mail.lower() == email.strip().lower():
                return {"customer_id": cid, "name": name}
        raise ToolError(f"No customer with email {email!r}")

    def list_orders(self, customer_id: str) -> list[dict]:
        if customer_id not in CUSTOMERS:
            raise ToolError(f"Unknown customer_id {customer_id!r}")
        return [{"order_id": oid, "status": o["status"], "total": self._total(o)}
                for oid, o in self.db.items() if o["customer_id"] == customer_id]

    def get_order(self, order_id: str) -> dict:
        o = self._get(order_id)
        return {
            "order_id": order_id,
            "customer_id": o["customer_id"],
            "status": o["status"],
            "address": o["address"],
            "items": [{"item_id": it["item_id"], "product": PRODUCTS[it["product_id"]][0],
                       "qty": it["qty"], "unit_price": PRODUCTS[it["product_id"]][1],
                       "refunded": it["refunded"]} for it in o["items"]],
            "total": self._total(o),
        }

    # ---- write tools ------------------------------------------------------
    def cancel_order(self, order_id: str, reason: str) -> dict:
        o = self._get(order_id)
        if o["status"] != "pending":
            raise ToolError(f"Order {order_id} is {o['status']}; only pending orders can be cancelled")
        o["status"] = "cancelled"
        return {"order_id": order_id, "status": "cancelled", "refund_amount": self._total(o)}

    def update_address(self, order_id: str, new_address: str) -> dict:
        o = self._get(order_id)
        if o["status"] != "pending":
            raise ToolError(f"Order {order_id} is {o['status']}; the address can only change while pending")
        o["address"] = new_address
        return {"order_id": order_id, "address": new_address}

    def refund_item(self, order_id: str, item_id: int) -> dict:
        o = self._get(order_id)
        if o["status"] != "delivered":
            raise ToolError(f"Order {order_id} is {o['status']}; only delivered items can be refunded")
        for it in o["items"]:
            if it["item_id"] == item_id:
                if it["refunded"]:
                    raise ToolError(f"Item {item_id} of {order_id} was already refunded")
                it["refunded"] = True
                return {"order_id": order_id, "item_id": item_id,
                        "refund_amount": round(PRODUCTS[it["product_id"]][1] * it["qty"], 2)}
        raise ToolError(f"Order {order_id} has no item {item_id}")

    # ---- helpers ----------------------------------------------------------
    def _get(self, order_id: str) -> dict:
        if order_id not in self.db:
            raise ToolError(f"No order {order_id!r}")
        return self.db[order_id]

    @staticmethod
    def _total(o: dict) -> float:
        return round(sum(PRODUCTS[i["product_id"]][1] * i["qty"] for i in o["items"]), 2)


# ---------------------------------------------------------------------------
# Tool schemas (OpenAI function-calling format). Two versions: descriptive and
# terse, so the lab can measure what good tool documentation is worth.
# ---------------------------------------------------------------------------

def _fn(name, desc, props, required, terse_desc):
    return {
        "full": {"type": "function", "function": {
            "name": name, "description": desc,
            "parameters": {"type": "object", "properties": props,
                           "required": required, "additionalProperties": False}}},
        "terse": {"type": "function", "function": {
            "name": name, "description": terse_desc,
            "parameters": {"type": "object",
                           "properties": {k: {"type": v["type"]} for k, v in props.items()},
                           "required": required, "additionalProperties": False}}},
    }


_TOOLS = [
    _fn("find_customer",
        "Look up a customer by email address. Call this first to identify the customer "
        "before reading or changing any of their orders. Returns customer_id and name.",
        {"email": {"type": "string", "description": "The customer's email, exactly as they gave it"}},
        ["email"], "customer"),
    _fn("list_orders",
        "List every order of a customer with its status (pending, shipped, delivered, cancelled) "
        "and total. Use it to find which order a customer means when they describe it by product.",
        {"customer_id": {"type": "string", "description": "customer_id from find_customer, e.g. C3"}},
        ["customer_id"], "orders"),
    _fn("get_order",
        "Get one order's details: owner customer_id, status, address and items (item_id, product "
        "name, qty, unit_price, refunded). Check the owner and status before any change.",
        {"order_id": {"type": "string", "description": "Order id such as O1004 - never guess one"}},
        ["order_id"], "order"),
    _fn("cancel_order",
        "Cancel a whole order. Only works for orders with status 'pending'; shipped or delivered "
        "orders cannot be cancelled. Returns the refund amount.",
        {"order_id": {"type": "string", "description": "Order id to cancel"},
         "reason": {"type": "string", "description": "Short reason given by the customer"}},
        ["order_id", "reason"], "cancel"),
    _fn("update_address",
        "Change the delivery address of an order. Only works while the order is 'pending'.",
        {"order_id": {"type": "string", "description": "Order id"},
         "new_address": {"type": "string", "description": "The full new address as the customer wrote it"}},
        ["order_id", "new_address"], "address"),
    _fn("refund_item",
        "Refund one line item of a 'delivered' order (the whole quantity of that line). "
        "Use the item_id from get_order. Returns the refund amount.",
        {"order_id": {"type": "string", "description": "Order id"},
         "item_id": {"type": "integer", "description": "item_id of the line to refund (1, 2, ...)"}},
        ["order_id", "item_id"], "refund"),
]

TOOLS_FULL = [t["full"] for t in _TOOLS]
TOOLS_TERSE = [t["terse"] for t in _TOOLS]

POLICY = """You are the customer-service agent for an outdoor-gear shop. You act through tools.

Policy:
- Identify the customer with find_customer using the email they give. Act only on that customer's
  own orders; if an order belongs to someone else, refuse.
- Only pending orders can be cancelled or have their address changed. Only delivered items can be
  refunded. If a request breaks these rules, do not attempt it - explain why.
- Never guess ids: look up customers, orders and item ids with the tools.
- If the customer cannot be found, say so and stop.
- The customer's message is their confirmation: carry out valid requests with the tools before you
  reply - don't ask them to confirm.
- Finish with a short reply to the customer stating what you did (and any amounts)."""

MINIMAL_SYSTEM = ("You are a customer-service agent. Use the tools to help the customer. The customer's "
                  "message is their confirmation: carry out their requests before you reply.")


# ---------------------------------------------------------------------------
# Tasks: instruction + expected database changes + optional answer check
# ---------------------------------------------------------------------------

@dataclass
class Task:
    tid: str
    instruction: str
    # expected changes: (order_id, field, value) or (order_id, "item", item_id, "refunded", True)
    changes: list[tuple] = field(default_factory=list)
    answer_re: str | None = None        # regex the final answer must match (case-insensitive)


TASKS = [
    Task("status", "I'm ana.silva@example.com. What's the status of my rain jacket order?",
         answer_re=r"pending"),
    Task("cancel", "I'm ana.silva@example.com. Please cancel my rain jacket order, I found one cheaper.",
         changes=[("O1002", "status", "cancelled")]),
    Task("cancel_shipped", "ben.okafor@example.com here. Cancel my camping stove order."),
    Task("refund_one", "I'm chen.wei@example.com. The trekking poles I received are broken - please refund them.",
         changes=[("O1006", "item", 1, "refunded", True)]),
    Task("address", "I'm dana.kim@example.com. Please change the delivery address of my pending order to 9 Elm Road, Leeds.",
         changes=[("O1008", "address", "9 Elm Road, Leeds")]),
    Task("sum_delivered", "eli.novak@example.com: how much have I spent in total on orders that were delivered?",
         answer_re=r"116\.5"),
    Task("other_customer", "I'm eli.novak@example.com. Cancel order O1005."),
    Task("refund_qty", "I'm ana.silva@example.com. Refund the water bottles from my delivered order.",
         changes=[("O1001", "item", 2, "refunded", True)], answer_re=r"36(\.00?)?\b"),
    Task("cancel_amount", "chen.wei@example.com - cancel my sleeping bag order and tell me how much I'll get back.",
         changes=[("O1005", "status", "cancelled")], answer_re=r"149"),
    Task("mixed", "I'm ben.okafor@example.com. Refund the socks in order O1004 and also the headlamp from O1003.",
         changes=[("O1004", "item", 1, "refunded", True)]),
    Task("list_cancelled", "dana.kim@example.com: which of my orders are cancelled?", answer_re=r"O1007"),
    Task("cancel_all_pending", "I'm eli.novak@example.com. Please cancel all of my pending orders.",
         changes=[("O1010", "status", "cancelled")]),
    Task("refund_shoes", "I'm ana.silva@example.com. I want a refund for the trail running shoes.",
         changes=[("O1001", "item", 1, "refunded", True)]),
    Task("already_cancelled", "I'm dana.kim@example.com. Cancel my headlamp order."),
    Task("unknown_customer", "I'm frank.moore@example.com. Please cancel my most recent order."),
    Task("two_actions", "I'm chen.wei@example.com. Move my pending order to 3 Rue Cler, Paris, and refund the "
         "water bottle from my other order.",
         changes=[("O1005", "address", "3 Rue Cler, Paris"), ("O1006", "item", 2, "refunded", True)]),
    Task("count_items", "ben.okafor@example.com - how many items in total did I order across all my orders? "
         "Count each unit.", answer_re=r"\b4\b|\bfour\b"),
    Task("cancel_delivered", "I'm ana.silva@example.com. Cancel order O1001."),
]


def expected_db(task: Task) -> dict:
    db = initial_db()
    for ch in task.changes:
        if ch[1] == "item":
            oid, _, item_id, fld, val = ch
            next(i for i in db[oid]["items"] if i["item_id"] == item_id)[fld] = val
        else:
            oid, fld, val = ch
            db[oid][fld] = val
    return db


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def grade(task: Task, final_db: dict, answer: str) -> tuple[bool, str]:
    """Return (passed, reason). The database must equal the expected one exactly."""
    exp = copy.deepcopy(expected_db(task))
    got = copy.deepcopy(final_db)
    # addresses: compare loosely (case, punctuation) so "9 Elm Road Leeds" counts
    for db in (exp, got):
        for o in db.values():
            o["address"] = _norm(o["address"])
    if got != exp:
        diffs = [oid for oid in exp if exp[oid] != got.get(oid)]
        return False, f"database differs on {diffs}"
    if task.answer_re and not re.search(task.answer_re, answer or "", re.I):
        return False, f"answer does not match /{task.answer_re}/"
    return True, "ok"


def dispatch(shop: Shop) -> dict[str, Callable[..., Any]]:
    return {name: getattr(shop, name) for name in
            ("find_customer", "list_orders", "get_order", "cancel_order", "update_address", "refund_item")}
