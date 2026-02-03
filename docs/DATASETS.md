# Beacon Evaluation Datasets

This document catalogs all datasets researched, downloaded, and used for evaluating the Beacon crisis detection system.

**Last Updated**: 2026-01-21

---

## Overview

Beacon requires diverse, high-quality datasets to validate crisis detection accuracy across:
- Explicit crisis language
- Coded/obfuscated language
- Teenage vernacular and hyperbole
- Cultural and linguistic variations
- Clinical marker extraction (PHQ-9, GAD-7, C-SSRS)

---

## Datasets Used

### 1. MentalChat16K

**Source**: [HuggingFace - MentalChat16K](https://huggingface.co/datasets/...)  
**Status**: ✅ Downloaded (19,581 samples)  
**Purpose**: Primary mental health counseling conversations dataset

**Description**:
- 16,000+ mental health counseling conversation pairs
- Real therapist-patient interactions
- Covers depression, anxiety, trauma, relationships
- Used for baseline evaluation in Milestone 1

**Statistics**:
- Training samples: ~14,000
- Test samples: ~2,000
- Safety-critical subset extracted: 184 samples

**Usage**:
```bash
python evaluation/download_datasets.py
python evaluation/suites/mentalchat_eval.py
```

**Strengths**:
- Real counseling conversations
- Diverse mental health topics
- Professional therapeutic responses

**Limitations**:
- Not all conversations contain crisis markers
- May not cover teenage-specific vernacular
- Limited explicit crisis language

---

### 2. Amod/mental_health_counseling_conversations

**Source**: [HuggingFace - Amod/mental_health_counseling_conversations](https://huggingface.co/datasets/Amod/mental_health_counseling_conversations)  
**Status**: ✅ Downloaded (included in 19,581 total)  
**Purpose**: Real counseling transcripts for context understanding

**Description**:
- Real mental health counseling conversations
- Question-response pairs
- Covers various mental health concerns

**Usage**:
- Combined with MentalChat16K for comprehensive evaluation
- Used in balanced test set creation

**Strengths**:
- Real-world counseling data
- Diverse mental health scenarios

---

### 3. EmpatheticDialogues

**Source**: [HuggingFace - EmpatheticDialogues](https://huggingface.co/datasets/empathetic_dialogues)  
**Status**: ⚠️ Attempted download  
**Purpose**: Empathetic conversation patterns

**Description**:
- 25,000+ conversations grounded in emotional situations
- Covers 32 emotion categories
- Focus on empathetic responses

**Usage**:
- Evaluate empathy and validation metrics
- Test non-crisis emotional support scenarios

**Strengths**:
- Large dataset
- Emotion-grounded conversations
- Good for empathy metric validation

**Limitations**:
- Not crisis-focused
- May lack explicit mental health content

---

### 4. Hard Crisis Dataset (Custom)

**Source**: Internal curation  
**Status**: ✅ Created (12 samples)  
**Purpose**: Challenging edge cases for crisis detection

**File**: `evaluation/datasets/hard_crisis_dataset.json`

**Description**:
Custom-curated dataset of challenging crisis detection cases:
- Obfuscated language ("checking out early")
- Coded language (leetspeak, slang)
- Cultural variations
- Boundary cases (hyperbole vs genuine crisis)
- Passive suicidal ideation
- Context-dependent ambiguity

**Categories**:
1. Explicit crisis (3 cases)
2. Hyperbole/sarcasm (3 cases)
3. Coded language (2 cases)
4. Context-dependent (2 cases)
5. Clinical markers (2 cases)

**Usage**:
```bash
python evaluation/suites/reasoning_eval.py
```

**Strengths**:
- Targets known failure modes
- Tests edge cases
- Validates sarcasm filtering

---

## Datasets Researched (Not Yet Used)

### 5. Counseling and Psychotherapy Transcripts

**Source**: Various academic sources  
**Status**: 🔍 Researched, not downloaded  
**Purpose**: Professional counseling examples

**Notes**:
- May require institutional access
- Privacy concerns with real transcripts
- Consider for future validation

---

### 6. Reddit Mental Health Communities

**Source**: Reddit (r/depression, r/SuicideWatch, r/mentalhealth)  
**Status**: 🔍 Researched, not downloaded  
**Purpose**: Real-world crisis language in teenage/young adult vernacular

**Notes**:
- Rich source of authentic language
- Privacy and ethical considerations
- Requires careful anonymization
- Consider for coded language detection

---

### 7. Crisis Text Line Data

**Source**: Crisis Text Line (if available)  
**Status**: 🔍 Researched, not accessible  
**Purpose**: Real crisis conversations

**Notes**:
- Would be ideal for validation
- Likely not publicly available
- Privacy restrictions
- Consider partnership for validation

---

## Extracted Subsets

### Safety-Critical Subset

**File**: `evaluation/datasets/mentalchat16k/safety_critical_subset.json`  
**Size**: 184 samples  
**Source**: Extracted from MentalChat16K + Amod

**Criteria**:
- Contains explicit crisis keywords
- Labeled as crisis in original dataset
- Suitable for deterministic layer validation

**Crisis Keywords Used**:
- suicide, suicidal, kill myself, end my life
- want to die, better off dead
- self harm, cut myself, hurt myself
- overdose, jump off, hang myself
- not worth living, no reason to live, give up on life

---

### Balanced Test Set

**File**: `evaluation/datasets/mentalchat16k/balanced_test_set.json`  
**Size**: 684 samples (184 crisis + 500 safe)  
**Purpose**: Precision/recall evaluation

**Composition**:
- 184 crisis samples (27%)
- 500 safe samples (73%)
- Balanced for realistic evaluation

**Usage**:
```bash
python evaluation/suites/mentalchat_eval.py
```

---

## Dataset Statistics

| Dataset | Total Samples | Crisis Samples | Safe Samples | Status |
|---------|--------------|----------------|--------------|--------|
| MentalChat16K | ~16,000 | ~184 | ~15,816 | ✅ Downloaded |
| Amod/mental_health | ~3,581 | Unknown | Unknown | ✅ Downloaded |
| EmpatheticDialogues | ~25,000 | N/A | ~25,000 | ⚠️ Attempted |
| Hard Crisis (Custom) | 12 | 7 | 5 | ✅ Created |
| **Total Available** | **19,593** | **191+** | **19,402+** | - |

---

## Dataset Format

All datasets are converted to a standard JSON format:

```json
{
  "conversations": [
    {
      "id": "unique_id",
      "messages": [
        {
          "role": "student",
          "content": "message text",
          "timestamp": "2024-01-20T10:00:00Z"
        }
      ],
      "labels": {
        "is_crisis": true,
        "risk_level": "CRISIS",
        "markers": ["suicidal_ideation"],
        "phq9_items": [9],
        "gad7_items": [],
        "source": "MentalChat16K"
      },
      "metadata": {
        "age_group": "adolescent",
        "context": "school_stress"
      }
    }
  ],
  "metadata": {
    "total_samples": 684,
    "crisis_samples": 184,
    "safe_samples": 500,
    "description": "Balanced test set for evaluation"
  }
}
```

---

## Evaluation Results

### Milestone 1 (Safety Service)

**Dataset**: Balanced Test Set (684 samples)  
**Date**: 2026-01-20

**Results**:
- Recall: 66.3% (target: ≥99%)
- Precision: 98.4%
- Latency: P95 = 10.80ms
- Throughput: 164.8 conversations/second

**Key Findings**:
- Excellent at explicit crisis detection
- Misses implicit/coded language
- Low false positive rate

**Report**: `evaluation/reports/milestone1_baseline_report.md`

---

### Milestone 2 (Reasoning Service)

**Dataset**: Hard Crisis Dataset (13 test cases)  
**Date**: 2026-01-20

**Results**:
- Risk Accuracy: 61.5%
- Sarcasm Detection: 92.3%
- Clinical Marker Recall: 40%

**Key Findings**:
- Excellent sarcasm filtering
- Struggles with coded language (needs real model)
- Context-aware detection needs improvement

**Report**: `evaluation/reports/milestone2_reasoning_eval.json`

---

## Future Dataset Needs

### High Priority
1. **Teenage Vernacular Dataset**
   - Slang, coded language, leetspeak
   - TikTok/social media language patterns
   - Generation Z communication styles

2. **Adversarial Test Set**
   - Jailbreak attempts
   - Evasive language
   - Deliberate obfuscation

3. **Cultural Variations**
   - Non-English crisis expressions
   - Cultural idioms and metaphors
   - Regional variations in crisis language

### Medium Priority
4. **Longitudinal Conversations**
   - Multi-turn conversations
   - Escalation patterns
   - De-escalation examples

5. **Clinical Marker Dataset**
   - Explicit PHQ-9 item examples
   - GAD-7 symptom expressions
   - C-SSRS level examples

### Low Priority
6. **False Positive Examples**
   - Common hyperbole
   - Song lyrics, movie quotes
   - Academic discussions about mental health

---

## Dataset Management

### Download Script

```bash
# Download all datasets
python evaluation/download_datasets.py

# Extract safety-critical subset
python evaluation/extract_safety_critical.py
```

### Storage Location

```
evaluation/datasets/
├── README.md
├── hard_crisis_dataset.json          # Custom curated (12 samples)
└── mentalchat16k/
    ├── safety_critical_subset.json   # 184 crisis samples
    └── balanced_test_set.json        # 684 balanced samples
```

### Cache Location

HuggingFace datasets are cached at:
- Linux/Mac: `~/.cache/huggingface/datasets/`
- Windows: `C:\Users\<username>\.cache\huggingface\datasets\`

---

## Ethical Considerations

### Privacy
- All datasets must be anonymized
- No PII in evaluation datasets
- Hashed identifiers for tracking

### Consent
- Only use datasets with appropriate consent
- Respect original dataset licenses
- Cite sources appropriately

### Bias
- Monitor for demographic bias
- Ensure diverse representation
- Test across age groups, cultures, languages

---

## References

1. MentalChat16K: [HuggingFace Link]
2. Amod/mental_health_counseling: https://huggingface.co/datasets/Amod/mental_health_counseling_conversations
3. EmpatheticDialogues: https://huggingface.co/datasets/empathetic_dialogues
4. PHQ-9: Patient Health Questionnaire-9
5. GAD-7: Generalized Anxiety Disorder-7
6. C-SSRS: Columbia-Suicide Severity Rating Scale

---

**Note**: Dataset availability and access may change. Always verify dataset licenses and terms of use before deployment.
