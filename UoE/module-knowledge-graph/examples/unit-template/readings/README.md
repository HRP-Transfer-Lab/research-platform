# Reading inputs

For the bootstrap milestone, place **locally extracted text or Markdown** here using the filenames referenced by `unit.yaml`.

Example:

```text
R1.md
R2.md
R3.md
R4.md
```

Recommended structure:

```markdown
# Article or chapter title

## Section heading

Paragraph text...

## Next section

Paragraph text...
```

Do not commit copyrighted PDFs or full licensed readings to a public repository unless you have the right to do so.

For real modules, a safer default is:

1. keep original PDFs/DOCX files locally;
2. run extraction locally;
3. keep the private extracted corpus outside Git where required;
4. commit only schemas, manifests, reviewed graph records and short provenance-safe excerpts where licensing permits.

Future ingestion adapters can read PDF/DOCX locally and emit the same passage contract used by the core engine.
