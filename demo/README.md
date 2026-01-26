# FinFind Demo Directory

This directory contains all materials for the hackathon demo and presentation.

## Contents

| File | Description |
|------|-------------|
| [DEMO_SCRIPTS.md](DEMO_SCRIPTS.md) | Step-by-step scripts for all 4 demo scenarios |
| [PRESENTATION_OUTLINE.md](PRESENTATION_OUTLINE.md) | Slide-by-slide content and speaker notes |
| [QA_PREPARATION.md](QA_PREPARATION.md) | Anticipated Q&A with prepared answers |
| [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) | Pre-submission verification checklist |
| [demo_data.py](demo_data.py) | Demo users, products, and seed data |
| [run_demo.py](run_demo.py) | Demo environment setup and verification |

## Quick Start

```bash
# Check demo readiness
python demo/run_demo.py

# Load demo data
python demo/run_demo.py --load-data

# Start demo environment
python demo/run_demo.py --start
```

## Demo Scenarios

1. **Vague Intent Search** - Student laptop with budget constraints
2. **Multi-Modal Search** - Image upload + voice refinement
3. **Personalized Recommendations** - Profile-based picks with explanations
4. **Smart Alternatives** - Out-of-budget handling

## Demo Users

| ID | Name | Budget | Persona |
|----|------|--------|---------|
| `demo_student_001` | Sarah Chen | $300-800 | College student |
| `demo_professional_001` | Marcus Johnson | $1,000-2,500 | Software engineer |
| `demo_parent_001` | Jennifer Martinez | $200-600 | Budget-conscious parent |

## Timing Guide

| Section | Duration |
|---------|----------|
| Problem & Solution | 4 min |
| Technical Deep-Dive | 4 min |
| Live Demo | 6 min |
| Results & Q&A | 6 min |
| **Total** | **20 min** |

## Tips

- Practice the demo 5+ times
- Have backup video ready
- Test from different network before presentation
- Keep water nearby
- Don't rush through features
