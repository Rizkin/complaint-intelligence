"""Simulated stakeholder discovery session (SIMULATED, not a real person).

Two LLM roles through OpenRouter:
  interviewer: Mom Test rules (past specifics, no compliments, no leading, no pitch until the final turn);
  persona:     Head of Complaints Triage at a large US bank, may state only what the desk-research notes (docs/discovery/01..06) support;
               otherwise hedges. Busy, terse, skeptical, and does NOT hand out polite commitments.
A third call analyzes the transcript: compliments and polite promises are not evidence; each claim is tagged source-backed or invented.

Usage: uv run python evals/sim_stakeholder.py --out docs/discovery/sim-01-head-of-complaints.md
"""

import argparse
import glob
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(".env")
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="docs/discovery/sim-01-head-of-complaints.md")
ap.add_argument("--persona-model", default="anthropic/claude-sonnet-5")
ap.add_argument("--interviewer-model", default="anthropic/claude-haiku-5.5")
ap.add_argument("--summary-model", default="anthropic/claude-sonnet-5")
ap.add_argument("--turns", type=int, default=10, help="persona answers (the last one answers the pitch)")
ap.add_argument("--session", default="1")
a = ap.parse_args()

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])
cost = 0.0


def chat(model, system, messages, temperature=0.7, max_tokens=1200):
    global cost
    r = client.chat.completions.create(model=model, temperature=temperature, max_tokens=max_tokens,
                                       messages=[{"role": "system", "content": system}] + messages,
                                       extra_body={"usage": {"include": True}})
    cost += float(getattr(r.usage, "cost", 0) or 0)
    text = (r.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError(f"empty reply from {model} (finish_reason={r.choices[0].finish_reason}); raise max_tokens")
    return text


notes = ""
for f in sorted(glob.glob("docs/discovery/0[1-6]-*.md")):
    notes += f"\n\n=== {os.path.basename(f)} ===\n" + open(f).read()

PERSONA = f"""You are role-playing a SIMULATED persona: Head of Complaints Triage for consumer deposits and cards at a large US bank.
You are not a real person and this is not a real bank. A builder is interviewing you about how complaints are triaged.

Behave like a busy senior practitioner:
- Short, plain answers (2-4 sentences). Do not volunteer more than you were asked. No corporate filler, no "great question".
- When asked about the past, give one concrete, plausible case but hedge its details ("roughly", "I'd have to check"). Do not narrate a flawless process:
  real teams have backlogs, workarounds, spreadsheets, disagreements, things that slip.
- State specifics (deadlines, regulations, exam findings, team structure, tools) ONLY if the sources below support them. For anything the sources do not cover
  (headcount, vendors, internal numbers) say you do not know or that it varies, or give an explicitly hedged guess. Never invent named people or real internal metrics.
- You are a skeptic: regulatory clocks (CFPB 15/60 days; Reg E 10 business days / 45 days; Reg Z 30 days / two billing cycles), exam findings, model risk
  management, explainability, false positives that waste senior time, anything that writes to a system of record, who is accountable if it is wrong.
- If asked a hypothetical or about the builder's idea, say that is not something you can answer from experience and steer back to what actually happens.
- When the builder finally pitches an idea: give at least two concrete objections, say what would have to be true to take it seriously, and do NOT promise
  a meeting, a data sample or an introduction just to be polite. You may say "send a one-pager, I'd need compliance and model risk to look at it" or decline.

SOURCES (desk research notes, public material):
{notes}
"""

INTERVIEWER = """You are a builder doing customer discovery for a complaint-triage tool. Follow the Mom Test strictly:
- ask about the PAST and specifics ("when did that last happen?", "what did you do?", "what did it cost you?"), never about opinions, the future or hypotheticals;
- NEVER compliment, reassure or evaluate ("sounds great", "that's thorough", "makes sense"). Acknowledge with at most two neutral words ("Okay.", "Got it.");
- do not lead: do not put the answer in the question; do not mention your product or any tool idea;
- one short question per turn, built on a concrete detail they just gave; if the answer was vague or polished, ask for the last actual instance;
- areas to cover over the interview: how a complaint is routed and prioritized today, who decides senior-reviewer escalation and on what signals, how deadlines are
  tracked and what slips, how Reg E / Reg Z / Reg DD are matched to a complaint, how a spike in one issue gets noticed, what was tried before and why it failed.
Output only your next message."""

PITCH = """FINAL turn. Reply with: (1) two sentences describing a daily ranked queue of new complaints with regulation tags and a spike alert; (2) ask for their
harshest objection; (3) ask what concrete next step, if any, they would commit to (a data sample, a 30-minute review, an introduction) and when. No compliments."""

transcript, history, inter_hist = [], [], []
opening = ("Thanks for the time. Think about the last complaint that got escalated to a senior reviewer on your team. "
           "Walk me through what happened from the moment it arrived.")
transcript.append(("Interviewer", opening))
history.append({"role": "user", "content": opening})
inter_hist.append({"role": "assistant", "content": opening})
for turn in range(1, a.turns + 1):
    ans = chat(a.persona_model, PERSONA, history)
    transcript.append(("Head of Complaints (simulated)", ans))
    history.append({"role": "assistant", "content": ans})
    inter_hist.append({"role": "user", "content": ans})
    if turn == a.turns:
        break
    final = turn == a.turns - 1
    q = chat(a.interviewer_model, INTERVIEWER + ("\n\n" + PITCH if final else f"\n\n(Turn {turn + 1} of {a.turns}. Do not pitch yet.)"),
             inter_hist, temperature=0.5, max_tokens=800)
    transcript.append(("Interviewer", q))
    history.append({"role": "user", "content": q})
    inter_hist.append({"role": "assistant", "content": q})

convo = "\n\n".join(f"{who}: {text}" for who, text in transcript)
SUMMARY = """You analyze a SIMULATED discovery interview for a builder. Be honest and skeptical; this is practice, not market evidence.
Rules from the Mom Test: compliments, hypotheticals and polite promises are NOT evidence; only concrete past behavior counts (and here even that is simulated).
Produce markdown with exactly these sections:
## What the persona described about today's workflow
(5-8 bullets; past, concrete behavior only)
## Objections and risks raised
(bullets, with the quoted words)
## Next step offered, and is it real?
(Did the persona commit to anything concrete? If it is a polite promise or a conditional, say so.)
## Hypotheses (from the brief)
H1: a daily risk score using only arrival-day fields puts at least 2x as many later-relief complaints in each day's top 50 as random ordering.
H2: consumer-chosen product/issue labels are wrong often enough that a narrative classifier is worth having.
H3: most relief-bearing complaints map to a few deadline-bound sections (Reg E 1005.11, Reg Z 1026.13), so citing the section helps the reviewer act inside the clock.
For each: supports / weakens / says nothing, with a one-line quote. Never write 'validated'.
## Source-backed vs invented
Which specifics match the desk-research sources and which look invented by the persona (treat as unverified).
## Interviewer mistakes (Mom Test)
Any compliments, leading questions, hypotheticals or early pitching in the interviewer's turns.
## Open questions for a real practitioner
(3-5 bullets)"""
summary = chat(a.summary_model, SUMMARY, [{"role": "user", "content": "SOURCES:\n" + notes[:12000] + "\n\nTRANSCRIPT:\n" + convo}],
               temperature=0.2, max_tokens=4000)

hdr = f"""# Simulated stakeholder session {a.session}: Head of Complaints Triage

> **SIMULATED.** No real person or bank was interviewed. Both sides are language models (persona `{a.persona_model}`, interviewer `{a.interviewer_model}`):
> an interviewer following Mom Test rules and a persona allowed to state only what the public desk-research notes in `docs/discovery/01..06` support.
> It tests my questioning and my assumptions, not the market. Simulated evidence is opinion, not data. Cost: ${cost:.3f}.

Date: 2026-10-15. Plan task W1-SIM-01 (replaces discovery call 1; no real outreach, decision D4).

## Transcript

"""
body = "\n\n".join(f"**{who}:** {text}" for who, text in transcript)
open(a.out, "w").write(hdr + body + f"\n\n---\n\n# Analysis (model-generated by `{a.summary_model}`; check it against the transcript)\n\n" + summary + "\n")
print(f"wrote {a.out}; messages {len(transcript)}; cost ${cost:.4f}")
