# Streamlit AI Lab

Streamlit 기반의 로컬 AI 워크벤치. Ollama를 통해 LLM을 실행하고, 자연어 프롬프트로 Excel/CSV 파일을 처리합니다.

## Demo Video (YouTube)

[![Streamlit AI Lab Demo](https://img.youtube.com/vi/9_hKYMj6v2w/maxresdefault.jpg)](https://youtu.be/9_hKYMj6v2w?si=bxu1iDOnps2_rmur)

## Features

- **Interactive Chat** — Ollama 모델과 대화형 프롬프트
- **File Management** — Excel/CSV 파일 업로드, 미리보기, 삭제
- **Excel Processing via Prompts** — 자연어로 파일 통합, 연산, 필터링 등 실행
  - LLM이 pandas 코드를 생성 → sandboxed 환경에서 실행 → 결과 반환
  - 처리 결과 Excel/CSV 다운로드
- **Export** — 대화 내용을 Markdown 파일로 저장

## Example

> 5개의 실험 결과 Excel 파일을 업로드 → 프롬프트: *"5개 파일을 하나로 통합하고, 동일 항목은 평균값으로 계산해줘"* → 코드 실행 → 결과 파일 다운로드

## Setup

```bash
# Clone
git clone git@github.com:prof-lijar/streamlit-ai-lab.git
cd streamlit-ai-lab

# Virtual environment
python -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt
```

## Prerequisites

[Ollama](https://ollama.com)가 실행 중이어야 합니다.

```bash
# Install a model
ollama pull llama3
# or a code-focused model
ollama pull codellama
```

## Run

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

## Usage

1. 사이드바에서 모델 선택
2. Excel/CSV 파일 업로드
3. 프롬프트로 파일 처리 요청 (예: *"performance_rating 컬럼을 삭제해줘"*)
4. LLM이 생성한 코드를 확인하고 **▶ Execute Code** 클릭
5. 결과 DataFrame 확인 및 파일 다운로드

## Project Structure

```
streamlit-ai-lab/
├── app.py                  # Streamlit main app
├── utils/
│   ├── ollama_client.py    # Ollama API client
│   ├── file_manager.py     # File upload/download/listing
│   ├── code_executor.py    # Sandboxed pandas code execution
│   └── export.py           # Chat export to Markdown
├── uploads/                # Uploaded files (gitignored)
├── results/                # Processed result files (gitignored)
├── requirements.txt
└── PROPOSAL.md
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| LLM Runtime | Ollama |
| Code Execution | pandas, openpyxl (sandboxed exec) |
| Language | Python 3.11+ |

## Security

코드 실행은 restricted exec 환경에서 수행됩니다:
- AST 기반 정적 분석으로 위험한 import/builtin 차단 (`os`, `subprocess`, `eval` 등)
- `save()` 함수는 `results/` 디렉토리에만 파일 쓰기 허용
- 30초 타임아웃으로 무한 루프 방지
- 사용자가 코드를 확인한 후 수동 실행 (자동 실행 없음)
