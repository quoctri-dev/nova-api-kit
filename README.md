# NoVa API Kit — AI API Integration Toolkit

> Swap AI providers in 1 click. Auto-retry & fallback. Structured output.

## Cái này làm gì?

Tool demo AI API integration patterns: chọn provider (Gemini/Claude), chạy 3 use cases (phân tích text, trích xuất data, tạo content). Tự động retry + fallback khi lỗi.

## Chạy nhanh (3 bước)

```bash
# 1. Cài packages
pip install -r requirements.txt

# 2. Set API key (ít nhất 1)
cp .env.example .env
# Mở .env → paste API key

# 3. Chạy
streamlit run app.py
```

## Cấu hình (.env)

| Biến | Bắt buộc | Lấy ở đâu | Swap |
|------|----------|------------|------|
| `GOOGLE_AI_API_KEY` | 1 trong 2 | [Google AI Studio](https://aistudio.google.com/apikey) | Primary (rẻ nhất) |
| `ANTHROPIC_API_KEY` | 1 trong 2 | [Anthropic Console](https://console.anthropic.com/settings/keys) | Fallback |

Hoặc paste key trực tiếp trong sidebar app (không lưu, chỉ dùng trong session).

## Use Cases

1. **Text Analyzer** — paste text → AI trả: summary, sentiment, entities, topics (JSON)
2. **Data Extractor** — paste text + chọn schema → AI trích xuất structured JSON
3. **Content Generator** — nhập topic + tone + format → AI tạo content

## Patterns demo

- **Provider Swap**: đổi Gemini ↔ Claude trong sidebar, business logic không đổi
- **Self-Healing**: retry 3 lần (exponential backoff) → fallback provider → error diagnosis
- **Error Classification**: mỗi lỗi = what + why + fix (không raw traceback)
- **Structured Output**: AI trả JSON, app parse + validate + hiển thị

## Stack

Python · Streamlit · Google GenAI SDK · Anthropic SDK · Pydantic

---

Built by [NoVa](https://novasentio.com)
