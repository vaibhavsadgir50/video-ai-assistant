import os

from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.summarize import summarize,generate_title
from core.extractor import splits
from core.transcriber import transcribe_all
from core.vector_store import build_vector_store, load_vector_store, get_retriver
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

def run_pipeline(source:str, language:str = "english") -> dict:
    print("Start AI Meeting Assistant")

    chunks= process_input(source)
    transcript = transcribe_all(chunks,language)
    print(f"raw transcription (first 300 characters ) {transcript[:300]}")

    title = generate_title(transcript)
    summary = summarize(transcript)
    analysis = splits(transcript)
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "analysis": analysis,
        "rag_chain": rag_chain,
    }
    

if __name__ == "__main__":
    # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"📌 Title: {result['title']}")
    print(f"\n📋 Summary:\n{result['summary']}")
    print(f"\n✅ Analysis:\n{result['analysis']}")
    print("=" * 60)

    # Phase 2 — Chat with your meeting via RAG
    print("\n💬 Chat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question)
        print(f"\n🤖 Assistant: {answer}\n")