# Vibe Code AI Agent System — Conceptual Model

**Status**: Ý tưởng, chưa implementation  
**Người thiết kế**: Snail (Security Engineer + BA, BTECO)  
**Ngày tạo**: Tháng 5, 2026  
**Nền tảng triển khai**: OpenClaw 2026.4.15 trên Linux  
**LLM Provider**: 1 combo provider duy nhất của Snail

---

## Mục lục

1. [Triết lý hệ thống](#triết-lý-hệ-thống)
2. [Kiến trúc 4 tầng](#kiến-trúc-4-tầng)
3. [Các thực thể (Agents)](#các-thực-thể-agents)
4. [Các cơ chế (Mechanisms)](#các-cơ-chế-mechanisms)
5. [Quy trình phát triển 5 phase](#quy-trình-phát-triển-5-phase)
6. [Chi tiết từng khối](#chi-tiết-từng-khối)
7. [Luồng end-to-end](#luồng-end-to-end)
8. [Ma trận quyền hạn](#ma-trận-quyền-hạn)
9. [Các quyết định quan trọng](#các-quyết-định-quan-trọng)

---

## Triết lý hệ thống

Hệ thống vận hành theo nguyên tắc **maximum autonomy with full traceability**.

**Nguyên tắc cốt lõi:**

- **Snail giao, hệ thống lo phần còn lại**: Snail chỉ cần mô tả yêu cầu phần mềm, hệ thống tự lo phân tích, thiết kế, code, test, ship lên GitHub
- **Ít gián đoạn nhất**: Snail chỉ được làm phiền khi có blocker tuyệt đối (cần credentials, business decision không suy đoán được)
- **Đổi lại sự tự chủ là full traceability**: Mọi hành động đều được ghi lại → Snail audit sau, hoặc feed back để hệ thống cải tiến
- **Tối đa hóa LLM**: Không chỉ code generation, mà cả phân tích, phản biện, test, review đều dùng LLM

**Mục tiêu chất lượng:**

- **Output code**: high-quality, well-tested, security-audited, well-documented
- **Output thinking**: architecture lựa chọn là result của advisory round, không phải gut feeling
- **Feedback loop**: Hệ thống tự học từ audit log (auto) + học từ feedback Snail (human)

---

## Kiến trúc 4 tầng

```
┌─────────────────────────────────────────┐
│ Tầng 1: Human Interface                 │
│ Snail ←→ Telegram Bot                   │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│ Tầng 2: Decision Layer                  │
│ • CEO Agent (portfolio manager)          │
│ • Advisory Board (dynamic spawn)         │
│ • Conflict Detector                      │
│ • Decision Engine                        │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│ Tầng 3: Execution Layer                 │
│ • Team Lead A, B, ..., N (per project)  │
│ • Sub-agents: Dev, Test, Review, DevOps,│
│   Doc Writer (per project)               │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│ Tầng 4: Infrastructure & Cross-cutting  │
│ • Model Router                           │
│ • Audit Log Service                      │
│ • Learning Loop                          │
│ • Status Board                           │
│ • Knowledge Base                         │
│ • Verification Gates                     │
│                                          │
│ Foundation: OpenClaw, Linux, Message Bus,│
│ Vault, Artifact Store, GitHub, State DB │
└─────────────────────────────────────────┘
```

---

## Các thực thể (Agents)

### 1. Snail (Human)

**Vai trò**: Người chủ hệ thống, giao việc, review, feedback

**Interface**: Telegram Bot  
**Tần suất contact**: Tối thiểu — chỉ khi blocker tuyệt đối  
**Quyền hạn**:
- Tạo dự án mới
- Pause / abort dự án bất kỳ
- Override CEO decision
- Edit Learning Loop
- Cung cấp credentials
- Review audit log
- Feedback agents

---

### 2. CEO Agent

**Vai trò**: Portfolio manager, orchestrator cấp cao, authority cao

**Ngõ vào:**
- Yêu cầu từ Snail (qua Telegram → Telegram bot → CEO inbox)
- Feedback runtime từ Team Lead (báo cáo, blocker)

**Ngõ ra:**
- Spawn advisor khi cần advisory
- Dispatch task tới Team Lead
- Escalate lên Snail khi cần
- Intervention channel tới sub-agent (đặc biệt)
- Status update định kỳ

**Thành phần nội bộ:**

| Module | Chức năng |
|--------|----------|
| Request Intake | Parse yêu cầu thô → structured intent (goal, constraint, scope, priority) |
| Project Context Manager | Switch namespace giữa các dự án; maintain priority queue |
| Decision Engine | Core brain: phân loại task (cần advisory hay tự quyết), chọn advisor cần spawn, tổng hợp opinions |
| Advisor Spawner | Dynamic create advisor agent với system prompt riêng cho từng vai trò |
| Team Lead Dispatcher | Giao PRD + chỉ đạo xuống Team Lead tương ứng |
| Intervention Channel | Direct line tới sub-agent khi CEO cần override |
| Escalation Filter | Lọc: blocker tuyệt đối → Snail, còn lại tự xử |

**Quy tắc quyết định (Decision Framework):**

- Task có độ phức tạp cao hoặc nhập nhằng → spawn advisory board
- Task rõ ràng → CEO tự quyết
- Conflict resolution: nếu advisor không đồng thuận sau 3 round → CEO veto (phải log reason)
- Escalation: chỉ cần credentials, business rule không suy đoán được

---

### 3. Advisory Board (Dynamic)

**Vai trò**: Tham vấn, phân tích, đề xuất phương án

**Đặc điểm**: Không phải fixed roles, mà **dynamic spawn theo task**

**Ví dụ các advisor có thể:**
- Architect Advisor (system design, scalability)
- Security Advisor (threat model, OWASP, CVE)
- BA Advisor (requirement analysis, BTECO rules)
- UX Advisor (user interface, usability)
- DevOps Advisor (deployment, CI/CD)
- Database Advisor (schema, optimization)
- Integration Advisor (API, third-party)
- Compliance Advisor (legal, regulatory)

**Mỗi advisor có:**
- **System prompt riêng** (định nghĩa persona, expertise)
- **Knowledge access** (database, document, feed chuyên biệt)
  - Ví dụ: Security Advisor → OWASP DB, CVE feed, threat model templates
  - BA Advisor → BTECO product knowledge, manday rules, quotation templates
- **Output format chuẩn** (opinion structured dễ tổng hợp)

**Quy trình hoạt động (Hybrid Model):**

1. **Phase 1 — Parallel Opinion Gathering**
   - CEO đặt câu hỏi, spawn N advisor cần thiết
   - Mỗi advisor đưa ý kiến độc lập (song song, LLM call riêng)

2. **Phase 2 — Conflict Detection**
   - Conflict Detector (LLM call ngắn của CEO) phân tích opinions
   - Phân loại: `consensus`, `soft_conflict`, `hard_conflict`

3. **Phase 3 — Conditional Discussion**
   - Nếu **consensus** → CEO tổng hợp ngay thành PRD + Tech Design
   - Nếu **conflict** → Discussion Round Manager kích hoạt round phản biện
     - Tối đa 3 round
     - Mỗi round: advisor phản biện advisor khác
     - Cố gắng tìm consensus

4. **Phase 4 — Synthesis**
   - Sau khi consensus hoặc 3 round → CEO tổng hợp opinions
   - Output: **PRD (Problem / Requirement / Design)** + **Tech Design Doc**

5. **Tie-breaker (nếu cần)**
   - Nếu 3 round không consensus → CEO veto (phải log decision + reason)

---

### 4. Team Lead Agent

**Vai trò**: Development manager per-project, orchestrate sub-agents, quality gate keeper

**Số lượng**: 1 Team Lead per project → hệ thống có thể quản multiple projects song song

**Ngõ vào:**
- PRD + Tech Design từ CEO
- Chỉ đạo runtime từ CEO

**Ngõ ra:**
- Dispatch task tới sub-agents
- Progress report tới CEO
- Escalate blocker lên CEO

**Context**: Mỗi Team Lead có **isolated namespace** — không biết gì về project khác

**Thành phần nội bộ:**

| Module | Chức năng |
|--------|----------|
| Task Decomposer | Chia PRD thành task DAG (directed acyclic graph); phân quyền sub-agent |
| Quality Judge | Đánh giá output từ sub-agent: pass gate hay cần retry? |
| Reporter | Tổng hợp progress, blocker, metrics gửi CEO |

**Quy trình chính:**

1. Nhận PRD từ CEO
2. DevOps: init GitHub repo, scaffold project, setup CI/CD
3. Task Decomposer: tạo DAG, assign sub-agent
4. Vòng lặp cho mỗi task:
   - Developer → Tester → Reviewer → DevOps (if release candidate)
   - Quality Judge: check pass threshold?
   - Nếu fail → retry (max N lần) hoặc escalate CEO
5. Synthesize PR, E2E test, auto-merge nếu pass
6. Tag release, báo CEO

---

### 5. Sub-agents

**Số lượng per Team Lead**: 5 loại (có thể là 5 agent instance riêng hoặc 5 role trong 1 agent)

**5 loại sub-agent:**

#### 5.1 Developer Agent

**Chức năng**: Code generation, implementation

**Multi-call LLM pattern (không sinh code 1 lần):**

1. **Skeleton generation**: LLM call 1 → outline structure
2. **Function-level code**: LLM call 2-N → viết từng function
3. **Self-review**: LLM call N+1 → review code vừa viết
4. **Refactor**: LLM call N+2 → optimize, clean up
5. **Docstring**: LLM call N+3 → write comprehensive docs

**Context**: Mỗi call có context narrow (chỉ function đó) để tăng quality

**Output**: `.py` / `.js` / `.go` file hoàn thiện (tùy tech stack)

#### 5.2 Tester Agent

**Chức năng**: Test generation, test execution, coverage analysis

**Multi-call LLM pattern:**

1. **Test case generation**: LLM call 1 → analyze code, sinh test scenarios
   - Boundary cases
   - Edge cases
   - Error paths
   - Happy path
2. **Test implementation**: LLM call 2 → viết test code
3. **Execution**: Run tests thật (Python pytest / JavaScript Jest / ...)
4. **Failure analysis**: LLM call 3 → phân tích fail, suggest fix
5. **Coverage check**: Verify coverage ≥ threshold (ví dụ 80%)

**Output**: Test suite (unit + integration tests), coverage report

#### 5.3 Reviewer Agent

**Chức năng**: Code review, security audit, performance check

**Pattern: 3 LLM call song song (3 reviewer personas):**

- **Reviewer 1 — Security**: SAST scan, input validation, auth/authz, secret leakage
- **Reviewer 2 — Performance**: Time complexity, memory usage, DB queries optimization
- **Reviewer 3 — Maintainability**: Readability, naming convention, SOLID principles

**Kỹ thuật bổ sung:**

- SAST scan tool (ví dụ SonarQube, Semgrep)
- Dependency audit (ví dụ npm audit, pip audit)
- Secret scan (ví dụ GitGuardian, truffleHog)

**Output**: Code review findings (severity, suggestion, code snippet)

#### 5.4 DevOps Agent

**Chức năng**: Infrastructure, CI/CD, repository management

**Trách nhiệm:**

- **Init phase**: Tạo GitHub repo, scaffold, setup CI/CD workflow
- **Development phase**: Manage branches, review CI/CD logs
- **Release phase**: Create PR, trigger full CI suite, merge strategy
- **Post-release**: Tag version, rollback preparation

**Kỹ thuật:**

- GitHub API integration
- CI/CD pipeline definition (GitHub Actions / GitLab CI / ...)
- Branch strategy (GitFlow / trunk-based)
- Release management

#### 5.5 Doc Writer Agent

**Chức năng**: Documentation generation

**Loại docs:**

- **README**: Project overview, how to run, how to contribute
- **API Documentation**: Endpoint spec, request/response, examples
- **User Guide**: Features, walkthrough, FAQ
- **Architecture Doc**: System design, data flow, deployment
- **Changelog**: Version history, breaking changes
- **Release Notes**: Feature highlights, bug fixes, migration guide

**Pattern**: LLM generate, review for accuracy against code

---

## Các cơ chế (Mechanisms)

### 1. Model Router

**Chức năng**: Route LLM call tới đúng model trong combo provider

**Input**: Task type từ agent (ví dụ `reasoning`, `code_gen`, `summarize`, `classify`)

**Logic**:
- Maintain bảng mapping: `task_type → model_id`
- Nếu model primary timeout → fallback model
- Log routing decision vào audit log

**Ví dụ mapping** (Snail có quyền edit):
```
reasoning     → model_complex (Opus)
code_gen      → model_coding (Sonnet)
summarize     → model_fast (Haiku)
review        → model_complex (Opus)
test_gen      → model_coding (Sonnet)
classify      → model_fast (Haiku)
```

**Benefit**: Snail có thể tune model choice mà không sửa agent code

---

### 2. Conflict Detector

**Chức năng**: Phân tích advisory opinions, detect conflict

**Input**: List of (advisor_id, opinion) từ advisory round

**LLM call**: 1 call ngắn từ CEO với prompt:
```
Analyze these advisor opinions on [question]:
- Architect: [opinion A]
- Security: [opinion B]
- BA: [opinion C]

Classify agreement level: CONSENSUS | SOFT_CONFLICT | HARD_CONFLICT
```

**Output**: Phân loại + extract conflict topics (nếu có)

---

### 3. Verification Gates

**Chức năng**: Quality checkpoint giữa các phase

**5 Gates (1 per phase):**

| Gate | Phase | Checklist | Pass Criteria |
|------|-------|-----------|---------------|
| Gate 1 | Intake | Ambiguity score, missing constraint check | Score < 0.3, all required fields filled |
| Gate 2 | Advisory | PRD completeness, advisor consensus, risk register | PRD checklist ✓, consensus ≥ 80%, risk ≤ 2 critical |
| Gate 3 | Planning | Repo ready, CI config valid, DAG valid | Repo initialized, CI workflow valid, DAG acyclic |
| Gate 4 | Development | Unit test pass rate, coverage, lint, SAST | Tests 100%, coverage ≥ 80%, lint clean, SAST 0 critical |
| Gate 5 | Release | E2E pass, smoke test, rollback plan | E2E 100%, smoke 100%, rollback doc complete |

**Behavior**:
- Nếu fail → loop lại phase trước hoặc escalate CEO
- Nếu pass → proceed next phase

---

### 4. Audit Log Service

**Chức năng**: Ghi toàn bộ action của hệ thống

**Scope**: Mọi LLM call, decision, message, file operation, git operation

**Log structure**:
```json
{
  "timestamp": "2026-05-16T10:30:45Z",
  "trace_id": "uuid",
  "agent_id": "ceo_agent",
  "project_id": "proj-001",
  "action_type": "llm_call | decision | message | file_op | git_op",
  "payload": {
    "model": "model_complex",
    "prompt": "...",
    "response": "...",
    "tokens_used": 1234
  }
}
```

**Trace ID**: Dùng để link các action liên quan thành chain → trace ngược từ code đến decision

**Query API**: Filter theo agent / project / time range / action type

**Retention**: Lưu vĩnh viễn (compliance)

---

### 5. Learning Loop

**Chức năng**: Cải tiến hệ thống qua thời gian

**Hai nhánh song song:**

#### Nhánh Auto (Retrospective Agent)

**Trigger**: Sau mỗi dự án hoàn thành

**Process**:
1. Read audit log của dự án
2. Extract patterns:
   - Lỗi lặp lại?
   - Decision tốt hay xấu?
   - Advisor nào hay đúng?
   - Phase nào mất thời gian?
3. Update Knowledge Base:
   - Advisor trust scores
   - Decision templates
   - Anti-patterns

**Ví dụ insight**:
```
- Security advisor: 3/3 đúng về OAuth (trust +)
- Architect advisor: 2/3 đúng về DB schema (trust neutral)
- Pattern: Authentication logic nên dùng library, không custom
```

#### Nhánh Human (Snail Feedback)

**Trigger**: Snail feedback qua Telegram (định kỳ hoặc ad-hoc)

**Format**: Structured feedback
```
Feedback for [agent_id]:
- Rating: 8/10
- What went well: [...]
- What could improve: [...]
- Next time: [...]
```

**Merge**: Feedback được merge vào cùng Knowledge Base

---

### 6. Status Board

**Chức năng**: Real-time portfolio view cho CEO / Snail

**Data**:
- Project list (name, phase, health, priority)
- Health metrics (blocker count, test pass rate, coverage)
- Timeline (start, planned end, actual end)
- Resource (Team Lead, sub-agent count)
- Risks (open, priority)

**Query**: CEO / Snail có thể query realtime (not batch refresh)

---

### 7. Knowledge Base

**Chức năng**: Store cross-project insights, reusable patterns

**Content**:
- Advisor trust scores (per domain, per topic)
- Decision templates (common scenarios)
- Anti-patterns (what not to do)
- Reusable code snippets / architecture patterns
- Lessons learned

**Update**: Via Learning Loop (auto + human feedback)

**Access**: CEO + Advisor query khi làm task mới

---

## Quy trình phát triển 5 phase

```
┌─────────────────────────────────────────────┐
│ Phase 1: Intake & Clarification             │
│ CEO parse yêu cầu → structured intent       │
│ Gate 1: Ambiguity < threshold?              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Phase 2: Advisory Analysis                  │
│ Advisory Board → hybrid discussion           │
│ Output: PRD + Tech Design                   │
│ Gate 2: PRD complete? Consensus?            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Phase 3: Planning & Scaffolding             │
│ Team Lead: repo init, task DAG, CI/CD       │
│ Gate 3: Repo valid? DAG valid?              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Phase 4: Development Loop (per task)        │
│ Dev → Test → Review → Fix loop (max N)      │
│ Gate 4: Coverage ≥ 80%? Lint clean?         │
│ Security gate: SAST 0 critical?             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Phase 5: Integration & Release              │
│ PR tổng → E2E test → auto-merge → tag       │
│ Gate 5: E2E 100%? Smoke test 100%?          │
│ Output: Release on GitHub, report to Snail  │
└─────────────────────────────────────────────┘
```

**Quy tắc cứng:**
- Mỗi gate có checklist cụ thể
- Nếu fail → hoặc loop lại phase trước hoặc escalate Snail
- Không phase nào được phép skip
- Mỗi gate check phải tự động hóa (hoặc có LLM validate)

---

## Chi tiết từng khối

### Khối CEO Agent — Internal Modules

```
┌──────────────────────────────────────────┐
│ Request Intake                           │
│ Parse intent → structured (goal, scope)  │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│ Project Context Manager                  │
│ Load/switch project namespace            │
│ Maintain priority queue                  │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│ Decision Engine (Core Brain)             │
│ - Classify task: advisory needed?        │
│ - Select advisor to spawn                │
│ - Synthesize opinions → decision         │
└──────────────────────────────────────────┘
         ↙   ↓   ↘
    ┌────┴───┴────┐
    ↓ Advisor     ↓ Team Lead    ↓ Intervention
    │ Spawner     │ Dispatcher   │ Channel
    └────┬───┬────┘
         ↓ escalation
    ┌────┴───────────┐
    │ Escalation Filter
    │ blocker? → Snail
    └──────────────────┘
```

---

### Khối Advisory Board — Hybrid Flow

**Phase 1: Parallel Opinion**
```
CEO đặt câu hỏi
    ↓
Spawn Architect + Security + BA + UX advisors
    ↓ (parallel LLM calls)
Each advisor gives opinion (independent)
```

**Phase 2: Conflict Detection**
```
Conflict Detector analyzes opinions
    ↓
    ├─ CONSENSUS → Phase 4
    ├─ SOFT_CONFLICT → Phase 3 (discussion)
    └─ HARD_CONFLICT → Phase 3 (discussion)
```

**Phase 3: Discussion (if conflict)**
```
Discussion Round Manager organizes
    ↓
Round 1: advisors phản biện nhau
    ↓
Round 2-3: refine (max 3 rounds)
    ↓
Try to reach consensus
    ↓ (if still no consensus after 3)
CEO veto + log reason
```

**Phase 4: Synthesis**
```
CEO synthesizes opinions into
    ├─ PRD (Problem/Requirement/Design)
    └─ Tech Design Doc
```

---

### Khối Team Lead — Per-project Development

**Structure per project:**
```
┌─────────────────────────────┐
│ Team Lead Agent             │
│ (Project A context)         │
├─────────────────────────────┤
│ • Task Decomposer           │
│ • Quality Judge             │
│ • Reporter                  │
├─────────────────────────────┤
│ Sub-agents:                 │
│ • Developer                 │
│ • Tester                    │
│ • Reviewer                  │
│ • DevOps                    │
│ • Doc Writer                │
└─────────────────────────────┘
```

**Development Loop per task:**
```
Developer              Tester           Reviewer
    ↓                    ↓                  ↓
Skeleton          Test case gen       Security review
  ↓                    ↓                  ↓
Function code     Test implement      Performance
  ↓                    ↓                  ↓
Self review       Run + analysis       Maintainability
  ↓                    ↓                  ↓
Refactor          Coverage check       Gộp findings
  ↓                    ↓                  ↓
Docstring      Coverage ≥ 80%?        SAST OK?
    └──────────┬───────────┬─────────┘
               ↓ (mỗi thành phần parallel)
        Quality Judge
        (all pass?)
            ↓
        YES → DevOps (PR + merge)
            NO → Retry (max N) / Escalate
```

---

### Khối Infrastructure — 6 Cross-cutting Components

**Model Router**
- Input: task_type
- Process: map → model_id via configurable table
- Output: route LLM call

**Audit Log Service**
- Scope: LLM calls, decisions, messages, file ops, git ops
- Format: JSON with trace_id
- Query API: filter-able
- Retention: permanent

**Learning Loop**
- Auto: Retrospective Agent reads audit log → extract insight
- Human: Snail feedback via Telegram → merge into KB
- Output: updated system prompts, advisor trust scores, templates

**Status Board**
- Data: project health, phase, blocker count, metrics
- Query: realtime
- Consumer: CEO, Snail

**Knowledge Base**
- Content: advisor scores, decision templates, anti-patterns
- Update: Learning Loop
- Access: CEO, Advisor query

**Verification Gates**
- 5 gates (1 per phase)
- Each with checklist + auto validation
- Gating logic: pass → next, fail → retry / escalate

---

## Luồng end-to-end

**Ví dụ: Snail yêu cầu "Tool tracking time cho BTECO team"**

```
Step 1: Snail Telegram
  "Cần tool tracking thời gian, tích hợp PMS"

Step 2: CEO Intake
  Parse → intent {
    goal: "tool tracking time",
    integration: "PMS",
    users: "BTECO team",
    priority: "normal"
  }
  Gate 1: ambiguity check → PASS

Step 3: Advisory Round
  CEO spawn: BA + Architect + Security + Integration
  Parallel → opinions
  Conflict detector: conflict on database schema
  Discussion round 1-2 → consensus
  Output: PRD + Tech Design Doc
  Gate 2: PRD complete → PASS

Step 4: CEO Dispatch
  Send PRD → Team Lead A

Step 5: Team Lead Planning
  DevOps init repo: github.com/bteco/time-tracker
  CI/CD setup
  Task DAG:
    - API endpoint: create_timesheet
    - API endpoint: update_timesheet
    - PMS integration module
    - Frontend: timesheet form
    - Tests, docs
  Gate 3: repo valid → PASS

Step 6: Development Loop
  Task 1: create_timesheet endpoint
    Developer: skeleton → function → self-review → refactor → docstring
    Tester: test cases → run → 11 pass, 1 fail → dev fix → rerun
    Reviewer: security/perf/maintain → 2 findings → dev fix
    Gate 4: coverage 87%, lint clean, SAST OK → PASS
  ... (more tasks)

Step 7: Mid-development Blocker
  Task 5 need OAuth creds for PMS API
  Team Lead → CEO: "Need PMS OAuth client_id + secret"
  CEO → Escalation Filter: blocker = credentials → ESCALATE
  Telegram to Snail: "Please provide PMS OAuth credentials"

Step 8: Snail Response
  Snail sends credentials via Telegram
  Vault stores encrypted → unblock Team Lead

Step 9: Finish Development
  All tasks complete
  Doc Writer: README, API docs, user guide
  E2E tests run

Step 10: Release
  PR created → GitHub
  CI suite full run → all pass
  Auto-merge
  Tag v1.0.0
  Gate 5: E2E 100%, smoke 100%, rollback OK → PASS
  Release complete

Step 11: CEO Report
  Telegram to Snail: "Done! Release: github.com/bteco/time-tracker/releases/v1.0.0"

Step 12: Post-release (Auto)
  Retrospective Agent reads audit log
  Extract: "Database schema design took 2 discussion rounds"
  → Trust score for Architect ↑
  → Update KB: "for schema-heavy features, allocate discussion time"

Step 13: Next time
  Similar feature → CEO + Advisor consult KB → shorter advisory round
```

---

## Ma trận quyền hạn

| Vai trò | Quyền | Hạn chế |
|---------|-------|---------|
| **Snail** | ✓ Tạo dự án · ✓ Pause/abort dự án · ✓ Override CEO · ✓ Edit KB · ✓ Cung cấp credentials · ✓ Audit log | Cách xa development (chỉ Telegram) |
| **CEO** | ✓ Spawn advisor · ✓ Quyết định strategy · ✓ Can thiệp sub-agent · ✓ Veto advisor · ✓ Escalate Snail · ✓ Set priority | ✗ Không tự code · ✗ Không escalate vô cớ |
| **Advisor** | ✓ Đưa ý kiến · ✓ Phản biện · ✓ Access domain knowledge | ✗ Không quyết định · ✗ Không can thiệp dev |
| **Team Lead** | ✓ Orchestrate sub-agent · ✓ Technical decision · ✓ Override sub-output · ✓ Báo CEO | ✗ Không cross-project · ✗ Không sửa PRD |
| **Sub-agent** | ✓ Execute scope · ✓ Tự retry · ✓ Receive CEO intervention | ✗ Không tự quyết scope · ✗ Không direct Snail |

---

## Các quyết định quan trọng

### Quyết định 1: Advisory Board Dynamic vs Fixed

**Lựa chọn**: Dynamic  
**Lý do**: Mỗi task cần advisor khác nhau; dynamic cho phép flexibility

---

### Quyết định 2: CEO Escalation Policy

**Lựa chọn**: Chỉ blocker tuyệt đối (credentials, business decision không suy đoán)  
**Lý do**: Maximize autonomy, minimize Snail interruption

---

### Quyết định 3: Conflict Resolution dalam Advisory

**Lựa chọn**: Hybrid (parallel → discussion → tie-breaker CEO)  
**Lý do**: Balance speed (no discussion nếu consensus) + quality (discussion khi cần)

---

### Quyết định 4: CEO Authority vs Decentralization

**Lựa chọn**: CEO có quyền can thiệp sub-agent (bypass Team Lead)  
**Lý do**: CEO cần thực quyền như CEO thật, nhất là khi critical issue

---

### Quyết định 5: LLM Provider

**Lựa chọn**: 1 combo provider duy nhất của Snail  
**Triển khai**: Model Router maps task type → model cụ thể  
**Benefit**: Độc lập, không phụ thuộc provider bên ngoài

---

### Quyết định 6: Quality Control

**Lựa chọn**: Audit log only (trust + verify after), không block-before  
**Lý do**: Phù hợp với maximum autonomy; verification gate trong mỗi phase là "block before"

---

### Quyết định 7: Learning Loop

**Lựa chọn**: Cả auto (retrospective) + human (Snail feedback)  
**Lý do**: 2 con đường cùng cải tiến: machine learning + human oversight

---

## Ranh giới và Quy tắc cứng

### Ranh giới giữa Tầng

- **Tầng 1 ↔ Tầng 2**: Telegram bot (chỉ escalation + báo cáo)
- **Tầng 2 ↔ Tầng 3**: PRD + chỉ đạo (CEO → Team Lead)
- **Tầng 3 ↔ Tầng 4**: Message bus, artifact store (sub-agent ↔ infrastructure)

### Quy tắc cứng

1. **Mọi action phải được ghi vào Audit Log** → không có exception
2. **Mỗi agent chỉ access data scope của mình** → context isolation
3. **Verification gate không được skip** → luôn execute mỗi phase
4. **Escalation filter**: chỉ blocker tuyệt đối lên Snail → Team Lead tự xử khác
5. **Learning Loop**: mỗi dự án hoàn thành phải trigger retrospective
6. **Model Router**: mỗi LLM call phải qua router → không direct access LLM

---

## Technology Stack (Đề xuất)

| Thành phần | Tech |
|-----------|------|
| Agent Framework | OpenClaw 2026.4.15 |
| LLM Provider | Combo provider của Snail |
| Message Bus | Redis Pub/Sub hoặc NATS |
| State Store | PostgreSQL hoặc SQLite |
| Artifact Store | Filesystem hoặc MinIO (S3-compatible) |
| Credential Vault | HashiCorp Vault hoặc custom (VAULT_PASSPHRASE env) |
| Git Integration | GitHub API |
| Telegram | Telegram Bot API |
| Deployment | Docker trên OpenClaw + Linux |

---

## Mối quan hệ với SecOps Sentinel

**Vibe Code Agent System** có thể được coi là bản "generalized" của **SecOps Sentinel**.

- **SecOps Sentinel**: Specialized cho penetration testing automation
- **Vibe Code**: General-purpose software development automation

**Reusable từ SecOps**: 
- Credential Vault pattern (VAULT_PASSPHRASE fallback)
- CLI + Telegram interface pattern
- Symlink rebuild + non-interactive auth pattern
- Skill directory convention

**Khác biệt chính**:
- Vibe Code có Advisory Board (SecOps không cần)
- Vibe Code có Learning Loop (SecOps có basic logging)
- Vibe Code xử lý multiple projects (SecOps internal-only)

---

## Next Steps — Khi chuyển từ Ý tưởng sang Implementation

1. **Folder structure design** (nơi code sẽ live trên OpenClaw)
2. **Agent base class** (abstraction cho tất cả agent)
3. **Message protocol** (định dạng message giữa các agent)
4. **Database schema** (State store, Audit log, KB)
5. **API documentation** (public interface của mỗi agent)
6. **Test strategy** (unit test agent, integration test workflow)
7. **Deployment & rollout** (cách start hệ thống, monitor health)

---

## Ghi chú cuối

Mô hình này là **conceptual complete** — tất cả các khối, cơ chế, luồng đều được định nghĩa. Implementation có thể bắt đầu từ bất kỳ khối nào (ví dụ start từ CEO Agent, hoặc từ Audit Log Service).

Snail giữ document này làm **spec gốc** — nó là source of truth cho mọi design decision và implementation detail tới sau.

---

**Document version**: 1.0  
**Last updated**: Tháng 5, 2026  
**Status**: Ready for implementation planning
