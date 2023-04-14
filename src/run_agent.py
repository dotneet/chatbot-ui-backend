import asyncio
import io

from dotenv import load_dotenv

from agent import TextModelAgent

load_dotenv()


async def main():
    question = "東京の人口は？"
    stream = io.StringIO()
    result = TextModelAgent(stream=stream).run(question)
    print("RESULT:")
    print(result)

asyncio.run(main())
