# Lab Proof: Creative Complaint Handler (LangChain agent)

## 1. Path chosen
**Tool-calling agent**, with a guardrail layered on top.

`normalobjects_langchain.py` builds the agent with `create_openai_tools_agent` +
`AgentExecutor` (`langchain_classic.agents`), backed by four `@tool`-decorated
functions (`consult_demogorgon`, `check_hawkins_records`,
`cast_interdimensional_spell`, `gather_party_wisdom`). This is the "agent" path,
not plain retrieval, because the LLM decides at runtime which tools to call, in
what order, and with what arguments — it isn't a fixed retrieve-then-generate
pipeline. A guardrail is bolted onto that agent via the system prompt's
"CRITICAL RULE": every factual claim in the final answer must cite a
`[SOURCE: ...]` tag, and the model must say plainly when a tool returns
`matched_key=NONE` rather than invent a record. That rule is enforced only by
prompting, not by code — which is exactly what Section 7/8 test.

## 2. Environment
- Python 3.14.4 (`.venv/Scripts/python.exe --version`)
- `langchain==1.3.14`
- `langchain-classic==1.0.8`
- Full pinned set in [requirements.txt](requirements.txt) (langchain-core 1.5.2,
  langchain-openai 1.4.1, langgraph 1.2.10, openai 2.50.0, etc.)

## 3. Setup finding: handout was wrong about imports
Reproduced the failure directly:

```
>>> from langchain.agents import AgentExecutor, create_openai_tools_agent
ImportError: cannot import name 'AgentExecutor' from 'langchain.agents'
(...langchain\agents\__init__.py)
```

Confirmed the fix works:

```
>>> from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
# no error
```

**Conclusion:** in this pinned version set, `langchain 1.3.14` no longer ships
`AgentExecutor`/`create_openai_tools_agent` from `langchain.agents` — that
surface was split out into the separate `langchain-classic` package. The
handout's import path is stale for this LangChain version; the working import
is `from langchain_classic.agents import ...`, which is what the script
actually uses.

## 4. The query
> My lamp keeps flickering and I think there is a portal in my closet. What do I do?

## 5. Tool evidence
Real run (`AGENT RUN 1`, temperature 0.7 — the LLM's tool choices vary between
runs, see Section 8):

```
[1] TOOL CALLED: check_hawkins_records
    ARGS: {'query': 'portal'}
    RETURNED: [SOURCE: check_hawkins_records | matched_key='portal' | query='portal']
HAWKINS LAB FILE 04-B: Portal instability logged Nov 1983. Gate breach originates in Sublevel 3. Containment: failed. Note: portals do not respond to written complaints.

[2] TOOL CALLED: check_hawkins_records
    ARGS: {'query': 'electricity'}
    RETURNED: [SOURCE: check_hawkins_records | matched_key='electricity' | query='electricity']
HAWKINS LAB FILE 02-C: Localized electrical anomalies precede gate activity by 4 to 6 hours. Flickering lights are a leading indicator, not a wiring fault.

[3] TOOL CALLED: consult_demogorgon
    ARGS: {'complaint': 'lamp flickering and possible portal in closet'}
    RETURNED: [SOURCE: consult_demogorgon | input='lamp flickering and possible portal in closet']
The Demogorgon has filed your complaint in the Upside Down. Expected resolution time: never, or last Tuesday.

[4] TOOL CALLED: cast_interdimensional_spell
    ARGS: {'problem': 'lamp flickering and possible portal in closet', 'creativity_level': 'high'}
    RETURNED: [SOURCE: cast_interdimensional_spell | problem='lamp flickering and possible portal in closet' | creativity_level='high' | spells_returned=3]
EGGO BINDING: offer waffles to 'lamp flickering and possible portal in closet'. Effective on most entities and all children.
CHRISTMAS LIGHT PROTOCOL: spell out 'lamp flickering and possible portal in closet' on the wall in fairy lights and wait for something to answer.
REVERSAL CHARM: turn 'lamp flickering and possible portal in closet' upside down. If it was already in the Upside Down, it is now merely inconvenient.
```

## 6. Final output

```
It sounds like you have a serious case of "lamp flickering and possible portal in closet," which is not only irregular but potentially dangerous!

Here's what I've found:

1. **Portals & Flickering Lights**: According to Hawkins Lab records, localized electrical anomalies (like flickering lights) are often a sign of impending gate activity, indicating that your lamp's flicker is not a simple wiring issue, but rather a leading indicator of a portal nearby. [SOURCE: check_hawkins_records | matched_key='electricity'] Moreover, the records also confirm that any portals in the area have a history of instability and can be quite unpredictable. [SOURCE: check_hawkins_records | matched_key='portal']

2. **Demogorgon Input**: I consulted the Demogorgon, and it seems your complaint has been filed in the Upside Down. Unfortunately, the expected resolution time is... never, or possibly last Tuesday. So, there's that! [SOURCE: consult_demogorgon | input='lamp flickering and possible portal in closet']

Now, for some creative solutions:

- **EGGO BINDING**: Offer waffles to the lamp and the closet. This spell is effective on most entities and all young children, so who knows what might happen?
- **CHRISTMAS LIGHT PROTOCOL**: Spell out "lamp flickering and possible portal in closet" on the wall using fairy lights and wait for a response. You might just get an answer!
- **REVERSAL CHARM**: Turn the whole situation upside down. If it was already in the Upside Down, it will just be a minor inconvenience instead of a full-blown crisis.

Choose wisely, and good luck!
```

## 7. Verification: which claims are grounded

| Claim | Source tag cited | Actually supported? |
|---|---|---|
| "not only irregular but potentially dangerous" | none | No — editorializing, no tool backs "dangerous" |
| Flickering lights are a leading indicator of impending gate activity, not a wiring fault | `check_hawkins_records \| matched_key='electricity'` | Yes — matches FILE 02-C verbatim |
| Portals in the area "have a history of instability" | `check_hawkins_records \| matched_key='portal'` | Yes — matches FILE 04-B ("Portal instability logged") |
| Portals "can be quite unpredictable" | same tag as above | Partial — record says instability/failed containment, never says "unpredictable"; a mild extrapolation dressed as a direct citation |
| Demogorgon filed complaint in the Upside Down, resolution "never, or last Tuesday" | `consult_demogorgon` | Yes — direct paraphrase of tool return |
| EGGO BINDING / CHRISTMAS LIGHT PROTOCOL / REVERSAL CHARM spells | `cast_interdimensional_spell` (implicit, no tag on this claim) | Yes in content, but the final answer never actually attaches a `[SOURCE: cast_interdimensional_spell...]` tag to these — a guardrail miss even though the content itself is grounded |

## 8. Failure / limitation
**The flickering finding:** the CRITICAL RULE is enforced by the model
choosing to comply, not by any code path that checks it — so both *which*
tools get called and *whether* every claim gets tagged flicker between runs of
the identical query at temperature 0.7.

Ran the exact same query three times:

- **Run 1** (above): 4 tool calls (`portal`, `electricity`, demogorgon, spell).
  Grounded the electricity/flickering claim correctly, but also let one
  ungrounded claim ("potentially dangerous") and one untagged-but-grounded
  claim (the spells) through.
- **Run 2**: only 2 tool calls (`portal`, demogorgon) — `check_hawkins_records`
  was never called with `electricity`, so the model had no source for a
  flickering/wiring claim and correctly avoided making one, but it also never
  investigated the most literal part of the complaint ("lamp keeps
  flickering").
- **Run 3**: same 2 tool calls as Run 2 (`portal`, demogorgon), same gap.

So the finding reproduced across all 3 runs: tool selection is
nondeterministic for an identical input, which means the guardrail's
guarantee ("every factual claim comes from a tool result") is only as
reliable as the model's per-run choice to (a) call the relevant tool at all
and (b) tag every sentence that depends on it. Nothing in the code enforces
either.

As a static counterfactual, calling the tool directly on the literal
complaint text proves the record exists and would have been available had the
agent queried it every time:

```
[SOURCE: check_hawkins_records | matched_key='electricity' | query='my lamp keeps flickering electricity']
HAWKINS LAB FILE 02-C: Localized electrical anomalies precede gate activity by 4 to 6 hours. Flickering lights are a leading indicator, not a wiring fault.
```