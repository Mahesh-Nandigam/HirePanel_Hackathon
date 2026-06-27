# How we built an AI hiring committee that actually remembers candidates

Most AI recruiting tools are glorified keyword matchers with amnesia. They read a resume, output a score, and completely forget that interaction by the time they evaluate the next candidate. I wanted to build something that felt like a real hiring committee—a team of specialized AI agents that debate a candidate's merits and, crucially, *remember* their past decisions to calibrate future ones. 

Here is how I built an AI Tech Lead and HR Partner that learn from past candidates using Hindsight, while keeping our LLM costs from spiraling out of control using cascadeflow.

## The Architecture: A Multi-Agent Debate

The system works in phases. First, an Intake Agent extracts facts from a resume, and specialized assessors (GitHub Agent, LinkedIn Agent) give it base scores. 

Then comes the fun part: the debate. We spin up two specialized agents—a Senior Tech Lead and an HR Business Partner. They review the scores and argue about the candidate. 

Without memory, they evaluate every candidate in a vacuum. With Hindsight embedded, they pull in context from past evaluations before making a decision.

## Embedding Memory with Hindsight

To give the agents long-term memory without managing a complex vector database, I embedded a local instance of Hindsight directly into our FastAPI backend. 

Here is what the initialization looks like for our Tech Lead agent:

```python
from hindsight import HindsightEmbedded
import os

hs_client = HindsightEmbedded(
    profile="hackathon",
    llm_provider="groq",
    llm_model="llama-3.3-70b-versatile",
    llm_api_key=os.environ.get("GROQ_API_KEY", "")
)
```

Before the Tech Lead evaluates a new candidate, it performs a `recall` to see how it treated similar candidates in the past:

```python
past = hs_client.recall(
    bank_id="tech_lead", 
    query=f"How did we evaluate candidates with resume score around {resume_score} and github score around {github_score}?"
)
memory_str = "\n".join([r.text for r in past.results]) if hasattr(past, 'results') else ""
```

We inject this `memory_str` directly into the agent's prompt. After the agent makes its decision, it performs a `retain` call to save the new outcome. The result? The agent starts saying things like, *"Similar to our last candidate with a high resume score but weak GitHub presence, this person lacks proven production code."* It actually calibrates its expectations.

## Taming the API Bill with cascadeflow

Running multiple 70B parameter models for every single resume is a great way to go broke. The Intake and Assessor agents perform relatively simple extraction tasks, while the Debate agents need serious reasoning.

Instead of writing complex fallback logic, I wrapped our model calls in `cascadeflow`:

```python
from cascadeflow import CascadeAgent, ModelConfig

agent = CascadeAgent(models=[
    ModelConfig(name="llama-3.1-8b-instant", provider="groq", cost=0.0001), # Drafter
    ModelConfig(name="llama-3.3-70b-versatile", provider="groq", cost=0.0005) # Verifier
])

res = asyncio.run(agent.run(messages=messages))
```

Cascadeflow automatically routes simpler extraction tasks to the lightning-fast 8B model, reserving the 70B model only when the cheaper model fails verification. This single change significantly reduced our token costs while maintaining the exact same decision quality during the debate phase. We log the cost savings directly to the console on every request.

## Lessons Learned

1. **Memory beats prompt engineering.** You can prompt an agent to be "skeptical" all day, but showing it a past mistake it made via Hindsight recall forces a much more authentic behavior change.
2. **Routing is mandatory for multi-agent systems.** If you have 5 agents in a pipeline, you cannot run your biggest model for all of them. `cascadeflow` makes this trivial to implement without writing your own router.
3. **Stateful agents are the future.** Building stateless wrappers around LLMs is table stakes now. Giving agents their own isolated memory banks makes them feel like colleagues rather than calculators.

If you want to build stateful agents, check out the [Hindsight GitHub](https://github.com/vectorize-io/hindsight) and read about [Vectorize agent memory](https://vectorize.io/what-is-agent-memory). For cost control, check out the [cascadeflow GitHub](https://github.com/lemony-ai/cascadeflow) and read the [cascadeflow docs](https://docs.cascadeflow.ai/).
