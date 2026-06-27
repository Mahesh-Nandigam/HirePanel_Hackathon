**Quick Intro (30 sec)**
"Hey everyone, I'm Mahesh Babu, and I built HirePanel.ai, an AI hiring committee that uses multiple agents to evaluate engineering candidates. Most AI agents today suffer from amnesia—they evaluate every task in a vacuum. I wanted to build an agent team that actually remembers past candidates and gets smarter over time."

**The Problem (30 sec)**
"Without memory or intelligence, multi-agent systems have two massive problems. First, they make the same mistakes repeatedly because they don't learn from past evaluations. Second, if you run a 70B parameter model for every single extraction task across five different agents, your API bill is going to explode. The agents run completely uncontrolled."

**Live Demo (2 min)**
"Let me show you how we fixed this. 
[Screen: Show the terminal and the HirePanel UI]
Here, I am uploading a resume to our FastAPI backend. Behind the scenes, we have a Tech Lead agent and an HR agent debating this candidate.

[Screen: Show the source code for TechLeadAgent]
Instead of just prompting the Tech Lead, we embedded a Hindsight memory bank directly into the agent. Before it evaluates, it recalls similar past candidates. 

[Screen: Show the UI results for the candidate]
Look at this output. The Tech Lead says, 'Similar to our last candidate with a high resume score but weak GitHub presence...' It actually calibrated its decision based on past interactions!

[Screen: Show the terminal logs where cascadeflow prints out Cost Saved]
And to keep costs down, look at the terminal. We wrapped all our model calls in cascadeflow. It automatically routed the simple resume parsing tasks to a cheap 8B model, and only escalated to the 70B model for the complex debate reasoning. You can see right here that cascadeflow saved us 75% on this single run."

**Wrap Up (30 sec)**
"The biggest takeaway for me was that memory beats prompt engineering. Showing an agent its past decisions via Hindsight forces a much more authentic behavior change than just telling it to be strict in a system prompt. Thanks for watching, and feel free to check out the repo!"
