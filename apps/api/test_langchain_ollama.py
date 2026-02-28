import asyncio
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama


class TestSchema(BaseModel):
    name: str = Field(description="Name")
    age: int = Field(description="Age")


async def main():
    llm = ChatOllama(model="llama3.2:3b", format="json")  # Using light model
    structured_llm = llm.with_structured_output(TestSchema)
    res = await structured_llm.ainvoke("Generate a persona for a random wizard in DND.")
    print(res)


if __name__ == "__main__":
    asyncio.run(main())
