# Mini RAG: Ask Questions About a Company That Doesn't Exist

A tiny **Retrieval-Augmented Generation (RAG)** demo for the CSAI club.

**Quokka Quantum Snacks** is a made-up snack company with an employee handbook, product catalog, office guide and more. No AI model has ever seen these documents, so ChatGPT can't answer questions about them... unless we use RAG.

```
1. INGESTION   docs/*.md  ->  chunks  ->  embedding vectors (384 numbers each)
2. RETRIEVAL   your question  ->  vector  ->  cosine similarity  ->  top 3 chunks
3. AUGMENT     paste those chunks into a prompt
4. GENERATE    you paste the prompt into ChatGPT / Claude / Gemini
```

It's all in **one file, [`rag.py`](rag.py)** (under 400 lines, lots of comments). Read it!

---

## Setup (about 2 minutes)

You **don't** need to install Python yourself. We use [**uv**](https://docs.astral.sh/uv/), which downloads the right Python and libraries for you.

### Step 1: Download this project

Click the green **`<> Code`** button at the top of this page, then **Download ZIP**.

- **Windows:** right-click the ZIP and choose **Extract All...**. Don't work from inside the ZIP!
- **Mac:** double-click the ZIP and it unzips itself.

You'll get a folder called `csai-rag-demo-main`.

(If you know git, `git clone` works too.)

### Step 2: Install uv

<table>
<tr><th>Windows</th><th>Mac</th></tr>
<tr><td>

Press the **Windows key**, type **PowerShell** and open it. Paste this and press Enter:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

</td><td>

Press **Cmd + Space**, type **Terminal** and open it. Paste this and press Enter:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</td></tr>
</table>

> **Close the terminal window and open a new one** when it finishes. This is the #1 thing people miss!

### Step 3: Open a terminal *in the project folder*

<table>
<tr><th>Windows</th><th>Mac</th></tr>
<tr><td>

Open the `csai-rag-demo-main` folder in File Explorer (the one containing `rag.py`). **Right-click an empty space** and choose **Open in Terminal**.

<sub>No such option? Click the address bar at the top of File Explorer, type `powershell` and press Enter.</sub>

</td><td>

In Terminal, type `cd ` (with a space after it), then **drag the `csai-rag-demo-main` folder** from Finder into the Terminal window and press Enter.

</td></tr>
</table>

### Step 4: Run it

```
uv run rag.py
```

The first run downloads Python, a few libraries and the embedding model (~150 MB total), so give it a minute. After that it starts instantly.

> **Tip for the meeting:** run `uv run rag.py --setup` ahead of time so everything is downloaded before the Wi-Fi gets crowded.

---

## How to use it

Type a question and press Enter:

```
ask> Can I work from Japan for a month?
```

You'll see:
1. The **top 3 chunks** it retrieved, with their **cosine similarity** scores (closer to 1 = more similar).
2. The **augmented prompt**, which is the chunks plus your question plus instructions. It's **copied to your clipboard** automatically (and saved to `prompt.txt`).

Paste it into [ChatGPT](https://chatgpt.com), [Claude](https://claude.ai) or [Gemini](https://gemini.google.com) and watch it answer correctly.

### Commands

| Command | What it does |
|---|---|
| `:vec king` | Show the embedding vector for some text (it's just a list of 384 numbers!) |
| `:sim king \| queen` | Cosine similarity between two pieces of text |
| `:keyword Who is the boss?` | Compare old-school keyword search vs embedding search |
| `:k 5` | Retrieve 5 chunks instead of 3 |
| `:docs` | List the documents and how many chunks each became |
| `:quit` | Exit |

---

## Missions

**1. RAG vs no RAG.** Ask ChatGPT (or any chatbot) *"Can I work from Japan for a month at Quokka Quantum Snacks?"* with no context. Then ask the same question in `rag.py` and paste the augmented prompt into the chatbot. What changed?

**2. Meaning beats matching.** Try `:keyword My computer got stolen, who should I call?` and `:keyword Who is the boss?`. The docs never say "computer", "stolen" or "boss". Why does embedding search still find the right chunks?

**3. Ask something that isn't there.** Try *"What is the 401k match?"*. Look at the scores: how do they compare to a question that *does* have an answer? Paste the prompt. Does the chatbot admit it doesn't know?

**4. Play with vectors.**
- `:sim king | queen`
- `:sim cat | dog`
- `:sim cat | spreadsheet`
- `:sim I love pizza | pizza is my favorite food`

Can you find two sentences with **no words in common** but a high score?

**5. Tinker.** Open `rag.py` in any text editor and change `CHUNK_SIZE`, `OVERLAP` or `TOP_K` near the top, then re-run. Or **add your own `.md` or `.txt` file to `docs/`**: invent a new company policy, or paste your class syllabus! The index rebuilds automatically.

**6. Bonus: catch the bug.** Ask *"How many vacation days do I get?"* and paste the prompt into a chatbot. Is the answer right? (Hint: look at `docs/employee-handbook.md` and `docs/pto-policy-2023.md`.) Why did this happen, and how would you fix it?

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `uv: command not found` / `'uv' is not recognized` | Close the terminal and open a new one. Still broken? **Mac:** run `source $HOME/.local/bin/env`. **Windows:** run `$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"` |
| `No such file or directory: rag.py` | Your terminal isn't in the project folder. Redo Step 3. |
| `Couldn't download the embedding model` | Check your Wi-Fi and try again in a minute. Hugging Face (where the model lives) is occasionally down. |
| Clipboard copy didn't work | Open `prompt.txt` in the project folder and copy from there. |
| Nothing works on my laptop | Use **GitHub Codespaces**: on this repo's page, click **`<> Code` -> Codespaces -> Create codespace**, then in the terminal at the bottom run `pip install uv` and then `uv run rag.py`. |

---

## What's in here

```
rag.py         the whole RAG pipeline: ingestion, retrieval, augmentation
docs/          12 made-up company documents (the "knowledge base")
.cache/        created on first run: the downloaded model + saved vectors
```

Embedding model: [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) running locally through [fastembed](https://github.com/qdrant/fastembed). Nothing you type leaves your computer (until you paste it into a chatbot).
