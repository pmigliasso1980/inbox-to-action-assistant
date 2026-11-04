"""Verify authentication, token counting, and low/high effort cost."""
from agents.llm import UsageLedger, call, count_tokens

PROMPT = "In one sentence, state what an agentic workflow is."


def main() -> None:
    print("prompt tokens:", count_tokens(PROMPT))
    ledger = UsageLedger("runs/usage.jsonl")
    for effort in ("low", "high"):
        text, usage = call(PROMPT, max_tokens=200, effort=effort)
        ledger.add(usage, label="verify_setup", effort=effort)
        print(f"\n--- {effort} response ---\n{text}")
        print({"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
               "cost_usd": round(usage.cost_usd, 8)})
    print("\n--- combined usage ---")
    print(ledger.summary())


if __name__ == "__main__":
    main()
