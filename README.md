# CSAI Club RAG Demo

Ask questions about **Quokka Quantum Snacks**, a snack company that doesn't exist, or about **Taco Bell "news" that we made up**. No AI model has ever seen these documents, so a chatbot on its own can only guess. This demo finds the right paragraphs and builds a prompt you paste into any chatbot, so you can compare its answers with and without RAG.

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
quokka ask> Can I work from Japan for a month?
```

You get two things back:

1. **A table of the 3 best-matching chunks** from the docs, with a **score** for each (higher = closer in meaning to your question) and which file it came from.
2. **A ready-made prompt** with those chunks, your question and some instructions. It's **already copied to your clipboard** (and saved to `prompt.txt`).

Paste the prompt into [ChatGPT](https://chatgpt.com), [Gemini](https://gemini.google.com) or any other chatbot and see what it says.

### Comparing with and without RAG

Type `:compare` before a question:

```
quokka ask> :compare Can I work from Japan for a month?
```

1. First it copies **just the question**. Paste it into a new chat: that's the chatbot **without RAG**.
2. Press Enter, and it copies the **RAG prompt**. Paste it into another new chat: that's the chatbot **with RAG**.

Put the two chats side by side and compare.

### Two knowledge bases

| Name | What it is | Switch to it |
|---|---|---|
| `quokka` (default) | Quokka Quantum Snacks, a completely made-up company: handbook, product catalog, office guide, org chart... | `:use quokka` |
| `tacobell` | **A real company with fake "news"**: a new menu item, a membership program, a spinning restaurant. **None of it is real.** Chatbots know Taco Bell, but they've never seen this "news". | `:use tacobell` |

### Commands

| Type this | What happens |
|---|---|
| any question | Find the best chunks and build the prompt |
| `:compare <question>` | Copy the question without RAG, then with RAG, so you can compare answers |
| `:use tacobell` | Switch to another knowledge base (any folder inside `docs/`) |
| `:vec king` | Show the vector (list of numbers) for some text |
| `:sim king \| queen` | Score how similar two pieces of text are |
| `:keyword Who is the boss?` | Compare plain keyword search with embedding search |
| `:k 5` | Use the top 5 chunks instead of 3 |
| `:docs` | List the documents and how many chunks each became |
| `:quit` | Exit |

### Questions to try

**Quokka Quantum Snacks:**
- How many PTO days do employees get?
- Why were Wave Function Wafers discontinued?
- Who should I call if I lose my laptop?

**Taco Bell (fake news):**
- What is the Crunchwrap Galaxy and how much does it cost?
- How much is the Fourth Meal Club?
- Where is Taco Bell opening a spinning restaurant?

---

## Missions

**1. With vs. without.** Run `:compare Can I work from Japan for a month?` and paste each step into its own new chat. What does the chatbot say on its own? What changes with RAG?

**2. Real company, fake news.** Type `:use tacobell`, then `:compare What is the Crunchwrap Galaxy and how much does it cost?`. Without RAG, the chatbot has never heard of it. With RAG, it repeats our made-up "news" as fact. Is that a good thing or a bad thing?

**3. Meaning beats matching.** Back in `:use quokka`, try `:keyword Who is the boss?` and `:keyword My computer got stolen, who should I call?`. The docs never use the words "boss", "computer" or "stolen". Which search still finds the right file?

**4. Ask something that isn't there.** Try *"What is the 401k match?"* Compare the scores to a question that does have an answer. Paste the prompt: does the chatbot admit it doesn't know?

**5. Play with vectors.** Try `:sim king | queen`, `:sim cat | dog` and `:sim cat | spreadsheet`. Can you find two sentences with **no words in common** that still score high?

**6. Tinker.** Open the `csai-rag-demo` folder (in your home folder) and edit `rag.py` in any text editor. Change `CHUNK_SIZE`, `OVERLAP` or `TOP_K` near the top, then start the demo again. Or make your own knowledge base: create a folder like `docs/mine/`, drop some `.md` or `.txt` files in it (class notes, a made-up policy...), and type `:use mine`.

**7. Bonus: catch the bug.** In `quokka`, ask *"How many vacation days do I get?"* and paste the prompt into a chatbot. Is the answer right? Compare `docs/quokka/employee-handbook.md` with `docs/quokka/pto-policy-2023.md`. Why did this happen, and how would you fix it?

> **Heads up:** some chatbots search the web on their own. If it does, notice that it finds nothing about the Crunchwrap Galaxy, because it doesn't exist. (A chatbot searching the web is doing RAG too, just with the internet as its documents!)

---

## What's in the folder

| File | What it is |
|---|---|
| `rag.py` | The whole demo in one file. The four steps are labeled: **ingestion**, **retrieval**, **augment**, **generate** |
| `docs/quokka/` | 12 documents from a made-up company |
| `docs/tacobell/` | 5 **fake** "news" documents about a real company ([details](docs/tacobell/README.md)) |
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
