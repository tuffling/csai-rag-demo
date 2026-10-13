# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#     "fastembed>=0.7,<1",
#     "numpy>=1.26",
#     "rich>=13",
#     "pyperclip>=1.8",
# ]
# ///
"""
A tiny RAG (Retrieval-Augmented Generation) demo, built for the CSAI club.

    uv run rag.py                  # interactive mode
    uv run rag.py --setup          # just download everything (do this before the meeting!)
    uv run rag.py --ask "How many PTO days do I get?"
    uv run rag.py --docs tacobell  # use a different knowledge base (any folder in docs/)

The pipeline, the same as on the slides:
    1. INGESTION   docs/<name>/*.md  ->  chunks  ->  embedding vectors
    2. RETRIEVAL   question  ->  vector  ->  cosine similarity  ->  top-k chunks
    3. AUGMENT     stuff the top-k chunks into a prompt
    4. GENERATE    paste that prompt into any chatbot (ChatGPT, Gemini, ...)
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# ---------------------------------------------------------------------------
# SETTINGS: try changing these!
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
DOCS_ROOT = HERE / "docs"  # every folder in here is a knowledge base (.md / .txt files)
DEFAULT_DOCS = "quokka"  # the knowledge base we start with
CACHE_DIR = HERE / ".cache"  # downloaded model + saved vectors live here

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # ~90 MB, 384 dimensions
CHUNK_SIZE = 60  # words per chunk
OVERLAP = 15  # words shared between neighbouring chunks
TOP_K = 3  # how many chunks we retrieve per question

PROMPT_TEMPLATE = """\
You are a helpful assistant. Answer the question using ONLY the context below.
If the answer is not in the context, say "I don't know based on the provided documents."
At the end, cite the source file name(s) you used.

### Context
{context}

### Question
{question}
"""

console = Console()


# ---------------------------------------------------------------------------
# The embedding model (turns text into vectors)
# ---------------------------------------------------------------------------

_model = None


def get_model():
    """Load the embedding model. The first run downloads it into .cache/models."""
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        console.print(f"Loading embedding model [bold]{EMBEDDING_MODEL}[/] ...")
        try:
            _model = TextEmbedding(
                model_name=EMBEDDING_MODEL, cache_dir=str(CACHE_DIR / "models")
            )
        except Exception as error:
            console.print(f"[red]{error}[/]")
            sys.exit(
                "Couldn't download the embedding model. Check your internet connection and try "
                "again in a minute (Hugging Face, where the model lives, is sometimes down)."
            )
    return _model


def normalize(vectors: np.ndarray) -> np.ndarray:
    """Scale every vector to length (magnitude) 1."""
    return vectors / np.linalg.norm(vectors, axis=-1, keepdims=True)


def embed_passages(texts: list[str]) -> np.ndarray:
    return normalize(np.array(list(get_model().passage_embed(texts))))


def embed_query(text: str) -> np.ndarray:
    return normalize(np.array(list(get_model().query_embed(text)))[0])


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """cos(angle) = (A . B) / (|A| * |B|)"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ---------------------------------------------------------------------------
# STEP 1: INGESTION. Load docs, split them into chunks, embed the chunks.
# ---------------------------------------------------------------------------


def available_docs() -> list[str]:
    return sorted(p.name for p in DOCS_ROOT.iterdir() if p.is_dir())


def load_documents(docs_name: str) -> list[tuple[str, str]]:
    folder = DOCS_ROOT / docs_name
    files = sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in {".md", ".txt"} and p.name.lower() != "readme.md"
    )
    docs = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)  # notes for humans, not for the model
        docs.append((p.name, text))
    return docs


def chunk_text(text: str) -> list[str]:
    """Slide a window of CHUNK_SIZE words over the text, stepping CHUNK_SIZE - OVERLAP."""
    words = text.split()
    step = CHUNK_SIZE - OVERLAP
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start : start + CHUNK_SIZE]))
        if start + CHUNK_SIZE >= len(words):
            break
    return chunks


def build_index(docs_name: str) -> tuple[list[dict], np.ndarray]:
    """Returns (chunks, vectors). Re-uses the saved vectors if nothing changed."""
    if not 0 <= OVERLAP < CHUNK_SIZE:
        sys.exit("OVERLAP must be smaller than CHUNK_SIZE (and not negative).")
    if not (DOCS_ROOT / docs_name).is_dir():
        sys.exit(f"No folder docs/{docs_name}. Available: {', '.join(available_docs())}")

    docs = load_documents(docs_name)
    if not docs:
        sys.exit(f"No .md or .txt files found in docs/{docs_name}")

    fingerprint = hashlib.sha256(
        json.dumps([EMBEDDING_MODEL, CHUNK_SIZE, OVERLAP, docs]).encode()
    ).hexdigest()
    index_file = CACHE_DIR / f"index-{docs_name}.json"
    vectors_file = CACHE_DIR / f"vectors-{docs_name}.npy"

    if index_file.exists() and vectors_file.exists():
        saved = json.loads(index_file.read_text(encoding="utf-8"))
        if saved["fingerprint"] == fingerprint:
            vectors = np.load(vectors_file)
            console.print(
                f"[dim]Loaded docs/{docs_name}: {len(docs)} docs -> {len(saved['chunks'])} chunks "
                f"-> vectors of shape {vectors.shape}[/]"
            )
            return saved["chunks"], vectors

    chunks = [
        {"source": name, "text": piece}
        for name, text in docs
        for piece in chunk_text(text)
    ]
    console.print(f"[bold]Ingesting[/] docs/{docs_name}: {len(docs)} docs -> {len(chunks)} chunks ...")
    vectors = embed_passages([c["text"] for c in chunks])
    console.print(f"Embedded! Our 'vector database' is a matrix of shape {vectors.shape}")

    CACHE_DIR.mkdir(exist_ok=True)
    np.save(vectors_file, vectors)
    index_file.write_text(
        json.dumps({"fingerprint": fingerprint, "chunks": chunks}), encoding="utf-8"
    )
    return chunks, vectors


# ---------------------------------------------------------------------------
# STEP 2: RETRIEVAL. Find the chunks whose vectors point the same way as the question.
# ---------------------------------------------------------------------------


def retrieve(question: str, chunks, vectors, k: int) -> list[tuple[float, dict]]:
    q = embed_query(question)
    # All vectors have length 1, so cosine similarity is just a dot product.
    # One matrix multiply = the similarity of the question to EVERY chunk at once.
    scores = vectors @ q
    best = np.argsort(scores)[::-1][:k]
    return [(float(scores[i]), chunks[i]) for i in best]


STOPWORDS = set(
    "a an and are at be by can do does for from how i in is it my of on or our "
    "the to was we what when where which who why will with you your".split()
)


def words_of(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOPWORDS


def keyword_search(question: str, chunks, k: int) -> list[tuple[float, dict]]:
    """Old-school search for comparison: what fraction of the question's words appear?"""
    q_words = words_of(question)
    if not q_words:
        return []
    scored = [(len(q_words & words_of(c["text"])) / len(q_words), c) for c in chunks]
    scored = [pair for pair in scored if pair[0] > 0]  # no shared words = no match at all
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


# ---------------------------------------------------------------------------
# STEP 3: AUGMENT. Put the retrieved chunks into the prompt.
# ---------------------------------------------------------------------------


def build_prompt(question: str, hits: list[tuple[float, dict]]) -> str:
    context = "\n\n".join(
        f"[{n}] (source: {chunk['source']})\n{chunk['text']}"
        for n, (_, chunk) in enumerate(hits, start=1)
    )
    return PROMPT_TEMPLATE.format(context=context, question=question)


# ---------------------------------------------------------------------------
# STEP 4: GENERATE. We don't run an LLM here: you paste the prompt into one!
# ---------------------------------------------------------------------------


def copy_to_clipboard(text: str) -> bool:
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception:
        return False


def hand_off(prompt: str) -> None:
    (HERE / "prompt.txt").write_text(prompt, encoding="utf-8")
    console.print(Panel(prompt, title="Augmented prompt", border_style="green"))
    if copy_to_clipboard(prompt):
        where = "[bold green]Copied to your clipboard[/] (also saved to prompt.txt)."
    else:
        where = "Saved to [bold]prompt.txt[/] (couldn't reach your clipboard)."
    console.print(f"{where} Paste it into ChatGPT, Gemini, or any chatbot.\n")


# ---------------------------------------------------------------------------
# Pretty printing + the interactive loop
# ---------------------------------------------------------------------------


def results_table(title: str, hits, score_label: str) -> Table:
    table = Table(title=title, title_justify="left", show_lines=True)
    table.add_column("#", justify="right")
    table.add_column(score_label, justify="right", style="bold cyan")
    table.add_column("source", style="magenta")
    table.add_column("chunk (preview)")
    for n, (score, chunk) in enumerate(hits, start=1):
        text = re.sub(r"[#*|]+", "", chunk["text"]).strip()
        preview = text[:160] + ("..." if len(text) > 160 else "")
        table.add_row(str(n), f"{score:.3f}", chunk["source"], preview)
    return table


def ask(question: str, chunks, vectors, k: int) -> list[tuple[float, dict]]:
    hits = retrieve(question, chunks, vectors, k)
    console.print(results_table(f"Top {k} chunks for: {question!r}", hits, "cosine"))
    hand_off(build_prompt(question, hits))
    return hits


def compare_with_without(question: str, chunks, vectors, k: int) -> None:
    """Hand the chatbot the bare question first, then the RAG prompt, to compare answers."""
    copied = copy_to_clipboard(question)
    console.print(Panel(
        f"{question}\n\n"
        + ("[bold green]Copied to your clipboard.[/] " if copied else "Copy the question above. ")
        + "Paste it into a [bold]NEW[/] chat and see what the chatbot says on its own.",
        title="Step 1: WITHOUT RAG", border_style="red"))
    try:
        console.input("[bold]Press Enter for step 2...[/]")
    except (EOFError, KeyboardInterrupt):
        console.print()
        return
    console.print("\n[bold]Step 2: WITH RAG.[/] Paste this into ANOTHER new chat and compare.")
    ask(question, chunks, vectors, k)


HELP = """\
[bold]Type a question[/] about the documents in docs/{docs}/ and press Enter.

[bold]Commands[/]
  :compare <question>  ask a chatbot WITHOUT RAG first, then WITH RAG
  :vec <text>          show the embedding vector for some text
  :sim <text> | <text> cosine similarity between two pieces of text
  :keyword <question>  compare keyword search vs embedding search
  :k <number>          change how many chunks get retrieved (now: {k})
  :use <name>          switch knowledge base (now: {docs}; available: {available})
  :docs                list the documents and how many chunks each became
  :help                show this message
  :quit                exit
"""


def show_vector(text: str) -> None:
    v = embed_query(text)
    shown = ", ".join(f"{x:.3f}" for x in v[:8])
    console.print(f"[bold]{text!r}[/] ->  [{shown}, ... ]")
    console.print(
        f"[dim]That's {len(v)} numbers (dimensions). Length of the vector: "
        f"{np.linalg.norm(v):.3f}[/]\n"
    )


def show_similarity(arg: str) -> None:
    if "|" not in arg:
        console.print("Usage: :sim cat | dog\n")
        return
    a, b = (part.strip() for part in arg.split("|", 1))
    score = cosine_similarity(embed_query(a), embed_query(b))
    console.print(f"cosine similarity({a!r}, {b!r}) = [bold cyan]{score:.3f}[/]\n")


def compare_keyword(question: str, chunks, vectors, k: int) -> None:
    keyword_hits = keyword_search(question, chunks, k)
    if keyword_hits:
        console.print(results_table("Keyword search", keyword_hits, "overlap"))
    else:
        console.print("[bold]Keyword search:[/] no chunk shares a single word with your question!")
    console.print(results_table("Embedding search", retrieve(question, chunks, vectors, k), "cosine"))


def show_docs(docs_name: str, chunks) -> None:
    table = Table(title=f"Documents in docs/{docs_name}/", title_justify="left")
    table.add_column("file", style="magenta")
    table.add_column("chunks", justify="right")
    counts: dict[str, int] = {}
    for c in chunks:
        counts[c["source"]] = counts.get(c["source"], 0) + 1
    for name, n in counts.items():
        table.add_row(name, str(n))
    console.print(table)


def interactive(docs_name: str) -> None:
    k = TOP_K
    chunks, vectors = build_index(docs_name)

    def help_text() -> str:
        return HELP.format(k=k, docs=docs_name, available=", ".join(available_docs()))

    console.print(Panel(help_text(), title="Mini RAG", border_style="cyan"))
    while True:
        try:
            line = console.input(f"[dim]{docs_name}[/] [bold cyan]ask> [/]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nBye!")
            return
        if not line:
            continue
        cmd, _, arg = line.partition(" ")
        arg = arg.strip()
        if cmd in (":quit", ":q", ":exit"):
            console.print("Bye!")
            return
        elif cmd == ":help":
            console.print(help_text())
        elif cmd == ":compare" and arg:
            compare_with_without(arg, chunks, vectors, k)
        elif cmd == ":vec" and arg:
            show_vector(arg)
        elif cmd == ":sim":
            show_similarity(arg)
        elif cmd == ":keyword" and arg:
            compare_keyword(arg, chunks, vectors, k)
        elif cmd == ":k" and arg.isdigit() and int(arg) > 0:
            k = min(int(arg), len(chunks))
            console.print(f"Now retrieving the top {k} chunks.\n")
        elif cmd == ":use":
            if arg in available_docs():
                docs_name = arg
                chunks, vectors = build_index(docs_name)
                k = min(k, len(chunks))
                console.print(f"Switched to [bold]docs/{docs_name}[/]. Ask away!\n")
            else:
                console.print(f"Usage: :use <name>. Available: {', '.join(available_docs())}\n")
        elif cmd == ":docs":
            show_docs(docs_name, chunks)
        elif cmd.startswith(":"):
            console.print("Unknown command. Type :help\n")
        else:
            ask(line, chunks, vectors, k)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tiny RAG demo")
    parser.add_argument("--setup", action="store_true", help="download the model and build every index, then exit")
    parser.add_argument("--ask", metavar="QUESTION", help="ask one question and exit")
    parser.add_argument("--docs", default=DEFAULT_DOCS, help="which folder in docs/ to use")
    parser.add_argument("--k", type=int, default=TOP_K, help="how many chunks to retrieve")
    parser.add_argument("--expect", metavar="FILE", help=argparse.SUPPRESS)  # used by the tests
    args = parser.parse_args()

    if args.setup:
        for name in available_docs():
            build_index(name)
        console.print("[bold green]All set![/] Start asking questions with [bold]uv run rag.py[/] "
                      "(or just paste the setup line again).")
    elif args.ask:
        chunks, vectors = build_index(args.docs)
        hits = ask(args.ask, chunks, vectors, args.k)
        if args.expect and hits[0][1]["source"] != args.expect:
            sys.exit(f"Expected top source {args.expect}, got {hits[0][1]['source']}")
    else:
        interactive(args.docs)


if __name__ == "__main__":
    main()
