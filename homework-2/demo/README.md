# Demo

**Author:** Vitalii Roditieliev

A runnable end-to-end demo of the Intelligent Customer Support System.

```bash
./demo/demo.sh
```

The script is fully self-contained: it starts its own server on port 8030
with a throwaway database, walks through the complete feature set, and
cleans up after itself (kills the server, deletes the demo DB).
Requirements: `uv`, `curl`, `python3` — nothing else.

## What it shows, in order

1. Creating a single ticket (as if submitted from a web form)
2. Auto-classification with explainable output — matched keywords,
   reasoning, confidence score
3. Bulk import of 50 tickets from CSV with on-the-fly classification
4. Importing a file with broken records — per-record error reporting
   (valid records accepted, each rejected one explained)
5. A structurally malformed file returning a clean 400, never a crash
6. Filtering: urgent tickets first
7. Combined filtering: category + priority
8. Manual override of an automatic decision (tracked as `manual`,
   confidence 1.0)
9. The classification audit log holding both the automatic and the manual
   decision with reasoning

A captured run is in [transcript.md](transcript.md) if you want to see the
output without running anything.
