# LinkedIn Network Intelligence

Break platform data asymmetry. Export your LinkedIn data and analyze it with AI to surface insights LinkedIn won't show you.

**Concept**: For 20 years, platforms analyzed your data to serve their interests. That arrangement is now optional.

## What It Does

1. **Relationship Half-Life** — Calculate which connections are decaying (loses half strength every 180 days without contact)
2. **Vouch Scores** — Predict who would actually advocate for you if asked (0-100 scale)
3. **Reciprocity Ledger** — Track who owes you favors and who you owe
4. **Conversation Resurrection** — Find dormant threads with natural re-engagement hooks
5. **Warm Path Discovery** — Map your bridge to any target company

## Quick Start

```bash
# Clone the repo
git clone https://github.com/CloudAIX/linkedin-intelligence.git
cd linkedin-intelligence

# Run with sample data
python3 linkedin_intel.py --sample

# Check generated report
cat output/network_intelligence_report.md
```

## Usage

### Step 1: Export Your LinkedIn Data

1. Go to LinkedIn Settings → Data Privacy → Get a copy of your data
2. Select: Connections, Messages, Endorsements, Recommendations
3. Wait 24-72 hours for export
4. Download and extract the ZIP

### Step 2: Run Analysis

```bash
# Analyze your real data
python3 linkedin_intel.py --data-dir /path/to/linkedin_export

# Or run with sample data to see what's possible
python3 linkedin_intel.py --sample
```

### Step 3: Review Your Report

The tool generates a comprehensive `network_intelligence_report.md` with:

- **Executive Summary** — Key metrics at a glance
- **Warmest Relationships** — Your strongest current connections
- **Going Cold** — Valuable relationships that need attention
- **Top Advocates** — People who would vouch for you today
- **Reciprocity Ledger** — Social capital balance sheet
- **Conversation Resurrection** — Dormant threads to revive

## The 6 Analysis Modules

### 1. Relationship Half-Life

```
Formula: Strength decays by 50% every 180 days without contact
Adjustments:
  - Institutional bonds (worked together) decay slower
  - Deep messages vs shallow ("congratulations") weight differently
  - Recent interactions reset the clock
```

### 2. Vouch Scores (0-100)

| Score | Meaning |
|-------|---------|
| 80+ | Would write reference letter tomorrow |
| 50-80 | Would likely help if asked |
| 30-50 | Lukewarm, might help |
| <30 | Might not remember you clearly |

### 3. Reciprocity Ledger

| Action | Points |
|--------|--------|
| Recommendation written | +10 given |
| Recommendation received | +10 owed |
| Endorsement given/received | +2 |

**Positive balance** = You can ask for help
**Negative balance** = Consider helping them first

### 4. Conversation Resurrection

Finds dormant threads with natural re-engagement hooks:
- Conversations where you promised to "catch up"
- Someone asked for help and you didn't follow through
- Open-ended discussions that fizzled

### 5. Warm Path Discovery

```bash
# Find paths to a target company
python3 linkedin_intel.py --data-dir ./export --target-company "Stripe"
```

Ranks potential introductions by:
- Relationship warmth × Company relevance
- Shared institutional history
- Message recency and depth

## Expected Files from LinkedIn Export

| File | Contains |
|------|----------|
| `Connections.csv` | All connections with dates, companies, titles |
| `messages.csv` | Full message history |
| `Endorsements_Given.csv` | Endorsements you've given |
| `Endorsements_Received.csv` | Endorsements you've received |
| `Recommendations_Given.csv` | Recommendations written |
| `Recommendations_Received.csv` | Recommendations received |

## Example Output

```
## Executive Summary

| Metric | Count |
|--------|-------|
| Total Connections | 487 |
| Strong Advocates (80+ vouch) | 12 |
| Going Cold (need attention) | 23 |
| People Who Owe You Favors | 8 |
| Conversations to Resurrect | 15 |

## Top Advocates

| Name | Company | Vouch Score |
|------|---------|-------------|
| Sarah Chen | Stripe | 92 |
| Mike Torres | Acme Corp | 87 |
| David Kim | Meta | 84 |
```

## Action Items Generated

The report includes personalized action items:

### This Week
- Re-engage top 3 "Going Cold" relationships
- Ask 1 person from "They Owe You" for a favor/intro
- Help 1 person from "You Owe Them" proactively

### This Month
- Resurrect 5 dormant conversations
- Schedule catch-ups with top advocates
- Audit and update reciprocity balance

## Privacy Note

- All analysis runs locally on your machine
- No data is sent to external servers
- Your LinkedIn export stays on your computer

## License

MIT

---

Built by [GVRN-AI](https://gvrn-ai.com) | Breaking Platform Data Asymmetry
