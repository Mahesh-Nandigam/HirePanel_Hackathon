# How I built an AI hiring committee that actually remembers candidates

Most AI recruiting tools are glorified keyword matchers with amnesia. They read a resume, output a score, and completely forget that interaction by the time they evaluate the next candidate. If they make a bad call on candidate #1, they’ll make the exact same bad call on candidate #50.

I got tired of stateless agents making the same mistakes over and over. So, I rebuilt our AI hiring pipeline into a multi-agent debate system where the agents actually remember past candidates. I also had to figure out how to stop the LLM costs from blowing up my wallet. 

Here’s how I did it using Hindsight and cascadeflow.

## The setup: Tech Lead vs HR

The core of the system is a debate. When a resume comes in, an extraction agent pulls the facts. Then, two specialized agents take over: a Senior Tech Lead and an HR Business Partner. 

The Tech Lead cares about architecture, real-world experience, and github commits. The HR agent cares about tenure, soft skills, and culture fit. They review the candidate and argue their case. 

Without memory, they evaluate every candidate in a vacuum. With [Hindsight agent memory](https://vectorize.io/what-is-agent-memory) embedded in the backend, they pull in context from past evaluations before making a decision.

## Giving agents a memory

I didn’t want to manage a separate vector database just to give these agents some context. So I used the embedded version of Hindsight straight in my FastAPI backend. 

Here is what the setup looks like for the Tech Lead agent:

```python
from hindsight import HindsightEmbedded
import os

hs_client = HindsightEmbedded(
    profile="hirepanel",
    llm_provider="groq",
    llm_model="llama-3.3-70b-versatile",
    llm_api_key=os.environ.get("GROQ_API_KEY", "")
)
```

Before the Tech Lead writes its evaluation, it runs a quick `recall` query to see if it has reviewed a similar candidate recently.

```python
# Tech Lead recalls past decisions
memory_query = f"Candidate with GitHub score {github_score} and Resume score {resume_score}"
past_context = hs_client.recall(memory_query)
```

This changes everything. Instead of relying purely on the system prompt telling it to be "strict," the agent actually looks at its past decisions. It might say, *"Similar to a candidate we saw last week who had a high resume score but weak GitHub, this person lacks proven production code. I'm passing."*

Once the debate finishes, the agents use `hs_client.retain()` to save their final decision to memory, so they learn for the next time. Check out the [Hindsight docs](https://hindsight.vectorize.io/) or the [Hindsight GitHub](https://github.com/vectorize-io/hindsight) to see how simple the API is.

## Stopping the bleeding with cascadeflow

Running a multi-agent debate with Llama-3.3-70B for every single resume gets expensive extremely fast. But I didn't want to downgrade the debate logic to an 8B model because the reasoning quality drops off a cliff.

I realized I only needed the 70B model for the deep reasoning part. The initial resume parsing? A smaller model can do that easily. 

I wrapped the extraction calls in [cascadeflow](https://github.com/lemony-ai/cascadeflow). It intercepts the LLM calls and routes them based on the task difficulty.

```python
from cascadeflow import CascadeAgent

extractor = CascadeAgent(
    primary_model="llama-3.3-70b-versatile",
    fallback_model="llama-3.1-8b-instant"
)

# cascadeflow automatically routes this simple task to the cheaper 8B model
parsed_data = extractor.run("Extract skills and tenure from this resume text.")
```

By adding cascadeflow, all the basic extraction stuff gets routed to `llama-3.1-8b-instant` for pennies, and we save our token budget for the heavy lifting in the debate phase. It dropped our overall token costs by about 75%. (You can read more in the [cascadeflow docs](https://docs.cascadeflow.ai/)).

## What I learned

1. **Memory beats prompt engineering.** Telling an agent to "be strict" in a system prompt works for one turn. Showing an agent its past decisions forces authentic behavior change.
2. **You don't need 70B for everything.** Routing simple tasks to smaller models is mandatory if you want to scale multi-agent systems without going broke.
3. **Stateful agents are the future.** Once you see an agent reference a past interaction to make a better decision today, stateless agents feel broken.

If you want to poke around the code, I open-sourced the whole thing on my GitHub. Let me know if you guys are messing around with agent memory too, I’d love to see how you're handling statefulness!
