"""Shared pieces for Code Lab 16-01: the shop tools as plain Python functions, the task subset,
grading and a small runner. Every agent_<framework>.py wraps the same tools and prompt, so the
only thing that varies between scripts is the framework."""

import argparse
import os
import time

import shop_env as env

# Six tasks that cover a read, three writes (one needing ownership checks), and two refusals.
TASK_IDS = ["status", "cancel", "refund_one", "address", "cancel_shipped", "other_customer"]

INSTRUCTIONS = env.POLICY


def make_tools(shop: env.Shop, approve=None) -> list:
    """Plain functions with type hints and docstrings - the lowest common denominator every
    framework can turn into a tool schema. Business-rule failures come back as error text so
    the model can read them (frameworks differ in how they report raised exceptions).

    approve: optional callable(tool_name, args) -> bool used as a human-approval gate on refunds.
    """

    def wrap(fn, *args):
        try:
            return fn(*args)
        except env.ToolError as e:
            return {"ok": False, "error": str(e)}

    def find_customer(email: str) -> dict:
        """Look up a customer by email address. Call this first to identify the customer before reading or changing any of their orders. Returns customer_id and name."""
        return wrap(shop.find_customer, email)

    def list_orders(customer_id: str) -> list | dict:
        """List every order of a customer with its status (pending, shipped, delivered, cancelled) and total. customer_id comes from find_customer, e.g. C3."""
        return wrap(shop.list_orders, customer_id)

    def get_order(order_id: str) -> dict:
        """Get one order's details: owner customer_id, status, address and items (item_id, product, qty, unit_price, refunded). Check the owner and status before any change."""
        return wrap(shop.get_order, order_id)

    def cancel_order(order_id: str, reason: str) -> dict:
        """Cancel a whole order. Only works for orders with status 'pending'. Returns the refund amount."""
        return wrap(shop.cancel_order, order_id, reason)

    def update_address(order_id: str, new_address: str) -> dict:
        """Change the delivery address of an order. Only works while the order is 'pending'."""
        return wrap(shop.update_address, order_id, new_address)

    def refund_item(order_id: str, item_id: int) -> dict:
        """Refund one line item of a 'delivered' order (its whole quantity). Use the item_id from get_order. Returns the refund amount."""
        if approve is not None and not approve("refund_item", {"order_id": order_id, "item_id": item_id}):
            return {"ok": False, "error": "A human reviewer declined this refund."}
        return wrap(shop.refund_item, order_id, item_id)

    return [find_customer, list_orders, get_order, cancel_order, update_address, refund_item]


def parse_args(description: str):
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1"))
    ap.add_argument("--model", default=os.getenv("MODEL", "mlx-community/Qwen3-8B-4bit"))
    ap.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", "not-needed"))
    ap.add_argument("--no-thinking", action="store_true",
                    help="send chat_template_kwargs={'enable_thinking': False} (Qwen3 on vLLM / mlx-lm)")
    ap.add_argument("--tasks", default=",".join(TASK_IDS))
    ap.add_argument("--trials", type=int, default=3)
    return ap.parse_args()


def extra_body(args) -> dict | None:
    return {"chat_template_kwargs": {"enable_thinking": False}} if args.no_thinking else None


def run_tasks(framework: str, args, run_one) -> None:
    """run_one(shop, instruction) -> final answer text. Prints one line per task and a summary."""
    tasks = [t for t in env.TASKS if t.tid in args.tasks.split(",")] * args.trials
    passed, t0 = 0, time.time()
    for task in tasks:
        shop = env.Shop()
        start = time.time()
        try:
            answer = run_one(shop, task.instruction) or ""
            ok, why = env.grade(task, shop.db, answer)
        except Exception as e:                      # a framework error counts as a failure
            answer, ok, why = "", False, f"{type(e).__name__}: {e}"
        passed += ok
        print(f"  {task.tid:16s} {'PASS' if ok else 'FAIL'}  {time.time() - start:5.1f}s  "
              f"{'' if ok else why[:80]} | {answer[:90]!r}", flush=True)
    print(f"[{framework}] {passed}/{len(tasks)} passed in {time.time() - t0:.0f}s", flush=True)
