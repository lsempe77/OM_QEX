import pandas as pd

# ----- PATHS -----
gt_path = "/Users/joshuapolanin/Documents/OM_QEX/data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv"
auto_path = "outputs/quant_extraction_form_PHRKN65M.csv"

# ----- READ GT CSV (Quant Extraction Form export) -----
gt = pd.read_csv(gt_path)

print("GT columns:", gt.columns.tolist())

# Find the StudyID column robustly
studyid_candidates = [c for c in gt.columns if "studyid" in str(c).lower()]
if not studyid_candidates:
    raise KeyError("Could not find a StudyID-like column in GT CSV.")
studyid_col = studyid_candidates[0]
print(f"Using GT StudyID column: {studyid_col!r}")

# Filter to TEEP (121294984)
gt_teep = gt[gt[studyid_col] == 121294984]

# Identity fields from GT (be robust to slight column name differences)
def find_col(df, name_fragment):
    matches = [c for c in df.columns if name_fragment.lower() in str(c).lower()]
    return matches[0] if matches else None

gt_outcome_name_col = find_col(gt, "Outcome name")
gt_outcome_desc_col = find_col(gt, "Outcome description")
gt_literal_col = find_col(gt, "Literal text")
gt_pos_col = find_col(gt, "Text position")

gt_id = gt_teep[[c for c in [
    gt_outcome_name_col,
    gt_outcome_desc_col,
    gt_literal_col,
    gt_pos_col
] if c is not None]]

print("\nGT TEEP rows:", len(gt_id))
print(gt_id.head())

# ----- READ AUTOMATED QUANT FORM -----
auto = pd.read_csv(auto_path)
auto_teep = auto[auto["StudyID"] == "PHRKN65M"]

auto_id = auto_teep[[
    "Outcome name",
    "Outcome description",
    "literal_text",
    "text_position"
]]

print("\nAUTO TEEP rows:", len(auto_id))
print(auto_id.head())
