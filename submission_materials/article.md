# I got tired of my AI agents having amnesia, so I built a Hiring Committee that actually remembers past candidates

*Disclaimer: If you are looking for a surface-level "Top 10 ChatGPT Prompts" post, please keep scrolling. I don't want to waste your time, and honestly, you will probably get bored. This breakdown is strictly for the tech brains—the builders who actually understand backend architecture and are tired of stateless, forgetful AI systems.*

---

Let me paint a picture that every single AI developer has experienced at least once in the last year. 

You build a shiny new multi-agent system. You spend three days tweaking the system prompts until you’re blue in the face. You tell Agent A to "be extremely strict," and you tell Agent B to "focus entirely on soft skills." You run a test, and it works flawlessly! The agents debate, they reason, they output a beautiful JSON response. You feel like a genius.

Then you deploy it. 

And immediately, you realize something horrifying: Your highly intelligent, carefully orchestrated agents are essentially goldfishes. They are glorified keyword matchers with severe amnesia. They read a prompt, output a result, and completely forget that interaction by the time they evaluate the next task. 

If they make a hilariously bad call on candidate #1, they’ll make the exact same bad call on candidate #50. They don't learn. They don't calibrate. They don't have a baseline. 

I got tired of stateless agents making the same mistakes over and over. So, I decided to completely rebuild our AI hiring pipeline. I wanted to build a multi-agent debate system where the agents actually *remember* past candidates and use that context to calibrate their current decisions. Oh, and I also had to figure out how to stop the LLM API costs from blowing up my wallet in the process, because passing 70B-parameter context windows back and forth gets aggressively expensive.

Here’s exactly how I did it using Hindsight for biomimetic memory and cascadeflow for budget-enforced runtime routing.

## The Setup: A High-Stakes Debate (Tech Lead vs HR)

First, some context on the system itself. I didn't want a single monolithic LLM trying to judge a resume from every possible angle, because that always results in a watered-down, average response. 

Instead, the core of the system is a debate. When a resume comes in, a fast extraction agent pulls the facts—years of experience, programming languages, past job titles, etc. Then, two highly specialized agents take over: a Senior Tech Lead and an HR Business Partner. 

These two do not like each other. 

The Tech Lead cares about architecture, real-world experience, and GitHub commits. It will absolutely shred a candidate who claims to know Kubernetes but has no actual production experience. The HR agent, on the other hand, cares about tenure, soft skills, and culture fit. It will defend a candidate who might have weaker technical chops but shows incredible loyalty and leadership potential. 

They review the candidate and argue their case. 

Without memory, they evaluate every single candidate in a complete vacuum. A "7/10" score from the Tech Lead on Monday means absolutely nothing on Tuesday, because the agent has no memory of what a "7" actually looks like. 

With [Hindsight agent memory](https://vectorize.io/what-is-agent-memory) embedded natively in the backend, they pull in context from past evaluations before making a decision.

## Giving Agents a Biomimetic Memory (Without the Headache)

Historically, if you wanted to give an agent memory, you had to spin up Pinecone or Qdrant, write a bunch of boilerplate RAG code, chunk the text, embed it, and query it. I didn’t want to manage a separate, clunky vector database just to give these agents some context. That's overkill for what should be a native feature.

Instead, I used the embedded version of Hindsight straight in my FastAPI backend. It runs a local PostgreSQL instance under the hood, meaning I get all the benefits of long-term memory without managing cloud infrastructure.

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

Notice how clean that is. I just hand it my Groq API key and tell it what model to use. 

But the real magic happens during the evaluation phase. Before the Tech Lead writes its scathing review of a candidate's messy GitHub repository, it runs a quick `recall` query to see if it has reviewed a similar candidate recently.

```python
# Tech Lead recalls past decisions to establish a baseline
memory_query = f"Candidate with GitHub score {github_score} and Resume score {resume_score}"
past_context = hs_client.recall(memory_query)

if past_context:
    prompt += f"\n\nPAST MEMORY CONTEXT:\n{past_context}\nUse this context to calibrate your strictness."
```

This changes absolutely everything about how the agent behaves. Instead of relying purely on a rigid system prompt telling it to be "strict," the agent actually looks at its own historical decisions. 

During testing, I watched the Tech Lead reject a candidate and explicitly cite its own past experience: *"Similar to a candidate we saw last week who had a high resume score but weak GitHub presence, this person lacks proven production code. I'm passing."* 

It wasn't just following rules anymore; it was establishing a precedent. 

Once the debate finishes, the agents use a single line of code, `hs_client.retain()`, to save their final decision to memory, so they learn for the next time. If you want to see how crazy simple the API is, you can check out the [Hindsight docs](https://hindsight.vectorize.io/) or the [Hindsight GitHub](https://github.com/vectorize-io/hindsight).

## Stopping the Bleeding with cascadeflow

So the memory was working beautifully. The agents were learning, adapting, and making incredibly nuanced decisions based on past candidates. 

There was just one massive problem: I was burning through tokens like a billionaire on a yacht. 

Running a multi-agent debate with Llama-3.3-70B for every single resume gets expensive extremely fast. Every time a candidate was processed, I was passing massive context windows back and forth. I watched my API dashboard light up in real-time, and I realized I had to optimize this before I went broke.

But I couldn't just downgrade the debate logic to an 8B model. I tried it, and the reasoning quality drops off a cliff. The 8B model couldn't hold the nuance of a multi-turn debate; it just kept agreeing with whatever the HR agent said.

I realized I only needed the 70B model for the deep reasoning part. The initial resume parsing? Extracting years of experience from a PDF? A smaller model can do that in its sleep. 

I needed a way to dynamically route requests based on task complexity. Enter [cascadeflow](https://github.com/lemony-ai/cascadeflow). 

Instead of hardcoding which model to use, I wrapped the LLM calls in cascadeflow. It intercepts the calls and intelligently routes them at runtime based on the budget and task requirements I set.

```python
from cascadeflow import CascadeAgent

# Create a budget-aware routing agent
extractor = CascadeAgent(
    primary_model="llama-3.3-70b-versatile",
    fallback_model="llama-3.1-8b-instant"
)

# cascadeflow automatically routes this simple extraction task to the cheaper 8B model
parsed_data = extractor.run("Extract skills, tenure, and previous titles from this resume text.")
```

By adding cascadeflow, I effectively created a quality gate. All the basic extraction and summarization stuff gets routed to `llama-3.1-8b-instant` for pennies. We save our token budget exclusively for the heavy lifting in the debate phase, where the 70B model is actually required to process the Hindsight memories and formulate arguments.

The result? It literally dropped our overall token costs by 75%, while keeping the exact same level of reasoning quality for the final hiring decision. You can actually see the "Cost Saved" printed directly in the terminal logs while the server runs. (You can read more about how the routing logic works in the [cascadeflow docs](https://docs.cascadeflow.ai/)).

## The Absolute Biggest Takeaways

Building this was a massive learning experience in how fragile modern AI systems really are, and what it takes to make them robust. If you are building multi-agent systems, here are the three biggest things you need to know:

### 1. Memory beats prompt engineering every single time. 
You can spend 40 hours tweaking a system prompt to handle edge cases, and the agent will still fail. Telling an agent to "be strict" works for one turn. Showing an agent its past decisions forces authentic behavior change. Biomimetic memory allows the system to calibrate itself naturally over time. 

### 2. You don't need 70B for everything. 
If you are passing every single task through your largest model, you are burning money for absolutely no reason. Routing simple tasks to smaller models is mandatory if you want to scale multi-agent systems without going broke. Put an intelligent router in front of your LLM calls and watch your bill drop overnight.

### 3. Stateful agents are the future.
Stateless agents are great for basic chatbots. But for complex, decision-making systems? They are broken by design. Once you see an agent reference a past interaction to make a better, more nuanced decision today, stateless agents feel completely obsolete. The future of AI is stateful.

If you want to poke around the architecture, steal the routing logic, or clone the repo, I open-sourced the whole thing on my GitHub. Let me know if you guys are messing around with agent memory too in the comments—I’d love to see how you're handling statefulness!
