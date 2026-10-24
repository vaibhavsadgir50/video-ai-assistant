
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openrouter import ChatOpenRouter
from core.summarize import split_transcript
import os

def get_llm():
    rate_limiter=InMemoryRateLimiter(requests_per_second=0.2, max_bucket_size=1)
    return ChatOpenRouter(model= "openrouter/free", openrouter_api_key = os.getenv("OPENROUTER_API_KEY"), temperature=0.3,max_retries=6,  rate_limiter = rate_limiter )

def build_chain(system_prompt:str):
    llm = get_llm()
    return (
        RunnablePassthrough ()| RunnableLambda(lambda x:{"text":x})| ChatPromptTemplate(
            [
                ("system", system_prompt),
                ("human", "{text}"), 
            ]) 
            | llm | StrOutputParser ()
    )

def extract_action_items(chunks: str)->str:
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.'"
    )

    actionable_items= [chain.invoke({"text":chunk}) for chunk in chunks]
    return actionable_items

def extract_key_decisions(chunks: str)->str:
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decisions found.'"
    )

    actionable_items= [chain.invoke({"text":chunk}) for chunk in chunks]
    return actionable_items

def extract_questions(chunks: str)->str:
    chain = build_chain(
        "From the meeting transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'"
    )

    actionable_items= [chain.invoke({"text":chunk}) for chunk in chunks]
    return actionable_items

ANALYZE_PROMPT = (
    "You are an expert meeting analyst. From the transcript, produce exactly these sections:\n"
    "## TITLE\n(max 8 words)\n"
    "## SUMMARY\n(bullet points)\n"
    "## ACTION ITEMS\n(extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.)"
    "## KEY DECISIONS\n(extract all key decisions made. Format as a numbered list. If none found say 'No key decisions found.)"
    "## OPEN QUESTIONS\n(From the meeting transcript, extract all unresolved questions or topics needing follow-up. Format as a numbered list. If none found say 'No open questions found.)"
)

def analyze(transcript: str) -> str:
    prompt = ChatPromptTemplate.from_messages([("system", ANALYZE_PROMPT), ("human", "{text}")])
    chain = prompt | get_llm() | StrOutputParser()
    return chain.invoke({"text": transcript})


def splits(transcript:str)->list:
    if len(transcript)>20000:
        chunks =split_transcript(transcript)
        return extract_action_items(chunks) ,extract_key_decisions(chunks), extract_questions(chunks)
    else:
        return analyze(transcript)