from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mlstore_lite.experiments.final_demo import run_final_demo


DOCS_DIR = ROOT_DIR / "docs"
WEEKLY_NOTES_DIR = DOCS_DIR / "weekly-notes"

PAGES = [
    "Home",
    "Demo",
    "Architecture",
    "DDIA",
    "Results",
    "Final Report",
    "Weekly Notes",
    "Limitations",
    "Future Work",
]

LAYER_CARDS = [
    {
        "title": "Storage",
        "subtitle": "One durable node",
        "body": "WAL, memtable, SSTable-like files, compaction, recovery.",
        "tag": "DDIA Ch. 3",
        "class": "blue",
    },
    {
        "title": "Replication",
        "subtitle": "Copies of the same data",
        "body": "Leader-follower writes, sync/async modes, manual failover.",
        "tag": "DDIA Ch. 5",
        "class": "green",
    },
    {
        "title": "Sharding",
        "subtitle": "Split the key space",
        "body": "Consistent hashing routes each feature key to one shard group.",
        "tag": "DDIA Ch. 6",
        "class": "purple",
    },
    {
        "title": "Batch",
        "subtitle": "Historical features",
        "body": "A local map-shuffle-reduce flow turns events into aggregates.",
        "tag": "DDIA Ch. 10",
        "class": "yellow",
    },
    {
        "title": "Stream",
        "subtitle": "Recent features",
        "body": "Append-only log, consumer offsets, tumbling windows.",
        "tag": "DDIA Ch. 11",
        "class": "orange",
    },
    {
        "title": "Inference",
        "subtitle": "AI consumer layer",
        "body": "Feature serving, deterministic model score, prediction log.",
        "tag": "Extension",
        "class": "rose",
    },
]

STATUS_ITEMS = [
    ("Storage", "Implemented", "local durable key-value node"),
    ("Replication", "Implemented", "leader plus two followers per shard"),
    ("Sharding", "Implemented", "2 shard groups, RF=3"),
    ("Batch", "Implemented", "local map-shuffle-reduce"),
    ("Stream", "Implemented", "single-process log and consumer offsets"),
    ("Observability", "Implemented", "JSONL experiment records and timings"),
    ("Inference", "Implemented", "feature serving plus deterministic scoring"),
    ("Networking", "Not implemented", "local objects instead of remote machines"),
]

DDIA_CONNECTIONS = [
    {
        "chapter": "Chapter 3",
        "topic": "Storage and Retrieval",
        "implemented": "Write-ahead log, memtable, SSTable-like files, compaction.",
        "simplified": "No bloom filters, compression, concurrent writes, or production LSM tuning.",
    },
    {
        "chapter": "Chapter 5",
        "topic": "Replication",
        "implemented": "Leader-follower replication with sync/async writes and manual failover.",
        "simplified": "No real networking, automatic leader election, quorum protocol, or consensus.",
    },
    {
        "chapter": "Chapter 6",
        "topic": "Partitioning",
        "implemented": "Consistent hashing, virtual nodes, request routing, shard distribution checks.",
        "simplified": "No live data migration, automatic rebalancing service, or multi-region placement.",
    },
    {
        "chapter": "Chapter 10",
        "topic": "Batch Processing",
        "implemented": "A small map-shuffle-reduce engine that produces user feature aggregates.",
        "simplified": "No distributed workers, scheduler, fault-tolerant task retry, or large file formats.",
    },
    {
        "chapter": "Chapter 11",
        "topic": "Stream Processing",
        "implemented": "Append-only event log, producers, consumers, offsets, tumbling windows.",
        "simplified": "No broker cluster, partitioned topic assignment, backpressure, or exactly-once guarantees.",
    },
    {
        "chapter": "MLOps extension",
        "topic": "Evaluation and Inference",
        "implemented": "Local timings, JSONL experiment logs, feature serving, model score, prediction logs.",
        "simplified": "No trained model registry, online API, A/B testing, or monitoring platform.",
    },
]

LIMITATIONS = [
    (
        "Local only",
        "Nodes are Python objects and local directories, not separate machines communicating over a network.",
    ),
    (
        "No consensus",
        "Failover is manual. The project does not implement Raft, Paxos, or automatic leader election.",
    ),
    (
        "Single-process processing",
        "Batch and stream processing show the dataflow ideas but do not run distributed workers in parallel.",
    ),
    (
        "Small benchmark scope",
        "Week 8 and Week 10 measurements are laptop-scale observations, not production performance claims.",
    ),
    (
        "Simple model",
        "The AI layer uses deterministic inference over stored features, not a trained production ML model.",
    ),
    (
        "Educational storage engine",
        "The storage layer exposes the ideas of an LSM-style engine but skips many production optimizations.",
    ),
]

FUTURE_WORK = [
    (
        "Add real networking",
        "Run nodes as separate processes and let the router communicate over HTTP or sockets.",
    ),
    (
        "Implement consensus",
        "Add a small Raft-inspired leader election experiment to replace manual failover.",
    ),
    (
        "Parallelize processing",
        "Split batch or stream work across multiple local workers to make scheduling and retries visible.",
    ),
    (
        "Train a model",
        "Use generated events to train a small model, then compare trained inference with the current rule-based scorer.",
    ),
    (
        "Add model monitoring",
        "Log feature distributions, prediction drift, and missing-feature rates over time.",
    ),
    (
        "Revisit with DDIA 2nd edition",
        "Use the newer book version and add small System Design Interview inspired mini-projects.",
    ),
]

APP_CSS = """
<style>
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #0f172a;
  }
  .ml-hero {
    border: 1px solid #d7e3f1;
    border-radius: 26px;
    padding: 30px;
    background:
      radial-gradient(circle at top left, rgba(14, 165, 233, 0.20), transparent 34%),
      linear-gradient(135deg, #f8fafc 0%, #edf7f3 55%, #fff7ed 100%);
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
  }
  .hero-kicker {
    color: #0369a1;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-size: 0.76rem;
    margin-bottom: 0.45rem;
  }
  .hero-title {
    color: #0f172a;
    font-size: 2.3rem;
    line-height: 1.06;
    font-weight: 850;
    max-width: 870px;
    margin-bottom: 0.8rem;
  }
  .hero-copy {
    color: #475569;
    font-size: 1.02rem;
    line-height: 1.65;
    max-width: 920px;
  }
  .hero-pills, .status-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
  }
  .pill, .status-pill {
    border: 1px solid rgba(15, 23, 42, 0.10);
    background: rgba(255, 255, 255, 0.74);
    color: #334155;
    padding: 8px 12px;
    border-radius: 999px;
    font-size: 0.86rem;
    font-weight: 700;
  }
  .tour-grid, .layer-grid, .ddia-grid, .mini-grid, .story-grid,
  .limit-grid, .future-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(245px, 1fr));
    gap: 14px;
    margin: 0.8rem 0 1.2rem 0;
  }
  .tour-card, .layer-card, .ddia-card, .mini-card, .story-card,
  .limit-card, .future-card, .friendly-card {
    border: 1px solid rgba(15, 23, 42, 0.10);
    border-radius: 18px;
    padding: 17px;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.07);
    min-height: 142px;
  }
  .tour-card strong, .layer-card strong, .ddia-card strong, .mini-card strong,
  .story-card strong, .limit-card strong, .future-card strong,
  .friendly-card h4 {
    display: block;
    color: #0f172a;
    font-size: 1.02rem;
    margin: 0 0 6px 0;
  }
  .tour-card .sub, .layer-card .sub, .ddia-card .sub, .mini-card .sub,
  .story-card .sub {
    color: #334155;
    font-weight: 760;
    font-size: 0.84rem;
    margin-bottom: 9px;
  }
  .tour-card .body, .layer-card .body, .ddia-card .body, .mini-card .body,
  .story-card .body, .limit-card .body, .future-card .body,
  .friendly-card p {
    color: #475569;
    font-size: 0.88rem;
    line-height: 1.45;
    margin: 0;
  }
  .tag {
    display: inline-block;
    margin-top: 13px;
    border-radius: 999px;
    padding: 5px 10px;
    color: #0f172a;
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(15, 23, 42, 0.08);
    font-size: 0.76rem;
    font-weight: 800;
  }
  .blue { background: linear-gradient(135deg, #e0f2fe, #f8fafc); }
  .green { background: linear-gradient(135deg, #dcfce7, #f8fafc); }
  .purple { background: linear-gradient(135deg, #ede9fe, #f8fafc); }
  .yellow { background: linear-gradient(135deg, #fef3c7, #f8fafc); }
  .orange { background: linear-gradient(135deg, #ffedd5, #f8fafc); }
  .rose { background: linear-gradient(135deg, #ffe4e6, #f8fafc); }
  .slate { background: linear-gradient(135deg, #f1f5f9, #ffffff); }
  .flow-wrap {
    border: 1px solid #dbe3ef;
    border-radius: 22px;
    padding: 22px;
    background:
      radial-gradient(circle at 8% 15%, rgba(14,165,233,0.16), transparent 25%),
      radial-gradient(circle at 75% 20%, rgba(251,191,36,0.20), transparent 24%),
      linear-gradient(135deg, #f8fafc 0%, #eef6ff 100%);
  }
  .flow-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 12px;
  }
  .flow-lanes {
    display: grid;
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .flow-lane {
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 18px;
    padding: 14px;
    background: rgba(255, 255, 255, 0.66);
  }
  .lane-label {
    color: #0f172a;
    font-weight: 800;
    font-size: 0.86rem;
    margin-bottom: 9px;
  }
  .flow-row, .mini-chain {
    display: flex;
    align-items: stretch;
    gap: 10px;
    flex-wrap: wrap;
  }
  .flow-card, .mini-node {
    min-width: 130px;
    border-radius: 16px;
    padding: 12px 13px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.10);
    border: 1px solid rgba(15, 23, 42, 0.08);
    background: #ffffff;
  }
  .flow-card strong {
    display: block;
    font-size: 0.95rem;
    color: #0f172a;
    margin-bottom: 4px;
  }
  .flow-card span, .mini-node span {
    color: #475569;
    font-size: 0.82rem;
    line-height: 1.25rem;
  }
  .flow-arrow, .mini-arrow {
    display: flex;
    align-items: center;
    color: #64748b;
    font-weight: 900;
    font-size: 1.1rem;
  }
  .raw { background: #dff4ff; }
  .batch { background: #dcfce7; }
  .stream { background: #fef3c7; }
  .store { background: #ede9fe; }
  .ai { background: #fae8ff; }
  .pred { background: #ffe4e6; }
  .obs { background: #f1f5f9; }
  .flow-note {
    color: #475569;
    font-size: 0.9rem;
    margin-top: 14px;
  }
  .status-board {
    border: 1px solid #dbe3ef;
    border-radius: 18px;
    padding: 18px;
    background: linear-gradient(135deg, #f8fafc, #ffffff);
  }
  .status-title {
    color: #0f172a;
    font-weight: 850;
    margin-bottom: 5px;
  }
  .status-note {
    color: #64748b;
    font-size: 0.86rem;
  }
  .implemented { border-color: #bbf7d0; background: #f0fdf4; }
  .not-implemented { border-color: #fecaca; background: #fff1f2; }

  .ml-hero {
    border: 1px solid rgba(32, 31, 28, 0.10);
    background:
      radial-gradient(circle at 14% 20%, rgba(240, 135, 90, 0.20), transparent 28%),
      radial-gradient(circle at 88% 18%, rgba(68, 118, 109, 0.18), transparent 27%),
      linear-gradient(135deg, #fbf7ef 0%, #f3eee4 52%, #fffaf0 100%);
    box-shadow: 0 30px 80px rgba(42, 38, 31, 0.11);
  }
  .hero-kicker {
    color: #7a4a22;
  }
  .hero-title {
    color: #1d1b17;
    letter-spacing: -0.055em;
  }
  .hero-copy {
    color: #5f5a51;
  }
  .pill, .status-pill {
    background: rgba(255, 252, 244, 0.82);
    color: #2f2b25;
    border-color: rgba(32, 31, 28, 0.10);
  }
  .tour-card, .layer-card, .ddia-card, .mini-card, .story-card,
  .limit-card, .future-card, .friendly-card, .flow-card, .mini-node,
  .flow-lane, .status-board {
    border-color: rgba(32, 31, 28, 0.10);
    box-shadow: 0 20px 55px rgba(42, 38, 31, 0.08);
  }
  .tour-card strong, .layer-card strong, .ddia-card strong, .mini-card strong,
  .story-card strong, .limit-card strong, .future-card strong,
  .friendly-card h4, .flow-title, .lane-label, .status-title {
    color: #1d1b17;
    letter-spacing: -0.018em;
  }
  .tour-card .body, .layer-card .body, .ddia-card .body, .mini-card .body,
  .story-card .body, .limit-card .body, .future-card .body,
  .friendly-card p, .flow-card span, .mini-node span, .flow-note,
  .status-note {
    color: #625d54;
  }
  .tag {
    color: #2b2823;
    background: rgba(255, 252, 244, 0.82);
    border-color: rgba(32, 31, 28, 0.08);
  }
  .blue { background: linear-gradient(135deg, #e8f1ef, #fffaf2); }
  .green { background: linear-gradient(135deg, #e7f0df, #fffaf2); }
  .purple { background: linear-gradient(135deg, #ede7f4, #fffaf2); }
  .yellow { background: linear-gradient(135deg, #f8ecc9, #fffaf2); }
  .orange { background: linear-gradient(135deg, #f7dfc7, #fffaf2); }
  .rose { background: linear-gradient(135deg, #f5d8d3, #fffaf2); }
  .slate { background: linear-gradient(135deg, #ebe7df, #fffaf2); }
  .raw { background: #e8f1ef; }
  .batch { background: #e7f0df; }
  .stream { background: #f8ecc9; }
  .store { background: #ede7f4; }
  .ai { background: #f1dde9; }
  .pred { background: #f5d8d3; }
  .obs { background: #ebe7df; }
  .flow-wrap {
    background:
      radial-gradient(circle at 8% 12%, rgba(240, 135, 90, 0.14), transparent 28%),
      radial-gradient(circle at 82% 12%, rgba(68, 118, 109, 0.14), transparent 28%),
      linear-gradient(135deg, #fffaf2 0%, #f3eee4 100%);
  }
</style>
"""

GLOBAL_CSS = """
<style>
  :root {
    --ink: #1d1b17;
    --muted: #625d54;
    --paper: #fbf7ef;
    --panel: #fffaf2;
    --line: rgba(32, 31, 28, 0.10);
    --accent: #d97845;
    --accent-dark: #9d4f25;
    --green: #44766d;
    --sidebar: #181713;
  }
  .stApp {
    background:
      radial-gradient(circle at 30% -10%, rgba(217, 120, 69, 0.16), transparent 28%),
      radial-gradient(circle at 95% 10%, rgba(68, 118, 109, 0.13), transparent 30%),
      linear-gradient(180deg, #fbf7ef 0%, #f4efe5 100%);
    color: var(--ink);
  }
  [data-testid="stHeader"] {
    background: rgba(251, 247, 239, 0.72);
    backdrop-filter: blur(12px);
  }
  [data-testid="stAppViewContainer"] .main .block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 4rem;
  }
  h1, h2, h3 {
    color: var(--ink) !important;
    letter-spacing: -0.04em;
  }
  p, li, div, span {
    font-variant-ligatures: common-ligatures;
  }
  [data-testid="stSidebar"] {
    background:
      radial-gradient(circle at 10% 0%, rgba(217, 120, 69, 0.18), transparent 32%),
      linear-gradient(180deg, #1c1b17 0%, #11100d 100%);
    border-right: 1px solid rgba(255, 250, 242, 0.08);
  }
  [data-testid="stSidebar"] > div {
    padding: 2rem 1.25rem;
  }
  .sidebar-brand {
    color: #fffaf2;
    font-size: 2rem;
    line-height: 1;
    letter-spacing: -0.065em;
    font-weight: 820;
    margin: 0 0 0.45rem 0;
  }
  .sidebar-subtitle {
    color: rgba(255, 250, 242, 0.58);
    font-size: 0.82rem;
    line-height: 1.35;
    margin-bottom: 1.35rem;
  }
  .nav-label {
    color: rgba(255, 250, 242, 0.42);
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 800;
    margin: 1.25rem 0 0.45rem 0;
  }
  .nav-active {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    color: #fffaf2;
    background: rgba(255, 250, 242, 0.12);
    border: 1px solid rgba(255, 250, 242, 0.13);
    border-radius: 14px;
    padding: 0.72rem 0.82rem;
    font-weight: 760;
    margin: 0.18rem 0;
    box-shadow: inset 3px 0 0 #d97845;
  }
  .nav-dot {
    width: 0.48rem;
    height: 0.48rem;
    border-radius: 999px;
    background: #d97845;
    box-shadow: 0 0 0 5px rgba(217, 120, 69, 0.18);
  }
  [data-testid="stSidebar"] .stButton > button {
    justify-content: flex-start;
    width: 100%;
    border-radius: 14px;
    border: 1px solid transparent;
    background: transparent;
    color: rgba(255, 250, 242, 0.78);
    font-weight: 690;
    padding: 0.72rem 0.82rem;
    transition: all 160ms ease;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
    color: #fffaf2;
    background: rgba(255, 250, 242, 0.09);
    border-color: rgba(255, 250, 242, 0.11);
    transform: translateX(2px);
  }
  [data-testid="stSidebar"] hr {
    border-color: rgba(255, 250, 242, 0.10);
  }
  .stButton > button {
    border-radius: 999px;
    border: 1px solid var(--line);
    background: rgba(255, 250, 242, 0.82);
    color: var(--ink);
    font-weight: 720;
    box-shadow: 0 10px 25px rgba(42, 38, 31, 0.07);
    transition: all 160ms ease;
  }
  .stButton > button:hover {
    border-color: rgba(217, 120, 69, 0.36);
    color: var(--accent-dark);
    transform: translateY(-1px);
    box-shadow: 0 14px 34px rgba(42, 38, 31, 0.10);
  }
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1d1b17, #3a352c);
    color: #fffaf2;
    border-color: rgba(29, 27, 23, 0.9);
  }
  [data-testid="stAlert"] {
    background: rgba(255, 250, 242, 0.72);
    border: 1px solid var(--line);
    border-radius: 18px;
    color: var(--ink);
  }
  [data-testid="stMetric"] {
    background: rgba(255, 250, 242, 0.72);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1rem;
    box-shadow: 0 16px 40px rgba(42, 38, 31, 0.06);
  }
  div[data-testid="stExpander"] {
    border: 1px solid var(--line);
    border-radius: 18px;
    background: rgba(255, 250, 242, 0.62);
    overflow: hidden;
  }
  code, pre {
    border-radius: 16px !important;
  }
</style>
"""

HERO_HTML = """
<div class="ml-hero">
  <div class="hero-kicker">Educational data systems prototype</div>
  <div class="hero-title">MLStore-Lite follows one feature pipeline from storage internals to model predictions.</div>
  <div class="hero-copy">
    The app is a guided view of the project: run the final demo, inspect the
    architecture, connect each layer to DDIA ideas, and read the report notes
    without hunting through the repository.
  </div>
  <div class="hero-pills">
    <span class="pill">2 shards</span>
    <span class="pill">RF=3</span>
    <span class="pill">batch + stream features</span>
    <span class="pill">local observability</span>
    <span class="pill">online inference</span>
  </div>
</div>
"""

SYSTEM_FLOW_DOT = """
digraph {
    graph [
        rankdir=LR,
        bgcolor="transparent",
        pad="0.4",
        nodesep="0.55",
        ranksep="0.85"
    ];

    node [
        shape=box,
        style="rounded,filled",
        fontname="Helvetica",
        fontsize=12,
        color="#334155",
        penwidth=1.4,
        fillcolor="#f8fafc"
    ];

    edge [
        color="#475569",
        arrowsize=0.8,
        penwidth=1.5,
        fontname="Helvetica",
        fontsize=10
    ];

    events [label="Raw user events\\nclicks, purchases", fillcolor="#e0f2fe"];
    batch [label="Batch features\\nhistorical aggregates", fillcolor="#dcfce7"];
    stream_log [label="Event log\\nappend-only stream", fillcolor="#fef3c7"];
    stream [label="Stream features\\nwindowed updates", fillcolor="#fef3c7"];
    store [label="Sharded replicated\\nfeature store\\n2 shards, RF=3", fillcolor="#ede9fe"];
    serving [label="Online feature server\\nreads user features", fillcolor="#fae8ff"];
    model [label="Purchase intent model\\nprobability + confidence", fillcolor="#ffe4e6"];
    predictions [label="Prediction log\\nJSON-lines records", fillcolor="#fee2e2"];
    observability [label="Evaluation + observability\\ntimings, logs, results", fillcolor="#f1f5f9"];

    events -> batch [label="finite history"];
    events -> stream_log [label="new events"];
    stream_log -> stream [label="consumer + offsets"];
    batch -> store [label="write features"];
    stream -> store [label="update features"];
    store -> serving [label="low-latency reads"];
    serving -> model [label="feature vector"];
    model -> predictions [label="logged output"];
    store -> observability [label="measure"];
    predictions -> observability [label="inspect"];
}
"""

SYSTEM_FLOW_HTML = """
<div class="flow-wrap">
  <div class="flow-title">End-to-end data path</div>
  <div class="flow-lanes">
    <div class="flow-lane">
      <div class="lane-label">Historical lane: rebuild features from finite data</div>
      <div class="flow-row">
        <div class="flow-card raw">
          <strong>Raw events</strong>
          <span>clicks, purchases, timestamps</span>
        </div>
        <div class="flow-arrow">-&gt;</div>
        <div class="flow-card batch">
          <strong>Batch job</strong>
          <span>historical user aggregates</span>
        </div>
        <div class="flow-arrow">-&gt;</div>
        <div class="flow-card store">
          <strong>Feature store</strong>
          <span>sharded + replicated, RF=3</span>
        </div>
        <div class="flow-arrow">-&gt;</div>
        <div class="flow-card ai">
          <strong>Feature server</strong>
          <span>builds model input vector</span>
        </div>
        <div class="flow-arrow">-&gt;</div>
        <div class="flow-card pred">
          <strong>Prediction log</strong>
          <span>probability, confidence, warnings</span>
        </div>
      </div>
    </div>

    <div class="flow-lane">
      <div class="lane-label">Streaming lane: keep recent features moving forward</div>
      <div class="flow-row">
        <div class="flow-card raw">
          <strong>New events</strong>
          <span>append-only event stream</span>
        </div>
        <div class="flow-arrow">-&gt;</div>
        <div class="flow-card stream">
          <strong>Stream processor</strong>
          <span>offsets + tumbling windows</span>
        </div>
        <div class="flow-arrow">-&gt;</div>
        <div class="flow-card store">
          <strong>Feature store</strong>
          <span>windowed feature updates</span>
        </div>
        <div class="flow-arrow">-&gt;</div>
        <div class="flow-card obs">
          <strong>Observability</strong>
          <span>timings, JSONL logs, reports</span>
        </div>
      </div>
    </div>
  </div>

  <div class="flow-note">
    Batch computes historical features. Stream processing keeps recent features
    updated. The model does not own the data pipeline; it consumes the features
    produced by the previous layers.
  </div>
</div>
"""

MINI_DIAGRAM_HTML = """
<div class="mini-grid">
  <div class="mini-card blue">
    <strong>Storage node internals</strong>
    <div class="sub">One node persists data locally</div>
    <div class="mini-chain">
      <div class="mini-node"><span>WAL</span></div>
      <div class="mini-arrow">-&gt;</div>
      <div class="mini-node"><span>MemTable</span></div>
      <div class="mini-arrow">-&gt;</div>
      <div class="mini-node"><span>SSTables</span></div>
      <div class="mini-arrow">-&gt;</div>
      <div class="mini-node"><span>Compaction</span></div>
    </div>
  </div>

  <div class="mini-card green">
    <strong>Replication group</strong>
    <div class="sub">One logical shard has several copies</div>
    <div class="mini-chain">
      <div class="mini-node"><span>Leader</span></div>
      <div class="mini-arrow">-&gt;</div>
      <div class="mini-node"><span>Follower 1</span></div>
      <div class="mini-node"><span>Follower 2</span></div>
    </div>
  </div>

  <div class="mini-card purple">
    <strong>Sharding route</strong>
    <div class="sub">A key is sent to one shard group</div>
    <div class="mini-chain">
      <div class="mini-node"><span>feature key</span></div>
      <div class="mini-arrow">-&gt;</div>
      <div class="mini-node"><span>hash ring</span></div>
      <div class="mini-arrow">-&gt;</div>
      <div class="mini-node"><span>shard-a or shard-b</span></div>
    </div>
  </div>

  <div class="mini-card rose">
    <strong>Inference path</strong>
    <div class="sub">The model consumes stored features</div>
    <div class="mini-chain">
      <div class="mini-node"><span>features</span></div>
      <div class="mini-arrow">-&gt;</div>
      <div class="mini-node"><span>score</span></div>
      <div class="mini-arrow">-&gt;</div>
      <div class="mini-node"><span>prediction log</span></div>
    </div>
  </div>
</div>
"""


def read_doc(relative_path: str) -> str:
    path = ROOT_DIR / relative_path
    return path.read_text(encoding="utf-8")


def weekly_note_paths() -> list[Path]:
    return sorted(WEEKLY_NOTES_DIR.glob("*.md"))


def render_html(components_module, html: str, height: int) -> None:
    components_module.html(APP_CSS + html, height=height, scrolling=False)


def card_grid(items: list[dict], grid_class: str, card_class: str) -> str:
    cards = [f'<div class="{grid_class}">']
    for item in items:
        cards.append(
            f"""
            <div class="{card_class} {item.get('class', 'slate')}">
              <strong>{item['title']}</strong>
              <div class="sub">{item.get('subtitle', '')}</div>
              <div class="body">{item['body']}</div>
              <span class="tag">{item.get('tag', '')}</span>
            </div>
            """
        )
    cards.append("</div>")
    return "".join(cards)


def go_to(st_module, page: str) -> None:
    st_module.session_state["current_page"] = page
    st_module.rerun()


def page_button(
    st_module,
    label: str,
    page: str,
    key: str,
    button_type: str = "secondary",
) -> None:
    if st_module.button(label, key=key, type=button_type, use_container_width=True):
        go_to(st_module, page)


def render_page_buttons(st_module, buttons: list[tuple[str, str, str]]) -> None:
    columns = st_module.columns(len(buttons))
    for column, (label, page, key) in zip(columns, buttons):
        with column:
            page_button(st_module, label, page, key)


def sidebar_page_button(st_module, label: str, page: str, key: str) -> None:
    if st_module.sidebar.button(label, key=key, use_container_width=True):
        go_to(st_module, page)


def render_sidebar_navigation(st_module) -> None:
    st_module.sidebar.markdown(
        """
        <div class="sidebar-brand">MLStore-Lite</div>
        <div class="sidebar-subtitle">
          A guided walkthrough of a local data-systems and ML infrastructure prototype.
        </div>
        <div class="nav-label">Navigate</div>
        """,
        unsafe_allow_html=True,
    )

    for index, page in enumerate(PAGES):
        if page == st_module.session_state["current_page"]:
            st_module.sidebar.markdown(
                f"""
                <div class="nav-active">
                  <span class="nav-dot"></span>
                  <span>{page}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            sidebar_page_button(
                st_module,
                page,
                page,
                f"sidebar_nav_{index}_{page.lower().replace(' ', '_')}",
            )

    st_module.sidebar.markdown(
        """
        <div class="nav-label">Shortcuts</div>
        """,
        unsafe_allow_html=True,
    )
    sidebar_page_button(st_module, "Start guided tour", "Home", "sidebar_home")
    sidebar_page_button(st_module, "Run final demo", "Demo", "sidebar_demo")
    sidebar_page_button(st_module, "Read report", "Final Report", "sidebar_report")


def render_home(st_module, components_module) -> None:
    tour_items = [
        {
            "title": "1. Architecture",
            "subtitle": "Start with the shape of the system",
            "body": "See how storage, replication, sharding, batch, stream, observability, and inference connect.",
            "tag": "Architecture tab",
            "class": "blue",
        },
        {
            "title": "2. Final demo",
            "subtitle": "Run the pipeline",
            "body": "Execute one local flow from raw events to feature values and prediction records.",
            "tag": "Demo tab",
            "class": "green",
        },
        {
            "title": "3. Results",
            "subtitle": "Look at the evidence",
            "body": "Inspect local timings, shard distribution, scaling experiments, and model outputs.",
            "tag": "Results tab",
            "class": "yellow",
        },
        {
            "title": "4. Report",
            "subtitle": "Read the submission story",
            "body": "Use the report, limitations, and future-work pages as the final explanation layer.",
            "tag": "Report tab",
            "class": "rose",
        },
    ]
    columns = st_module.columns(4)
    buttons = [
        ("Open Architecture", "Architecture", "home_architecture"),
        ("Run Demo", "Demo", "home_demo"),
        ("Inspect Results", "Results", "home_results"),
        ("Read Report", "Final Report", "home_report"),
    ]
    for column, item, (label, page, key) in zip(columns, tour_items, buttons):
        with column:
            render_html(
                components_module,
                card_grid([item], "tour-grid", "tour-card"),
                height=210,
            )
            page_button(st_module, label, page, key, button_type="primary")


def render_status_badges(components_module) -> None:
    badges = [
        """
        <div class="status-board">
          <div class="status-title">Implementation status</div>
          <div class="status-note">Green means implemented locally. Red means intentionally out of scope.</div>
          <div class="status-row">
        """
    ]
    for name, status, note in STATUS_ITEMS:
        css_class = "implemented" if status == "Implemented" else "not-implemented"
        badges.append(
            f"""
            <span class="status-pill {css_class}">
              {name}: {status} - {note}
            </span>
            """
        )
    badges.append("</div></div>")
    render_html(components_module, "".join(badges), 250)


def render_layer_cards(components_module) -> None:
    render_html(
        components_module,
        card_grid(LAYER_CARDS, "layer-grid", "layer-card"),
        height=420,
    )


def render_ddia_connections(st_module, components_module) -> None:
    cards = ['<div class="ddia-grid">']
    for item in DDIA_CONNECTIONS:
        cards.append(
            f"""
            <div class="ddia-card">
              <strong>{item['chapter']}: {item['topic']}</strong>
              <div class="sub">Implemented in MLStore-Lite</div>
              <div class="body">{item['implemented']}</div>
              <span class="tag">Simplified boundary</span>
              <div class="body" style="margin-top: 9px;">{item['simplified']}</div>
            </div>
            """
        )
    cards.append("</div>")
    render_html(components_module, "".join(cards), height=610)
    st_module.caption(
        "This is a project-to-book map in original words. It avoids copying DDIA text "
        "and instead explains what each chapter inspired in the implementation."
    )


def render_demo_intro(st_module, components_module) -> None:
    col1, col2, col3 = st_module.columns(3)
    with col1:
        render_html(
            components_module,
            """
            <div class="friendly-card blue">
              <h4>1. Produce features</h4>
              <p>Historical events go through batch processing. New events go through the local stream log.</p>
            </div>
            """,
            height=155,
        )
    with col2:
        render_html(
            components_module,
            """
            <div class="friendly-card green">
              <h4>2. Store them safely</h4>
              <p>Feature keys are routed to shards. Each shard has three local replicas.</p>
            </div>
            """,
            height=155,
        )
    with col3:
        render_html(
            components_module,
            """
            <div class="friendly-card rose">
              <h4>3. Serve the model</h4>
              <p>The AI layer reads features, scores purchase intent, and logs predictions.</p>
            </div>
            """,
            height=155,
        )


def render_demo_story(components_module, result: dict) -> None:
    shard_count = len(result["shard_distribution"])
    story_items = [
        {
            "title": "Raw history became features",
            "subtitle": f"{result['batch_event_count']} events -> {result['batch_feature_count']} feature writes",
            "body": "Batch processing summarizes finite historical data into reusable feature keys.",
            "tag": "batch lane",
            "class": "green",
        },
        {
            "title": "New events moved through offsets",
            "subtitle": f"{result['stream_event_count']} events -> offset {result['consumer_offset']}",
            "body": "The stream processor records how far it has read so the pipeline can continue later.",
            "tag": "stream lane",
            "class": "orange",
        },
        {
            "title": "Keys were partitioned",
            "subtitle": f"features spread across {shard_count} shard groups",
            "body": "The shard distribution table shows consistent hashing in a visible, local form.",
            "tag": "partitioning",
            "class": "purple",
        },
        {
            "title": "Users were scored",
            "subtitle": f"{result['prediction_count']} prediction records",
            "body": "The model consumes the feature store rather than bypassing the data-system layers.",
            "tag": "inference",
            "class": "rose",
        },
    ]
    render_html(
        components_module,
        card_grid(story_items, "story-grid", "story-card"),
        height=270,
    )


def render_prediction_table(st_module, predictions: list[dict]) -> None:
    st_module.table(
        [
            {
                "user_id": prediction["user_id"],
                "probability": prediction["purchase_probability"],
                "confidence": prediction["confidence"],
                "label": prediction["label"],
                "warnings": ", ".join(prediction["warnings"]),
            }
            for prediction in predictions
        ]
    )


def render_limitations(components_module) -> None:
    items = [
        {
            "title": title,
            "subtitle": "Intentional scope boundary",
            "body": body,
            "tag": "limitation",
            "class": "slate",
        }
        for title, body in LIMITATIONS
    ]
    render_html(components_module, card_grid(items, "limit-grid", "limit-card"), 455)


def render_future_work(components_module) -> None:
    items = [
        {
            "title": title,
            "subtitle": "Possible next iteration",
            "body": body,
            "tag": "future work",
            "class": "blue",
        }
        for title, body in FUTURE_WORK
    ]
    render_html(components_module, card_grid(items, "future-grid", "future-card"), 455)


def split_markdown_sections(markdown: str) -> tuple[str, list[tuple[str, str]]]:
    lines = markdown.splitlines()
    intro_lines = []
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        if line.startswith("## "):
            if current_title is None:
                intro_lines = current_lines
            else:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line.replace("## ", "", 1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_title is None:
        intro_lines = current_lines
    else:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return "\n".join(intro_lines).strip(), sections


def main() -> None:
    try:
        import streamlit as st
        import streamlit.components.v1 as components
    except ImportError as exc:
        raise SystemExit(
            "Streamlit is optional. Install it with: python -m pip install '.[ui]'"
        ) from exc

    st.set_page_config(page_title="MLStore-Lite Final Demo", layout="wide")
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Home"
    if st.session_state["current_page"] not in PAGES:
        st.session_state["current_page"] = "Home"

    render_sidebar_navigation(st)

    render_html(components, HERO_HTML, height=285)
    page = st.session_state["current_page"]

    if page == "Home":
        st.subheader("Guided Tour")
        st.info(
            "If this is your first time opening the project, follow these four "
            "steps. The app is designed to be read like a small project museum, "
            "not just a dashboard."
        )
        render_home(st, components)
        st.subheader("Current Implementation Status")
        render_status_badges(components)
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("Go to Architecture", "Architecture", "home_continue_architecture"),
                ("Run the Demo", "Demo", "home_continue_demo"),
                ("Open DDIA Map", "DDIA", "home_continue_ddia"),
            ],
        )

    elif page == "Demo":
        st.subheader("Run The Full Local Pipeline")
        st.info(
            "This button runs the same path the final report describes: raw events "
            "-> batch and stream feature computation -> sharded replicated feature "
            "store -> online feature serving -> model prediction log."
        )
        render_demo_intro(st, components)

        st.code("python -m mlstore_lite.experiments.final_demo", language="bash")

        if st.button("Run demo", type="primary"):
            with st.spinner("Running the local feature pipeline..."):
                result = run_final_demo()

            st.success("The full local pipeline completed successfully.")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Batch features", result["batch_feature_count"])
            col2.metric("Stream features", result["stream_feature_count"])
            col3.metric("Predictions", result["prediction_count"])
            col4.metric("Consumer offset", result["consumer_offset"])

            st.subheader("What Happened")
            render_demo_story(components, result)

            left, right = st.columns([1, 1.35])
            with left:
                st.subheader("Shard Distribution")
                st.table(
                    [
                        {"shard": shard, "keys": key_count}
                        for shard, key_count in result["shard_distribution"].items()
                    ]
                )
                st.caption(
                    "This is the visible result of partitioning: different feature "
                    "keys land on different shard groups."
                )

            with right:
                st.subheader("Predictions")
                render_prediction_table(st, result["predictions"])
                st.caption(
                    "The warnings are intentionally useful: they show when the model "
                    "is scoring with missing or incomplete feature context."
                )

            st.subheader("Generated Output")
            st.code(
                f"base_dir={result['base_dir']}\n"
                f"prediction_log={result['prediction_log_path']}",
                language="text",
            )
        else:
            st.info("Click 'Run demo' to execute the full local pipeline.")
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("Architecture", "Architecture", "demo_continue_architecture"),
                ("Results", "Results", "demo_continue_results"),
                ("Final Report", "Final Report", "demo_continue_report"),
            ],
        )

    elif page == "Architecture":
        st.subheader("System Flow")
        st.caption("Follow the data from raw events to logged model predictions.")
        render_html(components, SYSTEM_FLOW_HTML, height=455)

        st.subheader("Mini Diagrams")
        st.caption("The same architecture split into smaller ideas.")
        render_html(components, MINI_DIAGRAM_HTML, height=500)

        st.subheader("Layer Guide")
        render_layer_cards(components)

        st.subheader("Status Badges")
        render_status_badges(components)

        try:
            with st.expander("Show graph version"):
                st.graphviz_chart(SYSTEM_FLOW_DOT, use_container_width=True)
        except Exception:
            st.code(SYSTEM_FLOW_DOT, language="dot")

        with st.expander("Read architecture notes"):
            st.markdown(read_doc("docs/architecture.md"))
        with st.expander("Read cloud architecture sketch"):
            st.markdown(read_doc("docs/cloud-architecture.md"))
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("DDIA Connections", "DDIA", "architecture_continue_ddia"),
                ("Run Demo", "Demo", "architecture_continue_demo"),
                ("Limitations", "Limitations", "architecture_continue_limitations"),
            ],
        )

    elif page == "DDIA":
        st.subheader("DDIA Connections")
        st.info(
            "This page connects each implementation milestone to the DDIA idea it "
            "was meant to make visible. It is intentionally specific about what is "
            "implemented and what remains simplified."
        )
        render_ddia_connections(st, components)
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("Results", "Results", "ddia_continue_results"),
                ("Final Report", "Final Report", "ddia_continue_report"),
                ("Limitations", "Limitations", "ddia_continue_limitations"),
            ],
        )

    elif page == "Results":
        st.subheader("Representative Local Results")
        st.info(
            "These numbers are laptop-scale observations, not production benchmarks. "
            "Their value is educational: they make throughput, shard distribution, "
            "model outputs, and observability records visible."
        )
        st.markdown(read_doc("docs/final-report-draft/results.md"))
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("Run Demo", "Demo", "results_continue_demo"),
                ("Final Report", "Final Report", "results_continue_report"),
                ("Future Work", "Future Work", "results_continue_future"),
            ],
        )

    elif page == "Final Report":
        st.subheader("Final Report Draft")
        st.info(
            "The report is split into expandable sections here so it is easier to "
            "browse in the app than as one long wall of text."
        )
        report_intro, report_sections = split_markdown_sections(
            read_doc("docs/final-report-draft/final-report.md")
        )
        if report_intro:
            st.markdown(report_intro)
        for title, body in report_sections:
            expanded = title.startswith("1.") or title.startswith("2.")
            with st.expander(title, expanded=expanded):
                st.markdown(body)
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("Results", "Results", "report_continue_results"),
                ("Limitations", "Limitations", "report_continue_limitations"),
                ("Future Work", "Future Work", "report_continue_future"),
            ],
        )

    elif page == "Weekly Notes":
        st.subheader("Weekly Notes")
        st.info(
            "Use these as the learning diary. They are more detailed than the final "
            "report and useful when you want to remember why a layer was added."
        )
        notes = weekly_note_paths()
        selected = st.selectbox(
            "Choose a weekly note",
            notes,
            format_func=lambda path: path.name,
        )
        st.markdown(selected.read_text(encoding="utf-8"))
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("Architecture", "Architecture", "notes_continue_architecture"),
                ("DDIA Connections", "DDIA", "notes_continue_ddia"),
                ("Final Report", "Final Report", "notes_continue_report"),
            ],
        )

    elif page == "Limitations":
        st.subheader("Limitations")
        st.info(
            "These limitations are not failures. They define the boundary between "
            "an educational prototype and a production distributed system."
        )
        render_limitations(components)
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("Future Work", "Future Work", "limitations_continue_future"),
                ("Final Report", "Final Report", "limitations_continue_report"),
                ("Home", "Home", "limitations_continue_home"),
            ],
        )

    elif page == "Future Work":
        st.subheader("Future Work")
        st.info(
            "These ideas would deepen the project without changing its identity as "
            "a learning repo. They are good candidates after submission."
        )
        render_future_work(components)
        st.subheader("Continue")
        render_page_buttons(
            st,
            [
                ("Home", "Home", "future_continue_home"),
                ("Final Report", "Final Report", "future_continue_report"),
                ("Weekly Notes", "Weekly Notes", "future_continue_notes"),
            ],
        )


if __name__ == "__main__":
    main()
