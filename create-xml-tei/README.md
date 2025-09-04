# LLM NER to XML TEI

1) extract NER (dates, times, palces, names) using LLM and structured output
2) match NER occurences against dictionnaries (Lieux.xml, Prosopographie.xml)
3) write XML TEI

# usage

1) fill `.env` with `GROQ_API_KEY` (you can use any openai compatible provider --> replace `self.client` in `ner_matcher.py`)
2)
```python
python main.py textes/demo  --places ./Indexes/Lieux.xml --prosopography ./Indexes/Prosopographie.xml
```
3) see XML TEI output at `demo.xml`
