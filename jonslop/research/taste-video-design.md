# TASTE-SIA — Build-Ready Design + Feasibility + Plan

> Output of the taste-video design workflow (8 agents, all facts verified against live SIA code).
> Captured 2026-06-06. The chosen build. Pairs with [hackathon-brief.md](./hackathon-brief.md),
> [sia-framework-notes.md](./sia-framework-notes.md). Parachute = [shader-sia-design.md](./shader-sia-design.md).
> **Read §0 + the 3 feasibility findings before building — two non-negotiables: a Python 3.12 run venv and a
> verified image endpoint.**

**One sentence:** SIA self-improves a prompt-writer agent so a *frozen* image/video model renders in *your*
taste, scored each generation by a cheap CLIP taste-vector fit once from a human ranking — full video rendered
only for the before/after demo.

---

## 0. WHAT THE LIVE CODE CONFIRMED (these change the plan)
- No keys, no `.env`, no `sia` installed, default `python` is **3.14.3** — everything starts from zero.
- `uv venv` runs with **no `--python` flag** (`run_setup.py:94`) → run venv inherits **3.14**, where
  torch/open_clip wheels don't exist on macOS arm64. **#1 mechanical blocker.** Fix: build the run venv on **3.12**.
- `accuracy` is read as a raw top-level scalar (`context_manager.py:343-350`) then printed `{x:.2f}%`.
  **Emit `accuracy` on a 0–100 scale** so the curve reads naturally; keep `taste_score` 0–1 as alias.
- Evolution line is **first→LAST, not first→best** (`context_manager.py:293-304`); **no best-gen retention**
  in the optimization chain (Markov on previous gen). You MUST select best-gen yourself and plot running-max.
- Nebius repo base_url is `https://api.tokenfactory.us-central1.nebius.com/v1/` = the **LLM/chat** host;
  **unverified (likely wrong) for `images.generate` flux-schnell.** Smoke-test the real image host first.
- `SAMPLE_TASK_DESCRIPTIONS.md` required (`run_setup.py:67`/`layout.py:174`) or the run crashes.
  `dataset_dir = data/public` → the taste `w` vector MUST live in `data/private/`. evaluate.py + agent share
  the run venv and inherit parent env (keys visible). `EVAL_TIMEOUT=600`. `--sandbox none` (default; never docker).

---

## 1. SIA FRAMING
The `target_agent` is a **prompt-writer**: reads the user's taste context → emits a prompt for a *frozen* model.
The model never changes. What SIA *evolves as code* is the prompt-writer's **personalized-context-injection
architecture** — how the mood board / ranked examples / taste signal get folded into the prompt. Gen 1 ignores
taste (`prompt = SUBJECT`). Each gen, the Feedback-Agent reads the taste-score delta + trajectory and rewrites
the agent to inject taste better: read `taste.md` + captions, extract aesthetic tokens (16mm grain, teal-orange,
low-key, anamorphic flare), build a style suffix + negative prompt, few-shot prime on top-ranked captions,
multi-candidate self-selection. None hardcoded by us — the seed lacks it, the metric rewards it, SIA writes it.
Contribution = a reusable **task contract for taste transfer**: SIA optimizes the cheap text+still slice of an
expensive generative pipeline against a one-shot human-preference proxy.

Hook (stage): *"We pointed a self-improving AI at the one thing AI can't do — taste. The human ranks 12 images
once. SIA spends 5 generations learning to talk to a frozen video model in that person's aesthetic. Same model,
same seed — watch it go from generic to yours."*

## 2. TASK DEFINITION
Location: `/Users/johnnysheng/code/sia/jonslop/tasks/taste-video/` (in `jonslop/`, outside shipped `sia/tasks/`).
- **Solver (prompt-writer):** `default-target` = `claude-haiku-4-5` via anthropic (start here to de-risk;
  `qwen-nebius-target` is the H200 fallback). Meta/Feedback = `default-meta` (Claude Haiku, writes the code).
- **Frozen image model:** Nebius `black-forest-labs/flux-schnell`, 512×512, 4 steps, fixed seeds — the only
  variable across generations is the prompt text.
- **Submission (agent writes to `--working_dir`):** `prompt.txt` (the evolved artifact), `renders/seed{0,1,2}.png`
  (3 stills the AGENT renders — keeps evaluate.py a pure scorer), `agent_execution.json` (trajectory).
- **Taste inputs (`data/public/`, agent-readable):** `taste.md` (1 paragraph), `moodboard/ranking.json` +
  `rank_NN_*.png` (12–16 ranked stills, doubles as demo mood board), `moodboard/captions.json`.

### `data/public/task.md` (verbatim)
```markdown
# Task: Taste-Personalized Prompt Writing for a Frozen Image/Video Model
## Goal
You are a PROMPT-WRITER agent. A specific human director has an aesthetic ("taste").
A frozen text-to-image model (FLUX-schnell on Nebius) renders whatever prompt you produce.
The model is generic; YOUR job is to write a prompt that makes it render in THIS director's taste.
You are scored by an automated taste proxy fit from the director's one-time ranking of a mood board.
You CANNOT see the proxy or the score. You only see the taste context below.
## The shot (held constant)
Subject: "a lone figure walking down a rain-slicked city street at night"
(Render THIS subject every time. Change only STYLE/treatment, never the subject.)
## Inputs (read-only, in --dataset_dir)
- taste.md ; moodboard/ranking.json (BEST first) ; moodboard/rank_NN_*.png ; moodboard/captions.json
## Write to --working_dir
1. prompt.txt  — one FLUX prompt: fixed subject, taste in style/lighting/color/lens/grain/mood + a negative phrase.
2. renders/seed0..2.png — render prompt.txt 3x (seeds 0,1,2) via Nebius flux-schnell, 512x512, 4 steps, b64_json.
3. agent_execution.json — your reasoning/log.
## Rules
- Subject is FIXED. Optimizing = matching TASTE, not changing the scene. USE the ranked mood board + taste.md.
- Only pixels are scored, never your words.
```

## 3. PRE-RANKED TASTE BATCH (≈3 min human, ONCE before any run)
1. `tools/make_batch.py` → render 14 candidates off the fixed subject, varied style suffixes (or drop in the
   director's own work — stronger story).
2. Human ranks once → `moodboard/ranking.json` = best→worst (rename files or a 1-min CLI).
3. `tools/fit_taste.py` → fits the proxy, writes the **private** artifact. Commit before the run.

**Proxy DECISION: CLIP preference direction (Bradley-Terry on frozen ViT-B-32) as the optimization target;
VLM-judge as the honesty co-gate (ensemble).** CLIP = $0, deterministic, ms/call → honest gen-over-gen curve.
With ~12 images a linear BT fit is correctly-sized (a deep RM overfits). VLM-judge alone is non-deterministic +
costs per call → keep it only as the disagreement gate.

**CRITICAL split (dataset_dir = data/public):** the taste vector `w` must NOT be public or the agent games it.
- `data/private/taste_proxy.npz` — `w, lo, hi, model, pretrained, holdout_emb, holdout_rank`. evaluate.py loads it; agent never sees it.
- `data/public/moodboard/` — ranked stills + captions + ranking.json only (no vector). Agent reads this to *infer* taste.

```python
# tools/fit_taste.py — run ONCE offline after ranking. writes data/private/taste_proxy.npz
import numpy as np, open_clip, torch, json
from pathlib import Path; from PIL import Image
ROOT = Path(__file__).resolve().parent.parent; MB = ROOT/"data/public/moodboard"
model,_,pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); model.eval()
def embed(p):
    with torch.no_grad(): e = model.encode_image(pre(Image.open(p).convert("RGB")).unsqueeze(0))[0].numpy()
    return e/(np.linalg.norm(e)+1e-8)
ranked = json.load(open(MB/"ranking.json")); E = np.stack([embed(MB/f) for f in ranked]); N,D = E.shape
hold = [1, N-2]; keep = [i for i in range(N) if i not in hold]; Ek = E[keep]; nk=len(keep)
pairs = [(a,b) for ia,a in enumerate(keep) for b in keep[ia+1:]]   # a ranked above b
Dm = np.stack([E[a]-E[b] for a,b in pairs]); w = np.zeros(D); lr,lam = 0.5,1e-2
for _ in range(2000):
    p = 1/(1+np.exp(-(Dm@w))); w -= lr*(Dm.T@(p-1.0)/len(pairs) + lam*w)
w /= (np.linalg.norm(w)+1e-8); proj = Ek@w; lo,hi = float(proj.min()), float(proj.max())
np.savez(ROOT/"data/private/taste_proxy.npz", w=w, lo=lo, hi=hi, model="ViT-B-32",
         pretrained="laion2b_s34b_b79k", holdout_emb=E[hold], holdout_rank=np.array(hold))
print("pairwise train acc:", float((proj[:,None]>proj[None,:])[np.triu_indices(nk,1)].mean()))
```
The printed pairwise accuracy is **the number that licenses the demo** ("the proxy reproduces the ranking with X%").

## 4. EVALUATE.PY (loads private proxy → scores the agent's 3 stills → ensemble + gates → results.json)
results.json keys: `accuracy` (0–100, primary, higher-better — named `accuracy` on purpose for retention/curve),
`taste_score` (0–1 alias), `clip_taste`, `vlm_taste`, `taste_std`, `n_renders`, `gate_passed`, `holdout_ok`.
Honesty gates: held-out order check (2 held-out exemplars must order correctly under `w` or score→0); pixel-std
degeneracy (<0.02 → 0); ensemble disagreement penalty `final = max(0, 0.6*clip + 0.4*vlm - 0.5*|clip-vlm|)`
(no VLM key → vlm=clip, CLIP-only); scored on pixels never prompt text. Top of file:
`assert (TASK/'data/private/taste_proxy.npz').exists()` + torch-import guard → fail LOUD on gen_1, not silent-flat.

```python
# data/public/evaluate.py  --  python evaluate.py --gen-dir <gen_dir>
import argparse, json, glob, os, base64, numpy as np, open_clip, torch
from io import BytesIO; from pathlib import Path; from PIL import Image
TASK = Path(__file__).resolve().parent.parent.parent
ART  = np.load(TASK/"data/private/taste_proxy.npz", allow_pickle=True)
W, LO, HI = ART["w"], float(ART["lo"]), float(ART["hi"])
_m,_,_pre = open_clip.create_model_and_transforms(str(ART["model"]), pretrained=str(ART["pretrained"])); _m.eval()
def embed(p):
    with torch.no_grad(): e=_m.encode_image(_pre(Image.open(p).convert("RGB")).unsqueeze(0))[0].numpy()
    return e/(np.linalg.norm(e)+1e-8)
def clip_score(e): return float(np.clip((float(e@W)-LO)/(HI-LO+1e-8),0,1))
def degenerate(p): return (np.asarray(Image.open(p).convert("RGB"),float)/255).std() < 0.02
def holdout_ok(): d = ART["holdout_emb"]@W; return bool(d[0] > d[1])
def vlm_score(p):
    if not os.getenv("OPENAI_API_KEY"): return None
    try:
        from openai import OpenAI
        img=Image.open(p).convert("RGB"); buf=BytesIO(); img.save(buf,format="PNG")
        url="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
        tpl=(TASK/"data/public/judge_prompt.txt").read_text()
        r=OpenAI().chat.completions.create(model=os.getenv("OPENAI_VISION_MODEL","gpt-4o-mini"),temperature=0,
            messages=[{"role":"user","content":[{"type":"text","text":tpl},{"type":"image_url","image_url":{"url":url}}]}])
        return max(0.0,min(1.0,float(r.choices[0].message.content.split("SCORE:")[1].strip().split()[0])/10.0))
    except Exception: return None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--gen-dir",type=Path); a=ap.parse_args()
    rs=sorted(glob.glob(str(a.gen_dir/"renders"/"*.png"))); cs,vs,hok=[],[],holdout_ok()
    for r in rs:
        s = 0.0 if (degenerate(r) or not hok) else clip_score(embed(r)); cs.append(s)
        v=vlm_score(r); 
        if v is not None: vs.append(v)
    clip_mean=float(np.mean(cs)) if cs else 0.0; vlm_mean=float(np.mean(vs)) if vs else clip_mean
    final=max(0.0, 0.6*clip_mean + 0.4*vlm_mean - 0.5*abs(clip_mean-vlm_mean))
    out={"accuracy":100*final,"taste_score":final,"clip_taste":clip_mean,"vlm_taste":vlm_mean,
         "taste_std":float(np.std(cs)) if cs else 0.0,"n_renders":len(rs),
         "gate_passed":bool(cs and max(cs)>0),"holdout_ok":hok,"metric":"taste_proxy","higher_is_better":True}
    json.dump(out, open(a.gen_dir/"results.json","w"), indent=2); print(json.dumps(out))
if __name__=="__main__": main()
```
(NOTE: design printed `accuracy:final` 0–1; per §0 emit `100*final` so the `{:.2f}%` curve reads naturally.)
`judge_prompt.txt`: "You are this director's taste proxy. HIGH-ranked frames favor [auto-filled aesthetic];
LOW frames look generic/plastic/over-saturated. Score the CANDIDATE. Reply EXACTLY: SIMILARITY SCORE: <1-10>".

## 5. REFERENCE SEED AGENT (deliberately weak — the headroom SIA climbs)
`reference/reference_target_agent.py`: renders the bare subject with **zero taste injection** (opens dataset_dir
but never reads taste.md/moodboard; `prompt = SUBJECT`; renders 3 seeds via Nebius). What it lacks = what SIA
discovers (taste-token extraction, style suffix, negative prompt, few-shot priming, multi-candidate selection).
```python
#!/usr/bin/env python3
import argparse, os, base64, json; from pathlib import Path; from openai import OpenAI
SUBJECT = "a lone figure walking down a rain-slicked city street at night"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dataset_dir",required=True); ap.add_argument("--working_dir",required=True)
    a=ap.parse_args(); wd=Path(a.working_dir); (wd/"renders").mkdir(parents=True,exist_ok=True)
    prompt=SUBJECT; (wd/"prompt.txt").write_text(prompt)   # naive: subject only, no taste
    client=OpenAI(base_url="<VERIFIED_NEBIUS_IMAGE_BASE_URL>", api_key=os.environ["NEBIUS_API_KEY"]); steps=[]
    for s in range(3):
        img=client.images.generate(model="black-forest-labs/flux-schnell", prompt=prompt, response_format="b64_json",
            extra_body={"width":512,"height":512,"num_inference_steps":4,"seed":s})
        (wd/f"renders/seed{s}.png").write_bytes(base64.b64decode(img.data[0].b64_json)); steps.append({"seed":s,"prompt":prompt})
    json.dump({"approach":"naive subject-only, no taste injection","steps":steps}, open(wd/"agent_execution.json","w"), indent=2)
if __name__=="__main__": main()
```
`reference/SAMPLE_TASK_DESCRIPTIONS.md` — REQUIRED, one line ("aesthetic-conditioned text-to-image prompt
optimization; style-transfer prompt engineering; preference-aligned generation").
`reference/requirements.txt` — pinned CPU wheels: `torch open_clip_torch torchvision pillow numpy openai`.

## 6. RUN COMMANDS — see Plan §3 below.

## 7. DEMO STORYBOARD (3–4 min)
- 0:00–0:25 Hook + "same frozen model, same seed, same subject; only the prompt-writer changed."
- 0:25–1:00 Mood board (ranked stills best→worst) + the pairwise-accuracy number. "3 min of human ranking, the only input."
- 1:00–2:00 SIA self-improving: the **taste-score running-max curve** + a 3-line code diff (gen1 `prompt=SUBJECT` →
  SIA-authored taste extractor) + prompt.txt before/after. "SIA wrote that. The metric did."
- 2:00–3:15 **Before/after side-by-side** (naive vs taste-optimized), pre-rendered. Let it play silent 10s. "Feel the difference."
- 3:15–4:00 Framework claim + Q&A. Pre-render EVERYTHING (before/after, moodboard, curve PNG, prompt diff, acc number).

## 8. PARACHUTE
Bail to shader-synth (`jonslop/research/shader-sia-design.md`) ONLY if at minute 30 `import torch` fails on 3.12
AND all Nebius image hosts fail AND fal flux fallback fails (no cheap deterministic renderer). Same SIA contract,
deterministic free CPU render + LPIPS (MSE if torch dead), zero external-API. Decide at minute 30, stop debugging APIs.

---

## FEASIBILITY (3 verdicts, verified against live code)

**R1 (HIGH) — eval deps + cold-weights timeout.** Loop CAN run unattended (`--sandbox none`; agent + evaluate.py
share venv + inherit env; agent renders, evaluate.py scores; private artifact loadable host-side, invisible to
agent; `accuracy` drives retention/curve, higher-better). BUT torch+open_clip+Pillow are NOT in baseline venv
(`config.py:55-66`), only enter via `reference/requirements.txt`; if absent → ModuleNotFoundError, no results.json,
flat curve; wheel-resolution failure (`check=True`) aborts whole run; **open_clip downloads ~600MB ViT-B-32 on
first call inside the 600s eval timeout** → cold wifi can TimeoutExpired gen_1. Fix: pinned CPU `requirements.txt`;
verify `runs/run_N/venv/bin/python -c "import torch,open_clip,PIL"`; **pre-download CLIP into a fixed `HF_HOME`**
the run inherits; defensive asserts; smoke-test `--max_gen 1` first.

**R2 (BLOCKER) — no video / wrong image endpoint.** Zero API keys set; no `.env`; `sia` not installed; fal is
unprovisioned + NOT in the brief (brief provisions Nebius for LLM only); **the design's Nebius image base_url is
the LLM host — likely 404s for flux-schnell, which kills the CHEAP loop, not just the demo**; Python 3.14 torch
wheels missing; fal LTX-2 fast has no seed param + defaults audio on; video budget ~$1–8 not $1–2. Fix: smoke-test
all three Nebius hosts + fal flux, hardcode the one returning b64; **decouple demo from video — the IMAGE
before/after is the guaranteed spine**; time-box fal to 15 min; `generate_audio:false`.

**R3 (BLOCKER) — non-monotonic curve + first→last reporting.** No best-gen retention (Markov on previous gen);
context.md prints first→LAST so the on-stage curve can DECLINE; cherry-pick optics strengthen the "human/proxy
did it, not SIA" Q&A attack. Fix: run 3–4 times, **select best gen yourself** (max results.json accuracy), **plot
running-max** (monotonic by construction, standard for search), render AFTER artifact from that best gen, pre-script
the Q&A ("SIA writes/tests prompt-writer CODE against a frozen held-out preference the agent never sees; held-out
gate proves generalization; human is the eval not the optimizer; we ship best-of-search, not a smooth climb").

---

## BUILD PLAN

### GO/NO-GO SPIKE (first 30 min, one person, BLOCKING — nobody builds until green)
```bash
export NEBIUS_API_KEY=...  ANTHROPIC_API_KEY=...  OPENAI_API_KEY=...  FAL_KEY=...   # OPENAI optional
cd /Users/johnnysheng/code/sia
# 1. 3.12 venv + heavy deps (the whole loop risk surface)
~/.local/bin/uv venv .venv --python 3.12
~/.local/bin/uv pip install --python .venv/bin/python -e . torch open_clip_torch torchvision pillow numpy openai
.venv/bin/python -c "import torch, open_clip, PIL, sia; print('DEPS OK', torch.__version__)"
# 2. find the REAL Nebius image endpoint (design's host is probably wrong)
for U in "https://api.studio.nebius.ai/v1/" "https://api.tokenfactory.nebius.com/v1/" "https://api.tokenfactory.us-central1.nebius.com/v1/"; do
  .venv/bin/python - "$U" <<'PY'
import sys,os; from openai import OpenAI
try:
    c=OpenAI(base_url=sys.argv[1],api_key=os.environ["NEBIUS_API_KEY"])
    r=c.images.generate(model="black-forest-labs/flux-schnell",prompt="a cat",response_format="b64_json",
        extra_body={"width":512,"height":512,"num_inference_steps":4,"seed":0}); print(sys.argv[1],"OK",len(r.data[0].b64_json))
except Exception as e: print(sys.argv[1],"FAIL",repr(e)[:160])
PY
done
# 3. pre-download CLIP weights into a fixed cache the run inherits (kills 600s-timeout gamble)
export HF_HOME=/Users/johnnysheng/code/sia/jonslop/tasks/taste-video/.hfcache
.venv/bin/python -c "import open_clip; open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k'); print('CLIP cached')"
# 4. (parallel, 15-min box) fal LTX-2 video — DEMO ONLY, not on the loop critical path
.venv/bin/python -c "import fal_client,os; print(fal_client.subscribe('fal-ai/ltx-2/image-to-video/fast', arguments={'image_url':'https://picsum.photos/512','prompt':'cinematic rain street night','duration':6,'resolution':'1080p','generate_audio':False})['video']['url'])"
```
GO if step 1 + step 2 green. Video is a bonus, never a gate. If 1+2 red at min 30 → PARACHUTE to shader-synth.

### Hour-by-hour (4 tracks: A=Infra/SIA, B=Taste batch+proxy, C=Agent+contract, D=Demo)
- **H0 (→0:30):** A runs the spike, owns `.venv`(3.12) + verified base_url, writes `.env`. Others `mkdir` scaffold only. HARD CUT @0:30: parachute if torch/endpoint red.
- **H1 (0:30→1:30):** B `make_batch.py`→14 stills→rank→`ranking.json`+captions. C task.md + naive seed agent + SAMPLE_TASK_DESCRIPTIONS.md + pinned requirements.txt. A evaluate.py (0–100 accuracy, gates, asserts). D slide skeleton + moodboard.
- **H2 (1:30→2:30):** B `fit_taste.py`→`data/private/taste_proxy.npz` (print pairwise acc, commit). A **single-gen smoke test on real machine** (`--max_gen 1`, confirm nonzero results.json; check run venv is 3.12). C dry-run agent standalone. D curve-plot script (running-max). CUT @2:30: no nonzero gen_1 → fix loop, don't start 5-gen.
- **H3 (2:30→3:30):** A launch 3–4 `--max_gen 5` runs (each <$1). D once fal works, `render_video.py`→before/after (best gen's seed0.png as image_url, audio off) — pre-render only. B eyeball taste transfer. C grab prompt diff.
- **H4 (3:30→4:30):** A pick best gen across runs, generate running-max curve PNG. D assemble deck + backup `runs/` on disk. Everyone run Q&A script. HARD CUT @4:30: lock deck + mp4s, no new renders.
- **H5 (4:30→6pm):** buffer + dry-run on demo machine ×2.

### End-to-end commands
```bash
cd /Users/johnnysheng/code/sia
export NEBIUS_API_KEY=... ANTHROPIC_API_KEY=... OPENAI_API_KEY=... FAL_KEY=...
export HF_HOME=/Users/johnnysheng/code/sia/jonslop/tasks/taste-video/.hfcache
~/.local/bin/uv venv .venv --python 3.12
~/.local/bin/uv pip install --python .venv/bin/python -e . torch open_clip_torch torchvision pillow numpy openai
.venv/bin/python jonslop/tasks/taste-video/tools/make_batch.py      # 14 stills
#   --> human ranks: rename rank_NN_*.png, write moodboard/ranking.json
.venv/bin/python jonslop/tasks/taste-video/tools/fit_taste.py       # writes data/private/taste_proxy.npz (COMMIT)
.venv/bin/sia run --task_dir $PWD/jonslop/tasks/taste-video --target-agent-profile default-target \
  --meta-agent-profile default-meta --max_gen 1 --sandbox none      # prove the loop
cat runs/run_*/gen_1/results.json
for i in 1 2 3; do .venv/bin/sia run --task_dir $PWD/jonslop/tasks/taste-video --target-agent-profile default-target \
  --meta-agent-profile default-meta --max_gen 5 --sandbox none & done; wait
.venv/bin/python jonslop/tasks/taste-video/tools/render_video.py    # before.mp4 / after.mp4 from best gen
```
- Iteration: Nebius flux-schnell, fixed seeds, 512², 4 steps (~hundreds of stills × $0.0013 ≈ <$1).
- Demo video: fal `fal-ai/ltx-2/image-to-video/fast`, best gen's seed0.png as image_url, 6s@1080p, audio off (~$1–8).

### MVD (60% case) + parachute trigger
Spine guaranteed if the IMAGE loop works at all: moodboard + pairwise-acc number; taste-score running-max curve
(your PNG, not context.md); gen_1 vs best-gen prompt.txt diff; **IMAGE before/after** side-by-side. Video is a
bonus layer. Degradation ladder: full video before/after → image+one video → image before/after only →
curve+diff+moodboard. Parachute at minute 30 if no cheap deterministic renderer exists.

### Top 3 risks → mitigations (baked into timeline)
R1 deps/timeout → 3.12 venv + pinned reqs + pre-cached HF_HOME + loud asserts + `--max_gen 1` proof (H0–H2).
R2 video/endpoint → smoke-test+hardcode endpoint, decouple demo from video (image spine), 15-min fal box (H0–H3).
R3 non-monotonic curve → 3–4 runs, select best-gen yourself, plot running-max, pre-scripted Q&A (H3–H4).

**Two non-negotiables:** a verified image-endpoint base_url + a Python 3.12 run venv. Everything else degrades gracefully.

**Files to create** (under `jonslop/tasks/taste-video/`): `data/public/{task.md,evaluate.py,judge_prompt.txt}`,
`data/public/moodboard/{ranking.json,captions.json,rank_NN_*.png}`, `data/private/taste_proxy.npz` (private!),
`reference/{reference_target_agent.py,SAMPLE_TASK_DESCRIPTIONS.md,requirements.txt}`,
`tools/{make_batch.py,fit_taste.py,render_video.py}`.
