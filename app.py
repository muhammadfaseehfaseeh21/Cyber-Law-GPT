import os
import base64
import tempfile
from pathlib import Path

import faiss
import fitz  # PyMuPDF
import numpy as np
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer


# ============================================================
# CYBER LAW GPT
# ============================================================

APP_NAME = "Cyber Law GPT"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

DEFAULT_GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

# ============================================================
# PECA PDF
# ============================================================
# Keep the PECA PDF embedded here as in the previous app.py.
# Replace the value below with the PECA PDF base64 content
# from your existing app.py.

PECA_PDF_B64 = """YOUR_EXISTING_PECA_BASE64_CONTENT"""


# ============================================================
# GROQ API KEY
# ============================================================

def get_api_key():
    """Get Groq API key from Streamlit Secrets or environment."""

    try:
        key = st.secrets.get("GROQ_API_KEY")

        if key:
            return key

    except Exception:
        pass

    return os.getenv("GROQ_API_KEY")


# ============================================================
# RECREATE PECA PDF
# ============================================================

def write_embedded_pdf():

    temp_dir = Path(tempfile.gettempdir()) / "cyber_law_gpt"

    temp_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    pdf_path = temp_dir / "PECA.pdf"

    if not pdf_path.exists():

        pdf_path.write_bytes(
            base64.b64decode(PECA_PDF_B64)
        )

    return pdf_path


# ============================================================
# EXTRACT PDF AND CREATE CHUNKS
# ============================================================

def extract_pdf_chunks(
    pdf_path,
    chunk_size=1200,
    overlap=200
):

    document = fitz.open(pdf_path)

    chunks = []

    for page_number, page in enumerate(
        document,
        start=1
    ):

        text = page.get_text("text")

        text = text.replace(
            "\x00",
            " "
        ).strip()

        if not text:
            continue

        # Remove unnecessary whitespace
        text = " ".join(text.split())

        start = 0

        while start < len(text):

            end = min(
                start + chunk_size,
                len(text)
            )

            chunk_text = text[start:end].strip()

            if chunk_text:

                chunks.append(
                    {
                        "text": chunk_text,
                        "page": page_number,
                        "source": "PECA.pdf"
                    }
                )

            if end >= len(text):
                break

            start = max(
                end - overlap,
                start + 1
            )

    document.close()

    return chunks


# ============================================================
# BUILD FAISS INDEX
# ============================================================

@st.cache_resource(
    show_spinner="Creating Cyber Law knowledge base..."
)
def build_index():

    pdf_path = write_embedded_pdf()

    chunks = extract_pdf_chunks(
        pdf_path
    )

    if not chunks:

        raise RuntimeError(
            "No readable text was found in the PECA PDF."
        )

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    texts = [
        item["text"]
        for item in chunks
    ]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    ).astype("float32")

    index = faiss.IndexFlatIP(
        embeddings.shape[1]
    )

    index.add(embeddings)

    return (
        model,
        index,
        chunks
    )


# ============================================================
# RETRIEVE RELEVANT PECA CONTENT
# ============================================================

def retrieve(
    query,
    model,
    index,
    chunks,
    top_k=5
):

    query_vector = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    ).astype("float32")

    scores, indices = index.search(
        query_vector,
        min(top_k, len(chunks))
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx < 0:
            continue

        item = dict(
            chunks[int(idx)]
        )

        item["score"] = float(score)

        results.append(item)

    return results


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(results):

    parts = []

    for number, item in enumerate(
        results,
        start=1
    ):

        parts.append(
            f"""
[SOURCE {number}
PECA.pdf
Page {item['page']}]

{item['text']}
"""
        )

    return "\n\n".join(parts)


# ============================================================
# GENERATE ANSWER USING GROQ
# ============================================================

def generate_answer(
    question,
    context,
    technicality,
    response_size,
    language
):

    api_key = get_api_key()

    if not api_key:

        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add it to Streamlit Secrets."
        )

    client = Groq(
        api_key=api_key
    )

    technicality_instructions = {

        "Beginner":
        "Use simple language and explain difficult legal terms.",

        "Intermediate":
        "Use clear legal language with enough explanation.",

        "Advanced":
        "Use precise legal terminology and identify applicable sections and conditions."
    }

    size_instructions = {

        "Short":
        "Give a concise answer.",

        "Medium":
        "Give a balanced answer with the relevant section and explanation.",

        "Detailed":
        "Give a detailed answer with relevant sections, conditions, consequences, and information supported by the source."
    }

    system_prompt = f"""
You are Cyber Law GPT.

You are a retrieval-augmented legal information assistant.

Your primary source is the supplied Prevention of Electronic Crimes Act,
2016 (PECA) PDF.

IMPORTANT RULES:

1. Answer using the retrieved PECA passages.

2. Mention the relevant PECA section whenever supported.

3. Do not invent sections, punishments, procedures, definitions,
   authorities, or legal conclusions.

4. If the retrieved document does not contain enough information,
   clearly say so.

5. Do not use outside laws to fill missing information.

6. Explain the law in the selected language.

7. Include the relevant page/source reference when possible.

8. Keep the answer informational and document-grounded.

Technicality:
{technicality}

{technicality_instructions[technicality]}

Response size:
{response_size}

{size_instructions[response_size]}

Language:
{language}

This application provides legal information from the supplied document.
It is not a substitute for advice from a qualified lawyer.
"""

    user_prompt = f"""
QUESTION:

{question}


RETRIEVED PECA CONTENT:

{context}


Answer the question using the retrieved PECA content.
"""

    response = client.chat.completions.create(

        model=DEFAULT_GROQ_MODEL,

        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],

        temperature=0.1,

        max_tokens=1800
    )

    return response.choices[0].message.content


# ============================================================
# STREAMLIT PAGE
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="⚖️",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("⚖️ Cyber Law GPT")

st.caption(
    "AI-powered RAG assistant based on the supplied "
    "Prevention of Electronic Crimes Act, 2016 (PECA) document."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Answer Settings")

    technicality = st.selectbox(
        "Technicality Level",
        [
            "Beginner",
            "Intermediate",
            "Advanced"
        ]
    )

    response_size = st.selectbox(
        "Response Size",
        [
            "Short",
            "Medium",
            "Detailed"
        ],
        index=1
    )

    language = st.selectbox(
        "Answer Language",
        [
            "English",
            "Urdu",
            "Roman Urdu"
        ]
    )

    top_k = st.slider(
        "Source Passages",
        min_value=2,
        max_value=8,
        value=5
    )

    st.divider()

    # ========================================================
    # CYBER CRIME COMPLAINT SECTION
    # ========================================================

    st.subheader("🚨 Report a Cyber Crime")

    st.write(
        "If you want to submit a cyber-crime complaint, "
        "you can use the official NCCIA complaint portal:"
    )

    st.link_button(
        "🚨 Submit Cyber Crime Complaint",
        "https://complaint.nccia.gov.pk/",
        use_container_width=True
    )

    st.caption(
        "This link opens the NCCIA cyber-crime complaint portal."
    )

    st.divider()

    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    st.subheader("🤖 Model")

    st.write(
        f"Groq Model: `{DEFAULT_GROQ_MODEL}`"
    )

    st.write(
        f"Embedding Model: `{EMBEDDING_MODEL}`"
    )

    st.divider()

    st.info(
        "Answers are generated using the supplied PECA document "
        "and retrieved legal passages."
    )

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# CHAT MEMORY
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# STARTUP: CREATE KNOWLEDGE BASE
# ============================================================

try:

    embedding_model, faiss_index, chunks = build_index()

    st.success(
        f"Cyber Law knowledge base ready — "
        f"{len(chunks)} PECA passages indexed."
    )

except Exception as error:

    st.error(
        f"Startup error: {error}"
    )

    st.stop()


# ============================================================
# DISPLAY PREVIOUS MESSAGES
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# USER QUESTION
# ============================================================

question = st.chat_input(
    "Ask a question about Pakistani cyber law..."
)


if question:

    # Save user question

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):

        st.markdown(question)


    # ========================================================
    # AI RESPONSE
    # ========================================================

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching the PECA document..."
        ):

            results = retrieve(
                question,
                embedding_model,
                faiss_index,
                chunks,
                top_k
            )

            context = build_context(
                results
            )

            try:

                answer = generate_answer(
                    question,
                    context,
                    technicality,
                    response_size,
                    language
                )

            except Exception as error:

                answer = (
                    f"Unable to generate answer: {error}"
                )

        st.markdown(answer)


        # ====================================================
        # SHOW SOURCES
        # ====================================================

        with st.expander(
            "📚 Retrieved PECA Sources"
        ):

            for number, item in enumerate(
                results,
                start=1
            ):

                st.markdown(
                    f"**Source {number} — "
                    f"PECA.pdf — Page {item['page']}**"
                )

                st.write(
                    item["text"]
                )

                st.divider()


        st.caption(
            "Legal-information notice: "
            "Cyber Law GPT provides document-grounded information "
            "and is not a substitute for professional legal advice."
        )


    # Save AI answer

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )
    st.subheader("🚨 Report a Cyber Crime")

st.write(
    "If you want to submit a cyber-crime complaint, "
    "you can use the official NCCIA complaint portal:"
)

st.link_button(
    "🚨 Submit Cyber Crime Complaint",
    "https://complaint.nccia.gov.pk/",
    use_container_width=True
)
