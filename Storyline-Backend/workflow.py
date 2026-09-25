from typing import Annotated
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from tools import tools
from Instructions import SYSTEM_PROMPT, EVALUATOR_PROMPT

load_dotenv(override=True)

DB_PATH = "memory.db"
MAX_RETRIES = 0

booker_agent = create_agent(
    model="google_genai:gemini-3.8-flash",
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)

evaluator_llm = init_chat_model("google_genai:gemini-3.8-flash")



class Evaluation(BaseModel):
    passed: bool = Field(description="True if the script meets quality standards")
    feedback: str = Field(description="Specific feedback to improve the script, empty if passed")


evaluator_structured = evaluator_llm.with_structured_output(Evaluation)


class State(TypedDict):
    messages: Annotated[list, add_messages]
    retries: int
    feedback: str


def agent_node(state: State) -> dict:
    messages = list(state["messages"])
    if state.get("feedback"):
        messages.append({
            "role": "user",
            "content": f"Revise your previous answer based on this feedback: {state['feedback']}",
        })
    result = booker_agent.invoke({"messages": messages})
    new_messages = result["messages"][len(messages):]
    return {"messages": new_messages}


def evaluator_node(state: State) -> dict:
    last_reply = state["messages"][-1].content
    prompt = EVALUATOR_PROMPT.format(script=last_reply)
    evaluation = evaluator_structured.invoke(prompt)
    print(f"[EVALUATOR] passed={evaluation.passed} | feedback={evaluation.feedback}")
    retries = state.get("retries", 0) + 1
    feedback = "" if evaluation.passed else evaluation.feedback
    return {"feedback": feedback, "retries": retries}

def route_after_evaluation(state: State) -> str:
    if not state.get("feedback"):
        return END
    if state.get("retries", 0) >= MAX_RETRIES:
        return END
    return "agent"


builder = StateGraph(State)
builder.add_node("agent", agent_node)
builder.add_node("evaluator", evaluator_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", "evaluator")
builder.add_conditional_edges("evaluator", route_after_evaluation, {"agent": "agent", END: END})

_sqlite_ctx = SqliteSaver.from_conn_string(DB_PATH)
checkpointer = _sqlite_ctx.__enter__()

graph = builder.compile(checkpointer=checkpointer)    
    
def run_agent(user_message: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(
        {"messages": [{"role": "user", "content": user_message}], "retries": 0, "feedback": ""},
        config=config,
    )
    return {
        "reply": result["messages"][-1].content,
        "thread_id": thread_id,
        "passed_review": not bool(result.get("feedback")),
        "reviewer_notes": result.get("feedback", ""),
    }