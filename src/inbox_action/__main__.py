import argparse
import json
import os
from pathlib import Path

from pydantic import ValidationError

from .agents import ModelPool
from .evaluation import LiveEvaluator, load_cases
from .models import DraftReply, MessageAnalysis
from .service import InboxService
from .storage import InboxRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Turn messages into reviewed actions.")
    parser.add_argument("--db", default="inbox.db", help="Path to the SQLite database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Process a new message.")
    ingest.add_argument("body", help="Full message text.")
    ingest.add_argument("--sender", default="unknown")
    ingest.add_argument("--subject", default="No subject")
    ingest.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"))

    subparsers.add_parser("list", help="List processed messages.")
    evaluate = subparsers.add_parser(
        "eval-live", help="Evaluate live API cases without persisting results."
    )
    evaluate.add_argument("--cases", type=Path, default=Path("evals/daily_cases.json"))
    evaluate.add_argument("--case", action="append", dest="selected_cases")
    evaluate.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"))
    show = subparsers.add_parser("show", help="Show a message's complete result.")
    show.add_argument("id", type=int)

    history = subparsers.add_parser("history", help="Show a message's audit history.")
    history.add_argument("id", type=int)

    revise = subparsers.add_parser("revise", help="Revise an analysis or draft with validated JSON.")
    revise.add_argument("id", type=int)
    revise.add_argument("--analysis-file", type=Path)
    revise.add_argument("--draft-file", type=Path)
    revise.add_argument("--clear-draft", action="store_true")
    revise.add_argument("--note")

    for command, help_text in (
        ("approve", "Approve a reviewed result."),
        ("reject", "Reject a reviewed result."),
    ):
        decision = subparsers.add_parser(command, help=help_text)
        decision.add_argument("id", type=int)
        decision.add_argument("--note")
    return parser


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read valid JSON from {path}: {exc}") from exc


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "eval-live":
        if not os.getenv("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY is not set in this terminal.")
        from openai import OpenAI

        try:
            cases = load_cases(args.cases, args.selected_cases)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc
        report = LiveEvaluator(ModelPool(OpenAI(), args.model)).run(cases)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report["summary"]["failed"]:
            raise SystemExit(1)
        return

    repository = InboxRepository(args.db)
    if args.command == "list":
        print(json.dumps(repository.list_messages(), ensure_ascii=False, indent=2))
        return
    service = InboxService(ModelPool(None), repository)
    try:
        if args.command == "show":
            result = service.get(args.id).model_dump(mode="json")
        elif args.command == "history":
            result = [event.model_dump(mode="json") for event in service.history(args.id)]
        elif args.command == "revise":
            if args.draft_file and args.clear_draft:
                raise SystemExit("Use either --draft-file or --clear-draft, not both.")
            analysis = (
                MessageAnalysis.model_validate(_load_json(args.analysis_file))
                if args.analysis_file
                else None
            )
            draft = DraftReply.model_validate(_load_json(args.draft_file)) if args.draft_file else None
            result = service.revise(
                args.id,
                analysis=analysis,
                draft=draft,
                replace_draft=bool(args.draft_file or args.clear_draft),
                note=args.note,
            ).model_dump(mode="json")
        elif args.command in {"approve", "reject"}:
            result = service.decide(
                args.id, approved=args.command == "approve", note=args.note
            ).model_dump(mode="json")
        else:
            result = None
    except (LookupError, ValueError, ValidationError) as exc:
        raise SystemExit(str(exc)) from exc
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set in this terminal.")

    from openai import OpenAI

    service = InboxService(ModelPool(OpenAI(), args.model), repository)
    result = service.ingest(sender=args.sender, subject=args.subject, body=args.body)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
