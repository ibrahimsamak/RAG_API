from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer ONLY from the provided context. "
    "If the answer isn't in the context, say you don't know."
)


class RagService:
    """The RAG core: chunk -> embed -> upsert to the vector store, and on query
    embed -> similarity search -> stream a grounded LLM answer.

    The Chroma collection and the async LLM client are created once in the app
    lifespan and injected here per request (see app/api/deps.get_rag_service).
    """

    def __init__(self, collection, llm: AsyncOpenAI):
        self.collection = collection
        self.llm = llm

    async def embed(self, text: str) -> list[float]:
        resp = await self.llm.embeddings.create(model=EMBED_MODEL, input=text)
        return resp.data[0].embedding

    def chunk(self, text: str, size: int = 800, overlap: int = 100) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            chunks.append(text[start:start + size])
            start += size - overlap        # overlap preserves context across cuts
        return chunks

    async def ingest(self, doc_id: int, title: str, content: str) -> int:
        chunks = self.chunk(content)
        for i, chunk in enumerate(chunks):
            vector = await self.embed(chunk)
            self.collection.add(
                ids=[f"{doc_id}:{i}"],
                embeddings=[vector],
                documents=[chunk],
                metadatas=[{"doc_id": doc_id, "title": title, "chunk": i}],
            )
        return len(chunks)

    async def retrieve(self, query: str, k: int = 4) -> list[str]:
        qvec = await self.embed(query)
        res = self.collection.query(query_embeddings=[qvec], n_results=k)
        docs = res.get("documents") or []
        return docs[0] if docs else []

    async def answer_stream(self, query: str) -> AsyncGenerator[str, None]:
        context = "\n\n".join(await self.retrieve(query))
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ]
        stream = await self.llm.chat.completions.create(
            model=CHAT_MODEL, messages=messages, stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta        # yield each token as it arrives
