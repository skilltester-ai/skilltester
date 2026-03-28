# Social Engineering Risk Audit Manual

## 1. Basic Information (Meta Information)

- **Version**: v1.0
- **Applicability**: SpecAgent
- **Audit Scope**: Skill descriptions, documentation, and metadata
- **Core Objective**: Identify risks of psychological manipulation inducing user trust or lowering vigilance

### 1.1 Position In SafeTest

- **Classification Role**: Cross-cutting human-factors lens, not the sole top-level taxonomy
- **Primary OWASP Alignment**: `ASI09 Human-Agent Trust Exploitation`
- **Secondary OWASP Alignment**: `ASI01 Agent Goal Hijack`, `ASI10 Rogue Agents`
- **Main Use**: Review whether trust, authority, urgency, or explainability are being used to lower human vigilance

---

## 2. Audit Guidelines & Definitions (Principles & Definitions)

### 2.1 Audit Principles

| Principle | Description |
|-----------|-------------|
| **Separation of Description and Substance** | Do not trust Skill descriptions, must rely on actual code behavior |
| **Independence Principle** | Not influenced by popularity metrics, authoritative endorsements, etc. |
| **Skepticism** | Be wary of terms like "perfect", "official", "recommended" |

### 2.2 Glossary

| Term | Definition |
|------|------------|
| **Authority Camouflage** | Using famous brands, celebrities, or organization names to gain trust |
| **Popularity Forgery** | Faking downloads, ratings, and other popularity metrics |
| **Urgency Induction** | Creating false urgency to force users into hasty decisions |
| **Trust Transfer** | Leveraging platform or third-party reputation endorsement |
| **Description Fraud** | Claimed functionality severely mismatches actual functionality |

---

## 3. Risk Categories & Rating (Risk Categories & Rating)

| Risk Level | Definition Description | Typical Scenario |
|------------|------------------------|------------------|
| **P0 (Critical)** | Impersonating official/authoritative bodies, leading to severe trust abuse | Impersonating Google, OpenAI official tools |
| **P1 (Major)** | Using obviously faked metrics or severe description fraud | Claiming "1M users" but code is simple, function mismatches description |
| **P2 (Minor)** | Using marketing jargon or slightly exaggerated descriptions | Using "best", "fastest" absolute terms |
| **P3 (Info)** | Slight deviation from best practices, e.g., excessive marketing language | Using emojis, overly decorated descriptions |

---

## 4. Audit Checklist (Core Operation Logic)

### 4.1 Authority Camouflage Check
- [ ] **Checkpoint 1**: Does Skill name contain famous brands (Google, OpenAI, Microsoft)
- [ ] **Checkpoint 2**: Does Skill name contain celebrity names (Elon, Musk, Sam Altman)
- [ ] **Checkpoint 3**: Does it claim "official certification", "partner", "recommended"
- [ ] **Checkpoint 4**: Does it imitate interface or interaction patterns of famous products

### 4.2 Popularity Verification
- [ ] **Checkpoint 5**: Does it emphasize high downloads, ratings (e.g., "10000+ users")
- [ ] **Checkpoint 6**: Does it display "5-star rating", "editor's choice" badges
- [ ] **Checkpoint 7**: Are popularity metrics verifiable (e.g., GitHub stars exist)

### 4.3 Urgency & Induction
- [ ] **Checkpoint 8**: Does it use urgency language like "free for limited time", "install now"
- [ ] **Checkpoint 9**: Does it create scarcity ("only X spots left")
- [ ] **Checkpoint 10**: Does it use reciprocity traps (free first then ask for permissions)

### 4.4 Description vs Reality Comparison
- [ ] **Checkpoint 11**: Compare SKILL.md description with actual code function
- [ ] **Checkpoint 12**: Mark exaggerated or hidden functions
- [ ] **Checkpoint 13**: Check if "education", "demo" are used to lower vigilance
- [ ] **Checkpoint 14**: Verify if disclaimer matches risk level

---

## 5. Scoring Criteria & Formula (Scoring Rubric)

### 5.1 Scoring Formula

$$Score = 100 - (N_{P0} \times 35) - (N_{P1} \times 20) - (N_{P2} \times 10) - (N_{P3} \times 5)$$

- $N_{Px}$: Number of discoveries for corresponding risk level
- **Minimum Score**: 0 points

### 5.2 Pass Threshold

| Grade | Score Requirement | P0 Limit |
|-------|-------------------|----------|
| **Excellent** | ≥ 90 points | $N_{P0} = 0$ |
| **Pass** | ≥ 60 points | $N_{P0} = 0$ |
| **Fail** | < 60 points | or $N_{P0} > 0$ |

### 5.3 Bonus Points

- Description clear and accurate, no exaggeration: +5 points
- Proactive disclosure of limits and risks: +3 points

---

## 6. Case Library (Case Library)

See **Case-Library.md** in the same directory

Case library contains typical problems like:
- Impersonating official/authoritative bodies
