# Cyber-Law-GPT

Cyber Law GPT is a Retrieval-Augmented Generation (RAG) application for asking questions about the **supplied Prevention of Electronic Crimes Act, 2016 (PECA) PDF**.

The project intentionally contains **exactly three project files**:

- `app.py`
- `requirements.txt`
- `readme.md`

The supplied PECA PDF is embedded inside `app.py`, so you do **not** need to keep a fourth `PECA.pdf` file in your GitHub repository.

## What the app does

At startup, the app:

1. Recreates the supplied PECA PDF in a temporary folder.
2. Extracts the PDF text with PyMuPDF.
3. Splits the text into overlapping chunks.
4. Downloads/loads the SentenceTransformer embedding model.
5. Creates vector embeddings.
6. Stores the embeddings in a FAISS index.
7. Retrieves the most relevant PECA passages for each question.
8. Sends only those retrieved passages to Groq.
9. Generates an answer with section/page references.

This is designed to keep answers grounded in the supplied PECA document rather than allowing the model to freely invent legal information.

## UI options

The sidebar provides:

- **Technicality level**
  - Beginner
  - Intermediate
  - Advanced
- **Response size**
  - Short
  - Medium
  - Detailed
- **Answer language**
  - English
  - Urdu
  - Roman Urdu
- **Number of source passages**
  - 2 to 8
- Groq model display
- Embedding model display
- Clear chat button

## Important grounding behavior

Cyber Law GPT is instructed to:

- identify the relevant PECA section when supported;
- answer from retrieved PECA passages;
- avoid inventing sections or punishments;
- say when the supplied document does not contain enough information;
- avoid using outside law to fill missing information;
- show the retrieved source passages so the user can inspect the basis of an answer.

The supplied document is the legal source for this application. It is the **Prevention of Electronic Crimes Act, 2016**, and the PDF includes amendment text appearing in the supplied copy.

## API key

You need a Groq API key.

Do **not** put the API key directly into `app.py`.

The app looks for:

```text
GROQ_API_KEY
```

It first checks Streamlit Secrets and then the environment variable.

## Deploy on Streamlit Cloud

### 1. Create a GitHub repository

Create a new repository, for example:

```text
cyber-law-gpt
```

### 2. Upload exactly these three files

Upload:

```text
app.py
requirements.txt
readme.md
```

You do not need to upload `PECA.pdf` because its contents are embedded in `app.py`.

### 3. Create the Streamlit app

Open Streamlit Community Cloud and create a new app from your GitHub repository.

Select:

```text
Main file: app.py
```

### 4. Add the Groq secret

In the Streamlit app settings, open **Secrets** and add:

```toml
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
```

Save the secret and restart/redeploy the app.

### 5. First startup

On the first startup, Streamlit will download the SentenceTransformer embedding model and create the FAISS index.

The first startup can take longer than later reruns because the embedding model must be downloaded and the PDF must be indexed.

## Run in Google Colab

You can also run the same three-file project from Google Colab.

### 1. Upload the three files to Colab

Upload:

```text
app.py
requirements.txt
readme.md
```

### 2. Install dependencies

In a Colab cell run:

```python
!pip install -r requirements.txt
```

### 3. Add your Groq API key

For a simple temporary test:

```python
import os
os.environ["GROQ_API_KEY"] = "YOUR_GROQ_API_KEY"
```

For a real project, do not publish the key in notebooks or GitHub.

### 4. Start Streamlit

Run:

```python
!streamlit run app.py &>/content/streamlit.log &
```

Then use a suitable Colab tunneling method if you want to open the Streamlit interface externally.

## Suggested questions to test

Try questions such as:

```text
What is unauthorized access under PECA?
```

```text
What does Section 16 say about unauthorized use of identity information?
```

```text
What is the punishment for electronic fraud under Section 14?
```

```text
What does the Act say about cyber stalking?
```

```text
What does Section 32 say about retention of traffic data?
```

```text
What powers does an authorized officer have under Section 35?
```

```text
What does the Act say about cyberbullying?
```

The app should retrieve the relevant passages and show them under **Retrieved PECA sources**.

## Project architecture

```text
User Question
     |
     v
SentenceTransformer
     |
     v
FAISS Similarity Search
     |
     v
Relevant PECA Passages
     |
     v
Groq LLM
     |
     v
Grounded Answer + Sources
```

## Technology

- Python
- Streamlit
- FAISS
- SentenceTransformers
- PyMuPDF
- Groq API
- NumPy

## Cost

The application code uses open-source/local components for PDF extraction, embeddings, and vector search.

The LLM call uses Groq, so Groq account/model usage limits apply. Streamlit Cloud and Colab also have their own resource limits. The app itself does not require a paid database or paid vector database.

## Legal notice

Cyber Law GPT is a document-grounded information tool, not a lawyer, court, or official legal authority.

For a real legal matter, verify the applicable law and obtain advice from a qualified Pakistani legal professional. The application's answers should be treated as informational summaries of the supplied PECA document.

## Source document

The source PDF used to build this application is the supplied:

**THE PREVENTION OF ELECTRONIC CRIMES ACT, 2016**

The supplied document contains the Act and amendment text, including provisions such as Sections 3–28 on offences and punishments, Sections 29 onward on investigation and procedure, and later provisions concerning prosecution, preventive measures, and miscellaneous matters.
