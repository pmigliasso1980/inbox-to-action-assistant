"""Repository-level rules promoted from prose into executable contracts."""
from pathlib import Path

from graph.store import GraphStore

ROOT = Path(__file__).resolve().parents[1]


def test_repository_graph_has_no_unprovenanced_claims():
    """AGENTS.md hard constraint: every claim has source provenance and a span."""
    store = GraphStore(ROOT / "graph/knowledge.db")
    try:
        claims = store.nodes("Claim")
        assert claims, "the committed graph fixture must contain claims"
        for claim in claims:
            edges = store.provenance_edges(claim.id)
            assert edges, f"claim {claim.id} has no supports/derived_from edge"
            assert all(str(edge.properties.get("span", "")).strip() for edge in edges), (
                f"claim {claim.id} has provenance without a verbatim span"
            )
    finally:
        store.close()


def test_agents_index_is_bounded_and_topic_links_resolve():
    agents = (ROOT / "AGENTS.md").read_text()
    assert len(agents.splitlines()) < 200
    for relative in ("docs/REPOSITORY_GUIDE.md", "agents/README.md", "graph/README.md",
                     "reports/README.md", "docs/DECISIONS.md"):
        assert (ROOT / relative).exists(), relative
        assert relative in agents
