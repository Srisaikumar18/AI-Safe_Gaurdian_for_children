# 🔄 DATABASE MIGRATION GUIDE - Enhanced Schema

## OVERVIEW

Your continuous learning system has been upgraded with an **enhanced database schema** that provides:
- Better tracking of toxic words with severity levels
- Safe word whitelist for positive content
- Improved training data metadata
- Enhanced analytics capabilities

---

## 📊 NEW DATABASE SCHEMA

### 1. **training_data** (Enhanced from `training_samples`)

```sql
CREATE TABLE training_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,                    -- Links to video/audio session
    transcript_text TEXT NOT NULL,      -- Full transcribed text
    word_count INTEGER,                 -- Number of words
    toxic_words_detected TEXT,          -- JSON array of toxic words
    safety_label TEXT NOT NULL,         -- 'safe', 'toxic', 'unsafe'
    human_reviewed BOOLEAN DEFAULT FALSE,
    human_label TEXT,                   -- Human-corrected label
    confidence_score FLOAT,             -- Model confidence
    created_at TIMESTAMP,
    source_type TEXT,                   -- 'video', 'audio', 'chat'
    model_version TEXT,                 -- Which model made prediction
    was_corrected BOOLEAN,
    correction_label TEXT               -- Corrected label if wrong
);
```

**Key Improvements:**
- ✅ Tracks word count for each transcript
- ✅ Stores detected toxic words as JSON
- ✅ Supports human review workflow
- ✅ Links to specific session IDs
- ✅ Records which model version was used

---

### 2. **toxic_words** (NEW)

```sql
CREATE TABLE toxic_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE NOT NULL,
    severity TEXT NOT NULL,             -- 'low', 'medium', 'high', 'critical'
    occurrence_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP,
    context_examples TEXT,              -- JSON array of example sentences
    for_children BOOLEAN DEFAULT TRUE   -- Child safety specific
);
```

**Features:**
- ✅ Tracks frequency of each toxic word
- ✅ Severity classification
- ✅ Context examples for better understanding
- ✅ Automatically updated on every analysis
- ✅ Helps identify emerging toxic slang

**Example Data:**
```
| word     | severity | occurrence_count | last_seen           | context_examples          |
|----------|----------|------------------|---------------------|---------------------------|
| stupid   | medium   | 47               | 2026-04-03 10:15:00 | ["You are stupid", ...]   |
| hate     | high     | 23               | 2026-04-03 09:30:00 | ["I hate you", ...]       |
| idiot    | medium   | 31               | 2026-04-02 18:45:00 | ["Don't be an idiot", ...]|
```

---

### 3. **safe_words** (NEW)

```sql
CREATE TABLE safe_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE NOT NULL,
    category TEXT,                      -- 'educational', 'positive', 'neutral'
    occurrence_count INTEGER DEFAULT 1
);
```

**Purpose:**
- ✅ Builds whitelist of safe vocabulary
- ✅ Categorizes words by type
- ✅ Tracks usage frequency
- ✅ Helps reduce false positives

**Example Data:**
```
| word       | category     | occurrence_count |
|------------|--------------|------------------|
| excellent  | positive     | 15               |
| learn      | educational  | 28               |
| friend     | positive     | 42               |
| teacher    | educational  | 19               |
```

---

### 4. **model_versions** (Enhanced)

```sql
CREATE TABLE model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    trained_on DATE NOT NULL,
    accuracy FLOAT,
    precision FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    is_active BOOLEAN DEFAULT FALSE,
    training_samples_count INTEGER,     -- How many samples trained on
    model_path TEXT,
    vectorizer_path TEXT,
    notes TEXT                          -- Version changelog
);
```

**Improvements:**
- ✅ Tracks number of training samples per version
- ✅ Stores file paths for models
- ✅ Supports version notes/changelog
- ✅ Clear active/inactive status

---

## 🚀 MIGRATION PROCESS

### Automatic Migration

The system **automatically migrates** when you restart:

```python
# Old tables will be preserved
# New tables created alongside
# Data automatically copied over
```

### Manual Migration (If Needed)

```sql
-- 1. Create new tables
CREATE TABLE training_data_new AS SELECT * FROM training_samples;
ALTER TABLE training_data_new RENAME TO training_data;

-- 2. Migrate existing data
INSERT INTO training_data (transcript_text, safety_label, confidence_score, source_type)
SELECT text_content, label, confidence, source
FROM training_samples;

-- 3. Verify migration
SELECT COUNT(*) FROM training_data;
SELECT COUNT(*) FROM training_samples;
```

---

## 📈 ENHANCED ANALYTICS

### New Metrics Available:

#### 1. **Toxic Word Tracking**
```json
{
  "toxic_words_tracked": 127,
  "top_toxic_words": [
    {"word": "stupid", "severity": "medium", "occurrence_count": 47},
    {"word": "hate", "severity": "high", "occurrence_count": 23},
    {"word": "idiot", "severity": "medium", "occurrence_count": 31}
  ]
}
```

#### 2. **Safe Word Tracking**
```json
{
  "safe_words_tracked": 543,
  "safe_word_categories": {
    "positive": 312,
    "educational": 156,
    "neutral": 75
  }
}
```

#### 3. **Source Distribution**
```json
{
  "source_distribution": [
    {"source_type": "video", "count": 234},
    {"source_type": "audio", "count": 156},
    {"source_type": "chat", "count": 97}
  ]
}
```

#### 4. **Human Review Stats**
```json
{
  "human_reviewed_count": 45,
  "correction_rate": 0.08
}
```

---

## 🔍 NEW QUERIES & INSIGHTS

### Trending Toxic Words

```sql
-- Get toxic words increasing in frequency
SELECT word, severity, occurrence_count, last_seen
FROM toxic_words
WHERE last_seen > datetime('now', '-7 days')
ORDER BY occurrence_count DESC
LIMIT 10;
```

### Emerging Patterns

```sql
-- Find new toxic words appearing this week
SELECT word, MIN(last_seen) as first_appearance
FROM toxic_words
GROUP BY word
HAVING first_appearance > datetime('now', '-7 days');
```

### Safety by Source

```sql
-- Compare safety across different content types
SELECT 
    source_type,
    COUNT(*) as total,
    SUM(CASE WHEN safety_label = 'safe' THEN 1 ELSE 0 END) as safe_count,
    SUM(CASE WHEN safety_label IN ('toxic', 'unsafe') THEN 1 ELSE 0 END) as unsafe_count
FROM training_data
GROUP BY source_type;
```

### Model Performance Over Time

```sql
-- Track accuracy improvements across versions
SELECT 
    version,
    trained_on,
    accuracy,
    precision,
    recall,
    training_samples_count
FROM model_versions
ORDER BY trained_on DESC;
```

---

## 💡 USAGE EXAMPLES

### Example 1: Collect Sample with Enhanced Metadata

```python
from continuous_learning import ContinuousLearningSystem

learning_system = ContinuousLearningSystem()

# Collect sample with full metadata
sample_id = learning_system.collect_sample(
    text="Innova we are Associates of your business you do remember",
    prediction="unsafe",
    confidence=0.95,
    source="video",
    session_id="abc123",
    toxic_words=["remember"]  # Detected grooming language
)

# System automatically:
# 1. Stores in training_data table
# 2. Updates toxic_words tracking
# 3. Extracts and tracks safe words
# 4. Adds to retraining buffer
```

### Example 2: View Toxic Word Trends

```bash
curl http://localhost:5000/api/learning/analytics
```

**Response:**
```json
{
  "total_samples": 487,
  "toxic_words_tracked": 127,
  "top_toxic_words": [
    {
      "word": "stupid",
      "severity": "medium",
      "occurrence_count": 47,
      "context_examples": [
        "You are stupid",
        "That's so stupid"
      ]
    }
  ],
  "safe_words_tracked": 543,
  "label_distribution": [
    {"label": "safe", "count": 312},
    {"label": "unsafe", "count": 175}
  ],
  "source_distribution": [
    {"source_type": "video", "count": 234},
    {"source_type": "audio", "count": 156},
    {"source_type": "chat", "count": 97}
  ]
}
```

### Example 3: Identify Emerging Threats

```python
import sqlite3

conn = sqlite3.connect("melodywings.db")
c = conn.cursor()

# Find toxic words that appeared in last 24 hours
c.execute('''
SELECT word, severity, occurrence_count, context_examples
FROM toxic_words
WHERE last_seen > datetime('now', '-1 day')
ORDER BY occurrence_count DESC
''')

emerging_threats = c.fetchall()

print("🚨 Emerging Toxic Words (Last 24h):")
for word, severity, count, examples in emerging_threats:
    print(f"  {word}: {severity} ({count} occurrences)")
    print(f"     Examples: {examples[:2]}")
```

---

## 🎯 BENEFITS OF ENHANCED SCHEMA

### 1. **Better Toxic Pattern Detection**
- Track which toxic words appear most frequently
- Identify emerging slang or coded language
- Understand context through examples
- Severity-based prioritization

### 2. **Reduced False Positives**
- Safe word whitelist helps distinguish context
- Educational vs inappropriate usage
- Word frequency analysis

### 3. **Improved Model Training**
- More features available (word counts, toxic lists)
- Session-based tracking
- Human review integration
- Model version comparison

### 4. **Actionable Insights**
- Real-time toxic word trends
- Source-specific safety analysis
- Correction rate monitoring
- Performance metrics over time

---

## 📊 ANALYTICS DASHBOARD UPGRADES

### Add to Your Dashboard:

```html
<!-- Toxic Words Widget -->
<div class="widget">
    <h3>☠️ Toxic Words Tracked</h3>
    <div class="stat-value" id="toxicWordsCount">0</div>
    
    <div id="topToxicWords"></div>
</div>

<!-- Safe Words Widget -->
<div class="widget">
    <h3>✅ Safe Words Tracked</h3>
    <div class="stat-value" id="safeWordsCount">0</div>
    
    <div id="safeWordCategories"></div>
</div>

<!-- Source Distribution -->
<div class="widget">
    <h3>📊 Content Sources</h3>
    <canvas id="sourceChart"></canvas>
</div>

<script>
async function loadEnhancedAnalytics() {
    const response = await fetch('/api/learning/analytics');
    const data = await response.json();
    
    document.getElementById('toxicWordsCount').innerText = data.toxic_words_tracked;
    document.getElementById('safeWordsCount').innerText = data.safe_words_tracked;
    
    // Display top toxic words
    const toxicList = document.getElementById('topToxicWords');
    data.top_toxic_words.forEach(word => {
        toxicList.innerHTML += `
            <div class="toxic-word-item">
                <span class="word">${word.word}</span>
                <span class="severity severity-${word.severity}">${word.severity}</span>
                <span class="count">${word.occurrence_count}x</span>
            </div>
        `;
    });
}

setInterval(loadEnhancedAnalytics, 10000);
</script>
```

---

## 🔧 MAINTENANCE TIPS

### Weekly Tasks:

1. **Review Top Toxic Words**
   ```sql
   SELECT word, severity, occurrence_count
   FROM toxic_words
   ORDER BY occurrence_count DESC
   LIMIT 20;
   ```

2. **Check Human Review Queue**
   ```sql
   SELECT COUNT(*) 
   FROM training_data 
   WHERE human_reviewed = FALSE 
   AND confidence_score < 0.7;
   ```

3. **Archive Old Data**
   ```sql
   -- Export old training data monthly
   .mode csv
   .output training_data_2026_03.csv
   SELECT * FROM training_data
   WHERE created_at < datetime('now', '-30 days');
   ```

### Monthly Tasks:

1. **Analyze Model Drift**
   ```sql
   SELECT 
       version,
       accuracy,
       trained_on,
       training_samples_count
   FROM model_versions
   ORDER BY trained_on DESC
   LIMIT 10;
   ```

2. **Clean Up Toxic Words**
   ```sql
   -- Remove words not seen in 90 days
   DELETE FROM toxic_words
   WHERE last_seen < datetime('now', '-90 days')
   AND occurrence_count < 5;
   ```

---

## 🎉 SUCCESS METRICS

Track these KPIs with new schema:

| Metric | Baseline | Month 1 | Target |
|--------|----------|---------|--------|
| **Toxic Words Tracked** | 0 | 100+ | 500+ |
| **Safe Words Tracked** | 0 | 300+ | 2000+ |
| **Training Samples** | 0 | 500+ | 5000+ |
| **Human Reviewed** | 0 | 50+ | 500+ |
| **Model Versions** | 1 | 10+ | 50+ |
| **Accuracy** | 75% | 85% | 95% |

---

**Your continuous learning database is now ENTERPRISE-GRADE with comprehensive tracking and analytics!** 🚀📊
