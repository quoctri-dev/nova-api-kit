# NoVa API Kit — CONTINUITY
> Last updated: 2026-03-28

## State
- Phase: Stage 1 PROTOTYPE (build-engine)
- Status: app.py written, supporting files done, chưa test live
- Stack: Streamlit + google-genai + anthropic + pydantic
- Python: 3.13 (match project-reporly)

## Blockers
- Chưa test live (cần chạy streamlit run trên máy anh)
- Chưa deploy Streamlit Cloud

## Key Decisions
- 2026-03-28: Manual adapter pattern thay LiteLLM (security alert v1.82.7-8 + demo rõ pattern hơn)
- 2026-03-28: Gemini primary (rẻ nhất, paid tier) + Claude fallback
- 2026-03-28: 3 use cases: Text Analyzer, Data Extractor, Content Generator
- 2026-03-28: Dark mode default (UX-REFERENCE v1)

## Open Questions
- Deploy Streamlit Cloud hay self-host?
- Thêm provider nào cho Stage 2? (OpenAI, Groq)
- Có cần sample data files cho demo?

## Next
- [ ] Test live trên máy anh (streamlit run app.py)
- [ ] Fix bugs nếu có
- [ ] Deploy Streamlit Cloud
- [ ] Thêm card vào novasentio.com
- [ ] Stage 2: tách modules, thêm providers, smoke_test.py
