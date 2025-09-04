# Script Overview: NER Extraction & TEI XML Generation

## Purpose
Extracts named entities (names, dates, times, places) from text using LLM-powered NER and generates structured TEI XML output.

## Technology Stack
- **LLM**: Groq API (via `groq` client)
- **Structured Output**: Pydantic models for entity validation
- **XML Processing**: ElementTree for TEI XML generation
- **Entity Matching**: Fuzzy matching against prosopography and places indexes
- **Input**: French historical texts
- **Output**: JSON results + TEI XML with annotated entities

## Core Functionality
- Named Entity Recognition via LLM
- Entity matching against prosopography (Prosopographie.xml) and places (Lieux.xml)
- Automatic TEI XML markup generation