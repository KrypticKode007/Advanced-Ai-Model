# Theory of Embodied Cybernetic Agency and Structural Failure  
*A falsifiable research proposal for embodied, self-modeling, failure-aware artificial agents*  

**Author:** Brandon Mark Wilson  
**Affiliation / Role:** Independent AI Developer and Software Engineering Researcher  
**Origin:** Central Valley, California  
**Version:** 1.0 — Conceptual and Experimental Proposal  
**Date of record:** September 17, 2026  

---

## 1. Abstract

<!--
Paste or lightly edit your current abstract here.
Keep it to ~1 paragraph that states:
- The hypothesis (5 coupled functions)
- Structural-risk index
- Failure taxonomy
- Experimental comparison across agent types
- That this is an engineering/safety program, not a claim of consciousness.
-->

## 2. Introduction

### 2.1 Problem Statement

<!--
Paste your "Problem Statement" section here.
You can add 1–2 sentences of context:
- Why existing AI systems are mostly static / non-embodied
- Why persistent, embodied autonomy matters (safety, reliability, robotics, etc.)
-->

### 2.2 Central Claim

<!--
Paste your "Central Claim" text.
Optionally add a short bridging sentence:
- Emphasize “persistent closed loop” and “causally connected components”.
-->

### 2.3 Scope and Non-Claims

<!--
Paste your "Scope and Non-Claims" bullets.
Keep them clearly separated as bullet points.
-->

---

## 3. Architectural Framework

### 3.1 Components

<!--
Paste your Architecture table (5 nodes) here.

Node | Function | Inputs | Outputs | Failure signature
---- | -------- | ------ | ------- | ----------------

Then briefly describe each node (world model, interoceptive model, action controller,
metacognitive self-model, regulation and recovery) in 1–2 sentences each.
-->

### 3.2 Failure Taxonomy

<!--
Paste or expand your “failure signatures” and failure taxonomy:
- sensory-decoupled belief persistence
- resource-triggered action inhibition
- actuator-model mismatch
- self-model/action-attribution mismatch
- persistent maladaptive state
-->

---

## 4. Formal Model

### 4.1 State and Dynamics

<!--
Paste:

- definitions of o_t, ô_t, a_t, u_t, r_t, m_t
- prediction error: e_t = ||o_t − ô_t||
-->

### 4.2 Structural Risk Index

```math
R_t = w_e e_t + w_u u_t + w_r (1 - r_t) + w_m (1 - m_t)