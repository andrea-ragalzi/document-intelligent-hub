"""
Demo: Sources in Answer - Automatic Inclusion of PDF Names

This demonstrates the new feature where source document names (PDF files)
are automatically appended to the answer text in the user's language.

BEFORE (old behavior):
----------------------
Answer: "Python is a high-level programming language..."
Sources (separate field): ["python_guide.pdf", "tutorial.pdf"]

AFTER (new behavior):
---------------------
Answer: "Python is a high-level programming language...

📚 Fonti:
- python_guide.pdf
- tutorial.pdf"

Sources (still in separate field): ["python_guide.pdf", "tutorial.pdf"]

KEY FEATURES:
-------------
1. Sources automatically appended to answer text
2. Language-aware label ("Fonti" in Italian, "Sources" in English, etc.)
3. Clean bullet-point formatting
4. Sources still available in separate field for UI flexibility
5. Works with all supported languages

SUPPORTED LANGUAGES:
--------------------
IT: Fonti
EN: Sources
FR: Sources
DE: Quellen
ES: Fuentes
PT: Fontes
NL: Bronnen
RU: Источники
ZH: 来源
JA: 情報源
KO: 출처
AR: المصادر
PL: Źródła
TR: Kaynaklar
SV: Källor
NO: Kilder
DA: Kilder
FI: Lähteet
CS: Zdroje
HU: Források
RO: Surse

EXAMPLE RESPONSES:
------------------

ITALIAN QUERY:
Query: "Cos'è Python?"
Response: "Python è un linguaggio di programmazione ad alto livello...

📚 Fonti:
- python_guida.pdf
- manuale_python.pdf"

ENGLISH QUERY:
Query: "What is Python?"
Response: "Python is a high-level programming language...

📚 Sources:
- python_guide.pdf
- python_manual.pdf"

FRENCH QUERY:
Query: "Qu'est-ce que Python?"
Response: "Python est un langage de programmation de haut niveau...

📚 Sources:
- guide_python.pdf
- manuel_python.pdf"

IMPLEMENTATION DETAILS:
-----------------------
Location: backend/app/services/rag_service.py

Step 1: Extract source documents from context
```python
source_documents = sorted(list(set(
    doc.metadata.get("original_filename", "Unknown") 
    for doc in context_docs
)))
```

Step 2: Get translated "Sources" label
```python
sources_label = self._get_sources_label(target_response_language)
```

Step 3: Format and append to answer
```python
if source_documents:
    sources_list = "\\n".join([f"- {doc}" for doc in source_documents])
    final_answer = f"{final_answer}\\n\\n📚 {sources_label}:\\n{sources_list}"
```

BENEFITS:
---------
1. **Better UX**: Sources immediately visible in chat without scrolling
2. **Transparency**: Users know which documents were used
3. **Citation**: Easy to reference specific sources
4. **Multilingual**: Automatically adapts to user's language
5. **Backward Compatible**: Still returns sources in separate field

FRONTEND COMPATIBILITY:
-----------------------
The frontend already displays sources separately in a collapsible section.
Now sources appear BOTH:
1. In the answer text (new)
2. In the separate sources section (existing)

This gives maximum flexibility for different UI designs.

API EXAMPLE:
------------
POST /rag/query/
{
  "query": "Quali sono i requisiti?",
  "user_id": "user-123",
  "output_language": "IT"
}

Response:
{
  "answer": "I requisiti principali sono...\\n\\n📚 Fonti:\\n- requirements.pdf\\n- specs.pdf",
  "source_documents": ["requirements.pdf", "specs.pdf"]
}

The answer text now includes the formatted sources list!
"""

print(__doc__)

# Simulate the formatting behavior
def format_answer_with_sources(answer: str, sources: list, language: str) -> str:
    """Simulate the backend's source formatting"""
    sources_labels = {
        "IT": "Fonti",
        "EN": "Sources",
        "FR": "Sources",
        "DE": "Quellen",
        "ES": "Fuentes",
    }
    
    if sources:
        label = sources_labels.get(language, "Sources")
        sources_list = "\n".join([f"- {doc}" for doc in sources])
        return f"{answer}\n\n📚 {label}:\n{sources_list}"
    return answer

# Example 1: Italian
print("="*80)
print("EXAMPLE 1: Italian Query")
print("="*80)
answer_it = "Python è un linguaggio di programmazione interpretato, ad alto livello."
sources_it = ["python_guida.pdf", "tutorial_python.pdf"]
formatted_it = format_answer_with_sources(answer_it, sources_it, "IT")
print(formatted_it)
print()

# Example 2: English
print("="*80)
print("EXAMPLE 2: English Query")
print("="*80)
answer_en = "Python is a high-level, interpreted programming language."
sources_en = ["python_guide.pdf", "python_tutorial.pdf"]
formatted_en = format_answer_with_sources(answer_en, sources_en, "EN")
print(formatted_en)
print()

# Example 3: Multiple sources
print("="*80)
print("EXAMPLE 3: Multiple Sources")
print("="*80)
answer_multi = "The system requirements include 8GB RAM and 100GB storage."
sources_multi = ["requirements.pdf", "specs.pdf", "hardware_guide.pdf", "installation.pdf"]
formatted_multi = format_answer_with_sources(answer_multi, sources_multi, "EN")
print(formatted_multi)
print()

print("="*80)
print("✅ Feature Implementation Complete!")
print("="*80)
print("\nSources are now automatically included in all RAG responses.")
print("The format adapts to the user's language automatically.")
