import pandas as pd
import re
import numpy as np
import spacy
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction import DictVectorizer

nlp = spacy.load("en_core_web_sm")

df = pd.read_csv("data/validation_sets/claim_strength_v1.csv")

def primary_label(lbl):
    lbl = str(lbl).strip()
    m = re.match(r"^([ABCDN])", lbl)
    return m.group(1) if m else None

df["primary"] = df["label"].apply(primary_label)
work = df[df["primary"].notna()].copy()
proto = work[work["split"] == "P"].copy()
held = work[work["split"] == "H"].copy()

print(f"Prototype set: {len(proto)} rows, classes {sorted(proto['primary'].unique())}")
print(f"Heldout set: {len(held)} rows\n")
print("=== Class distribution (prototype) ===")
print(proto["primary"].value_counts())
print("\n=== Class distribution (heldout) ===")
print(held["primary"].value_counts())
print()

HEDGE_WORDS = {"could", "may", "might", "can", "theoretically", "possibly",
               "potentially", "if", "hypothetically", "conditionally"}
SUPERLATIVES = {"revolutionary", "phenomenally", "perfectly", "exceptional",
                "ultimate", "massive", "powerhouse", "incredible", "incredibly",
                "absolute", "sweet spot", "best", "groundbreaking"}
ABSENCE_PHRASES = {"no peer-reviewed", "novelty lies", "first to", "no literature",
                    "lacks", "not yet been", "no prior work", "gap in",
                    "does not establish", "does not show", "from memory",
                    "needs investigation", "not empty territory", "isn't empty territory"}
DEFINITIONAL_PATTERNS = {"is defined as", "stands for", "refers to", "means",
                          "is a", "are a", "describes what", "uses exactly",
                          "consists of", "is called", "is the", "generates",
                          "operates by", "conditions on"}
CERTAINTY_INFLATORS = {"certified", "ensures", "successfully", "established",
                        "legitimate", "exact", "already exists"}

def extract_features(claim):
    doc = nlp(claim.lower())
    tokens = [t.text for t in doc]
    text = claim.lower()

    has_number = any(t.like_num for t in doc)
    has_unit_pattern = bool(re.search(r"\d+(\.\d+)?", claim))
    hedge_count = sum(1 for w in HEDGE_WORDS if w in tokens)
    superlative_count = sum(1 for w in SUPERLATIVES if w in text)
    absence_count = sum(1 for p in ABSENCE_PHRASES if p in text)
    definitional_count = sum(1 for p in DEFINITIONAL_PATTERNS if p in text)
    certainty_count = sum(1 for w in CERTAINTY_INFLATORS if w in text)

    first_tok = doc[0] if len(doc) else None
    starts_with_verb = bool(first_tok and first_tok.pos_ == "VERB" and first_tok.tag_ == "VB")
    starts_with_wh_question = bool(first_tok and first_tok.text in
                                    ("what", "do", "does", "would", "should", "want", "can", "is"))
    has_comparison_word = any(t.text in ("than", "compared") for t in doc)

    return {
        "has_number": int(has_number or has_unit_pattern),
        "hedge_count": hedge_count,
        "superlative_lexical": superlative_count,
        "absence_count": absence_count,
        "definitional_count": definitional_count,
        "certainty_inflator_count": certainty_count,
        "starts_with_verb": int(starts_with_verb),
        "starts_with_wh_question": int(starts_with_wh_question),
        "has_comparison_word": int(has_comparison_word),
        "claim_length": len(doc),
    }

proto_feats = [extract_features(c) for c in proto["claim"]]
held_feats = [extract_features(c) for c in held["claim"]]

vec = DictVectorizer(sparse=False)
X_train = vec.fit_transform(proto_feats)
X_test = vec.transform(held_feats)
y_train = proto["primary"].values
y_test = held["primary"].values

clf = DecisionTreeClassifier(max_depth=6, random_state=42, class_weight="balanced")
clf.fit(X_train, y_train)
preds = clf.predict(X_test)

results = held[["ID", "claim", "primary", "label"]].copy()
results["predicted"] = preds
results["correct"] = results["primary"] == results["predicted"]

pd.set_option("display.width", 140)
pd.set_option("display.max_colwidth", 40)
print("=== Decision tree (structural features) results ===")
print(results.to_string(index=False))
print(f"\nAccuracy: {results['correct'].mean():.3f}  ({results['correct'].sum()}/{len(results)})")
print("\nPer-class accuracy:")
print(results.groupby("primary")["correct"].mean())

print("\n=== Feature importances ===")
importances = sorted(zip(vec.get_feature_names_out(), clf.feature_importances_), key=lambda x: -x[1])
for name, imp in importances:
    if imp > 0:
        print(f"{name}: {imp:.3f}")

# prototype sanity check
proto_preds = clf.predict(X_train)
proto_acc = (proto_preds == y_train).mean()
print(f"\nPrototype-set (training) accuracy: {proto_acc:.3f}")

results.to_csv("data/validation_sets/stage1_structural_analysis_151rows.csv", index=False)