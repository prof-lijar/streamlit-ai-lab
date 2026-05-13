# Streamlit AI Lab - Project Proposal

## Overview

Streamlit 기반의 로컬 AI 워크벤치로, Ollama를 통해 다양한 LLM을 실행하고 Excel 파일을 자연어 프롬프트로 처리할 수 있는 도구입니다.

## Background

연구 및 교육 환경에서 다수의 Excel 파일을 수작업으로 통합/분석하는 작업은 반복적이고 시간이 많이 소요됩니다. 본 프로젝트는 자연어 프롬프트를 통해 이러한 작업을 자동화하고, 로컬 GPU 서버(RTX 5090, Spark)에서 오픈소스 LLM을 직접 실행하여 데이터 프라이버시와 비용 효율성을 확보합니다.

## Core Features

### 1. Interactive Chat UI (Streamlit)
- 대화형 프롬프트 인터페이스
- 채팅 히스토리 관리
- 모델 선택 UI (사이드바)

### 2. AI Model Management
- **Ollama 기반 로컬 모델 실행**
  - Llama 3, Mistral, Gemma, CodeLlama 등
  - 모델 다운로드(pull), 목록 조회, 삭제
- **API 기반 모델 연동** (선택적 확장)
  - OpenAI (GPT-4o), Google Gemini 등
  - API Key 관리

> **Note:** OpenAI, Gemini 등의 상용 모델은 로컬 다운로드가 불가하며 API 호출 방식으로만 사용 가능합니다. 로컬 실행은 Ollama 지원 오픈소스 모델에 한합니다.

### 3. File Management
- Excel 파일(.xlsx, .xls, .csv) 업로드
- 업로드된 파일 목록 조회 및 미리보기
- 파일 삭제
- 다중 파일 동시 업로드

### 4. Excel Processing via Prompts
- 자연어 프롬프트로 Excel 데이터 처리
- **처리 방식:** LLM이 pandas 코드를 생성 → 서버에서 실행 → 결과 반환
- 지원 작업:
  - 다중 파일 통합 (merge/concat)
  - 동일 항목 평균값 계산
  - 필터링, 정렬, 피벗
  - 수식 적용 및 연산
- 처리 결과 Excel/CSV 다운로드

### 5. Result Export
- 프롬프트 대화 내용 Markdown(.md) 파일로 저장
- 처리 결과 파일 다운로드 및 전송

## Architecture

```
┌─────────────────────────────────────────────┐
│                 Streamlit UI                │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ Chat     │ │ File     │ │ Model       │ │
│  │ Interface│ │ Manager  │ │ Selector    │ │
│  └────┬─────┘ └────┬─────┘ └──────┬──────┘ │
│       │             │              │        │
│  ┌────▼─────────────▼──────────────▼──────┐ │
│  │           Backend Service              │ │
│  │  ┌────────────┐  ┌──────────────────┐  │ │
│  │  │ LLM Engine │  │ Code Executor    │  │ │
│  │  │ (Ollama)   │  │ (Sandboxed)      │  │ │
│  │  └────────────┘  └──────────────────┘  │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │           Storage                      │ │
│  │  uploads/  │  results/  │  history/    │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Remote Server   │
│  RTX 5090/Spark  │
│  (Ollama Host)   │
└─────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| LLM Runtime | Ollama |
| Code Execution | pandas, openpyxl (sandboxed) |
| Language | Python 3.11+ |
| Server | RTX 5090 / Spark (원격) |

## Development Phases

### Phase 1: MVP (2주)
- [ ] Streamlit 기본 채팅 UI
- [ ] Ollama 연동 (모델 목록, 채팅)
- [ ] Excel 파일 업로드 및 미리보기

### Phase 2: Core Feature (2주)
- [ ] 프롬프트 기반 Excel 처리 (LLM → pandas 코드 생성 → 실행)
- [ ] 다중 파일 통합 기능
- [ ] 결과 파일 다운로드

### Phase 3: Polish (1주)
- [ ] 채팅 히스토리 저장 (Markdown 내보내기)
- [ ] 파일 관리 기능 (삭제, 목록)
- [ ] 에러 핸들링 및 UI 개선

### Phase 4: Extension (선택)
- [ ] API 기반 모델 연동 (OpenAI, Gemini)
- [ ] 원격 서버 배포 설정
- [ ] 추가 파일 포맷 지원

## Key Design Decisions

### LLM은 코드를 생성하고, 직접 계산하지 않음
Excel 데이터 처리 시 LLM이 직접 수치를 계산하면 오류 가능성이 높습니다. 대신 LLM이 pandas 코드를 생성하고, 이를 sandboxed 환경에서 실행하는 방식을 채택합니다. 이를 통해 정확한 연산 결과를 보장합니다.

### 로컬 모델 우선, API 모델은 선택적 확장
Ollama 기반 로컬 모델 실행을 기본으로 하여 데이터 프라이버시와 비용 절감을 우선합니다. OpenAI/Gemini 등 API 모델은 Phase 4에서 선택적으로 추가합니다.

## Example Use Case

> **시나리오:** 5개의 실험 결과 Excel 파일을 업로드하고, 동일한 표 항목의 평균값으로 통합

1. 사용자가 5개의 `.xlsx` 파일을 업로드
2. 프롬프트 입력: *"업로드된 5개 파일을 하나로 통합하고, 동일한 항목은 평균값으로 계산해줘"*
3. LLM이 pandas 코드를 생성:
   ```python
   import pandas as pd
   dfs = [pd.read_excel(f) for f in uploaded_files]
   merged = pd.concat(dfs).groupby(key_columns).mean().reset_index()
   merged.to_excel("result.xlsx", index=False)
   ```
4. 코드 실행 후 결과 파일 다운로드 제공
5. 대화 내용을 `.md` 파일로 저장 가능

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM이 잘못된 pandas 코드 생성 | 코드 실행 전 사용자에게 미리보기 제공, sandboxed 실행 |
| 대용량 Excel 처리 시 메모리 부족 | 파일 크기 제한, chunked 처리 |
| Ollama 모델 응답 품질 | 코드 생성 특화 모델(CodeLlama) 우선 사용 |
| 보안 (임의 코드 실행) | pandas/openpyxl만 허용하는 restricted exec 환경 |
