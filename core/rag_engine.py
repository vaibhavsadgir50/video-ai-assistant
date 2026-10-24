import os
from langchain_core import retrievers
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openrouter import ChatOpenRouter
from core import vector_store
from core.vector_store import build_vector_store, load_vector_store, get_retriver


def get_llm():
    rate_limiter = InMemoryRateLimiter(requests_per_second=0.2, max_bucket_size=1)
    return ChatOpenRouter(
        model="openrouter/free",
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.3,
        max_retries=6,
        rate_limiter=rate_limiter,
    )


def format_doc(docs):
    return "\n\n".join([doc.page_content for doc in docs])


def build_rag_chain(transcript: str):
    vector_store = build_vector_store(transcript)
    retriever = get_retriver(vector_store, k=4)
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert meeting assistant. Answer the user's question based ONLY on the meeting transcript context provided below. 
                If the answer is not found in the context, say: "I could not find this information in the meeting transcript." 
                Always be concise and precise. If quoting someone, mention it clearly. Context from meeting transcript:
                {context}""",
            ),
            ("human", "{question}"),
        ]
    )
    #full LCEL pipeline 
    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_doc),
            "question": RunnablePassthrough() 
        }
        | prompt  | llm | StrOutputParser()
    )
    return rag_chain



def load_rag_chain():
    vector_store = load_vector_store()
    retriver = get_retriver(vector_store)

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert meeting assistant. Answer the user's question based ONLY on the meeting transcript context provided below. 
                If the answer is not found in the context, say:  "I could not find this information in the meeting transcript." 
                Always be concise and precise. If quoting someone, mention it clearly. Context from meeting transcript: 
                {context}""",
            ),
            ("human", "{question}"),
        ]
    )

    rag_chain = (
        {
            "context":  retriver| RunnableLambda(format_doc),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_question(rag_chain, question:str)->str:
    print(f"question: {question}")
    answer=rag_chain.invoke(question)

    print(f"answer: {answer}")
    return answer