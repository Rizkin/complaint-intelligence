# Simulated stakeholder session 1: Head of Complaints Triage

> **SIMULATED.** No real person or bank was interviewed. Both sides are language models (persona `anthropic/claude-sonnet-5`, interviewer `anthropic/claude-haiku-5.5`):
> an interviewer following Mom Test rules and a persona allowed to state only what the public desk-research notes in `docs/discovery/01..06` support.
> It tests my questioning and my assumptions, not the market. Simulated evidence is opinion, not data. Cost: $0.266.

Date: 2026-10-15. Plan task W1-SIM-01 (replaces discovery call 1; no real outreach, decision D4).

## Transcript

**Interviewer:** Thanks for the time. Think about the last complaint that got escalated to a senior reviewer on your team. Walk me through what happened from the moment it arrived.

**Head of Complaints (simulated):** Roughly two, three weeks back — a Reg E unauthorized-transfer complaint, customer claiming around $900 in transfers they didn't make, came in through the CFPB portal. Front-line ops logged it, pulled transaction history, but it sat about four days before anyone flagged it was coming up on the 10-business-day mark without provisional credit decisioned, so it got kicked up to me because of the clock, not because anyone caught a risk signal early. I ended up pushing it through same-day once I saw it, but honestly it was a spreadsheet flag someone noticed, not a system alert — that's the part that worries me when I think about volume.

**Interviewer:** Okay. Who was looking at that spreadsheet when the flag got noticed, and what made them open it that day?

**Head of Complaints (simulated):** I'd have to check exactly who — one of the senior analysts on the ops side, not me directly, flags it to me. Why that day specifically, I'm not sure it was anything systematic; could've been a scheduled daily review of aging items, could've been they were clearing their queue and it happened to be near the top. That's kind of my point — I can't tell you it's a reliable trigger, it's whoever's got eyes on the tracker that day.

**Interviewer:** Okay. Before this one, when was the last time someone flagged an item from that tracker to you? What was the item, and how long had it been open?

**Head of Complaints (simulated):** I don't have an exact date for you — it's not something I log separately, it's ad hoc. My rough recollection is a few weeks before that, a billing dispute, card charge the customer said was duplicated, and it had been sitting closer to three weeks before it got to me — past where I'd want it, honestly, for a Reg Z billing-error clock. That's the pattern I'd flag to you: it's not a steady cadence, it's whatever surfaces when someone happens to scan the aging column.

**Interviewer:** Okay. For that billing dispute, what happened in the three weeks before it reached you? Who had it, and what did they do with it each time it sat?

**Head of Complaints (simulated):** Honestly, I can't walk you through week-by-week — that level of touch-by-touch history isn't something I have visibility into after the fact, and I doubt it's reconstructable cleanly from our side either. My rough understanding is it sat in a general ops queue, probably got a first-pass documentation request to the merchant or card network, then waited on a response, and nobody re-touched it until it aged into view. That gap — no one owning "is this clock about to blow" in between actions — is exactly the kind of thing that gets us written up, not the actual resolution.

**Interviewer:** Got it. When that billing dispute got written up, what did you have to do afterward, and how much of your time did it take?

**Head of Complaints (simulated):** Once it's past where I want it, it's damage control: I pull the file, confirm whether we're inside or outside the 1026.13 acknowledgment/resolution clock, decide if we owe a written explanation either way, and draft or edit the response memo myself rather than trust the first draft. For something like that, call it half a day between review, writing, and looping in whoever touched it originally to understand the gap — plus it goes in my notes for the next compliance reporting cycle since a near-miss on the clock is the kind of thing that gets asked about. Multiply that by however many slip through and it's a real chunk of senior time that isn't going to root-cause work.

**Interviewer:** Okay. The last time one of these got written up, what did your team change, and what happened to that change after a few weeks?

**Head of Complaints (simulated):** We talked about adding a daily aging-report check specifically for anything inside 5 business days of a Reg E or Reg Z deadline — sounds simple. In practice it half-stuck: for a couple weeks someone ran it manually every morning, then that person rotated onto something else and it lapsed back to the ad hoc scan. I don't think it's formally anyone's job description to run that report, which is the gap — we fixed the symptom for the one case, not the ownership problem.

**Interviewer:** Okay. When the daily check lapsed, what was the first item that got past its deadline without anyone catching it? Walk me through how it surfaced.

**Head of Complaints (simulated):** I don't have a clean answer — honestly I'm not sure one did blow past, or if it did, I don't know that we'd necessarily know it in a tidy "here's the moment it surfaced" way. My best guess is it'd surface the same way the billing one did — someone scanning the aging column, or it comes back in a monthly complaint summary rollup and someone notices a timeliness number looks off versus internal target. We don't have a clean trigger-to-detection story here, which is really the honest answer.

**Interviewer:** Okay. When did you last see a timeliness number in a monthly summary that looked off? What was the number, and what did someone do after they saw it?

**Head of Complaints (simulated):** I don't have a specific instance to point to — I'm speculating that's *how* it would surface, not reporting that it did. Our timeliness on the regulator-facing clock has actually been fine historically, high nineties percent; it's the internal Reg E/Z clocks running underneath that worry me, and those aren't rolled into the monthly pack as a clean number today, they're more anecdotal when someone like me catches one. That gap — no systematic internal-clock metric — is honestly the thing I'd want fixed before I trust any dashboard telling me it's fine.

**Interviewer:** Okay. When you last pulled the regulator-facing timeliness number, where did it come from, and how long did getting it take?

**Head of Complaints (simulated):** That one's easier because it's a cleaner pull — comes out of the CFPB portal export itself, or a summary someone on the reporting side runs in Excel against it, cut by product and response type. Takes maybe an hour or two to assemble for the monthly pack, not because the data's hard to get but because someone's reconciling it against our own case-tracking numbers to make sure they match. It's the internal Reg E/Z clock piece layered on top of that export where we don't have an equivalent clean pull — that part's manual and incomplete, which is the whole reason I keep coming back to it.

**Interviewer:** Here is the idea in two sentences: each morning, the tool would rank all new complaints by how close they are to their Reg E, Reg Z, or Reg DD deadlines, with the regulation tag on each one. It would also fire a spike alert when one issue type rises above its normal volume, so no one has to notice it by scanning the aging column.

What is the harshest objection you would raise against this?

If that objection doesn't kill it, what concrete next step would you commit to, such as a data sample, a 30-minute review of your current aging report, or an introduction to whoever owns the reporting pull? Tell me what it is and by when.

**Head of Complaints (simulated):** Harshest objection: the regulation tag is the whole ballgame, and that's exactly where I don't trust an automated pass. If the tool mis-tags something as "no regulation applies" when it's actually a 1005.11 case, or over-tags a routine service complaint as Reg E, I've traded "nobody noticed in time" for "someone trusted a wrong flag and didn't notice in time" — and now there's a system of record saying we had a ranked list and still missed the clock. That's a worse exam conversation, not a better one. Second thing right behind it: who owns reacting to the spike alert at 7am — if it's the same ad hoc person scanning a column today, you've just automated the detection, not the accountability gap I actually described to you.

What would have to be true for me to take it seriously: the regulation-tagging logic has to be auditable — I need to see false-negative rate on "this should've been flagged as a clock item and wasn't," not just overall accuracy, and it needs model-risk and compliance sign-off before it touches anything that looks like an official tracker. I'm not committing to a meeting or a data pull today. Send me a one-pager on how the tagging works and what the backtest against closed cases looks like — precision and recall on the regulation label specifically — and I'll decide whether it's worth 30 minutes with compliance in the room.

---

# Analysis (model-generated by `anthropic/claude-sonnet-5`; check it against the transcript)

## What the persona described about today's workflow

- A Reg E unauthorized-transfer complaint (~$900) "sat about four days before anyone flagged it was coming up on the 10-business-day mark without provisional credit decisioned" before escalation.
- Escalation happened because "it got kicked up to me because of the clock, not because anyone caught a risk signal early" — a spreadsheet flag noticed by a senior analyst, not a system alert.
- A prior billing dispute (duplicate card charge) "had been sitting closer to three weeks before it got to me," which the persona says is "past where I'd want it… for a Reg Z billing-error clock."
- After that billing dispute was escalated, the persona personally "pull[ed] the file, confirm[ed] whether we're inside or outside the 1026.13 acknowledgment/resolution clock," decided on written explanation, and drafted/edited the response memo — "call it half a day."
- The team tried adding "a daily aging-report check specifically for anything inside 5 business days of a Reg E or Reg Z deadline"; it was run manually each morning for "a couple weeks," then lapsed when the person running it "rotated onto something else."
- Regulator-facing timeliness numbers come from "the CFPB portal export itself, or a summary someone on the reporting side runs in Excel against it, cut by product and response type," taking "maybe an hour or two" monthly, mostly for reconciliation against internal case-tracking.
- No internal Reg E/Reg Z clock metric exists in the monthly pack today — "those aren't rolled into the monthly pack as a clean number today, they're more anecdotal when someone like me catches one."

## Objections and risks raised

- "the regulation tag is the whole ballgame, and that's exactly where I don't trust an automated pass" — fear of mis-tagging (false negatives on real Reg E/Z cases, or over-tagging routine complaints).
- "I've traded 'nobody noticed in time' for 'someone trusted a wrong flag and didn't notice in time' — and now there's a system of record saying we had a ranked list and still missed the clock. That's a worse exam conversation, not a better one."
- Accountability gap, not just detection: "who owns reacting to the spike alert at 7am — if it's the same ad hoc person scanning a column today, you've just automated the detection, not the accountability gap."
- Needs auditability: "I need to see false-negative rate on 'this should've been flagged as a clock item and wasn't,' not just overall accuracy."
- Governance gate: "it needs model-risk and compliance sign-off before it touches anything that looks like an official tracker."

## Next step offered, and is it real?

Not a real commitment. The persona explicitly declines: "I'm not committing to a meeting or a data pull today." The only thing offered is conditional and passive — the interviewer should "send me a one-pager," after which the persona "will decide whether it's worth 30 minutes with compliance in the room." This is a polite deferral/conditional promise, not concrete action, date, or resource commitment from the persona's side.

## Hypotheses (from the brief)

**H1** (arrival-day risk score beats random 2x on relief): Says nothing directly — persona never discusses a backtest or ranking performance; describes manual aging scans and clock proximity, not a scored ranking against relief outcomes. Quote: "it's whoever's got eyes on the tracker that day." (Not evidence for or against the specific 2x claim.)

**H2** (consumer-chosen labels are wrong often enough to need a narrative classifier): Says nothing — the persona never discusses the accuracy of consumer-chosen product/issue labels at all; concern is about automated *regulation* tagging, not consumer-chosen issue labels. Quote: "the regulation tag is the whole ballgame."

**H3** (relief-bearing complaints map to deadline-bound sections, citing section helps reviewer act in time): Weakens/complicates — the persona agrees the sections (1005.11, 1026.13) are the real clocks that matter, but argues citing the section via automated tagging could backfire if wrong, and that detection isn't the bottleneck, accountability/ownership is. Quote: "If the tool mis-tags something as 'no regulation applies' when it's actually a 1005.11 case... I've traded 'nobody noticed in time' for 'someone trusted a wrong flag and didn't notice in time.'"

## Source-backed vs invented

- **Matches sources:** Reg E 10-business-day / provisional credit clock, Reg Z 1026.13 acknowledgment/resolution clock, CFPB portal timeliness being "high nineties percent" historically (99.55% in note 01), monthly reporting pulled from portal export in Excel — all consistent with notes 01–03.
- **Invented/unverified (persona-specific specifics, simulated):** the exact $900 Reg E case, the "about four days" sitting time, "three weeks" for the billing dispute, "half a day" of senior time, the manual aging-report experiment and its lapse after "a couple weeks," and all internal timing/ownership details — none of these appear in the desk-research sources; they are simulated elaborations consistent with the sources' *shape* (note 02's "sampling for risk indicators," note 03's clock findings) but not themselves sourced facts.

## Interviewer mistakes (Mom Test)

- The pitch itself ("Here is the idea in two sentences: each morning, the tool would rank...") is an early pitch before any further discovery, though it's somewhat justified as it's the designed test beat.
- No leading/complimenting language is present in this transcript's interviewer turns — questions are consistently past-behavior probes ("What happened...", "Who had it...", "When did you last see..."). This is a well-run Mom-Test-style interview; no compliments or hypotheticals were used to get agreement.
- Minor: the interviewer's objection-and-next-step turn bundles two asks in one utterance ("What is the harshest objection... If that objection doesn't kill it, what concrete next step...") — a compound question that gives the persona an easy out to answer only the first half, though in this case the persona did address both.

## Open questions for a real practitioner

- How is "who owns reacting to the spike alert" assigned today for *any* existing alert/report, and has that model worked for anything comparable in the past?
- What specifically would the model-risk/compliance sign-off process require before a tagging tool could touch an "official tracker" — timeline, criteria, prior examples?
- Can the practitioner share (even redacted) an actual instance of a near-miss or missed internal clock, with real dates, to replace the hypothetical/reconstructed billing-dispute story?
- What would a false-negative rate on regulation tagging need to be (quantitatively) for them to trust it, and against what backtest dataset size/source?
- Is there any existing systematic internal Reg E/Z clock metric anywhere in the organization (even outside the monthly pack) that could be used as ground truth for a backtest?
