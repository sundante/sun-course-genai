"""The shop agent with CrewAI: one Agent with a role, one Task, a Crew to run it. CrewAI has no
built-in pause-and-resume for a single tool call, so the approval gate is the approve callback
inside the tool (common.make_tools).

    pip install -r requirements-crewai.txt
    python agent_crewai.py --no-thinking
"""

from crewai import LLM, Agent, Crew, Task
from crewai.tools import tool

import common

args = common.parse_args(__doc__)
llm = LLM(model=f"openai/{args.model}", base_url=args.base_url, api_key=args.api_key,
          temperature=1.0, **({"extra_body": common.extra_body(args)} if args.no_thinking else {}))


def approve(name, call_args):
    print(f"    approval requested: {name}({call_args}) -> approve")
    return True


def run_one(shop, instruction: str) -> str:
    tools = [tool(fn.__name__)(fn) for fn in common.make_tools(shop, approve=approve)]
    agent = Agent(role="Customer support agent", goal="Resolve the customer's request correctly",
                  backstory=common.INSTRUCTIONS, tools=tools, llm=llm, max_iter=20, verbose=False)
    task = Task(description=instruction, expected_output="The reply to send to the customer", agent=agent)
    return str(Crew(agents=[agent], tasks=[task], verbose=False).kickoff())


common.run_tasks("crewai", args, run_one)
