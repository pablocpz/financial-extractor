**Useful links**

https://github.com/PritiG1/Multimodal-RAG/blob/main/src/chunk_embed.py

https://medium.com/@pritigupta.ds/docling-powered-rag-querying-over-complex-pdfs-d99f5f58bc33


CHATGPT CONV
https://chatgpt.com/share/68b00262-4898-800b-8f7e-23b10967c6fa


**RAG OVER COMPLEX MULTIMODAL MARKDOWN PDFS w/ docling**

----------------------
⸻

1. Why RAG in this context?

Think of your quarterly reports:
	•	Each report can be dozens of pages, sometimes with text + tables + images.
	•	You want to pull specific fields (NAV, valuation date, commitments, distributions, fees, etc.).
	•	If you naively send the whole document to the LLM for extraction:
	•	You hit the context window limit (10k–200k tokens depending on the model).
	•	You pay more in tokens and latency.
	•	The model’s accuracy drops, because it has to search a haystack of irrelevant text.

👉 RAG solves this:
Instead of sending everything, you retrieve only the chunks that are most likely to contain each field. That way:
	•	You stay under context budget.
	•	The LLM sees only relevant evidence, boosting precision.
	•	It scales to hundreds of reports over time.


**STEPS FOR THIS (BASELINE)**


1) Ingest & normalize (Markdown + external images)
	•	Parse Markdown structurally (don’t treat it as plain text): keep block boundaries, headings (#..####), lists, code fences, and tables. Persist a clean AST plus raw text for each node.
	•	Link + image resolution: for each ![alt](url) store {doc_id, section_path, img_url, alt}.
	•	If images can contain values you need (tables/figures), run captioning + OCR at ingest and store the text alongside the chunk (cheap at query-time). BLIP-2 is a strong captioner; pair with OCR (Tesseract or docTR) for text in charts/tables.  ￼ ￼ ￼
	•	Housekeeping: strip boilerplate (TOCs, disclaimers), normalize whitespace/currency symbols, fix malformed tables, hash each node for dedupe, and record byte/line offsets for provenance.

2) Chunking (Markdown-aware, table-safe)
	•	Split on headings first, then enforce a max token window (e.g., 400–800 tokens) with ~10–15% overlap. Keep tables whole with their header row. Libraries like LangChain’s MarkdownHeaderTextSplitter or LlamaIndex’s Markdown node parsers are good references.  ￼ ￼ ￼
	•	Metadata: store doc_id, section_path (e.g., Overview/NAV/2025-Q2), token_count, and any img_caption_ocr strings tied to this chunk.

3) Index (hybrid retrieval + optional reranking)
	•	Hybrid search reliably beats “dense only” or “BM25 only” for messy, financial text: build BM25 for exact term recall + a dense index (FAISS/Qdrant) for semantics; combine scores or do reciprocal-rank fusion.  ￼ ￼
	•	Rerank (optional but effective): apply a cross-encoder (e.g., BAAI bge-reranker) on the top-K to sharpen precision before you spend tokens. Be mindful of cost at scale.  ￼ ￼
	•	Images: index captions/OCR text alongside the same chunk_id. If you truly need visual search, add a CLIP image-embedding index keyed to the chunk.  ￼

4) Retrieval (field-scoped, budget-aware)

For each target field in your schema (e.g., NAV_Date, NAV_Value, Commitments_QTD, Distributions_QTD, Management_Fee):
	•	Build field-specific queries + synonyms:
	•	NAV_Date: “NAV as of”, “valuation date”, “NAV date”, “NAV @”.
	•	Commitments: “capital commitments”, “total commitments”, “committed capital”, etc.
	•	Stage 1 (recall): fetch ~20–50 candidates via hybrid retrieval; filter by section_path patterns (e.g., “Financials”, “Capital Account”, “Management Fee”).
	•	Stage 2 (precision): rerank to top 3–6 chunks, ensuring total ≤ your token budget (e.g., <2–3k tokens/extraction call). Maintain a field→chunk map so different fields can reuse overlapping chunks without duplicate tokens.  ￼ ￼
	•	Images: by default pass caption/OCR text. Only pass the image itself to a multimodal model if the value clearly depends on a figure/screenshot table.  ￼

5) Extraction (strict schema, citations, retries)
	•	Use Structured Outputs (JSON Schema) so the model must return exactly your schema. Provide enums, formats (date, currency), and examples. Validate with jsonschema/Pydantic; retry with a shorter prompt if validation fails.  ￼ ￼ ￼
	•	Map→Reduce extraction:
	•	Map: run extraction per retrieved chunk (cheap, parallel).
	•	Reduce: merge candidates per field using confidence + business rules; keep provenance {doc_id, section_path, line_offset | table_ref | img_url}. This mirrors standard map-reduce summarization patterns.  ￼
	•	Confidence: combine (a) reranker score, (b) lexical hits (e.g., presence of “as of”), (c) JSON Schema validation success, and (d) optional LLM self-estimated confidence.

6) Keep context under control
	•	Never stuff full reports. Impose hard caps: e.g., max 6 chunks per call, ≤3k input tokens.
	•	Add few, surgical exemplars (1–2) and compress long instruction blocks with LLMLingua / LongLLMLingua / LLMLingua-2 to preserve guidance while fitting the window.  ￼
	•	Cache per-section headnotes (short factual bullet digests) at ingest; retrieve headnotes instead of full text unless ambiguity remains.

7) Post-processing & QA (finance-specific)
	•	Normalization: unify currencies (store value + currency), parse NAV_Date to ISO-8601, parse human numerals (“€1.2bn”→1200000000 w/ magnitude=bn).
	•	Arithmetic checks:
	•	Ending_NAV = Beginning_NAV + Contributions – Distributions ± P&L ± Fees (tolerances for rounding).
	•	Quarter deltas consistent with YTD.
	•	Provenance first-class: attach the exact source section lines (and image URL if used) for each field → makes audits painless.

8) When to send pixels (vs. text about pixels)
	•	Default: only pass caption/OCR strings from images—nearly free in tokens and good enough for most tables/charts.
	•	Send the image only when (detectors): (i) chunk has a table screenshot with numbers but weak OCR confidence, (ii) caption is vague, or (iii) the value is visually encoded (e.g., a figure footnote). Use a multimodal call for just those fields.  ￼

⸻

Practical wiring (minimal, production-lean)

Data model

Chunk(id, doc_id, section_path, text, tokens, img_caption_ocr:list[str], offsets, hash)
ImageRef(doc_id, section_path, url, alt, caption, ocr_text)

Index
	•	BM25: Elastic/Lucene or Tantivy.
	•	Dense: FAISS (IVF/HNSW) or Qdrant; store embedding + chunk_id.  ￼
	•	(Optional) Rerank: BAAI/bge-reranker-large as a service; score top-K then keep top-M.  ￼

Retrieval per field

query = field_templates[field_name](synonyms, company, quarter, doc_date)
cands = hybrid_search(query, top_k=50) → filter by section_path → rerank → top_m=3–6

Extraction call (strict JSON)
	•	Use OpenAI Structured Outputs with your JSON Schema (or Pydantic model_json_schema()), set response format to schema; include just the selected chunks, a short instruction, 1–2 examples, and a hard max_input_tokens. Validate → retry on fail.  ￼

Aggregation
	•	If multiple chunks claim the same field: prefer (1) exact phrase anchors (“NAV as of”), then (2) highest rerank score, then (3) most recent date within quarter; attach all candidate provenances for audit.

QA rules (examples)
	•	Dates inside quarter; currency consistent with company base; MgmtFee ~ mgmt_rate × committed/invested within tolerance; reject if any required term missing in the source snippet.

Logging
	•	Save the prompt hash, selected chunk ids, and schema validation events. This makes drift, failures, and cost visible.

⸻

What you gain vs. “send the whole report”
	•	Scales to hundreds of reports without blowing context windows (hard caps + hybrid retrieval).  ￼
	•	Higher precision on the right sections (cross-encoder reranking when needed).  ￼
	•	Deterministic outputs via Structured Outputs + JSON Schema validation.  ￼
	•	Token efficiency via LLMLingua-style prompt compression for instructions/examples.  ￼
	•	Images handled without always paying multimodal costs (caption/OCR first, pixels only on demand).  ￼

⸻

If you want, I can tailor this to your exact schema (e.g., your NAV_Date, Valuation_Date, FONDO_TARGET_ASSET, etc.) and sketch the concrete Python code (ingestion, hybrid retrieval, structured extraction, validators).