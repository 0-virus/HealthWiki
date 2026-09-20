---
type: index
created: 2026-09-20
updated: 2026-09-20
status: reviewed
tags: [navigation, workout]
---
# 운동 기록

[전체 목차](../index.md) · [대시보드](../monitoring/dashboard.md) · [운동 기록 스킬](../../.agents/skills/workout-log/SKILL.md)

## 등록 종목

| 종목 | 기록 위치 | 양식 |
| --- | --- | --- |
| 크로스핏 | `crossfit/YYYY-MM-DD.md` | [크로스핏](../../templates/workout-crossfit.md) — 사전 운동 → WOD, 입력 형태를 유지하며 영어로 번역 |
| 클라이밍 | `climbing/records/YYYY-MM-DD.md`, 사진·영상은 `climbing/assets/` | [클라이밍](../../templates/workout-climbing.md) — 지점·시간·색상별 클리어와 문제별 메모·첨부 |

위치는 이 폴더 기준이다. 같은 날 별도 세션은 `-02` 등의 접미사로 구분한다. 미등록 종목은 첫 기록 때 전용 형식을 정하고 이 표와 양식 안내에 등록한다.

운동 상세는 이 폴더의 종목별 파일을 기준으로 관리한다. 기존 일별 관찰의 운동 내용은 당시 접수 기록으로 보존하며, 같은 세션을 두 번 집계하지 않는다. 통증·식사·회복은 일별 관찰과 연결한다.

## 크로스핏 기록

- [2026-09-18](crossfit/2026-09-18.md) — EMOM 20min. 사용자 입력의 번호·동작 묶음·무게 위치를 유지한 영어 기록.
- [2026-09-15](crossfit/2026-09-15.md) — For time (time cap: 25min), I go You go.

## 클라이밍 기록

- [지점별 난이도 등록부](climbing/venues.md) — 지점명·확인된 별칭·스티커 색상 순서, 새 지점 확인 대기 목록.
- [2026-09-20](climbing/records/2026-09-20.md) — 서울숲클라이밍 잠실점(입력명: 잠실새내점), 1시간 30분·8개 클리어. 피부 상태로 중단, 지점·난이도 확인 완료, 영상 9개 연결(실패 표시 2개 포함).

2026-03-03의 지점·클리어 목록은 사용자가 형식 설명을 위해 제공한 예시이며 실제 운동 이력으로 등록하지 않았다.
