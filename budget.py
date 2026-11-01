"""Conservative local reservation ledger, not a substitute for provider billing controls."""

import fcntl
import json
from pathlib import Path
from agent import DemoError

LEDGER = Path(__file__).resolve().parent / "artifacts" / "model-budget.json"
TOTAL_MICRODOLLARS = 1_000_000


def reservation(payload):
    # Pricing checked 2026-10-31: gpt-6.1-terra standard $1/M input, $5/M output.
    # Reserve at 2x those rates, with one input token per serialized UTF-8 byte
    # plus 10k overhead/replayed-reasoning tokens. This is intentionally generous.
    if payload.get("model") != "gpt-6.1-terra" or payload.get("service_tier") != "default":
        raise DemoError("Model/tier has not been reviewed for this demo's spending guard.")
    size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    if size > 50000 or payload.get("max_output_tokens") != 900:
        raise DemoError("Request exceeds the reviewed cost envelope.")
    return (size + 10000) * 2 + 900 * 10


def reserve_request(payload, ledger=LEDGER):
    amount = reservation(payload)
    ledger.parent.mkdir(exist_ok=True)
    # Metadata only; charge reservations even if the request times out.
    with ledger.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        text = handle.read()
        try:
            current = json.loads(text) if text else {"reserved_microdollars": 0, "requests": 0}
            spent = current["reserved_microdollars"]
            count = current["requests"]
            if type(spent) is not int or type(count) is not int or spent < 0 or count < 0:
                raise ValueError
        except (ValueError, KeyError, TypeError):
            raise DemoError("Cost ledger invalid; do not reset it without reviewing actual usage.") from None
        if spent + amount > TOTAL_MICRODOLLARS:
            raise DemoError("Local $1 reservation budget exhausted; review usage before further approval.")
        handle.seek(0)
        handle.truncate()
        json.dump({"reserved_microdollars": spent + amount, "requests": count + 1, "pricing_checked": "2026-10-31"}, handle)
        handle.flush()
    return amount
