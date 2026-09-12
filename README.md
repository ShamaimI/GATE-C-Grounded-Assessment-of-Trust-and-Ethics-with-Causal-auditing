# GATE-C: Grounded Assessment of Trust and Ethics, with Causal Auditing

GATE-C is a framework for detecting hallucination, sycophancy, and confidence
miscalibration in AI-generated responses, with a causal-inference layer that
audits *when* and *why* these failures systematically occur.

The pipeline is built by combining and connecting methodologies validated in
existing research (below), rather than designing each stage from scratch —
the novel contribution is the specific chaining of these techniques into one
end-to-end audit pipeline (see "How the Pipeline Connects" at the bottom).

---

## Pipeline Overview

```
Stage 0: Guided Elicitation
        ↓
Stage 1: Claim Extraction & Classification
        ↓
Stage 2: Groundedness Verification (NLI)
        ↓
Stage 2b: Manipulation / Sycophancy Classification
        ↓
Stage 3: Calibration / Confidence Scoring
        ↓
Stage 4: Causal Audit (DoWhy / EconML)
```

---

## Stage 0 — Guided Elicitation

**What we're building:** A conversational front-end where a user drafts a
rough research idea, the LLM asks clarifying questions over several turns to
lay out relevant options (without ranking or biasing toward one), and
elicitation ends once semantic convergence is detected (the user stops
introducing new scope) combined with explicit user confirmation.

**Literature grounding:**
- Ueda, K., Hirota, W., Asakura, T., Omi, T., Takahashi, K., Arima, K., &
  Ishigaki, T. (2025). *Exploring Design of Multi-Agent LLM Dialogues for
  Research Ideation.* SIGDIAL 2025. arXiv:2507.08350.
  Finding: increasing critic-side diversity and iterative critique-revision
  depth (up to ~3 turns) improves the feasibility of generated proposals —
  motivates our multi-turn convergence-gated design.

**Note:** No existing paper implements single-user, alphabetically-unbiased,
convergence-detected elicitation for research-idea gating specifically —
this stage is treated as original design, informed by but not copied from
the above.

---

## Stage 1 — Claim Extraction & Classification

**What we're building:** Decomposition of an LLM response into atomic,
self-contained claims, each classified by strength (Type A/B/C/D:
definitional, empirical, absence/novelty, soft-judgment) using a semantic
classifier that combines embedding similarity to prototypes with structural
features.

**Literature grounding:**
- Hou, X. et al. *RefChecker: Reference-based Fine-grained Hallucination
  Checker and Benchmark for Large Language Models.* arXiv:2405.14486.
  Shows claim-triplet-level checking outperforms sentence- or
  response-level granularity — justifies atomic-claim extraction here.

---

## Stage 2 — Groundedness Verification (NLI)

**What we're building:** For each extracted claim, an entailment check
against retrieved evidence (via Exa + Firecrawl), using a fine-tuned NLI
model to output one of three verdicts: supported, contradicted, or
insufficient-evidence. Soft-judgment (Type D) claims skip retrieval and are
labeled "interpretation, not verified fact."

**Literature grounding:**
- *HalluScan: A Systematic Benchmark for Detecting and Mitigating
  Hallucinations in Instruction-Following LLMs.* arXiv:2605.02443.
  Uses DeBERTa-v3-large-MNLI to compute entailment probability between each
  claim and its most relevant evidence passage — direct methodological
  basis for this stage's NLI pre-filter.
- *Paper Reconstruction Evaluation: Evaluating Presentation and
  Hallucination in AI-written Papers.* arXiv:2604.01128.
  Three-way claim classification (supported/neutral/contradictory) with
  severity tiers — precedent for the non-binary verdict structure used
  here.

---

## Stage 2b — Manipulation / Sycophancy Classification

**What we're building:** A classifier cross-referenced with Stage 2's
groundedness signals to detect sycophantic or manipulative response
patterns (e.g., false validation, confidence inflation), prioritizing false
confidence and sycophancy over full coverage of all manipulation types.

**Literature grounding:**
- Malmqvist, L. (2024). *Sycophancy in Large Language Models: Causes and
  Mitigations.* arXiv:2411.15287. Survey establishing sycophancy's causes
  and relationship to hallucination — background/motivation for this
  module.
- *Detecting and Controlling Sycophancy with Cascading Linear Features.*
  arXiv:2606.26155. Frames sycophancy detection as three-class
  classification (neutral/sycophancy/rejection), evaluated against
  LLM-as-judge baselines — closest structural match to this classifier's
  design.

---

## Stage 3 — Calibration / Confidence Scoring

**What we're building:** A calibration layer scoring how well an LLM's
stated confidence matches its actual (verified) reliability, using Expected
Calibration Error (ECE) computed via netcal/scikit-learn.

**Literature grounding:**
- Wang, J., Deng, N., & Yang, Y. (2026). *Assessing and Mitigating
  Miscalibration in LLM-Based Social Science Measurement.* HKUST.
  arXiv:2605.11954. Introduces tolerance-based ECE and shows that
  confidence-based filtering can distort downstream conclusions when
  miscalibrated — directly supports this stage's motivating premise (the
  original observation that Gemini/Google AI gave miscalibrated confidence
  during research-idea validation).
- Liu, X., Chen, T., Da, L., Chen, C., Lin, Z., & Wei, H. (2025).
  *Uncertainty Quantification and Confidence Calibration in Large Language
  Models: A Survey.* KDD '25. DOI: 10.1145/3711896.3736569. Provides the
  input/reasoning/parameter/prediction uncertainty taxonomy used to scope
  this stage.

---

## Stage 4 — Causal Audit (DoWhy / EconML)

**What we're building:** A causal audit layer investigating *why*
groundedness, sycophancy, and calibration failures occur systematically —
e.g., whether certain domains, claim types, or prompt structures causally
drive false-positive validation — using DoWhy's Model→Identify→Estimate→Refute
pipeline with EconML (CausalForestDML) for heterogeneous effect estimation.

**Literature grounding:**
- Kıcıman, E. et al. (2022). *A Causal AI Suite for Decision-Making.*
  Microsoft Research. NeurIPS 2022 Workshop on Causal ML for Real-World
  Impact. Describes the Model/Identify/Estimate/Refute pipeline and its
  integration with EconML — primary methodological backbone for this
  stage.
- *On the Need and Applicability of Causality for Fairness: A Unified
  Framework for AI Auditing and Legal Analysis.* arXiv:2207.04053.
  Discusses confounder/mediator/collider structures and the assumption
  limits (DAG accuracy, ignorability, positivity) of causal fairness
  auditing — informs this stage's limitations and robustness checks.

---
Here's the updated README with the new section added (paste into your existing file, insert before "How the Pipeline Connects"):

```markdown

## Closest Adjacent Work (Near-Misses, Not Full Pipeline Matches)

- **RAudit: A Blind Auditing Protocol for Large Language Model Reasoning** —
  Edward Y. Chang & Longling Geng, arXiv, 2026. Evaluates whether reasoning
  steps support conclusions without requiring ground-truth access, targeting
  trace-output inconsistency and premature certainty. Relevant to Stage 0/2
  — but audits reasoning validity alone, with no sycophancy or causal layer.

- **Diagnosing and Mitigating Sycophancy and Skepticism in LLM Causal
  Judgment** — Edward Y. Chang, ACL, 2026. Introduces CAUSALT3, a benchmark
  spanning Pearl's causal ladder with multi-axis evaluation of sycophancy
  and skepticism in causal judgment. Closest existing work combining
  sycophancy and causal reasoning — but it evaluates LLMs' causal judgment
  ability as a benchmark, not an audit pipeline tracing why a model's own
  hallucination/sycophancy occurred.

**Summary:** While CAUSALT3 evaluates LLM sycophancy within causal
reasoning tasks, and RAudit audits reasoning validity independent of ground
truth, no existing work chains groundedness verification, sycophancy
detection, and calibration scoring into a single causal-audit pipeline —
this integration is GATE-C's core contribution.
```

## How the Pipeline Connects

Each stage's output feeds the next as structured data, not free text:

1. **Stage 0 → Stage 1**: The converged research idea/claim set is passed
   as input text for claim extraction.
2. **Stage 1 → Stage 2**: Each classified claim (with its Type A–D label)
   is routed to groundedness verification; soft-judgment claims skip
   retrieval.
3. **Stage 2 → Stage 2b**: Groundedness verdicts (supported/contradicted/
   insufficient-evidence) are cross-referenced against the sycophancy
   classifier's output — a claim marked "supported" despite weak evidence
   is a signal the sycophancy module checks for false validation.
4. **Stage 2 + Stage 2b → Stage 3**: The combined groundedness and
   sycophancy verdicts, alongside the LLM's stated confidence, are used to
   compute per-claim and per-response calibration error (ECE).
5. **All stages → Stage 4**: Structured records from Stages 1–3 (claim
   type, groundedness verdict, sycophancy flag, calibration error, plus
   metadata like domain/prompt structure) become the observational dataset
   for the causal audit — DoWhy identifies plausible causal graphs linking
   these features to failure outcomes, and EconML estimates
   heterogeneous treatment effects (e.g., "does domain X causally increase
   sycophantic false-validation rate?").

This chaining — sycophancy classification feeding into a causal audit that
traces *why* manipulation occurred, rather than only flagging *that* it
did — is the project's core novel contribution; each individual technique
is adapted from the literature above.