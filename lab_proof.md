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

## 8. Failure modes (four distinct) + one guardrail success

The CRITICAL RULE is enforced by the model choosing to comply, not by any
code path that checks it. `normalobjects_langchain.py` was extended
(`print_trace`, a counterfactual call, and two new `EXTRA_COMPLAINTS`) to run
three different queries through the agent in one execution and capture the
full tool trace for each — `AGENT RUN 1` (the flickering-lamp/portal query),
`AGENT RUN 2` (a query with no matching record in either lookup tool), and
`AGENT RUN 3` (a query that pulls from two different tools).

**Everything quoted below comes from one single execution**
(`PYTHONIOENCODING=utf-8 python normalobjects_langchain.py`, output saved to
`run_capture.txt`, not committed) — no mixing across runs. Because tool
choice is temperature-0.7 and nondeterministic, a different execution
(compare Section 5, or the earlier draft of this section) can and does pick
different tools, different keys, and different phrasing for the *same*
queries. That instability is itself part of the finding in 8.1, not a
reason to average runs together.

### 8.1 Tool-selection nondeterminism — relevant tool never called

`AGENT RUN 1`, same query as Section 4-6, called only 2 tools this run:

```
[1] TOOL CALLED: check_hawkins_records
    ARGS: {'query': 'portal'}
[2] TOOL CALLED: consult_demogorgon
    ARGS: {'complaint': 'my lamp keeps flickering and I think there is a portal in my closet'}
```

`check_hawkins_records` was never called with `electricity` — the most
literal part of the complaint ("lamp keeps flickering") went
uninvestigated. (Section 5's earlier-recorded run *did* call it — same
query, different execution, different tool selection.) The counterfactual in
the script proves the record was reachable the whole time:

```
=== COUNTERFACTUAL ===
[SOURCE: check_hawkins_records | matched_key='electricity' | query='my lamp keeps flickering electricity']
HAWKINS LAB FILE 02-C: Localized electrical anomalies precede gate activity by 4 to 6 hours. Flickering lights are a leading indicator, not a wiring fault.
```

### 8.2 Substring-match collision: an irrelevant record cited as relevant advice

Both `check_hawkins_records` and `gather_party_wisdom` match by plain
substring —`if key in query.lower()` (`normalobjects_langchain.py:52`,
`:100`) — with no relevance check beyond "does this word appear."

`AGENT RUN 3` ("My friend Dustin says the monsters in my garage are just
raccoons. Is this dangerous?") shows the consequence:

```
[1] TOOL CALLED: gather_party_wisdom
    ARGS: {'question': 'Is it dangerous to confuse raccoons with monsters?'}
    RETURNED: [SOURCE: gather_party_wisdom | matched_key='danger' | question='Is it dangerous to confuse raccoons with monsters?']
LUCAS: 'Everyone calm down. We need a plan, a weapon, and at least one person who is not being dramatic.'
```

`'danger'` matched because the question contains the word "dangerous" — not
because Lucas's line is about raccoons, garages, or anything in the
complaint. It's a generic stock line about staying calm. The final answer
nonetheless presents it as situational safety guidance:

> "Lucas would recommend that you 'calm down' and 'need a plan, a weapon,
> and at least one person who is not being dramatic' when it comes to
> potential dangers lurking about [SOURCE: gather_party_wisdom]."

The citation is technically accurate — that is what the tool returned — but
the retrieval step had no way to tell "advice about raccoons" from "advice
containing the letters d-a-n-g-e-r." Any question with "dangerous" in it
gets the same canned Lucas quote, regardless of topic.

### 8.3 Untagged editorializing

`AGENT RUN 1`'s final answer opens with a confidence claim that has no
tool behind it at all:

> "First off, your concern about the flickering lamp and the potential
> portal in your closet is quite valid!"

No tool returned an assessment of whether the complaint is "valid" —
`check_hawkins_records` returned a portal-instability log, not a verdict on
this user's specific situation. Same pattern as "not only irregular but
potentially dangerous" in Section 7: an evaluative claim asserted in the
model's own voice, untagged, sitting right next to properly cited material
in the same paragraph.

### 8.4 Tagged claim that generalizes record content past what it supports

Also in `AGENT RUN 1`, immediately after the portal citation:

> "This suggests that portals can indeed be a real issue around here,
> especially if they are in your home [SOURCE: check_hawkins_records]."

FILE 04-B says a portal was logged in 1983 in "Sublevel 3" — a lab, not
"your home." The citation is real and attached to the right tool call, but
the claim stretches a specific historical record into a general statement
about the reader's own house. Distinct from 8.2: here the *tool call was
relevant*, the record was the right one to fetch — the overreach happens
in how the model paraphrases it, not in which record got matched.

### 8.5 Guardrail success: correct handling of `matched_key=NONE`

`AGENT RUN 2` ("My landlord keeps mailing me letters about the smell in the
basement. Is this normal?") is the clean case. Both tools came back empty:

```
[1] TOOL CALLED: check_hawkins_records
    ARGS: {'query': 'smell in basement'}
    RETURNED: [SOURCE: check_hawkins_records | matched_key=NONE | query='smell in basement']
NO RECORD FOUND. Searched keys: ['portal', 'monsters', 'psychics', 'electricity']. No documented evidence exists for this query.

[2] TOOL CALLED: gather_party_wisdom
    ARGS: {'question': 'Is it normal for a landlord to send letters about a smell in the basement?'}
    RETURNED: [SOURCE: gather_party_wisdom | matched_key=NONE | question='Is it normal for a landlord to send letters about a smell in the basement?']
The party huddles and argues. No consensus reached. Searched keys: ['friends', 'science', 'danger', 'drawing'].
```

And the final answer honors both misses instead of inventing a record or an
opinion:

> "It appears that there are no official Hawkins Lab records regarding the
> smell in basements, so we can't say for sure if it's normal or not.
> [SOURCE: check_hawkins_records | matched_key=NONE]
>
> As for the party's opinion, they couldn't reach a consensus on whether
> it's normal for a landlord to send letters about a smell in the basement.
> [SOURCE: gather_party_wisdom | matched_key=NONE]"

This is the guardrail working as designed: on two separate `NONE` results,
the model said so plainly, twice, with the miss tagged both times, rather
than fabricating a Hawkins file or a party opinion that doesn't exist.

### Summary

| # | Mode | Run | Root cause |
|---|---|---|---|
| 8.1 | Tool-selection nondeterminism — relevant tool never called | 1 | Model's per-run choice, not enforced |
| 8.2 | Substring-match collision — irrelevant record cited as relevant | 3 | `if key in query.lower()` has no relevance check |
| 8.3 | Untagged editorializing | 1 | CRITICAL RULE compliance is voluntary |
| 8.4 | Tagged claim generalized past what the record says | 1 | Correct retrieval, unfaithful paraphrase |
| 8.5 | Guardrail success on `matched_key=NONE` (×2 in one run) | 2 | Model followed the rule as intended |

Four distinct failure modes and one success, all from a single execution.
Nothing in the code checks tool coverage, verifies citation accuracy, or
constrains retrieval to relevant matches — the guardrail's reliability is
bounded entirely by the model's per-run behavior, not by anything
`AgentExecutor` or `HAWKINS_RECORDS`'s substring lookup guarantees.