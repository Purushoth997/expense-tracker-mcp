"""End-to-end MCP Protocol verification script.

Simulates an MCP Client (such as Claude Desktop or MCP Inspector) communicating
with main.py over standard input / output (stdio) JSON-RPC protocol.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def run_protocol_verification() -> bool:
    print("=" * 60)
    print("🚀 Running MCP Protocol Verification against main.py")
    print("=" * 60)

    # Use a temporary DB for verification
    with tempfile.TemporaryDirectory() as td:
        test_db = Path(td) / "verify_expenses.db"
        env = os.environ.copy()
        env["EXPENSE_TRACKER_DB_PATH"] = str(test_db)
        env["PYTHONUTF8"] = "1"
        env["PYTHONUNBUFFERED"] = "1"

        python_exe = sys.executable

        # Start main.py as a subprocess
        proc = subprocess.Popen(
            [python_exe, "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env,
        )

        def send_request(req: dict) -> dict:
            line = json.dumps(req) + "\n"
            proc.stdin.write(line)
            proc.stdin.flush()
            # Read response
            resp_line = proc.stdout.readline()
            if not resp_line:
                stderr_output = proc.stderr.read()
                raise RuntimeError(f"Server closed connection unexpectedly. Stderr: {stderr_output}")
            return json.loads(resp_line)

        def send_notification(req: dict) -> None:
            line = json.dumps(req) + "\n"
            proc.stdin.write(line)
            proc.stdin.flush()

        try:
            # 1. Initialize
            print("\n1. Testing 'initialize'...")
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            }
            init_res = send_request(init_req)
            assert "result" in init_res, f"Init failed: {init_res}"
            print("   ✅ Server Initialized! Server info:", init_res["result"].get("serverInfo"))

            # Notification initialized
            send_notification({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            })

            # 2. tools/list
            print("\n2. Testing 'tools/list'...")
            list_tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            tools_res = send_request(list_tools_req)
            tool_names = [t["name"] for t in tools_res["result"]["tools"]]
            print(f"   ✅ Discovered tools: {tool_names}")
            assert "add_expense" in tool_names
            assert "monthly_total" in tool_names
            assert "top_categories" in tool_names

            # 3. tools/call add_expense
            print("\n3. Testing 'tools/call' -> add_expense...")
            call_add1 = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "add_expense",
                    "arguments": {
                        "amount": 250.0,
                        "category": "Food",
                        "description": "Lunch at canteen",
                        "expense_date": "2026-10-17",
                    },
                },
            }
            res_add1 = send_request(call_add1)
            text_add1 = res_add1["result"]["content"][0]["text"]
            print("   ✅ Output:\n", "     " + text_add1.replace("\n", "\n     "))
            assert "Expense recorded successfully!" in text_add1

            # Add second expense
            call_add2 = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "add_expense",
                    "arguments": {
                        "amount": 750.0,
                        "category": "Transport",
                        "description": "Monthly metro pass",
                        "expense_date": "2026-10-17",
                    },
                },
            }
            send_request(call_add2)

            # 4. tools/call monthly_total
            print("\n4. Testing 'tools/call' -> monthly_total...")
            call_tot = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "monthly_total",
                    "arguments": {"year": 2026, "month": 10},
                },
            }
            res_tot = send_request(call_tot)
            text_tot = res_tot["result"]["content"][0]["text"]
            print("   ✅ Output:\n", "     " + text_tot.replace("\n", "\n     "))
            assert "Total Spending: ₹1,000.00" in text_tot
            assert "Total Transactions: 2" in text_tot

            # 5. tools/call top_categories
            print("\n5. Testing 'tools/call' -> top_categories...")
            call_top = {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "top_categories",
                    "arguments": {"year": 2026, "month": 10, "limit": 5},
                },
            }
            res_top = send_request(call_top)
            text_top = res_top["result"]["content"][0]["text"]
            print("   ✅ Output:\n", "     " + text_top.replace("\n", "\n     "))
            assert "Transport: ₹750.00" in text_top
            assert "Food: ₹250.00" in text_top

            # 6. resources/list and resources/read
            print("\n6. Testing 'resources/list' and 'resources/read'...")
            res_list = send_request({"jsonrpc": "2.0", "id": 7, "method": "resources/list", "params": {}})
            uris = [r["uri"] for r in res_list["result"]["resources"]]
            print(f"   ✅ Discovered resources: {uris}")
            assert "expenses://monthly" in uris

            read_res = send_request({
                "jsonrpc": "2.0",
                "id": 8,
                "method": "resources/read",
                "params": {"uri": "expenses://monthly"},
            })
            resource_content = read_res["result"]["contents"][0]["text"]
            parsed_json = json.loads(resource_content)
            print(f"   ✅ Resource parsed successfully! (record_count: {parsed_json['record_count']}, total: {parsed_json['total_inr']})")
            assert parsed_json["record_count"] == 2

            # 7. prompts/list and prompts/get
            print("\n7. Testing 'prompts/list' and 'prompts/get'...")
            p_list = send_request({"jsonrpc": "2.0", "id": 9, "method": "prompts/list", "params": {}})
            p_names = [p["name"] for p in p_list["result"]["prompts"]]
            print(f"   ✅ Discovered prompts: {p_names}")
            assert "budget_summary" in p_names

            p_get = send_request({
                "jsonrpc": "2.0",
                "id": 10,
                "method": "prompts/get",
                "params": {"name": "budget_summary", "arguments": {"year": "2026", "month": "10"}},
            })
            prompt_msg = p_get["result"]["messages"][0]["content"]["text"]
            print("   ✅ Prompt retrieved:\n", "     " + prompt_msg.split("\n")[0])
            assert "October 2026" in prompt_msg

            print("\n" + "=" * 60)
            print("🎉 ALL MCP PROTOCOL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
            print("=" * 60)
            return True

        finally:
            proc.terminate()
            proc.wait()


if __name__ == "__main__":
    success = run_protocol_verification()
    sys.exit(0 if success else 1)
