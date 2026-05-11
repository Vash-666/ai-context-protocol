# Quality Cut Process - Repeatable System Refinement

**Purpose:** Keep the system lean and mean after project bursts  
**Frequency:** Run after every 2-3 major projects  
**Duration:** 2-4 hours (with optimized @quality chunking)  
**Goal:** Remove accumulated "fat," optimize architecture, maintain quality

---

## 🎯 **When to Run Quality Cut**

### **Triggers:**
1. **After major project completion** (2-3 projects accumulated)
2. **System quality drops** below 8.5/10 for 2+ weeks
3. **Complexity increases** significantly (new agents, features, infrastructure)
4. **Quarterly review** (end of quarter maintenance)
5. **Before major release** (optimize before showcasing)

### **Don't Run If:**
- System quality already ≥9.0/10 and stable
- Less than 2 projects completed since last cut
- Major project in progress (wait for completion)
- Technical debt being actively addressed

---

## 📋 **Quality Cut Process (Step-by-Step)**

### **Milestone 0: Validation (30 minutes)**

**Task 0.1 - @orchestrator: System Health Check**
```
Check current system status:
- Quality score (estimate + Quality Equation tool)
- Context preservation (SESSION-CONTEXT.md protocol)
- Cost savings (model usage ratio)
- Active agents count
- Recent projects completed
- Outstanding technical debt

Output: System status summary
Decision: Proceed if quality <9.0 or complexity high
```

**Task 0.2 - @quality (chunked): Validate Refinement Need**
```
Chunk 1: Review system metrics (provided)
- Quality score vs. baseline
- Complexity vs. last cut
- Technical debt count

Chunk 2: Recommend YES/NO
- Should we proceed with Quality Cut?
- Brief reasoning (one sentence)

Timeout: 5 minutes per chunk
```

**Task 0.3 - @orchestrator: Decision Point**
```
If @quality recommends YES → Proceed to Milestone 1
If @quality recommends NO → Document decision, exit gracefully
If @quality fails → Use proxy evaluation, document technical issues
```

---

### **Milestone 1: Full Inventory & Evaluation (1-2 hours)**

**Task 1.1 - @orchestrator: Complete System Inventory**
```
Compile inventory across 6 categories:

1. Core Framework Components
   - List all framework elements
   - Note quality scores (if known)

2. Production Agents
   - List all agents with handles
   - Note quality scores and roles

3. Completed Projects
   - List all projects since last cut
   - Note status and GitHub links

4. Technical Infrastructure
   - List all infrastructure components
   - Note stability and usage

5. Content & Branding
   - List content rules and guidelines
   - Note consistency and effectiveness

6. Communication Setup
   - List all channels and status
   - Note reliability and maintenance

Output: Complete inventory (markdown table format)
File: `quality-cut-inventory-YYYY-MM-DD.md`
```

**Task 1.2 - @quality (chunked): Audit Each Category**
```
For each category (6 total chunks):

Chunk X: Score category items
- Items: [5-10 items max per chunk]
- Criteria: Quality, Usage, Maintenance, Value, Technical Debt
- Output: Item, score (1-10), brief reason
- Timeout: 5 minutes

Process all 6 categories sequentially
Collect all results before proceeding
```

**Task 1.3 - @orchestrator: Compile Decision Table**
```
Based on @quality audit results:

For each item:
- Current score (from @quality)
- Decision: KEEP (≥8.0), IMPROVE (7.0-7.9), DECOMMISSION (<7.0)
- Priority: Critical, High, Medium, Low
- Rationale: Why this decision?
- Action items: What specific improvements needed?

Output: Decision table (markdown format)
File: `quality-cut-decision-table-YYYY-MM-DD.md`
```

---

### **Milestone 2: Implementation Planning (30 minutes)**

**Task 2.1 - @orchestrator: Create Implementation Roadmap**
```
Based on decision table:

1. Critical Actions (immediate, 1-2 days)
   - Essential fixes
   - System blockers
   - Security/stability issues

2. High-Value Improvements (short-term, 3-7 days)
   - Important optimizations
   - High-impact changes
   - Technical debt reduction

3. Medium Optimizations (medium-term, 1-2 weeks)
   - Valuable refinements
   - Performance tuning
   - Feature consolidation

4. Low Priority (long-term, 2-4 weeks)
   - Nice-to-have improvements
   - Future considerations
   - Experimental features

Output: Implementation roadmap with timelines
File: `quality-cut-roadmap-YYYY-MM-DD.md`
```

**Task 2.2 - @orchestrator: Assign Priorities and Timelines**
```
For each action item:
- Estimated time to complete
- Assigned agent (if applicable)
- Dependencies (what must be done first)
- Success criteria (how to know it's done)
- Impact assessment (quality improvement expected)

Output: Detailed task list with schedules
File: `quality-cut-tasks-YYYY-MM-DD.md`
```

---

### **Milestone 3: Execution (1-2 hours)**

**Task 3.1 - @orchestrator: Execute Critical Actions**
```
For each critical action:
1. Verify prerequisites met
2. Execute improvement
3. Test/validate changes
4. Document completion
5. Update quality metrics

Track progress in: `quality-cut-progress-YYYY-MM-DD.md`
```

**Task 3.2 - @quality (chunked): Validate Improvements**
```
For each completed action (chunks of 5):

Chunk X: Review completed improvements
- Actions: [5 actions from Task 3.1]
- Validation: Did action achieve goal?
- Quality impact: Score before/after
- Output: Action, validated (yes/no), impact assessment

Timeout: 5 minutes per chunk
```

**Task 3.3 - @orchestrator: Decommission Items**
```
For items marked DECOMMISSION:
1. Archive relevant files/code
2. Remove from active system
3. Update documentation
4. Update MEMORY.md with decisions
5. Verify no dependencies broken

Output: Decommission log
File: `quality-cut-decommissioned-YYYY-MM-DD.md`
```

---

### **Milestone 4: Validation & Documentation (30 minutes)**

**Task 4.1 - @orchestrator: Measure Quality Impact**
```
Compare before/after metrics:
- Quality score (before vs. after)
- System complexity (agent count, feature count)
- Maintenance burden (estimated time saved)
- Cost efficiency (model usage optimization)
- Technical debt (issues resolved)

Output: Impact report
File: `quality-cut-impact-YYYY-MM-DD.md`
```

**Task 4.2 - @quality (single chunk): Final Validation**
```
Simple validation task:

Question: Did Quality Cut achieve goals?

Provided metrics:
- Quality before: X.XX/10
- Quality after: Y.YY/10
- Items decommissioned: N
- Improvements made: M
- Time invested: H hours

Output: YES/NO + brief assessment
Timeout: 5 minutes
```

**Task 4.3 - @orchestrator: Update Memory & Documentation**
```
Update key files:
1. MEMORY.md - Add Quality Cut summary and lessons learned
2. AGENTS.md - Update procedures based on improvements
3. TOOLS.md - Update environment after decommissions
4. SESSION-CONTEXT.md - Clear for next work phase

Create summary:
- What was cut (decommissioned items)
- What was improved (optimization actions)
- What was kept (core system)
- Lessons learned (process improvements)

Output: Quality Cut summary
File: `quality-cut-summary-YYYY-MM-DD.md`
```

---

## 🔧 **Technical Optimizations**

### **@quality Chunking Strategy (Critical):**

**For complex evaluations, always chunk:**
```python
# Instead of this (FAILS):
❌ "@quality: Evaluate entire system with vector similarity + Quality Equation"

# Do this (SUCCEEDS):
✅ Chunk 1: "@quality: Score core framework items 1-5 (provided criteria)"
✅ Chunk 2: "@quality: Score agents 1-6 (provided criteria)"
✅ Chunk 3: "@quality: Compare scores to baseline (provided scores)"
✅ Chunk 4: "@quality: Recommend actions (provided comparison)"
✅ Chunk 5: "@quality: Synthesize into final recommendation"
```

### **Pre-Compute Heavy Operations:**
```python
# Before spawning @quality, prepare data:
✅ Run vector retriever separately (if needed)
✅ Calculate Quality Equation separately (if needed)
✅ Compile all metrics and scores
✅ Provide results TO @quality (don't ask @quality to compute)
```

### **Timeout Management:**
```python
# All @quality tasks:
✅ Default timeout: 5 minutes (300 seconds)
✅ Expected completion: 30 seconds to 2 minutes
✅ If timeout: Chunk task further

# All heavy computations:
✅ Run outside @quality session
✅ Provide results to @quality
✅ Monitor progress with health checks
```

---

## 📊 **Expected Outcomes**

### **Metrics:**
- **Quality improvement:** +0.5 to +1.5 points (e.g., 8.79 → 9.29+)
- **Complexity reduction:** 15-25% (fewer agents, features, or infrastructure)
- **Maintenance reduction:** 20-30% (less time on upkeep)
- **Cost optimization:** Maintain or improve cost savings ratio
- **Technical debt:** Resolve 2-5 high-priority issues

### **Deliverables:**
- System inventory (complete feature list)
- Audit results (@quality scored evaluations)
- Decision table (keep/improve/decommission)
- Implementation roadmap (prioritized actions)
- Impact report (before/after comparison)
- Summary document (lessons learned)

---

## 🎯 **Success Criteria**

### **Quality Cut is successful if:**
1. **Quality score improved** by ≥0.3 points
2. **Technical debt reduced** (2+ issues resolved)
3. **System complexity** reduced or stable
4. **No regressions** (nothing broken during refinement)
5. **Process documented** (lessons learned captured)

### **Quality Cut is marginal if:**
1. **Quality score stable** (no improvement)
2. **Some improvements** made but not dramatic
3. **Process completed** but high time cost

### **Quality Cut failed if:**
1. **Quality score decreased** (regressions introduced)
2. **System broken** (functionality lost)
3. **Process incomplete** (stuck or abandoned)

---

## 📅 **Scheduling as Cron Job**

### **Recommended Schedule:**
```bash
# Option 1: Monthly (end of month review)
# Schedule: Last Saturday of month, 9:00 AM
# Cron: 0 9 * * 6 [ $(date +\%d) -gt 24 ] && /path/to/quality-cut.sh

# Option 2: Quarterly (end of quarter)
# Schedule: Last day of Mar/Jun/Sep/Dec, 9:00 AM
# Cron: 0 9 31 3,6,9,12 * /path/to/quality-cut.sh

# Option 3: Project-triggered (manual)
# After completing 2-3 major projects, run manually:
# openclaw execute --task quality-cut
```

### **Cron Job Content (Next Section):**
Will create executable script for automation.

---

## 🚨 **Common Pitfalls & Solutions**

### **Pitfall 1: @quality Times Out**
**Cause:** Task too complex (vector retriever + Quality Equation)  
**Solution:** Use chunking strategy (5-minute max per chunk)  
**Prevention:** Always chunk complex evaluations

### **Pitfall 2: Framework Requires Monolithic Evaluation**
**Cause:** Framework designed for single-pass evaluation  
**Solution:** Adapt framework with proxy evaluation  
**Prevention:** Design frameworks with tool limitations in mind

### **Pitfall 3: Quality Cut Takes Too Long**
**Cause:** Technical issues (stuck sessions, infinite loops)  
**Solution:** Use timeouts aggressively, monitor progress  
**Prevention:** Fix underlying technical debt first

### **Pitfall 4: Too Much Decommissioned**
**Cause:** Over-aggressive cutting  
**Solution:** Review decision table with human before execution  
**Prevention:** Use conservative thresholds (decommission only <7.0)

### **Pitfall 5: Process Abandoned Mid-Way**
**Cause:** Lost momentum, unclear next steps  
**Solution:** Use this documented process, track progress  
**Prevention:** Block dedicated time for Quality Cut

---

## 📝 **Process Improvements (Lessons Learned)**

### **From 2026-04-18 Quality Cut:**

1. **@quality chunking is critical** (proven: 3s success vs. 3h+ failure)
2. **Proxy evaluations acceptable** when technical issues occur
3. **Framework adaptation** better than abandonment
4. **Timeout limits essential** (5-minute max per task)
5. **Document technical issues** for future fixes
6. **Context preservation works** (SESSION-CONTEXT.md protocol successful)
7. **Cost-benefit analysis needed** (4.5 hours lost = high cost)

### **Future Improvements:**
1. Fix vector retriever (CRITICAL - root cause of failures)
2. Optimize Quality Equation (HIGH - scoring discrepancy)
3. Add health checks for long-running tasks
4. Implement circuit breakers for infinite loops
5. Create @quality performance monitoring

---

## 🎯 **Next Steps After This Document**

1. **Create cron job script** (`quality-cut-cron.sh`)
2. **Test script** on current system
3. **Schedule cron** job (monthly or quarterly)
4. **Document in TOOLS.md** for reference
5. **Update MEMORY.md** with process location

---

_Last updated: 2026-04-18 - Created during first Quality Cut implementation_
