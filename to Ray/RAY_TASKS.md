# Ray 的任務分工
# PiMatch · Hacktech 2026

Alex 負責全部 v1.0 後端架構和 API。你負責下面三件事，兩件 block Alex 的進度，請按優先順序做。

---

## 任務一：Caltech PI 種子數據 🔴 最高優先，馬上開始

**文件位置**: `data/seeds/caltech_pis.json`

Alex 的 matching 算法寫好以後，沒有真實 PI 數據就沒辦法測試和 demo。這件事不需要寫代碼，需要你去查真實資料手寫 JSON。

### 目標
5 個真實 Caltech PI（CS 或 Bio 方向），每個 PI 一個 JSON 對象。

### 每個 PI 需要包含的字段

```json
{
  "name": "Katherine Bouman",
  "institution": "Caltech",
  "department": "Computing and Mathematical Sciences",
  "email": "klbouman@caltech.edu",
  "lab_website": "https://computationalcameras.org",
  "tier": 1,
  "location": "CA",
  "lab_size": 8,
  "is_recruiting": true,

  "research_areas": [
    "computational imaging",
    "inverse problems",
    "computer vision",
    "black hole imaging"
  ],

  "recent_abstracts": [
    "We present a method for reconstructing images from sparse interferometric measurements...",
    "Event Horizon Telescope imaging pipeline uses regularized maximum likelihood...",
    "..."
  ],

  "nsf_grants": [
    {
      "title": "Computational Imaging for Extreme Environments",
      "amount": 500000,
      "expiry_date": "2026-08-31",
      "citizen_only": false
    }
  ],
  "has_active_nsf_grant": true,
  "total_active_funding_usd": 500000,
  "funding_citizen_restricted": false,

  "semantic_scholar_id": "optional, fill if easy to find",
  "co_author_ids": [],
  "papers_last_12_months": 3,
  "reply_likelihood": null,

  "pi_survey": {
    "research_philosophy": "I believe in tackling problems at the intersection of math and real-world imaging challenges...",
    "what_i_look_for": "Students with strong mathematical foundations and curiosity about how images encode information...",
    "typical_student_week": "Monday group meeting, independent research Tue–Thu, Friday one-on-ones...",
    "mentorship_approach": "I meet weekly with each student. I give significant independence but expect clear communication...",
    "funding_outlook": "Currently funded through 2026 with NSF grant. Actively applying for renewal...",
    "advice_to_applicants": "Come in knowing what problem excites you. Read our recent papers before reaching out..."
  },

  "student_survey_responses": [
    {
      "lab_culture": "Collaborative and supportive. People share code and ideas freely.",
      "meeting_frequency": "Weekly one-on-ones + Monday group meeting",
      "independence": "High. Professor trusts you to run your own experiments.",
      "wished_i_knew": "The project scope can shift quickly — be flexible.",
      "thrives_here": "Self-starters who like ownership over their research direction.",
      "struggles_here": "Students who need frequent validation or very structured guidance."
    },
    {
      "lab_culture": "Small and tight-knit. Everyone knows what everyone else is working on.",
      "meeting_frequency": "Weekly, sometimes biweekly when professor is traveling.",
      "independence": "Very high. After first 6 months, you're mostly self-directing.",
      "wished_i_knew": "Publishing timeline is longer than expected — first paper took 18 months.",
      "thrives_here": "People with a mix of theory and implementation skills.",
      "struggles_here": "Students who prefer very applied work without mathematical depth."
    }
  ]
}
```

### 資料從哪裡找

| 需要什麼 | 去哪找 |
|---|---|
| 論文摘要 | Google Scholar → 搜 PI 名字 → 複製近3年論文的 Abstract |
| NSF 資助 | nsf.gov/awardsearch → 搜 PI 姓氏 → 看 Active Awards |
| Lab 規模 | PI 的 lab website → Team 頁面數人頭 |
| pi_survey | 根據 lab website / 論文風格 / 公開訪談推測，合理即可 |
| student_survey_responses | 完全虛構，但要真實（參考 Glassdoor 風格） |

### 必須滿足的 demo 條件
- 至少 1 個 PI 的 NSF 資助有 `citizen_only: true`（觸發 🇺🇸 flag）
- 至少 1 個 PI 是 Alex 或其他 demo 學生的「已知教授」的合著者（觸發 🔗 間接連結）
- 所有 5 個 PI 的 research_areas 要覆蓋不同子領域（不要全是 CV，要有多樣性）

---

## 任務二：Research Match Agent 🔴 高優先，和任務一並行

**文件位置**: `agents/research_match.py`

這是整個產品最核心的 AI 功能。Alex 的 matching 算法會直接調用你這個函數。

### 函數簽名（不能改）

```python
def score_research_fit(
    student_background: str,
    pi_abstracts: list[str],
    pi_research_areas: list[str]
) -> tuple[float, str]:
    """
    Returns: (score: float 0–100, rationale: str)
    """
```

### 你需要做的

1. 寫一個 Claude prompt，讓它讀 PI 近三年論文摘要，對比學生研究背景，輸出分數 + 具體理由
2. 理由必須具體（"Your background in protein structure prediction aligns with Dr. X's 2024 paper on AlphaFold applications" — not "Your interests seem related"）
3. 輸出格式必須是 JSON：`{"score": 78.5, "rationale": "..."}`
4. 用 try/except 包住 `json.loads()`，失敗時 fallback score = 50

### Claude API 調用方式

```python
import anthropic
import json
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def score_research_fit(student_background, pi_abstracts, pi_research_areas):
    abstracts_text = "\n\n".join(pi_abstracts)
    
    prompt = f"""You are evaluating the research fit between a PhD applicant and a PI.

PI's research areas: {', '.join(pi_research_areas)}

PI's recent paper abstracts (last 3 years):
{abstracts_text}

Applicant's research background:
{student_background}

Score the research fit from 0–100. Be specific — cite actual paper topics and the applicant's specific background. Do not use generic phrases.

Respond ONLY with valid JSON: {{"score": float, "rationale": str}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.content[0].text)
        return float(result["score"]), result["rationale"]
    except Exception:
        return 50.0, "Unable to compute research fit score."
```

---

## 任務三：PI Avatar Builder 🟡 在任務一二完成後再做

**文件位置**: `agents/pi_avatar.py`

這是 v2.0 的基礎。Alex 的 v1.0 完成後，他需要這個來繼續做 v2.0。

### 函數簽名（不能改）

```python
def build_pi_avatar(pi_profile: dict) -> str:
    """
    Returns: system prompt string for the PI avatar
    """
```

### 要求

- 返回一個 system prompt，讓 Claude 扮演這個 PI
- Avatar 說話要具體（引用真實論文名、資助項目名）
- Avatar 每次回覆必須問申請者 1 個問題（這是 demo 的關鍵互動）
- Avatar 遇到不知道的事情要說"我不確定，建議你直接聯繫我" — 絕不捏造
- System prompt 要融合 pi_survey（官方聲音）和 student_survey_responses（真實體驗，匿名）

---

## 接口約定（你的函數，Alex 會調用）

```python
# Alex 會這樣調用你的代碼：

from agents.research_match import score_research_fit
score, rationale = score_research_fit(student_bg, abstracts, areas)

from agents.pi_avatar import build_pi_avatar
system_prompt = build_pi_avatar(pi_profile_dict)
```

不要改函數名或簽名。

---

## 時間目標

| 時間 | 目標 |
|---|---|
| 現在 → 凌晨 3AM | 任務一完成（5 個 PI 的 JSON） + 任務二完成（research_match.py 測試通過） |
| 上午 6AM | 任務三完成（pi_avatar.py） |
| 上午 9AM | Alex 的 v1.0 跑通，你開始配合他 debug |
