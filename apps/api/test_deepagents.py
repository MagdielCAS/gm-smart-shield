import asyncio
from deepagents import create_deep_agent
from gm_shield.shared.llm.subagents import SUBAGENTS


async def main():
    agent = create_deep_agent(
        name="GmOrchestrator", model="ollama:llama3.2:3b", subagents=SUBAGENTS, tools=[]
    )
    res = await agent.ainvoke({"messages": [("user", "Hello!")]})
    print(res)


if __name__ == "__main__":
    asyncio.run(main())
