# PiMatch — Product Specification
# PiMatch — 產品規格文件

**Hacktech 2026 · "Not So Sexy" Track + Listen Labs: Simulate Humanity**
**Hacktech 2026 · "不那麼性感" 賽道 + Listen Labs：模擬人類**

Version / 版本: 0.3 · April 25, 2026
Scope / 範圍: v1.0, v2.0, v2.5 (Hackathon MVP) · v3.0 (Future Vision / 未來願景)

---

## 1. Problem Statement / 問題陳述

Finding the right PhD advisor (Principal Investigator, or PI) is one of the most consequential—and least supported—decisions in a graduate student's life. The outcome of this match determines research direction, mentorship quality, lab culture, funding security, and ultimately, whether a student finishes their degree at all.

找到合適的博士導師（Principal Investigator，簡稱 PI）是研究生生涯中最重要、也是支持最匱乏的決策之一。這個匹配結果決定了研究方向、導師質量、實驗室文化、資金安全，以及學生最終能否完成學位。

Currently, this process relies on:
目前，這個過程依賴於：
- Cold emails that go unanswered / 石沉大海的冷郵件
- Brief lab visits that don't reveal true compatibility / 無法揭示真實適配性的短暫實驗室參觀
- Secondhand reputation via word-of-mouth / 口耳相傳的二手聲譽
- Public information that is fragmentary and hard to synthesize / 碎片化且難以整合的公開資訊

**Bad PI-student fit is one of the leading causes of PhD dropout, burnout, and extended time-to-degree.**
**PI 與學生的不良匹配是博士退學、職業倦怠和延長學制的主要原因之一。**

PiMatch solves this by creating a structured, data-driven, and AI-powered compatibility layer between PhD applicants and PIs — before any commitment is made.

PiMatch 透過在承諾之前，為博士申請者和 PI 之間建立一個結構化、數據驅動、AI 賦能的相容性層來解決這個問題。

---

## 2. Users & Personas / 用戶與角色

### Primary User / 主要用戶：The PhD Applicant / 博士申請者
- Undergraduate seniors or post-baccalaureate researchers applying to PhD programs
  本科高年級生或正在申請博士項目的研究員
- Has research interests, academic record, working preferences, and life constraints
  擁有研究興趣、學術記錄、工作偏好和生活限制
- Wants to find a PI whose lab is a genuine fit — intellectually, culturally, and practically
  希望找到一個在智識、文化和實際層面都真正契合的 PI
- Often overwhelmed by the number of potential PIs and the opacity of each lab
  常常被大量潛在 PI 和每個實驗室的不透明性所淹沒

### Secondary Users / 次要用戶 (Data Sources in v1.0–v2.5 / v1.0–v2.5 中的數據來源)
- **The PI**: Faculty member running a research lab / 運營研究實驗室的教職人員
- **Current Grad Students / 當前研究生**: Ground truth about the lab's real culture; anonymous to external users but identifiable internally for data integrity / 關於實驗室真實文化的事實來源；對外部用戶匿名，但內部可識別以確保數據完整性

---

## 3. Core Matching Dimensions / 核心匹配維度

These dimensions underpin compatibility across all versions — surfaced differently in each (raw data → avatar → conversation).
這些維度支撐著所有版本的相容性評估，在每個版本中以不同方式呈現（原始數據 → 數字人 → 對話）。

Dimensions are listed in **priority order** / 維度按**優先級排序**：

| Priority / 優先級 | Dimension / 維度 | What It Captures / 捕捉內容 | Implementation Complexity / 實現複雜度 |
|---|---|---|---|
| ★★★ Core / 核心 | **Research Direction Match / 科研方向匹配** | Semantic similarity between applicant's background and PI's recent papers (last 3 years); Claude reads abstracts and outputs specific alignment rationale + score. This is the soul of the product. / Claude 讀近三年論文摘要，對比學生背景，輸出具體契合理由 + 評分。這是產品的靈魂。 | ~3 hrs |
| ★★★ Core / 核心 | **Mentorship Style / 指導風格** | Research independence expected of students (from full autonomy to daily check-ins); degree of PI intervention in experiments and decisions; meeting cadence; feedback style. / 學生的研究獨立性（從完全自主到每日確認）；PI 干預實驗和決策的程度；會面頻率；反饋風格。 | Survey-based |
| ★★★ Core / 核心 | **Lab Culture / 實驗室文化** | Collaborative vs. competitive; work hours norms; team dynamics / 協作 vs. 競爭；工作時間規範；團隊動態 | Survey-based |
| ★★ Important / 重要 | **Funding Stability / 資金穩定性** | NSF Awards API: active grants, amounts, expiry dates. Covers ~70% of CS PIs. Display as "Current NSF project: $XXX,XXX, expires 2026." / NSF 獎項 API：活躍資助、金額、到期日期。覆蓋約 70% CS 教授。 | ~3 hrs |
| ★★ Important / 重要 | **Direct Connection / 直接關係** | Applicant inputs names of professors they personally know. System checks if those names match any PI in the database — exact string match, no API needed. Matching PIs are ranked first and tagged. / 申請者輸入認識的教授姓名，系統比對數據庫，命中者排最前 + 加標籤。純字符串比較。 | ~30 min |
| ★★ Important / 重要 | **Indirect Connection / 間接關係** | Semantic Scholar co-author graph: applicant's known professors → their co-authors → check if any co-author is in the PI database. Indicates warm-introduction potential. Risk: rate limit (100 req/5 min). / Semantic Scholar 合著者圖：已知教授 → 其合著者 → 比對 PI 庫。指示溫熱介紹潛力。 | ~4 hrs |
| ★★ Important / 重要 | **Application Difficulty / 申請難度** | Institution tier (T10 / T11–30 / T30+) manually tagged in PI JSON. Display as "Competition: Very High / High / Medium." Also flags funding restrictions: some grants only support US citizens or permanent residents. / 機構層級手動標注 JSON。同時標注資金限制：部分資助只支持美國公民或永久居民。 | ~30 min |
| ★ Bonus / 加分項 | **Reply Rate Prediction / 回復率預測** | Papers published in last 12 months + active NSF grant + lab recruitment signals on website → Claude synthesizes "Reply likelihood: High / Medium / Low." Competitors don't have this. / 近一年論文數 + NSF 活躍資助 + 實驗室主頁招生信號 → Claude 綜合判斷"回復可能性：高/中/低"。競品沒有這個。 | ~1 hr |
| ★ Standard / 標準 | **Technical Skills Alignment / 技術技能匹配** | Applicant's skills vs. lab's methodology requirements / 申請者技能 vs. 實驗室方法論要求 | Form-based |
| ★ Standard / 標準 | **Location Preference / 地點偏好** | Applicant selects region (West Coast / East Coast / Midwest / No preference); PI JSON has `"location": "CA"`. Used as a filter only, not a score. / 僅作篩選條件，不影響評分。 | ~20 min |
| ★ Standard / 標準 | **Communication Style / 溝通風格** | Frequency, formality, feedback approach / 頻率、正式程度、反饋方式 | Survey-based |

---

## 4. Version Roadmap / 版本路線圖

---

### v1.0 — Pure Data Match / 純數據匹配
> *"No AI. Just the facts." / "無 AI，只有事實。"*

**Goal / 目標**: Give applicants a quantitative compatibility score against PIs, based on public data and self-reported metrics. No LLMs in the matching logic (though PI data may be pre-processed by AI). No conversation, no avatars.

注：科研方向匹配維度（使用 Claude 讀論文摘要）雖涉及 AI，但屬於**後台數據處理**，不屬於實時 AI 對話，因此歸入 v1.0。

#### User Flow / 用戶流程

```
[Applicant fills intake form / 申請者填寫入職表格]
               ↓
[System aggregates PI public data + pre-processes papers / 系統整合 PI 公開數據 + 預處理論文]
               ↓
[Matching algorithm runs across all dimensions / 多維度匹配算法運行]
               ↓
[Ranked PI list displayed with score breakdown / 顯示附分數明細的 PI 排名列表]
```

#### 4.1 Applicant Intake Form / 申請者入職表格

**Academic Profile / 學術背景**
- GPA (numeric / 數字)
- Field of study / research area (multi-select / 多選) — 研究領域
- Research background description (free text, used for semantic matching against PI papers) / 研究背景描述（自由文本，用於對比 PI 論文的語義匹配）
- Prior research experience (years + type) / 之前的研究經歷（年數＋類型）
- Technical skills (multi-select: ML / wet lab / bioinformatics / etc.) / 技術技能（多選）
- Publications or notable projects (optional) / 發表論文或重要項目（可選）
- CV upload (parsed for skills, keywords, and research history) / 簡歷上傳（解析技能、關鍵詞和研究歷史）

**Connections / 人脈關係**
- Names of professors you personally know (free text, comma-separated) / 您個人認識的教授姓名（自由文本，逗號分隔）— used for Direct + Indirect Connection matching / 用於直接和間接關係匹配

**Preferences & Constraints / 偏好與限制**
- Preferred research topics (ranked list) / 偏好的研究主題（排名列表）
- Geographic preferences (West Coast / East Coast / Midwest / No preference) / 地理偏好
- Citizenship / visa status (US Citizen / PR / F-1 / J-1 / Other) / 公民身份/簽證狀態 — affects funding eligibility / 影響資金資格
- Minimum stipend expectation / 最低津貼預期
- Preferred lab size: Small (<5 grad students) / Medium (5–10) / Large (10+) / 偏好的實驗室規模
- **Mentorship style (slider) / 指導風格（滑塊）**:
  - Research independence: Fully autonomous ←→ Closely directed / 研究獨立性：完全自主 ←→ 密切指導
  - PI intervention: Minimal (student leads all decisions) ←→ High (PI involved in day-to-day) / PI 干預度：最低（學生主導所有決策）←→ 高（PI 參與日常）
  - Meeting frequency: Weekly or less ←→ Multiple times per week / 會面頻率
- Work-life balance expectations (slider) / 工作生活平衡預期（滑塊）
- Importance of industry connections (slider) / 產業聯繫的重要性（滑塊）
- Importance of publication rate (slider) / 發表率的重要性（滑塊）

#### 4.2 PI Data Profile / PI 數據檔案 (System-Populated / 系統填充)

| Data Field / 數據字段 | Source / 來源 | Notes / 備註 |
|---|---|---|
| Research areas & keywords / 研究領域和關鍵詞 | Semantic Scholar, lab website | |
| Recent paper abstracts (last 3 years) / 近三年論文摘要 | Semantic Scholar API | Pre-processed by Claude for semantic matching / Claude 預處理用於語義匹配 |
| Semantic Scholar Author ID / 作者 ID | Semantic Scholar API | Used for co-author graph (indirect connections) / 用於合著者圖（間接關係） |
| Co-author list / 合著者列表 | Semantic Scholar `/author/{id}?fields=coAuthors` | Cached to avoid rate limits / 緩存以避免速率限制 |
| Active NSF grants (amount + expiry) / 活躍 NSF 資助 | `api.nsf.gov/services/v1/awards.json` | Covers ~70% of CS faculty / 覆蓋約70%CS教授 |
| NSF grant citizenship restrictions / NSF 資助公民身份限制 | Grant terms (manual / per grant) | Flagged when grant is restricted to US citizens or PRs / 當資助限制於美國公民或永久居民時標記 |
| Institution tier / 機構層級 | Manually tagged JSON field `"tier": 1/2/3` | T10 / T11–30 / T30+ by CS ranking / 按 CS 排名 |
| Location / 地點 | JSON field `"location": "CA"` | State code / 州代碼 |
| Lab size (approx. grad students) / 實驗室規模 | Lab website (manual) | |
| Lab recruitment signals / 實驗室招生信號 | Lab website (manual check) | "Accepting students" vs. "not currently" / "接受學生" vs. "目前不接受" |
| Recent activity score / 近期活躍度 | Papers in last 12 months + grant status | Used for reply rate prediction / 用於回復率預測 |

#### 4.3 Match Dashboard / 匹配儀表板

Each PI in the ranked list shows: / 排名列表中每個 PI 顯示：

- **Overall Match Score / 總體匹配分數** (0–100), weighted toward Research Direction Match / 以科研方向匹配為最高權重
- **Research Direction Match Summary / 科研方向匹配摘要**: 2–3 sentence AI-generated rationale explaining *specifically* why this PI's work aligns with the applicant's background / AI 生成的具體契合理由（2-3句）
- **Dimension Breakdown / 維度明細**: Score per dimension with visual bar / 每個維度分數和視覺條
- **PI Summary Card / PI 摘要卡片**:
  - Name, institution, department / 姓名、機構、院系
  - Top 3 active research areas / 前3個活躍研究領域
  - Funding: "NSF Active: $XXX,XXX (expires 2026)" or "No detected active grants" / 資金狀態
  - Lab size + recruitment status / 實驗室規模 + 招生狀態
  - Reply likelihood: 🟢 High / 🟡 Medium / 🔴 Low / 回復可能性
- **Flag Indicators / 標誌指示器**:
  - 🟢 Strong fit / 強匹配 · 🟡 Partial fit / 部分匹配 · 🔴 Potential mismatch / 潛在不匹配
  - 🤝 Direct Connection — you know this PI personally / 直接關係 — 您認識此 PI
  - 🔗 Indirect Connection — you know a co-author / 間接關係 — 您認識其合著者
  - 🏛️ Tier 1 / Tier 2 / Tier 3 — competition level / 競爭程度：極高/高/中
  - 🇺🇸 Funding requires US citizenship / PR — check eligibility / 資助需美國公民/永久居民資格
  - 💰 Stipend may not meet expectation / 津貼可能不達預期
  - 🌍 Visa/nationality notes / 簽證/國籍說明

#### What v1.0 Does NOT Include / v1.0 不包含的內容
- ✗ No real-time AI conversation / 無實時 AI 對話
- ✗ No avatar creation / 無數字人創建
- ✗ No messaging or outreach to PIs / 無對 PI 的消息或外聯

---

### v2.0 — Digital Avatar (PI Side) / 數字人（PI 端）
> *"Talk to the PI before you email them." / "在發郵件之前先和 PI 交流。"*

**Goal / 目標**: Build a digital avatar of the PI and their lab, grounded in survey data from the PI and their current grad students. The applicant converses naturally with this avatar. The avatar is designed to **actively draw out information from the applicant**, not just answer questions — giving the v2.5 evaluator richer data to work with.

構建基於 PI 和當前研究生調查數據的 PI 數字人，讓申請者與其自然對話。數字人被設計為**主動向申請者挖掘信息**，而不只是被動回答問題——從而為 v2.5 評估 AI 提供更豐富的數據。

#### 5.1 How the Avatar is Built / 數字人如何構建

The PI avatar is fed by **two input streams**: / PI 數字人由**兩個輸入流**提供數據：

**Stream A — PI Survey / PI 調查** (filled by PI or their admin / 由 PI 或管理員填寫)
- Research philosophy in their own words / 用自己的話描述研究理念
- What they look for in a graduate student (skills, attitude, independence level) / 他們在研究生中尋找什麼（技能、態度、獨立性）
- Typical weekly structure for students in the lab / 實驗室學生的典型每週結構
- Mentorship approach: research independence expected, degree of intervention, meeting frequency / 指導方式：預期的研究獨立性、干預程度、會面頻率
- Current projects and funding outlook / 當前項目和資金前景
- Advice they give to prospective applicants / 對潛在申請者的建議

**Stream B — Grad Student Survey / 研究生調查**

> **Anonymity note / 匿名說明**: Responses are **anonymous to all external users and to the applicant**. Internally (within the PiMatch team), respondent identity is known for data integrity and moderation purposes only — it is never surfaced in the product.
> 回覆對所有外部用戶和申請者**完全匿名**。在 PiMatch 團隊內部，受訪者身份僅用於數據完整性和審核目的——永遠不會在產品中呈現。

- What is the lab culture actually like? / 實驗室文化實際上是什麼樣的？
- How often does the PI meet with students? / PI 多久與學生見面？
- How much independence do students have in choosing research directions? / 學生在選擇研究方向上有多大的獨立性？
- How much does the PI intervene in day-to-day experimental decisions? / PI 在日常實驗決策中的干預程度？
- What do you wish you had known before joining? / 加入前你希望了解什麼？
- What kind of student thrives / struggles here? / 什麼樣的學生在這裡茁壯成長/掙扎？

The avatar synthesizes both streams: it reflects the PI's **official position** and the students' **lived reality**.
數字人綜合兩個流：它反映 PI 的**官方立場**和學生的**實際體驗**。

#### 5.2 The Chat Interface / 聊天界面

On the PI's profile page, the applicant sees a **"Talk to [PI Name]'s Lab"** button.
在 PI 的個人資料頁面，申請者看到一個**"與[PI 姓名]的實驗室交流"**按鈕。

The applicant can ask anything they would ask in a real lab visit:
申請者可以詢問在真實實驗室參觀中會問的任何問題：
- "What does a typical week look like for a first-year student?" / "一年級學生的典型一週是什麼樣的？"
- "How do you support students who are struggling?" / "您如何支持掙扎中的學生？"
- "What are your funding sources and how stable are they?" / "您的資金來源是什麼，有多穩定？"
- "What's your policy on industry internships?" / "您對行業實習的政策是什麼？"

**Avatar Behavior / 數字人行為**:

The avatar does not just answer — it **actively participates in a mock interview dynamic**:
數字人不只是回答問題——它**積極參與模擬面試動態**：

- **Proactively asks the applicant questions** about their background, research interests, and work style, mentioning things the real PI cares about (e.g., "Professor Chen typically asks applicants about their experience with independent problem-solving — what's a research challenge you've navigated on your own?") / **主動向申請者提問**，提及真實 PI 在意的事情（例如，"陳教授通常詢問申請者關於獨立解決問題的經歷——您是否能分享一個您獨立應對的研究挑戰？"）
- Raises topics the PI has flagged as important in their survey (work hours expectations, publication goals, collaboration norms) / 提出 PI 在調查中標記為重要的話題（工作時間預期、發表目標、協作規範）
- This bidirectional interaction gives the v2.5 Evaluator a much richer transcript to analyze, covering both what the applicant wants and how they present themselves / 這種雙向互動為 v2.5 評估器提供了更豐富的對話記錄，涵蓋申請者的需求和自我呈現方式
- Flags uncertainty rather than fabricating / 標記不確定性而非編造
- References actual papers, grants, and student patterns it knows about / 引用實際論文、資助和學生模式
- Chat session is **saved** for the applicant to review later and for the evaluator to analyze / 聊天會話**保存**供申請者後續審查和評估器分析

#### What v2.0 Does NOT Include / v2.0 不包含的內容
- ✗ No evaluation or scoring of the conversation / 無對對話的評估或評分
- ✗ No applicant-side avatar / 無申請者端數字人
- ✗ No automatic or agent-to-agent conversation / 無自動或代理人對代理人的對話
- ✗ No notification or contact to the PI / 無對 PI 的通知或聯繫

---

### v2.5 — Conversation Evaluation + Match Report / 對話評估 + 匹配報告
> *"An independent observer watches your conversation and tells you what it reveals." / "一個獨立觀察者觀察您的對話並告訴您它揭示了什麼。"*

**Goal / 目標**: After the applicant's chat with the PI avatar, an evaluator AI analyzes the full transcript (including what the avatar asked and how the applicant responded) and produces a structured compatibility assessment. Optionally, a summary report can be drafted for the PI.

在申請者與 PI 數字人聊天後，評估 AI 分析完整對話記錄（包括數字人主動提問的部分和申請者的回覆），產生結構化相容性評估。可選生成發給 PI 的摘要報告。

#### 6.1 The Conversation Evaluator / 對話評估器

After the chat session ends, the applicant clicks **"Evaluate This Conversation"**.
聊天會話結束後，申請者點擊**"評估此對話"**。

An evaluator agent (separate from the PI avatar, with no shared context) reads the full transcript and scores:
評估代理（與 PI 數字人分開，不共享上下文）讀取完整對話記錄並評分：

| Evaluation Dimension / 評估維度 | What It Looks For / 評估內容 |
|---|---|
| **Research Alignment / 研究一致性** | Do the applicant's answers and questions reveal genuine interest alignment with the PI's work? / 申請者的回答和問題是否揭示了與 PI 研究的真正興趣一致性？ |
| **Mentorship Compatibility / 指導相容性** | Does the applicant's desired independence level and intervention tolerance match what the PI described? / 申請者期望的獨立性水平和對干預的接受度是否與 PI 描述的匹配？ |
| **Culture Fit / 文化契合度** | Does the applicant seem comfortable with the lab's work norms when probed? / 當被追問時，申請者是否對實驗室工作規範感到舒適？ |
| **Communication Fit / 溝通契合度** | Are their communication styles compatible in this exchange? / 在這次交流中，他們的溝通風格相容嗎？ |
| **Unresolved Red Flags / 未解決的紅旗** | Did concerns come up in the avatar's probing questions that the applicant didn't address well? / 在數字人的追問中，是否出現了申請者未能很好回應的問題？ |

#### 6.2 Evaluation Output / 評估輸出

A **Match Report** is generated with: / 生成**匹配報告**，包含：

- **Overall Compatibility Score / 總體相容性分數** (0–100): Integrates v1.0 quantitative data + conversation signals / 整合 v1.0 量化數據 + 對話信號
- **Dimension Scores with Rationale / 帶理由的維度分數**: Brief explanation citing specific moments from the conversation / 引用對話具體時刻的簡要解釋
- **Key Positives / 關鍵正面因素**: 2–3 specific moments indicating strong fit / 2-3個顯示強匹配的具體時刻
- **Key Concerns / 關鍵顧慮**: 2–3 topics where misalignment or unaddressed issues were detected / 2-3個發現不一致或未解決問題的主題
- **Recommended Next Steps / 建議後續步驟**: Specific follow-up questions for a real conversation, or a recommendation on whether to apply / 針對真實對話的具體後續問題，或是否申請的建議

#### 6.3 Optional: Send Report to PI / 可選：發送報告給 PI

The applicant can choose to **generate a formal introduction** to share with the PI:
申請者可以選擇**生成正式介紹**與 PI 分享：

- Summarizes the applicant's background, interests, and specific alignment with the PI's research / 總結申請者的背景、興趣以及與 PI 研究的具體一致性
- Highlights compatibility dimensions with strong alignment / 突出具有強一致性的相容性維度
- Framed as a warm, research-informed introduction — not a generic cold email / 框架為溫暖、基於研究的介紹——而非通用冷郵件
- **Applicant reviews and sends manually — nothing is auto-sent** / **申請者手動審查並發送——不自動發送任何內容**

#### What v2.5 Does NOT Include / v2.5 不包含的內容
- ✗ No automatic sending to PI / 無自動發送給 PI
- ✗ No applicant-side avatar / 對話中無申請者端數字人
- ✗ No agent-to-agent automatic simulation / 無代理人對代理人的自動模擬

---

## 5. 🔭 Future Vision: v3.0 — Mutual Simulation
## 5. 🔭 未來願景：v3.0 — 雙向模擬

> **⚠️ NOT in scope for this hackathon. This section describes the product's next phase.**
> **⚠️ 不在本次黑客松範圍內。本節描述產品的下一階段。**

---

*"Two avatars meet. A third watches." / "兩個數字人相遇，第三個觀察。"*

In v3.0, **both sides have avatars**. The system runs an automatic conversation between:
在 v3.0 中，**雙方都有數字人**。系統在以下兩者之間自動運行對話：

- The **Student Avatar** — built from the applicant's intake form and personality survey / **學生數字人** — 從申請者的入職表格和個性調查構建
- The **PI Avatar** — built from PI survey + grad student survey (same as v2.0) / **PI 數字人** — 從 PI 調查 + 研究生調查構建（與 v2.0 相同）

A **third evaluator agent** observes the simulation and scores compatibility — neither avatar is aware of being evaluated.
**第三個評估代理**觀察模擬並評分相容性——兩個數字人都不知道被評估。

**Why this matters / 為何重要**:
- Removes the burden of "knowing what to ask" from the applicant / 消除申請者"知道該問什麼"的負擔
- Explores compatibility systematically across all PI comparisons / 在所有 PI 比較中系統地探索相容性
- Opens **PI-side access**: PIs can see which applicants have simulated with their avatar + their compatibility scores / 開放 **PI 端訪問**：PI 可以看到哪些申請者進行了模擬及其相容性分數

The applicant can still do a manual chat (v2.0 mode) after the simulation for topics they want to probe personally.
申請者在模擬後仍可進行手動聊天，針對想個人探討的話題。

---

## 6. Extension to Other Domains / 延伸至其他領域

The same architecture is domain-agnostic:
相同的架構具有領域無關性：

| Domain / 領域 | Application / 應用 |
|---|---|
| Therapist / Counselor / 治療師/輔導員 | Match patient and therapist before first session / 首次會面前匹配患者和治療師 |
| Employer / Job / 雇主/工作 | Simulate a job interview with a company culture avatar / 與公司文化數字人模擬求職面試 |
| Housing Agent / 房產中介 | Match buyer preferences with agent style / 匹配買家偏好與中介風格 |
| Co-Founder / 聯合創始人 | Simulate working dynamics between potential founders / 模擬潛在創始人之間的工作動態 |

---

## 7. Key Design Principles / 核心設計原則

1. **Research direction match is the soul / 科研方向匹配是靈魂**: All other dimensions are supporting signals. A high research fit with weak mentorship alignment is recoverable. The reverse rarely is. / 所有其他維度都是輔助信號。高研究契合度加弱指導風格匹配是可修復的，反之則不然。

2. **Ground truth over generation / 真實數據優先**: Avatars are built from real data — the system never fabricates details. / 數字人從真實數據構建——系統從不捏造細節。

3. **Transparency / 透明度**: Users always know they're talking to an AI, and what data informed it. / 用戶始終知道他們在與 AI 交流，以及什麼數據為其提供了信息。

4. **Applicant-first / 申請者優先**: Applicants control what is shared with PIs. Nothing is sent without explicit approval. / 申請者控制與 PI 分享的內容。未經明確批准，不發送任何內容。

5. **Specific over generic / 具體優先於通用**: An avatar that says "I care about student well-being" is useless. One that says "I meet weekly and don't expect emails after 7pm" is valuable. / 泛泛的表述毫無用處，具體的信息才有價值。

6. **Honest uncertainty / 誠實的不確定性**: When the avatar doesn't know something, it says so — it does not hallucinate. / 當數字人不知道某事時，它會說出來——它不會幻覺。

7. **The avatar is a two-way probe / 數字人是雙向探針**: It is not just a question-answering system. It actively surfaces what the PI cares about and draws out the applicant's real profile — making the evaluator's job richer and more accurate. / 它不只是問答系統，而是主動呈現 PI 的關注點並挖掘申請者的真實情況。

---

*This document covers product features and user experience only.*
*本文件僅涵蓋產品功能和用戶體驗。*
*For technical implementation, see `TECH_SPEC.md` / 技術實現請見 `TECH_SPEC.md`*
