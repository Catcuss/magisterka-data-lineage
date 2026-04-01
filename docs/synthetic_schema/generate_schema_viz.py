"""
Wizualizacja syntetycznego schematu bazy danych — ilustracja broken lineage.
Generuje PNG dla 3 scenariuszy: stan pełny vs. stan po broken lineage.

Uruchomienie:
    python docs/synthetic_schema/generate_schema_viz.py
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viz_output")
os.makedirs(OUT_DIR, exist_ok=True)

# --- Kolory spójne z visualize_graphs.py ---
NODE_COLORS = {
    "Data Table": "#4C72B0",   # niebieski
    "Data Job":   "#C44E52",   # czerwony
    "Data Table (staging)": "#A0A0D0",  # jasnoniebieski (tabele tymczasowe)
}
EDGE_COLORS = {
    "DATA_FLOW":        "#DD8800",  # pomarańczowy
    "DATA_FLOW_broken": "#FF4444",  # czerwony (zerwana krawędź)
    "DATA_FLOW_missing":"#44AA44",  # zielony (krawędź do odtworzenia, przerywana)
}


def _node_color(G, node):
    t = G.nodes[node].get("asset_type", "Data Table")
    return NODE_COLORS.get(t, "#888888")


def _draw_graph(ax, G, pos, broken_edges=None, missing_edges=None, title=""):
    """Rysuje graf na osi ax."""
    broken_edges = broken_edges or []
    missing_edges = missing_edges or []

    normal_edges = [(u, v) for u, v in G.edges()
                    if (u, v) not in broken_edges and (u, v) not in missing_edges]

    node_colors = [_node_color(G, n) for n in G.nodes()]

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=1200, alpha=0.92)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=7, font_color="white",
                            font_weight="bold")

    # Normalne krawędzie
    if normal_edges:
        nx.draw_networkx_edges(G, pos, edgelist=normal_edges, ax=ax,
                               edge_color=EDGE_COLORS["DATA_FLOW"],
                               arrows=True, arrowsize=20,
                               connectionstyle="arc3,rad=0.05",
                               width=2.0)

    # Zerwane krawędzie (przekreślone czerwone)
    if broken_edges:
        existing_broken = [(u, v) for u, v in broken_edges if G.has_edge(u, v)]
        if existing_broken:
            nx.draw_networkx_edges(G, pos, edgelist=existing_broken, ax=ax,
                                   edge_color=EDGE_COLORS["DATA_FLOW_broken"],
                                   arrows=True, arrowsize=20,
                                   style="dashed",
                                   connectionstyle="arc3,rad=0.05",
                                   width=2.5, alpha=0.7)

    # Brakujące krawędzie (zielone przerywane — "do odtworzenia")
    for u, v in missing_edges:
        if not G.has_edge(u, v):
            G.add_edge(u, v)
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], ax=ax,
                                   edge_color=EDGE_COLORS["DATA_FLOW_missing"],
                                   arrows=True, arrowsize=18,
                                   style="dotted",
                                   connectionstyle="arc3,rad=0.15",
                                   width=2.5, alpha=0.85)
            G.remove_edge(u, v)

    ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
    ax.axis("off")


def _make_legend():
    return [
        mpatches.Patch(color=NODE_COLORS["Data Table"], label="Data Table"),
        mpatches.Patch(color=NODE_COLORS["Data Table (staging)"], label="Data Table (staging/temp)"),
        mpatches.Patch(color=NODE_COLORS["Data Job"], label="Data Job"),
        mpatches.Patch(color=EDGE_COLORS["DATA_FLOW"], label="DATA_FLOW (istniejąca)"),
        mpatches.Patch(color=EDGE_COLORS["DATA_FLOW_broken"], label="DATA_FLOW (zerwana)"),
        mpatches.Patch(color=EDGE_COLORS["DATA_FLOW_missing"], label="DATA_FLOW (do odtworzenia)"),
    ]


# =============================================================================
# Scenariusz A — Usunięcie tabeli staging stg_daily_call_agg
# =============================================================================

def scenario_a():
    # --- Graf pełny ---
    G_full = nx.DiGraph()
    nodes_full = [
        ("raw_calls",         {"asset_type": "Data Table"}),
        ("job_agg_daily",     {"asset_type": "Data Job"}),
        ("stg_daily_agg",     {"asset_type": "Data Table (staging)"}),
        ("job_rev_mart",      {"asset_type": "Data Job"}),
        ("dm_revenue",        {"asset_type": "Data Table"}),
        ("job_kpi_mart",      {"asset_type": "Data Job"}),
        ("dm_cust_kpis",      {"asset_type": "Data Table"}),
        ("raw_billing",       {"asset_type": "Data Table"}),
    ]
    G_full.add_nodes_from(nodes_full)
    edges_full = [
        ("raw_calls",     "job_agg_daily"),
        ("job_agg_daily", "stg_daily_agg"),
        ("stg_daily_agg", "job_rev_mart"),
        ("stg_daily_agg", "job_kpi_mart"),
        ("job_rev_mart",  "dm_revenue"),
        ("raw_billing",   "job_rev_mart"),
        ("job_kpi_mart",  "dm_cust_kpis"),
    ]
    G_full.add_edges_from(edges_full)

    pos_full = {
        "raw_calls":     (0, 2),
        "job_agg_daily": (1, 2),
        "stg_daily_agg": (2, 2),
        "job_rev_mart":  (3, 3),
        "job_kpi_mart":  (3, 1),
        "dm_revenue":    (4, 3),
        "dm_cust_kpis":  (4, 1),
        "raw_billing":   (2, 3.8),
    }

    # --- Graf po broken lineage (bez stg_daily_agg) ---
    G_broken = nx.DiGraph()
    nodes_broken = [
        ("raw_calls",     {"asset_type": "Data Table"}),
        ("job_agg_daily", {"asset_type": "Data Job"}),
        ("job_rev_mart",  {"asset_type": "Data Job"}),
        ("dm_revenue",    {"asset_type": "Data Table"}),
        ("job_kpi_mart",  {"asset_type": "Data Job"}),
        ("dm_cust_kpis",  {"asset_type": "Data Table"}),
        ("raw_billing",   {"asset_type": "Data Table"}),
    ]
    G_broken.add_nodes_from(nodes_broken)
    edges_broken = [
        ("raw_calls",    "job_agg_daily"),
        ("job_rev_mart", "dm_revenue"),
        ("raw_billing",  "job_rev_mart"),
        ("job_kpi_mart", "dm_cust_kpis"),
    ]
    G_broken.add_edges_from(edges_broken)

    pos_broken = {k: v for k, v in pos_full.items() if k != "stg_daily_agg"}

    missing = [
        ("job_agg_daily", "job_rev_mart"),
        ("job_agg_daily", "job_kpi_mart"),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Scenariusz A — Usunięcie tabeli staging (stg_daily_call_agg)",
                 fontsize=13, fontweight="bold")

    _draw_graph(ax1, G_full, pos_full, title="Graf pełny (przed broken lineage)")
    _draw_graph(ax2, G_broken, pos_broken, missing_edges=missing,
                title="Graf po broken lineage\n(stg_daily_agg usunięta — zielone = krawędzie do odtworzenia)")

    fig.legend(handles=_make_legend(), loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    out = os.path.join(OUT_DIR, "scenario_A_broken_lineage.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] Scenariusz A ->", out)


# =============================================================================
# Scenariusz B -- Ukryta zaleznosc przez UDF (dim_region_lookup -> job_enrich)
# =============================================================================

def scenario_b():
    # Graf "pełny" (gdyby UDF był transparentny dla systemu lineage)
    G_full = nx.DiGraph()
    nodes_full = [
        ("raw_customers",       {"asset_type": "Data Table"}),
        ("dim_region_lookup",   {"asset_type": "Data Table"}),
        ("job_enrich_cust",     {"asset_type": "Data Job"}),
        ("stg_cust_enriched",   {"asset_type": "Data Table (staging)"}),
        ("job_kpi_mart",        {"asset_type": "Data Job"}),
        ("dm_cust_kpis",        {"asset_type": "Data Table"}),
    ]
    G_full.add_nodes_from(nodes_full)
    edges_full = [
        ("raw_customers",     "job_enrich_cust"),
        ("dim_region_lookup", "job_enrich_cust"),   # ← ukryta przez UDF
        ("job_enrich_cust",   "stg_cust_enriched"),
        ("stg_cust_enriched", "job_kpi_mart"),
        ("job_kpi_mart",      "dm_cust_kpis"),
    ]
    G_full.add_edges_from(edges_full)

    pos = {
        "raw_customers":     (0, 2),
        "dim_region_lookup": (0, 0.5),
        "job_enrich_cust":   (1.5, 1.5),
        "stg_cust_enriched": (3, 1.5),
        "job_kpi_mart":      (4.5, 1.5),
        "dm_cust_kpis":      (6, 1.5),
    }

    # Graf z broken lineage (UDF ukrywa zależność od dim_region_lookup)
    G_broken = nx.DiGraph()
    G_broken.add_nodes_from(nodes_full)
    edges_broken = [
        ("raw_customers",     "job_enrich_cust"),
        # dim_region_lookup → job_enrich_cust BRAK (ukryta przez UDF)
        ("job_enrich_cust",   "stg_cust_enriched"),
        ("stg_cust_enriched", "job_kpi_mart"),
        ("job_kpi_mart",      "dm_cust_kpis"),
    ]
    G_broken.add_edges_from(edges_broken)

    missing = [("dim_region_lookup", "job_enrich_cust")]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))
    fig.suptitle("Scenariusz B — Ukryta zależność przez UDF\n(dim_region_lookup → job_enrich_customers)",
                 fontsize=13, fontweight="bold")

    _draw_graph(ax1, G_full, pos,
                title="Graf pełny\n(gdyby UDF był transparentny dla systemu lineage)")
    _draw_graph(ax2, G_broken, pos, missing_edges=missing,
                title="Graf z broken lineage\n(zielona = krawędź ukryta przez UDF, do odtworzenia)")

    fig.legend(handles=_make_legend(), loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=[0, 0.1, 1, 1])
    out = os.path.join(OUT_DIR, "scenario_B_udf_hidden.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Scenariusz B → {out}")


# =============================================================================
# Scenariusz C — Usunięcie widoku zmaterializowanego
# =============================================================================

def scenario_c():
    G_full = nx.DiGraph()
    nodes_full = [
        ("raw_billing",       {"asset_type": "Data Table"}),
        ("job_refresh_mv",    {"asset_type": "Data Job"}),
        ("mv_monthly_billing",{"asset_type": "Data Table (staging)"}),
        ("job_rev_mart",      {"asset_type": "Data Job"}),
        ("dm_revenue",        {"asset_type": "Data Table"}),
    ]
    G_full.add_nodes_from(nodes_full)
    edges_full = [
        ("raw_billing",        "job_refresh_mv"),
        ("job_refresh_mv",     "mv_monthly_billing"),
        ("mv_monthly_billing", "job_rev_mart"),
        ("job_rev_mart",       "dm_revenue"),
    ]
    G_full.add_edges_from(edges_full)

    pos_full = {
        "raw_billing":        (0, 1.5),
        "job_refresh_mv":     (1.5, 1.5),
        "mv_monthly_billing": (3, 1.5),
        "job_rev_mart":       (4.5, 1.5),
        "dm_revenue":         (6, 1.5),
    }

    # Po migracji: mv i job_refresh_mv usunięte; raw_billing → job_rev_mart bezpośrednio
    G_after = nx.DiGraph()
    nodes_after = [
        ("raw_billing",  {"asset_type": "Data Table"}),
        ("job_rev_mart", {"asset_type": "Data Job"}),
        ("dm_revenue",   {"asset_type": "Data Table"}),
    ]
    G_after.add_nodes_from(nodes_after)
    G_after.add_edges_from([
        ("raw_billing", "job_rev_mart"),
        ("job_rev_mart", "dm_revenue"),
    ])
    pos_after = {
        "raw_billing":  (0, 1.5),
        "job_rev_mart": (3, 1.5),
        "dm_revenue":   (6, 1.5),
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))
    fig.suptitle("Scenariusz C — Usunięcie widoku zmaterializowanego (mv_monthly_billing_summary)",
                 fontsize=13, fontweight="bold")

    _draw_graph(ax1, G_full, pos_full,
                title="Graf historyczny\n(przed migracją systemu rozliczeniowego)")
    _draw_graph(ax2, G_after, pos_after,
                title="Graf po migracji\n(mv + job_refresh_mv usunięte z katalogu)\nHistoryczny lineage utracony")

    fig.legend(handles=_make_legend(), loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=[0, 0.1, 1, 1])
    out = os.path.join(OUT_DIR, "scenario_C_materialized_view.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Scenariusz C → {out}")


# =============================================================================
# Panel zbiorczy — wszystkie 3 scenariusze razem (przegląd)
# =============================================================================

def summary_panel():
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Trzy scenariusze broken lineage — graf po usunięciu pośrednich obiektów",
                 fontsize=13, fontweight="bold")

    # --- A (uproszczony) ---
    GA = nx.DiGraph()
    GA.add_nodes_from([
        ("raw_calls",    {"asset_type": "Data Table"}),
        ("job_agg",      {"asset_type": "Data Job"}),
        ("job_rev",      {"asset_type": "Data Job"}),
        ("dm_revenue",   {"asset_type": "Data Table"}),
    ])
    GA.add_edges_from([("raw_calls", "job_agg"), ("job_rev", "dm_revenue")])
    posA = {"raw_calls": (0, 1), "job_agg": (1, 1), "job_rev": (2, 1), "dm_revenue": (3, 1)}
    _draw_graph(axes[0], GA, posA,
                missing_edges=[("job_agg", "job_rev")],
                title="A: Tabela staging usunięta\nBrakuje: job_agg → job_rev")

    # --- B (uproszczony) ---
    GB = nx.DiGraph()
    GB.add_nodes_from([
        ("raw_cust",     {"asset_type": "Data Table"}),
        ("dim_region",   {"asset_type": "Data Table"}),
        ("job_enrich",   {"asset_type": "Data Job"}),
        ("dm_kpis",      {"asset_type": "Data Table"}),
    ])
    GB.add_edges_from([("raw_cust", "job_enrich"), ("job_enrich", "dm_kpis")])
    posB = {"raw_cust": (0, 2), "dim_region": (0, 0), "job_enrich": (1.5, 1), "dm_kpis": (3, 1)}
    _draw_graph(axes[1], GB, posB,
                missing_edges=[("dim_region", "job_enrich")],
                title="B: UDF ukrywa zależność\nBrakuje: dim_region → job_enrich")

    # --- C (uproszczony) ---
    GC = nx.DiGraph()
    GC.add_nodes_from([
        ("raw_billing",  {"asset_type": "Data Table"}),
        ("job_rev",      {"asset_type": "Data Job"}),
        ("dm_revenue",   {"asset_type": "Data Table"}),
    ])
    GC.add_edges_from([("raw_billing", "job_rev"), ("job_rev", "dm_revenue")])
    posC = {"raw_billing": (0, 1), "job_rev": (1.5, 1), "dm_revenue": (3, 1)}
    _draw_graph(axes[2], GC, posC,
                title="C: Widok zmaterializowany usunięty\nHistoryczny lineage utracony")

    fig.legend(handles=_make_legend(), loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=[0, 0.1, 1, 1])
    out = os.path.join(OUT_DIR, "scenarios_summary_panel.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Panel zbiorczy → {out}")


if __name__ == "__main__":
    print("Generowanie wizualizacji scenariuszy broken lineage...")
    scenario_a()
    scenario_b()
    scenario_c()
    summary_panel()
    print(f"\nWszystkie pliki zapisane w: {OUT_DIR}/")
