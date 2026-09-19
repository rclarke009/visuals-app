from __future__ import annotations

import argparse

from dataset.extract import write_dataset
from dataset.graph import audit_all, audit_family
from dataset.llm import llm_enabled
from dataset.queue import accept, accept_roots, list_proposals, reject, reject_roots
from dataset.roots import propose_root_links
from dataset.sync_html import sync_html


def main() -> None:
    p = argparse.ArgumentParser(description="Grounded word-dataset review factory")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("extract", help="Pull FAMILIES from the HTML into data/families.json")

    a = sub.add_parser("audit", help="Run the LangGraph audit and write proposals/")
    a.add_argument("--family", help="Audit one hub (thin, angry, …)")
    a.add_argument("--no-llm", action="store_true", help="Skip Claude even if ANTHROPIC_API_KEY is set")
    a.add_argument("--llm", action="store_true", help="Require Claude (fail if no key)")

    sub.add_parser("roots", help="Propose shared root.id from grounded trails")

    q = sub.add_parser("queue", help="Review proposals")
    q.add_argument("action", choices=["list", "accept", "reject", "accept-roots", "reject-roots"])
    q.add_argument("word", nargs="?")
    q.add_argument("--sync", action="store_true", help="After accept, copy families.json into the HTML")

    sub.add_parser("sync", help="Write data/families.json into nuance-cube-v0.1.html")

    args = p.parse_args()
    if args.cmd == "extract":
        write_dataset()
        return
    if args.cmd == "audit":
        use_llm = False if args.no_llm else (True if args.llm else None)
        if args.llm and not llm_enabled():
            raise SystemExit("ANTHROPIC_API_KEY is missing")
        if args.family:
            audit_family(args.family, use_llm=use_llm)
        else:
            audit_all(use_llm=use_llm)
        propose_root_links()
        return
    if args.cmd == "roots":
        propose_root_links()
        return
    if args.cmd == "queue":
        if args.action == "list":
            list_proposals()
        elif args.action == "accept":
            if not args.word:
                raise SystemExit("queue accept needs a word")
            accept(args.word, do_sync=args.sync)
        elif args.action == "reject":
            if not args.word:
                raise SystemExit("queue reject needs a word")
            reject(args.word)
        elif args.action == "accept-roots":
            accept_roots(do_sync=args.sync)
        else:
            reject_roots()
        return
    if args.cmd == "sync":
        sync_html()


if __name__ == "__main__":
    main()
