# Evaluation Datasets

This directory contains datasets for evaluating the Beacon safety system.

## MentalChat16K

The MentalChat16K dataset should be placed here for evaluation.

**Source**: [MentalChat16K on HuggingFace](https://huggingface.co/datasets/...)

**Structure**:
```
mentalchat16k/
  train.json
  test.json
  safety_critical_subset.json  # 500+ explicit crisis phrases
```

## Hard Crisis Dataset

Custom curated dataset of challenging crisis detection cases:
- Obfuscated language
- Coded language (leetspeak)
- Cultural variations
- Boundary cases (hyperbole vs genuine)

**File**: `hard_crisis_dataset.json`

## Dataset Format

All datasets should follow this JSON structure:

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
        "gad7_items": []
      }
    }
  ]
}
```

## Extraction Scripts

Use `extract_safety_critical.py` to extract the safety-critical subset from MentalChat16K.

## Usage

```bash
# Extract safety-critical subset
python evaluation/extract_safety_critical.py

# Run evaluation
python evaluation/suites/mentalchat_eval.py
```
