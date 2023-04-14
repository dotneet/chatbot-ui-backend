import io
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Union

from langchain import OpenAI, Wikipedia
# pyright: reportUnknownVariableType=false
from langchain.agents import AgentExecutor, AgentType, Tool, initialize_agent
from langchain.agents.react.base import DocstoreExplorer
from langchain.callbacks import CallbackManager
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import AgentAction, AgentFinish, LLMResult


def create_tools(callback_manager: CallbackManager) -> List[Tool]:
    docstore = DocstoreExplorer(Wikipedia())
    return [
        Tool(
            name="Search",
            func=docstore.search,
            description="useful for when you need to ask with search",
            callback_manager=callback_manager
        ),
        Tool(
            name="Lookup",
            func=docstore.lookup,
            description="useful for when you need to ask with lookup",
            callback_manager=callback_manager
        )
    ]


class AgentBase():
    output_queue: queue.Queue[Optional[str]]

    def __init__(self) -> None:
        self.output_queue = queue.Queue()

    def finish(self):
        self.output_queue.put(None)

    def output_generator(self):
        while True:
            item = self.output_queue.get()
            if item is None:
                break
            yield item


class ChatModelAgent(AgentBase):
    agent: AgentExecutor

    def __init__(self, stream: Optional[io.StringIO] = None):
        super().__init__()
        self.agent = self._create_agent(stream=stream)

    def _create_agent(self, stream: Optional[io.StringIO] = None) -> AgentExecutor:
        handler = AgentCallbackHandler(
            agent=self, stream=stream, verbose=True)
        callback_manager = CallbackManager(handlers=[handler])
        tools = create_tools(callback_manager)
        llm = ChatOpenAI(client=None, temperature=0, model_name="gpt-3.5-turbo",
                         callback_manager=callback_manager)
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True)

        return initialize_agent(tools, llm, agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                                verbose=True, callback_manager=callback_manager, memory=memory)

    def run(self, query: str) -> str:
        return self.agent.run(query)


class TextModelAgent(AgentBase):
    agent: AgentExecutor

    def __init__(self, stream: Optional[io.StringIO] = None):
        super().__init__()
        self.agent = self._create_agent(stream=stream)

    def _create_agent(self, stream: Optional[io.StringIO] = None) -> AgentExecutor:
        callback_manager = CallbackManager(handlers=[])
        handler = AgentCallbackHandler(
            agent=self, stream=stream, verbose=True)
        callback_manager.add_handler(handler)
        tools = create_tools(callback_manager)
        llm = OpenAI(client=None, temperature=0, model_name="text-davinci-003",
                     callback_manager=callback_manager, verbose=True)
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True)
        return initialize_agent(tools, llm, agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                                callback_manager=callback_manager, memory=memory, verbose=True)

    def run(self, query: str) -> str:
        return self.agent.run(query)


class AgentCallbackHandler(BaseCallbackHandler):
    verbose = True
    agent: AgentBase
    stream: Optional[io.StringIO] = None

    def __init__(self, agent: AgentBase, stream: Optional[io.StringIO] = None, verbose: bool = True) -> None:
        super().__init__()
        self.agent = agent
        self.stream = stream
        self.verbose = verbose

    @property
    def always_verbose(self) -> bool:
        return self.verbose

    def on_text(self, text: str, **kwargs: Any) -> Any:
        print(text)
        pass

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        pass

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        pass

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        self.agent.finish()
        pass

    def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        pass

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        pass

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        pass

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        print(serialized)
        if self.stream is not None:
            self.stream.write(f"{serialized['name']}を実行中...\n\n")
        pass

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        pass

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        self.agent.finish()
        pass

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> Any:
        print(serialized)
        pass

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        pass

    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        self.agent.finish()
        pass


def _read_stream(stream: io.StringIO, q: queue.Queue[Optional[str]]):
    while True:
        stream.seek(0)
        lines = stream.getvalue()
        time.sleep(0.1)
        if stream.closed:
            break
        elif lines:
            print(lines)
            q.put(lines)
            stream.seek(0)
            stream.truncate()


def _run_agent(agent: AgentExecutor, query: str, q: queue.Queue[Optional[str]]):
    result = agent.run(query)
    q.put(result)
    q.put(None)


async def query(query_str: str):
    stream = io.StringIO()
    agent: TextModelAgent = TextModelAgent(stream=stream)
    read_thread = threading.Thread(target=_read_stream, args=[
                                   stream, agent.output_queue])
    read_thread.start()
    agent_thread = threading.Thread(
        target=_run_agent, args=[agent, query_str, agent.output_queue])
    agent_thread.start()
    for message in agent.output_generator():
        yield message
    agent_thread.join()
