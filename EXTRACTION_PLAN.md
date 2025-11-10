# OM_QEX Data Extraction App - Development Plan

## 🎯 Goal
Extract structured quantitative data from 95 papers (TEI XML format) using LLM, matching the human extraction format.

## 📋 Extraction Fields (66 total)

### Categories:
1. **General Info** (2 fields)
   - Coder name
   - Notes

2. **Publication Info** (5 fields)
   - StudyID
   - EstimateID  
   - Author name
   - Year of publication
   - Publication type

3. **Intervention Info** (12 fields)
   - Intervention abbreviation and name
   - Intervention description
   - Country
   - First year of intervention
   - Length of follow up
   - Exposure to intervention
   - 7 components (consumption support, healthcare, assets, skills, savings, coaching, social empowerment)

4. **Method Info** (2 fields)
   - Evaluation Design
   - Evaluation Method

5. **Outcome Info** (4 fields)
   - Outcome name
   - Outcome description
   - Reverse sign
   - Outcome dataset

6. **Treatment Variable Info** (4 fields)
   - Treatment
   - Comparison
   - Subgroup
   - Subgroup information

7. **Estimate Info** (4 fields)
   - Analysis type
   - Unit of analysis
   - Covariate adjustment
   - Source

8. **Estimate Data** (31 statistical fields)
   - Pre/Post means and SDs
   - Effect sizes, confidence intervals
   - Sample sizes, clusters

## 🏗️ Architecture (Simplified from paper-screening-pipeline)

```
om_qex_extraction/
├── config/
│   └── config.yaml           # API keys, model settings
├── prompts/
│   └── extraction_prompt.txt # LLM extraction instructions
├── src/
│   ├── tei_parser.py        # Parse TEI XML (reuse from screening pipeline)
│   ├── extraction_engine.py # Single LLM extraction engine
│   ├── field_validator.py   # Validate extracted data
│   └── models.py            # Data models for extraction
├── scripts/
│   └── run_extraction.py    # CLI to run extraction
├── data/                    # Already have this!
└── outputs/
    └── extractions/         # JSON + CSV outputs
```

## 🚀 Development Phases

### Phase 1: Setup (30 min)
- [ ] Create project structure
- [ ] Copy/adapt TEI parser from screening pipeline
- [ ] Define data models for extraction fields
- [ ] Create config file

### Phase 2: Prompt Engineering (1-2 hours)
- [ ] Design extraction prompt with all 66 fields
- [ ] Include examples from human extraction
- [ ] Add validation rules and field definitions
- [ ] Test on 2-3 papers manually

### Phase 3: Engine Development (2-3 hours)
- [ ] Build extraction_engine.py
- [ ] Implement structured JSON output
- [ ] Add field validation
- [ ] Error handling and logging

### Phase 4: Testing & Refinement (2-3 hours)
- [ ] Run on 5 papers from human_extraction
- [ ] Compare with human extraction (ground truth)
- [ ] Calculate field-level accuracy
- [ ] Refine prompt based on errors

### Phase 5: Full Extraction (runtime)
- [ ] Run on all 95 papers
- [ ] Export to CSV matching human format
- [ ] Generate comparison report

## 🔧 Technical Decisions

### Single Engine vs Dual Engine
**Decision: Single Engine**
- Reason: Extraction (not classification), need consistency
- Dual engine better for yes/no decisions
- Single engine faster and cheaper

### Model Selection
**Recommended: Claude 3.5 Haiku or GPT-4o**
- Haiku: Fast, cheap, good structured output
- GPT-4o: More accurate for complex statistical extraction
- Can test both and compare

### Output Format
**JSON → CSV conversion**
- LLM outputs structured JSON
- Convert to CSV matching human format
- Preserve hierarchical structure

### Validation Strategy
**Three levels:**
1. Schema validation (field types, required fields)
2. Range validation (years, sample sizes, etc.)
3. Comparison with human extraction (accuracy metrics)

## 📊 Success Metrics

### Accuracy Targets
- **Bibliographic fields**: 95%+ (straightforward)
- **Intervention components**: 85%+ (complex interpretation)
- **Statistical estimates**: 75%+ (often missing/unclear)

### Comparison with Human
- Field-by-field agreement
- Missing data patterns
- Error analysis

## 🎯 Next Steps

1. **Review this plan** - Confirm approach
2. **Set up environment** - Install dependencies
3. **Start Phase 1** - Create basic structure
4. **Prompt design** - Most critical step

## 💡 Key Advantages

1. **Data already prepared**: TEI XML + metadata ready
2. **Ground truth available**: Human extraction for validation
3. **Proven architecture**: Adapt from screening pipeline
4. **Clear schema**: Know exactly what to extract

## ⚠️ Challenges

1. **Complex statistical data**: Many papers won't have all fields
2. **Multiple estimates per paper**: Need to handle multiple rows
3. **Validation complexity**: 66 fields to validate
4. **Prompt length**: Need to fit all field definitions

## 📝 Notes

- Start simple: Extract 10-15 most important fields first
- Iterate: Add more fields as prompt improves
- Compare: Always validate against human extraction
- Document: Keep track of what works/doesn't work
