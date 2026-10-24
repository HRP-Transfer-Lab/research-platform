# Runnable synthetic example

This fixture contains only synthetic text and can be committed safely.

From `UoE/module-knowledge-graph/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/module_graph.py ingest \
  examples/unit-template/unit.yaml \
  --out outputs/example-week-01/canonical_graph.json
```

This first command creates reading and passage nodes with stable provenance and hashes. It does **not** yet infer concepts or edges.

After reviewed concept/relation records have been added to the graph, the current projection command is:

```bash
python src/module_graph.py reading-map \
  outputs/example-week-01/canonical_graph.json \
  --out outputs/example-week-01/reading_map.md
```

Next adapters will add:

1. Ollama/Qwen embedding of passages;
2. similarity-based candidate concept clusters;
3. constrained LLM extraction into candidate nodes and edges;
4. reconciliation and human review;
5. generators for all nine teaching views.
