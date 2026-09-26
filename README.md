# HealthWiki

운동과 관련된 **영양학·해부학·생리학의 메커니즘**을 공부하고, 그 근거를 나의 운동·식단·통증 기록과 연결하는 개인 위키입니다.

시작 페이지: [내 대시보드](wiki/monitoring/dashboard.md) · [전체 목차](wiki/index.md)

## 처음 열기

Obsidian에서 **폴더를 보관함으로 열기**를 선택하고 이 `HealthWiki` 폴더를 지정하세요. `wiki/monitoring/dashboard.md`를 열어 북마크하면 됩니다. 일반 Markdown과 상대 링크를 사용하므로 추가 플러그인은 필요하지 않습니다.

에이전트 설정은 [공통 운영 지침](AGENTS.md), [위키 지침](wiki/AGENTS.md), [원본 지침](raw/AGENTS.md)과 `.agents/`에 모았습니다. 이 폴더를 작업 디렉토리로 열고 운영 지침을 적용하도록 요청하세요. 폴더별 지침에는 파일의 용도와 작성·수정 규칙이 있습니다. 자동 탐색 지원 여부에 관계없이 다음처럼 파일을 직접 지정해 시작할 수 있습니다.

> AGENTS.md와 작업 대상 폴더의 AGENTS.md를 읽고 이 위키를 관리해줘. 요청에 맞는 스킬을 .agents/skills/에서 읽고 적용해줘.

검색 스킬은 일반 Markdown 지침이며, 현재 에이전트에서 사용할 수 있는 검색·파일 도구를 활용합니다.

## 다른 PC에서 같은 에이전트 환경으로 사용하기

**클론으로 복원되는 것은 커밋되어 원격에 올라간 파일입니다.** 현재와 같은 에이전트 작업 환경을 만들려면 프로젝트 지침·스킬과 함께 실행 도구·권한·인증도 복원해야 합니다. 이 저장소는 Markdown 위키이므로 서버 실행이나 빌드 과정은 없습니다.

### 1. 기존 PC에서 준비

저장소 루트에서 다음을 확인합니다.

```sh
git status --short
git ls-files --others --exclude-standard
git ls-files --others --ignored --exclude-standard --directory
git rev-parse HEAD
```

변경·미추적 파일 중 옮길 위키, 원본, 사진, 스킬을 검토해 커밋하고 원격에 push합니다. 클라이밍 영상은 Git에서 제외하므로 별도 백업하고 새 PC의 같은 상대 경로로 복원합니다. 마지막 명령의 커밋 ID를 적어 두면 새 PC와 비교할 수 있습니다. 개인 건강 기록이 포함되므로 원격 저장소의 공개 범위와 접근 권한을 확인합니다.

| 항목 | 클론 포함 여부와 필요한 조치 |
| --- | --- |
| `AGENTS.md`, `wiki/`, `raw/`, `templates/` | Git에 추적된 문서·사진은 포함. 클라이밍 영상은 `.gitignore`로 추적 제외하며 Git LFS도 사용하지 않음 |
| `wiki/workouts/climbing/`의 영상, `analysis-videos/` | 최신 커밋의 파일 복원 대상에서 제외. 로컬 파일을 별도 백업해 같은 상대 경로로 복원. 이미 추적했던 영상은 추적만 해제하므로 과거 커밋에는 남아 있음 |
| `.agents/skills/`, `skills-lock.json` | 프로젝트 스킬 8개와 참고 문서·스크립트가 포함. 별도 재설치 없이 사용하며, 동일 구성 복원 중에는 최신판으로 덮어쓰지 않음 |
| `package.json`, `package-lock.json` | 포함. `node_modules/`는 제외되므로 아래의 `npm ci`로 복원 |
| `.env`, `.env.*`, `.venv/` | 제외(`.env.example`은 제외 규칙의 예외이나 현재 파일은 없음). 필요한 환경 변수는 새 PC에서 설정하고 Python 환경은 재생성 |
| 에이전트 앱·모델 설정·전역 스킬·플러그인·외부 도구 연결·로그인 | 저장소에 포함되지 않음. 사용하는 앱에서 별도 설치·설정·재인증 |
| 커밋하지 않은 자료·저장소 밖 파일·이전 채팅 | 클론으로 옮겨지지 않음. 필요한 자료는 별도 보관하고, 작업 맥락은 위키에 기록 |

기존 PC의 에이전트 앱 버전, 사용 모델·추론 설정, 사용자 공통 지침, 사용하는 전역 스킬·플러그인과 연결 서비스를 기록해 새 PC에 맞춥니다. 2026-09-21 작업 환경에 제공된 `pdf:pdf`, `video`, `ponytail:ponytail` 등은 저장소의 `.agents/skills/`와 별개입니다. 같은 기능·작업 방식을 원하면 해당 플러그인·전역 스킬을 같은 버전으로 설치하거나 사용자 정의 스킬 폴더와 참조 파일을 별도 복원합니다. Ponytail은 당시 `full` 모드였습니다. 인증 정보는 Git에 넣지 말고 새 PC에서 다시 로그인합니다. 파일·설정을 맞춰도 모델 응답과 외부 검색 결과까지 완전히 동일해지는 것은 아닙니다.

### 2. 클론하고 에이전트 설정하기

Git과 기존에 사용하던 에이전트 앱을 설치하고, 에이전트 계정 로그인과 저장소 접근에 필요한 Git 인증을 준비합니다.

```sh
git clone https://github.com/0-virus/HealthWiki.git
cd HealthWiki
git rev-parse HEAD
git status --short
```

기존 PC에서 기록한 커밋 ID와 비교합니다. 경로는 자유롭게 선택할 수 있으며 기존 `C:\Users\halma\Desktop\HealthWiki`를 재현할 필요는 없습니다. 파일 링크는 상대 경로를 유지합니다. Git은 빈 폴더를 복원하지 않으므로 아직 자료가 없는 폴더는 첫 저장 때 만들면 됩니다.

에이전트에서 **클론 루트 전체**를 작업 디렉토리로 지정합니다. 설정에 기존 PC의 절대 경로가 있으면 새 경로로 바꿉니다. 다음 기능을 사용할 수 있도록 앱의 도구 연결과 권한을 설정합니다.

- 저장소의 숨김 폴더를 포함한 파일 읽기와 `wiki/`, `raw/`, `templates/` 등 작업 대상의 파일 쓰기.
- 터미널 명령 실행. 기존 환경처럼 빠른 파일 검색을 하려면 `rg`(ripgrep)를 설치하고 실행 경로에 추가.
- 외부 웹 검색·URL 원문 열람. PDF·사진·영상 분석이 필요하면 해당 입력을 읽는 도구도 별도로 연결.
- 스킬·운영 지침을 수정하는 작업에는 `.agents/skills/`와 `AGENTS.md`의 쓰기 권한. 앱의 신뢰·승인 설정도 기존 작업 범위에 맞춤.

프로젝트 전용 설정 디렉토리를 새로 만들 필요는 없습니다. 자동 스킬 탐색이 안 되면 `SKILL.md` 경로를 직접 지정합니다. 새 대화에서는 다음처럼 시작합니다.

> AGENTS.md와 wiki/index.md, wiki/log.md를 먼저 읽어줘. 작업 대상 폴더의 AGENTS.md와 .agents/skills/의 해당 SKILL.md를 적용하고, 기존 프로필·기록·계획을 이어서 관리해줘. 사용할 수 있는 검색·파일·첨부 처리 도구를 확인하고, 없는 기능은 수행한 것처럼 기록하지 마. 날짜는 Asia/Seoul 기준으로 처리해줘.

### 3. 검색 도구 복원

기존 위키 열람·운동 기록에는 Node.js나 API 키가 필요하지 않습니다. 현재 저장소에 선언된 검색 CLI까지 복원하려면 Node.js와 npm을 설치합니다. 2026-09-21 로컬 확인 버전은 Node.js `24.12.0`, npm `11.7.0`, `parallel-web-cli` `0.9.3`이며, CLI 패키지의 Node.js 요구 조건은 `>=18`입니다. 최소 요구 조건은 지원 중인 Node.js 버전의 권장과는 별개입니다.

Windows PowerShell에서 저장소 루트 기준:

```powershell
node --version
npm.cmd --version
npm.cmd ci
& .\node_modules\.bin\parallel-cli.cmd --version
& .\node_modules\.bin\parallel-cli.cmd login
& .\node_modules\.bin\parallel-cli.cmd auth
```

macOS·Linux에서는 `npm ci`를 실행하고 `./node_modules/.bin/parallel-cli --version`, `./node_modules/.bin/parallel-cli login`, `./node_modules/.bin/parallel-cli auth`로 확인합니다. 전역 설치 없이 프로젝트의 CLI를 사용합니다. Windows에서 `npm.ps1` 실행 정책 오류가 나면 위의 `npm.cmd`를 사용하면 됩니다.

`npm ci`는 잠금 파일의 버전을 복원하며 설치 중 해당 OS의 CLI 바이너리를 GitHub Releases에서 내려받습니다. npm 레지스트리와 GitHub에 접근할 수 있어야 하고 설치 스크립트를 허용해야 합니다. 현재 패키지의 지원 대상은 Windows x64, macOS·Linux x64/arm64입니다. `--ignore-scripts` 또는 `PARALLEL_CLI_SKIP_DOWNLOAD=1`로 설치하면 바이너리 준비가 생략됩니다.

인증은 위의 로그인 또는 `PARALLEL_API_KEY` 환경 변수로 설정합니다. 키는 에이전트가 실행하는 프로세스에서도 사용할 수 있어야 하며, `.env`를 만드는 것만으로 모든 도구가 자동으로 읽는다고 가정하지 않습니다. 인증·사용 가능 한도는 계정에서 확인합니다. [Parallel CLI 공식 인증 안내](https://docs.parallel.ai/integrations/cli)를 참고하세요.

CLI 설치만으로 에이전트에 검색 도구가 자동 연결되는 것은 아닙니다. 에이전트가 위 실행 파일을 호출할 수 있게 하거나 앱의 웹 검색 기능을 연결합니다. 전용 CLI가 없어도 `health-query`는 사용 가능한 웹 검색과 PubMed·원문 제공처로 진행할 수 있습니다.

### 4. 필요한 선택 기능만 복원

문헌 조사 스킬을 읽는 데 Python 설치는 필요하지 않습니다. 포함된 보조 스크립트를 실행할 때만 준비합니다. 현재 로컬 Python은 `3.13.9`이며 Python 패키지 버전을 고정한 잠금 파일은 없습니다.

| 기능 | 필요한 준비 |
| --- | --- |
| `verify_citations.py` 서지 확인 | Python 3, `requests`, 외부 네트워크 접근 |
| `search_databases.py` | Python 3 표준 라이브러리. 실제 DB 검색기가 아니라 이미 확보한 결과 JSON의 중복 제거·정렬·변환 도구 |
| `generate_pdf.py` | Python 3, Pandoc, XeLaTeX와 사용할 글꼴. 한글 PDF는 한글 지원 글꼴·템플릿을 준비하고 출력 확인. 서지 파일을 쓰면 해당 CSL 인용 스타일 파일도 필요 |
| `generate_schematic.py` / `generate_schematic_ai.py` | Python 3, `requests`, `OPENROUTER_API_KEY` 및 서비스 사용 권한. 일반 위키 질의에는 불필요 |

예를 들어 서지 확인용 환경은 Windows에서 다음처럼 만듭니다. 가상 환경 활성화 없이 실행할 수 있습니다.

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install requests
& .\.venv\Scripts\python.exe -c "import requests; print(requests.__version__)"
```

macOS·Linux에서는 `python3 -m venv .venv`와 `.venv/bin/python`을 사용합니다. 기존에 보조 기능을 사용했다면 기존 가상 환경의 `python -m pip freeze` 결과, Pandoc·XeLaTeX 버전, 글꼴·CSL·템플릿도 별도 보관해 새 환경에 맞춥니다. `.venv/`와 `node_modules/` 자체를 다른 OS로 복사하지 않습니다.

### 5. 복원 완료 확인과 이후 동기화

- 에이전트에 “AGENTS.md와 wiki/index.md, wiki/log.md를 읽고 적용할 규칙과 최근 작업을 요약해줘”라고 요청해 지침 접근을 확인합니다. `ingest`, `query`, `lint`, `workout-log`, `climbing-video-analysis`, `health-query`와 연계 조사 스킬 2개를 읽을 수 있어야 합니다.
- 저장소 내 임시 파일을 하나 작성·읽기·삭제하게 해 파일 수정 권한을 확인합니다. 기존 기록이나 원본은 이 시험에 사용하지 않습니다.
- 별도 백업한 영상을 복원한 뒤 [클라이밍 기록](wiki/workouts/climbing/records/2026-09-20.md)의 첨부가 존재하는지 확인합니다. 영상 분석도 재현하려면 연결한 영상 도구로 실제 구간을 읽을 수 있는지 별도로 확인합니다.
- 검색을 쓸 경우 공개 주제로 검색과 원문 열람을 한 번 확인합니다. `--version` 성공은 설치 확인이며, `auth`와 실제 검색 성공까지 확인해야 검색 환경 복원이 끝납니다.
- 필요한 보조 스크립트만 실행해 확인합니다. PDF 환경은 `python .agents/skills/literature-review/scripts/generate_pdf.py --check-deps`로 점검한 뒤 실제 출력도 확인합니다.
- 마지막으로 `git status --short`에서 의도하지 않은 위키 변경이 없는지 확인합니다.

여러 PC에서 번갈아 작업할 때는 로컬 변경을 먼저 확인하고 `git pull --ff-only`로 시작합니다. 작업 후 변경 파일을 검토해 커밋·push한 뒤 다른 PC로 전환합니다. 충돌이 나면 원본과 기존 로그를 보존하며 해결합니다. 에이전트의 인증·전역 설정은 이 Git 동기화에 포함되지 않으므로 변경 시 따로 반영합니다.

## 폴더 안내

| 경로 | 담는 내용 |
| --- | --- |
| `wiki/AGENTS.md`, `raw/AGENTS.md` | 각 폴더의 에이전트 지침 |
| `wiki/index.md` | 실제 위키 페이지의 목록과 파일별 설명 |
| `wiki/log.md` | 최신 항목을 앞에 추가하고 기존 기록은 보존하는 작업 이력 |
| `raw/books/` | 책 메모, 발췌와 판본·쪽수 |
| `raw/videos/` | 유튜브 URL 메모, 자막과 타임스탬프 |
| `raw/papers/` | 논문 PDF, 확보한 원문 |
| `raw/personal/` | 검사 결과, 사용자가 제공한 개인 기록 |
| `raw/assets/` | 원본 이미지 등 첨부 자료 |
| `raw/setup/` | 구축 아이디어와 요구사항 인터뷰 |
| `wiki/sources/` | 원본별 요약, 서지 정보, 검증 상태 |
| `wiki/topics/` | 해부학·생리학·영양학·운동역학을 연결한 주제 지식 |
| `wiki/queries/` | 출처를 검증한 질문별 분석과 검색 이력 |
| `wiki/plans/` | 개인 목표별 실행안, 재평가 기준과 변경 이력 |
| `wiki/monitoring/` | 프로필, 대시보드, 일별 기록과 주간 회고 |
| `wiki/workouts/` | [운동 기록 안내](wiki/workouts/index.md), 종목별 Markdown 기록. 클라이밍은 `records/`와 사진·영상용 `assets/` 분리 |
| `analysis-videos/` | 클라이밍 파생 분석 영상·프레임 좌표·구간별 리포트. Git 제외 대상이므로 PC 간 이동 시 별도 보관 |
| [`pathfinding-images/`](pathfinding-images/README.md) | 영상별 패스파인딩용 원본 벽·홀드 후보 표시·스타트 이미지 3장과 [전체 이미지 목록](pathfinding-images/index.html) |
| `templates/` | 자료 요약·주제·질문·계획·일별 기록·회고 양식 |
| `.agents/skills/` | ingest·query·lint·workout-log·climbing-video-analysis·health-query와 literature-review·scientific-critical-thinking 절차 |

주제는 폴더를 계속 쪼개는 대신 태그와 링크로 연결합니다. 같은 관절이나 운동에 관한 영양·해부학·생리학 내용을 하나의 주제에서 함께 읽을 수 있습니다.

## 이렇게 사용하세요

| 스킬 | 역할 | 요청 예시 |
| --- | --- | --- |
| [ingest](.agents/skills/ingest/SKILL.md) | 요약·목적 인터뷰 후 출처와 주제 통합 | “ingest로 이 책 메모를 반영해줘.” |
| [workout-log](.agents/skills/workout-log/SKILL.md) | 종목별 운동 기록·첨부와 새 종목 형식 등록 | “오늘 크로스핏 운동을 기록해줘.” |
| [climbing-video-analysis](.agents/skills/climbing-video-analysis/SKILL.md) | 인물 확인 후 관절·무게중심 표시 영상, 1초·중요 구간 0.1초 분석과 메모 기반 리포트 | “이 실패 영상을 분석해줘. 메모: 오른쪽으로 쏠리며 발이 떨어졌어.” |
| [query](.agents/skills/query/SKILL.md) | 기존 위키에서 답을 찾고 분석을 다시 저장 | “query로 지금까지 읽은 자료의 공통점과 차이를 정리해줘.” |
| [lint](.agents/skills/lint/SKILL.md) | 출처·모순·오래된 주장·링크·개인 기록 점검 | “lint로 위키를 점검해줘.” |
| [health-query](.agents/skills/health-query/SKILL.md) | 논문 검색과 건강 근거 검증·개인화 | “health-query로 운동과 영양 근거를 조사해줘.” |

`query`는 기존 위키를 먼저 읽고, 전문 조사가 필요하면 `health-query` 절차를 이어서 적용합니다. 스킬 이름을 인식하지 못하는 환경에서는 위 표의 `SKILL.md` 경로를 직접 지정하세요.

**자료 넣기** — 적합한 `raw/` 폴더에 파일을 넣거나 채팅에 자료·링크를 주세요.

> 이 책 메모를 읽고 핵심을 요약해줘. 업로드 목적을 짧게 인터뷰한 후 위키에 반영해줘.

LLM은 먼저 요약과 목적 질문 1~3개를 제시합니다. 답변을 받은 후 출처 요약과 관련 주제를 갱신합니다. 이미 목적을 설명했다면 반복해서 묻지 않습니다. 원본은 보존합니다.

**근거 검색과 질문** — 논문 검색 전용 도구가 연결되어 있으면 활용하고, 현재 가능한 웹 검색과 PubMed·원문 제공처로도 진행할 수 있습니다. 외부 검색이 불가능하면 그 한계를 기록합니다.

> health-query 절차로 스쿼트 중 무릎 앞쪽 통증을 조사해줘. 필요한 개인 정보를 먼저 확인하고, 가능한 메커니즘과 근거를 비교해줘.

> health-query 절차로 내 프로필과 최근 기록을 바탕으로 근성장 식단 초안을 만들어줘. 수치의 근거와 식품 중량 기준을 표시해줘.

> health-query 절차로 관절 통증 관리 장기 계획을 검토해줘. 현재 계획과 주간 기록을 연결하고 재평가 기준을 정리해줘.

검색 답변은 `wiki/queries/`에 남깁니다. 새 외부 자료를 주제 지식에 통합할 때에도 목적이 불명확하면 짧게 인터뷰합니다. **계획 초안 저장과 실제 실행 시작은 구분**합니다.

**개인 기록** — 파일을 직접 쓰거나 채팅으로 알려주면 됩니다.

운동 상세는 [종목별 운동 기록](wiki/workouts/index.md)에 저장합니다. 크로스핏은 사전 운동을 WOD 앞에 두고 입력 형태를 유지하며 영어로 번역합니다. 클라이밍은 지점·시간·클리어 목록과 문제별 메모·첨부를 연결합니다. 새로운 운동 종목은 처음 기록할 때 양식을 정해 등록합니다. 통증·식사·회복은 일별 관찰에 연결합니다.

> 오늘 운동·식사·통증 기록을 정리해줘. 측정하지 않은 항목은 미기록으로 두고 대시보드를 갱신해줘.

> 최근 7일 기록을 회고해줘. 기록이 있는 날짜 수, 통증과 운동량 변화, 다음 확인 질문을 정리해줘.

**위키 점검**

> lint로 위키를 점검해줘. 출처 누락, 서로 모순되는 주장, 오래된 근거, 끊어진 링크, 누락된 기록을 확인해줘.

## 첫 개인화

[프로필](wiki/monitoring/profile.md)과 [대시보드](wiki/monitoring/dashboard.md)에 기존 목적·기록·계획 상태를 유지합니다. 다른 PC에서 열어도 개인화를 처음부터 반복하지 않습니다. 새 계획을 만들 때 현재 운동, 목표 우선순위, 증상·검사 정보, 식사 조건 등 **그 질문에 필요한 미확인 항목만** 인터뷰합니다.

원본 → 출처 요약 → 주제/분석 → 실행 계획 → 관찰 기록 → 재평가 순서로 지식이 축적됩니다. 계획은 초안부터 시작하며, 관찰된 변화만으로 원인을 확정하지 않습니다.
