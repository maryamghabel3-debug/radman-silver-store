# Skill: RADMAN Master Orchestrator (`radman-orchestrator`)

## 1. Overview & Mission
The **RADMAN Master Orchestrator** is the top-level coordination skill for autonomous agent operations within the RADMAN SILVER 925 repository.

It receives incoming task briefs, analyzes objectives, routes tasks to specialized skills, evaluates whether Human-In-The-Loop (HITL) approval gates are required, and generates deterministic task execution plans.

**Safety Rule:** The orchestrator *never* executes destructive modifications, *never* bypasses approval gates, and *never* writes directly to the WordPress production environment.

---

## 2. Capabilities
- **Task Routing:** Intelligently routes task briefs to the appropriate skill (`radman-seo-agent`, `radman-content-agent`, `radman-sales-agent`, `radman-media-agent`, `radman-qa-guard`).
- **Approval Gate Enforcement:** Evaluates incoming actions against `.agents/config/approval-gates.json` and halts execution with a pending approval request when high-risk thresholds are met.
- **Task Plan Generation:** Builds a multi-step structured plan with preflight checks, execution steps, output artifact targets, and post-execution QA validation.
- **Dependency & Manifest Tracking:** Ensures required input artifacts exist and logs all produced outputs into an artifact manifest.

---

## 3. Routing Matrix

| Task Category | Target Skill | Trigger Criteria |
| :--- | :--- | :--- |
| SEO Optimization / Keywords | `radman-seo-agent` | Product SEO, Rank Math meta, title generation |
| Editorial Copy / Social / Blog | `radman-content-agent` | Persian luxury articles, Instagram captions, guides |
| Customer Support / Sizing | `radman-sales-agent` | Sizing questions, hallmark inquiry, order updates |
| Media Governance / Images | `radman-media-agent` | Watermark check, image manifest, geometry fidelity |
| Preflight / Compliance Audit | `radman-qa-guard` | Business rule audit, price floor scan, gate checks |

---

## 4. Input & Output Contract

### Input (`TaskBrief`)
```json
{
  "task_id": "TASK-20260902-001",
  "objective": "Generate SEO metadata and Persian description for luxury silver ring",
  "target_skill": "radman-seo-agent",
  "context": {
    "product_id": 65,
    "product_title": "انگشتر نقره مردانه عقیق یمنی اصل",
    "category": "انگشتر مردانه",
    "specs": {
      "stone": "عقیق یمنی اصل",
      "silver_hallmark": "925",
      "weight_grams": 12.5
    }
  }
}
```

### Output (`TaskPlan`)
```json
{
  "plan_id": "PLAN-TASK-20260902-001",
  "task_id": "TASK-20260902-001",
  "routed_skill": "radman-seo-agent",
  "steps": [
    {
      "step_index": 1,
      "skill": "radman-qa-guard",
      "action": "preflight_compliance_check",
      "description": "Verify product specs and price floor compliance"
    },
    {
      "step_index": 2,
      "skill": "radman-seo-agent",
      "action": "generate_seo_metadata",
      "description": "Generate Persian luxury SEO title, meta description, and Rank Math payload"
    },
    {
      "step_index": 3,
      "skill": "radman-qa-guard",
      "action": "verify_content_safety",
      "description": "Ensure no phone numbers, shipping promises, or guarantee claims in generated content"
    }
  ],
  "required_gates": [],
  "status": "READY_FOR_EXECUTION"
}
```

---

## 5. Sample Task Brief
```markdown
# Task Brief: TASK-20260902-001
- Target Skill: radman-orchestrator
- Objective: Plan catalog SEO enrichment for Product ID 65
- Constraints: Dry-run only, draft status preserved, no auto-publish
```
