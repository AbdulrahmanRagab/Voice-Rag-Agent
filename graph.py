import os
from typing import List, Annotated, Sequence
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages 

# Load environment variables
load_dotenv(".env.local")

# Verify API Key
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")

def create_workflow():
    # 1. Initialize LLM and Embeddings
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 2. Load and Process PDF
    pdf_path = os.getenv("PDF_PATH", "./Abdulrahman Ragab AI Engineer CV.pdf")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}. Please check the path.")

    print(f"Loading PDF from: {pdf_path}")
    pages = PyPDFLoader(pdf_path).load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=350, chunk_overlap=150)
    pages_split = text_splitter.split_documents(pages)

    # 3. Create Vector Store
    vectorstore = Chroma.from_documents(
        documents=pages_split,
        embedding=embeddings,
        collection_name="rag_collection"
    )

    retriever = vectorstore.as_retriever(
        search_type='mmr', 
        search_kwargs={'k': 3, 'lambda_mult': 0.5}
    )

    # 4. Define State
    # CHANGED: We now use 'messages' to be compatible with LiveKit Adapter
    class RAGState(BaseModel):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        retrieved_docs: List[Document] = []

    # 5. Define Graph Nodes
    def retrieve_docs(state: RAGState) -> dict:
        """Retrieves documents based on the LAST message (the user's question)."""
        
        # Extract the user's latest query from the messages list
        last_message = state.messages[-1]
        question = last_message.content
        
        print(f"Retrieving docs for: {question}")
        docs = retriever.invoke(question)
        return {"retrieved_docs": docs}

    def generate_answer(state: RAGState) -> dict:
        """Generates an answer using the retrieved documents."""
        
        # Get the question again
        question = state.messages[-1].content
        
        # Combine context
        context = "\n\n".join([doc.page_content for doc in state.retrieved_docs])
        
        prompt = (
            f"You are a helpful assistant. Answer the user's question based strictly on the context below.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}"
        )
        
        response = llm.invoke(prompt)
        
        # CHANGED: Return a 'messages' update, not just a string
        return {"messages": [response]}

    # 6. Build the Graph
    builder = StateGraph(RAGState)

    builder.add_node("retriever", retrieve_docs)
    builder.add_node("responder", generate_answer)

    builder.set_entry_point("retriever")
    
    builder.add_edge("retriever", "responder")
    builder.add_edge("responder", END)

    return builder.compile()
