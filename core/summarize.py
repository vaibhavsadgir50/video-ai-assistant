
import os
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openrouter import ChatOpenRouter

_rate_limiter = InMemoryRateLimiter(requests_per_second=0.2, max_bucket_size=1)  # shared by every call

def get_llm():
    return ChatOpenRouter(
        model="openrouter/free",
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.3, max_retries=6, rate_limiter=_rate_limiter,
    )

def split_transcript(transcript: str, chunk_size: int = 20000) -> list:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=500
    ).split_text(transcript)

def summarize(transcript: str) -> str:
    llm = get_llm()
    chunks = split_transcript(transcript)

    map_chain = ChatPromptTemplate.from_messages([
        ("system", "Summarize this portion of a meeting transcript concisely."),
        ("human", "{text}"),
    ]) | llm | StrOutputParser()

    partials = [map_chain.invoke({"text": c}) for c in chunks]
    if len(partials) == 1:
        return partials[0]          # no combine step needed

    combine_chain = ChatPromptTemplate.from_messages([
        ("system", "You are an expert meeting summarizer. Combine these partial summaries "
                    "into one final professional meeting summary in bullet points."),
        ("human", "{text}"),
    ]) | llm | StrOutputParser()
    return combine_chain.invoke({"text": "\n\n".join(partials)})

def generate_title(transcript: str):
    transcript=transcript[:200]
    llm =get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Analyze this meeting transcript and give a 3-4 words title"), 
        ("human", "{text}")
        ]
    )
    chain= prompt | llm | StrOutputParser()
    
    return chain.invoke({"text":transcript})