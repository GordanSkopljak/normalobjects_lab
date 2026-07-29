"""
NormalObjects: Creative Complaint Handler
Week 4 / Day 3 - Chaos agent lab
"""

import os
import random
from typing import List, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not found. Check your .env file.")

print("Setup OK")


@tool
def consult_demogorgon(complaint: str) -> str:
    """Consult the Demogorgon about a complaint regarding the Upside Down.
    Returns a chaotic, unpredictable response. Use for complaints that need
    a monster's perspective."""
    responses = [
        "The Demogorgon shrieks and points at the ceiling. Interpretation: your complaint is valid but the ceiling is the problem.",
        "The Demogorgon tilts its head, unfolds its face, and refolds it. This is considered a polite refusal.",
        "The Demogorgon has filed your complaint in the Upside Down. Expected resolution time: never, or last Tuesday.",
    ]
    choice = random.choice(responses)
    return f"[SOURCE: consult_demogorgon | input='{complaint}']\n{choice}"


HAWKINS_RECORDS = {
    "portal": "HAWKINS LAB FILE 04-B: Portal instability logged Nov 1983. Gate breach originates in Sublevel 3. Containment: failed. Note: portals do not respond to written complaints.",
    "monsters": "HAWKINS LAB FILE 11-D: Three confirmed entity classes. Demogorgon (predatory), Demodogs (pack), Mind Flayer (distributed). All exhibit hostility to light and paperwork.",
    "psychics": "HAWKINS LAB FILE 07-A: Subject Eleven demonstrates telekinesis and remote viewing. Nosebleeds correlate with exertion. Waffle supply must be maintained.",
    "electricity": "HAWKINS LAB FILE 02-C: Localized electrical anomalies precede gate activity by 4 to 6 hours. Flickering lights are a leading indicator, not a wiring fault.",
}


@tool
def check_hawkins_records(query: str) -> str:
    """Search the official Hawkins Lab records for factual information.
    Topics on file: portal, monsters, psychics, electricity.
    Use this when a complaint needs documented evidence rather than opinion."""
    for key, record in HAWKINS_RECORDS.items():
        if key in query.lower():
            return f"[SOURCE: check_hawkins_records | matched_key='{key}' | query='{query}']\n{record}"
    return (
        f"[SOURCE: check_hawkins_records | matched_key=NONE | query='{query}']\n"
        f"NO RECORD FOUND. Searched keys: {list(HAWKINS_RECORDS.keys())}. "
        f"No documented evidence exists for this query."
    )


@tool
def cast_interdimensional_spell(problem: str, creativity_level: str = "medium") -> str:
    """Cast an interdimensional spell to solve a problem creatively.
    creativity_level must be 'low', 'medium', or 'high'. Higher levels return
    more solutions. Use when a complaint needs an inventive fix rather than a
    documented one."""
    multipliers = {"low": 1, "medium": 2, "high": 3}
    n = multipliers.get(creativity_level.lower(), 2)

    spells = [
        f"REVERSAL CHARM: turn '{problem}' upside down. If it was already in the Upside Down, it is now merely inconvenient.",
        f"CHRISTMAS LIGHT PROTOCOL: spell out '{problem}' on the wall in fairy lights and wait for something to answer.",
        f"EGGO BINDING: offer waffles to '{problem}'. Effective on most entities and all children.",
        f"WALKMAN WARD: play music at '{problem}' until it releases its grip. Requires fresh batteries.",
    ]

    n = min(n, len(spells))
    selected = random.sample(spells, n)
    return (
        f"[SOURCE: cast_interdimensional_spell | problem='{problem}' | "
        f"creativity_level='{creativity_level}' | spells_returned={n}]\n"
        + "\n".join(selected)
    )


PARTY_WISDOM = {
    "friends": "MIKE: 'Friends don't lie. If your complaint involves a friend lying, that is the actual complaint.'",
    "science": "DUSTIN: 'This is textbook interdimensional physics. Also I am the only one here who read the textbook.'",
    "danger": "LUCAS: 'Everyone calm down. We need a plan, a weapon, and at least one person who is not being dramatic.'",
    "drawing": "WILL: 'I drew it before it happened. I always do. Nobody looks at the drawings until it is too late.'",
}


@tool
def gather_party_wisdom(question: str) -> str:
    """Ask the party (Mike, Dustin, Lucas, Will) for their opinion on a question.
    Topics they have opinions on: friends, science, danger, drawing.
    Use when a complaint needs advice rather than documented facts."""
    for key, response in PARTY_WISDOM.items():
        if key in question.lower():
            return f"[SOURCE: gather_party_wisdom | matched_key='{key}' | question='{question}']\n{response}"
    return (
        f"[SOURCE: gather_party_wisdom | matched_key=NONE | question='{question}']\n"
        f"The party huddles and argues. No consensus reached. "
        f"Searched keys: {list(PARTY_WISDOM.keys())}."
    )


TOOLS = [
    consult_demogorgon,
    check_hawkins_records,
    cast_interdimensional_spell,
    gather_party_wisdom,
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are the Complaint Handler for NormalObjects, a shop in Hawkins, Indiana "
     "that sells entirely normal objects. Customers complain about things that are "
     "not normal.\n\n"
     "You have four tools. Use as many as you think the complaint deserves, in any "
     "order. Be creative and funny.\n\n"
     "CRITICAL RULE: every factual claim in your final answer must come from a tool "
     "result. Quote the [SOURCE: ...] tag for each claim you make. If a tool returns "
     "matched_key=NONE, you must say plainly that no record was found. Never invent "
     "Hawkins Lab records."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, TOOLS, prompt)

executor = AgentExecutor(
    agent=agent,
    tools=TOOLS,
    verbose=True,
    max_iterations=6,
    return_intermediate_steps=True,
)


def print_trace(result):
    """Print the final answer and the full tool trace for one agent run."""
    print("\n--- FINAL ANSWER ---")
    print(result["output"])

    print("\n--- TOOL TRACE ---")
    for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
        print(f"\n[{i}] TOOL CALLED: {action.tool}")
        print(f"    ARGS: {action.tool_input}")
        print(f"    RETURNED: {observation}")


if __name__ == "__main__":

    # ------------------------------------------------------------------
    # Baseline: tools called directly. No agent, no LLM.
    # Establishes that the retrieval layer is deterministic on both the
    # hit path and the miss path before any model is involved.
    # ------------------------------------------------------------------
    print("\n=== DIRECT TOOL TEST (no agent, no LLM) ===\n")

    print(consult_demogorgon.invoke({"complaint": "my lights keep flickering"}))
    print()
    print(check_hawkins_records.invoke({"query": "tell me about the portal"}))
    print()
    print(check_hawkins_records.invoke({"query": "what about my landlord"}))
    print()
    print(cast_interdimensional_spell.invoke(
        {"problem": "slime on the walls", "creativity_level": "high"}))
    print()
    print(gather_party_wisdom.invoke({"question": "is this dangerous"}))
    print()
    print(gather_party_wisdom.invoke({"question": "where are my keys"}))

    # ------------------------------------------------------------------
    # Agent run 1: the primary traced query.
    # Contains two retrievable topics (portal, electricity).
    # ------------------------------------------------------------------
    print("\n\n=== AGENT RUN 1 ===\n")

    query = "My lamp keeps flickering and I think there is a portal in my closet. What do I do?"
    print(f"QUERY: {query}\n")
    result = executor.invoke({"input": query})
    print_trace(result)

    # ------------------------------------------------------------------
    # Counterfactual: proves the 'electricity' record is always reachable
    # from the user's own wording. Any run that misses it is a tool
    # SELECTION failure, not a retrieval failure.
    # ------------------------------------------------------------------
    print("\n\n=== COUNTERFACTUAL ===\n")
    print(check_hawkins_records.invoke(
        {"query": "my lamp keeps flickering electricity"}))

    # ------------------------------------------------------------------
    # Agent runs 2 and 3.
    #   Run 2 matches NO key in either lookup tool -> exercises the
    #          matched_key=NONE branch of the guardrail.
    #   Run 3 matches 'monsters', 'friends' and 'danger' across two
    #          different tools -> exercises tool chaining.
    # ------------------------------------------------------------------
    EXTRA_COMPLAINTS = [
        "My landlord keeps mailing me letters about the smell in the basement. Is this normal?",
        "My friend Dustin says the monsters in my garage are just raccoons. Is this dangerous?",
    ]

    for n, q in enumerate(EXTRA_COMPLAINTS, 2):
        print(f"\n\n=== AGENT RUN {n} ===\n")
        print(f"QUERY: {q}\n")
        print_trace(executor.invoke({"input": q}))
