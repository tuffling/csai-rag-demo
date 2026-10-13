# CSAI Club RAG Demo

Ask questions about **Quokka Quantum Snacks**, a snack company that doesn't exist. No AI model has ever seen its documents, so a chatbot on its own can only guess. This demo finds the right paragraphs and builds a prompt you paste into any chatbot to get the real answer.

---

## Setup

Copy the line for your computer, paste it into a terminal and press Enter.

**Mac:**

```bash
curl -LsSf https://raw.githubusercontent.com/tuffling/csai-rag-demo/main/install.sh | sh
```

**Windows:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/tuffling/csai-rag-demo/main/install.ps1 | iex"
```

That's it. It installs [uv](https://docs.astral.sh/uv/) (which handles Python for you), downloads the demo into a `csai-rag-demo` folder in your home folder, and starts it. The first run downloads ~150 MB, so give it a minute.

**To start it again later, paste the same line again.** It won't re-download anything or overwrite your changes.

---

## Using the demo

When you see `ask>`, type a question and press Enter:

```
ask> Can I work from Japan for a month?
```

You get two things back:

1. **A table of the 3 best-matching chunks** from the company docs, with a **score** for each (higher = closer in meaning to your question) and which file it came from.
2. **A ready-made prompt** with those chunks, your question and some instructions. It's **already copied to your clipboard** (and saved to `prompt.txt`).

Paste the prompt into [ChatGPT](https://chatgpt.com), [Gemini](https://gemini.google.com) or any other chatbot and see what it says.

### Commands

| Type this | What happens |
|---|---|
| any question | Find the best chunks and build the prompt |
| `:vec king` | Show the vector (list of numbers) for some text |
| `:sim king \| queen` | Score how similar two pieces of text are |
| `:keyword Who is the boss?` | Compare plain keyword search with embedding search |
| `:k 5` | Use the top 5 chunks instead of 3 |
| `:docs` | List the documents and how many chunks each became |
| `:quit` | Exit |

### Questions to try

- How many PTO days do employees get?
- Why were Wave Function Wafers discontinued?
- Who should I call if I lose my laptop?
- What is Project Tachyon?
- How much is the per diem for a trip to Toronto?

---

## Missions

**1. With vs. without.** Ask a chatbot *"Can I work from Japan for a month at Quokka Quantum Snacks?"* on its own. Then ask the same thing in the demo and paste the prompt into a new chat. What changed?

**2. Meaning beats matching.** Try `:keyword Who is the boss?` and `:keyword My computer got stolen, who should I call?`. The docs never use the words "boss", "computer" or "stolen". Which search still finds the right file?

**3. Ask something that isn't there.** Try *"What is the 401k match?"* Compare the scores to a question that does have an answer. Paste the prompt: does the chatbot admit it doesn't know?

**4. Play with vectors.** Try `:sim king | queen`, `:sim cat | dog` and `:sim cat | spreadsheet`. Can you find two sentences with **no words in common** that still score high?

**5. Tinker.** Open the `csai-rag-demo` folder (in your home folder) and edit `rag.py` in any text editor. Change `CHUNK_SIZE`, `OVERLAP` or `TOP_K` near the top, then start the demo again. Or drop your own `.md` or `.txt` file into `docs/` (a made-up policy, your class notes...) and ask about it.

**6. Bonus: catch the bug.** Ask *"How many vacation days do I get?"* and paste the prompt into a chatbot. Is the answer right? Compare `docs/employee-handbook.md` with `docs/pto-policy-2023.md`. Why did this happen, and how would you fix it?

---

## What's in the folder

| File | What it is |
|---|---|
| `rag.py` | The whole demo in one file. The four steps are labeled: **ingestion**, **retrieval**, **augment**, **generate** |
| `docs/` | 12 made-up company documents: handbook, product catalog, office guide, org chart... |
| `.cache/` | Created on the first run: the downloaded embedding model and the saved vectors |
| `prompt.txt` | The last prompt the demo built |

The embedding model is [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). It runs on your laptop, so your questions don't leave your computer until you paste them somewhere.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Couldn't download the embedding model` | Check your Wi-Fi and paste the line again in a minute. The model host (Hugging Face) is occasionally down. |
| Clipboard copy didn't work | Open `prompt.txt` in the `csai-rag-demo` folder and copy it from there. |
| Nothing works on my laptop | Use **GitHub Codespaces**: on this page click **`<> Code` → Codespaces → Create codespace**, then paste the **Mac** line into the terminal at the bottom. |

Already know git? `git clone` this repo and run `uv run rag.py` inside it.
