# Document Intelligence for Contract Risk Analysis

An evidence-grounded contract risk analysis system that uses Deep Learning, NLP, semantic validation, and Generative AI to identify and explain potentially important clauses in contracts.

## Overview

Long contracts can contain hundreds of pages and many legally important clauses.

This project builds a multi-stage pipeline that:

- Extracts text from PDF contracts
- Detects contract sections
- Classifies sections into 33 clause categories using RoBERTa
- Validates predictions using semantic similarity
- Validates clause evidence against the contract text
- Applies strict evidence validation
- Generates grounded risk analysis using Llama 3.2 3B
- Produces a structured PDF risk report

The system is designed to be conservative: a model prediction does not automatically become a final finding. Evidence must pass multiple validation stages first.

---

## Architecture

```text
                    Contract PDF
                         │
                         ▼
                PDF Text Extraction
                         │
                         ▼
              Contract Section Detection
                         │
                         ▼
             RoBERTa Clause Classification
                         │
                         ▼
              Semantic Validation
                  (MiniLM)
                         │
                         ▼
               Evidence Validation
                         │
                         ▼
             Strict Clause Validation
                         │
                         ▼
             Verified Contract Evidence
                         │
                         ▼
               Llama 3.2 3B / Ollama
                         │
                         ▼
                Risk Analysis
                         │
                         ▼
             Contract Risk Report PDF
