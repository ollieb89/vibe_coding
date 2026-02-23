---
title: SuperClaude 명령어 가이드
source: docs/user-guide-kr/commands.md
---

# SuperClaude 명령어 가이드

SuperClaude는 개발자를 위한 AI 도구로, 프로젝트의 모든 단계에서 편리하고 효율적인 작업을 지원합니다. 이 문서에서는 SuperClaude의 주요 명령어를 설명합니다.

## 개발 명령어

### workflow
- **목적**: 구현 계획
- **최적 사용처**: 프로젝트 로드맵, 스프린트 계획

```bash
/sc:workflow "구현 계획"
```

### implement
- **목적**: 기능 개발
- **최적 사용처**: 풀스택 기능, API 개발

```bash
/sc:implement "기능 이름"
```

### build
- **목적**: 프로젝트 컴파일
- **최적 사용처**: CI/CD, 프로덕션 빌드

```bash
/sc:build
```

### design
- **목적**: 시스템 아키텍처
- **최적 사용처**: API 스펙, 데이터베이스 스키마

```bash
/sc:design "시스템 아키텍처"
```

## 분석 명령어

### analyze
- **목적**: 코드 평가
- **최적 사용처**: 품질 감사, 보안 검토

```bash
/sc:analyze --focus quality
```

### business-panel
- **목적**: 전략적 분석
- **최적 사용처**: 비즈니스 결정, 경쟁 평가

```bash
/sc:business-panel
```

### spec-panel
- **목적**: 사양 검토
- **최적 사용처**: 요구사항 검증, 아키텍처 분석

```bash
/sc:spec-panel @existing_spec.yml --mode critique
```

### troubleshoot
- **목적**: 문제 진단
- **최적 사용처**: 버그 조사, 성능 문제

```bash
/sc:troubleshoot "문제 설명"
```

### explain
- **목적**: 코드 설명
- **최적 사용처**: 학습, 코드 검토

```bash
/sc:explain "코드 영역"
```

## 품질 명령어

### improve
- **목적**: 코드 향상
- **최적 사용처**: 성능 최적화, 리팩토링

```bash
/sc:improve --preview
```

### cleanup
- **목적**: 기술 부채
- **최적 사용처**: 데드 코드 제거, 정리

```bash
/sc:cleanup
```

### test
- **목적**: 품질 보증
- **최적 사용처**: 테스트 자동화, 커버리지 분석

```bash
/sc:test --coverage
```

### document
- **목적**: 문서화
- **최적 사용처**: API 문서, 사용자 가이드

```bash
/sc:document --type api
```

## 프로젝트 관리

### task
- **목적**: 작업 관리
- **최적 사용처**: 복잡한 워크플로우, 작업 추적

```bash
/sc:task "작업 이름"
```

### spawn
- **목적**: 메타 오케스트레이션
- **최적 사용처**: 대규모 프로젝트, 병렬 실행

```bash
/sc:spawn "작업 이름" --num-workers 4
```

## 유틸리티 명령어

### help
- **목적**: 모든 명령어 나열
- **최적 사용처**: 사용 가능한 명령어 발견

```bash
/sc:help
```

### index
- **목적**: 명령어 발견
- **최적 사용처**: 기능 탐색, 명령어 찾기

```bash
/sc:index "명령어"
```

### select-tool
- **목적**: 도구 최적화
- **최적 사용처**: 성능 최적화, 도구 선택

```bash
/sc:select-tool "도구 이름"
```

## 세션 명령어

### load
- **목적**: 컨텍스트 로딩
- **최적 사용처**: 세션 초기화, 프로젝트 온보딩

```bash
/sc:load
```

### save
- **목적**: 세션 지속성
- **최적 사용처**: 체크포인팅, 컨텍스트 보존

```bash
/sc:save "세션 이름"
```

### reflect
- **목적**: 작업 검증
- **최적 사용처**: 진행 상황 평가, 완료 검증

```bash
/sc:reflect "작업 이름"
```

## 문제 해결

**명령어 문제:**
- **명령어를 찾을 수 없음**: 설치 확인: `python3 -m SuperClaude --version`
- **응답 없음**: Claude Code 세션 재시작
- **처리 지연**: MCP 서버 없이 테스트하려면 `--no-mcp` 사용

**빠른 수정:**
- 세션 재설정: `/sc:load`로 다시 초기화
- 상태 확인: `SuperClaude install --list-components`
- 도움말 받기: [문제 해결 가이드](../reference/troubleshooting.md)

## 다음 단계

- [플래그 가이드](flags.md) - 명령어 동작 제어
- [에이전트 가이드](agents.md) - 전문가 활성화
- [예제 모음](../reference/examples-cookbook.md) - 실제 사용 패턴

[source: docs/user-guide-kr/commands.md]