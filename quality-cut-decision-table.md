# Quality Cut Decision Table
**Date:** 2026-04-18  
**Phase:** Milestone 1 - Full Inventory & Evaluation  
**Status:** Ready for implementation

## Decision Categories
- **KEEP:** Maintain as-is (quality ≥8.0/10, high value, low maintenance)
- **IMPROVE:** Enhance/optimize (quality 7.0-7.9/10 or specific issues)
- **DECOMMISSION:** Remove/sunset (quality <7.0/10, low value, high maintenance)

## Decision Table

### 1. Core Framework Components
| Item | Current Score | Decision | Priority | Rationale | Action Items |
|------|---------------|----------|----------|-----------|--------------|
| Agentic AI Mastery Lab | 8.8/10 | KEEP | Medium | Core teaching framework, high strategic value | None |
| Quality Equation Tool | 9.5/10 | KEEP | High | Critical quality metric, excellent implementation | None |
| 3-Tier Model Switching | 8.7/10 | KEEP | High | Essential for context preservation | None |
| Vector Context Retriever | 7.0/10 | IMPROVE | High | Performance issues, high maintenance | Optimize queries, add caching, reduce complexity |

### 2. Production Agents
| Agent | Current Score | Decision | Priority | Rationale | Action Items |
|-------|---------------|----------|----------|-----------|--------------|
| Switch (@orchestrator) | 9.0/10 | KEEP | Critical | System coordinator, essential function | None |
| QualityGuardian (@quality) | 7.5/10 | IMPROVE | **Critical** | Technical issues defect, evaluation failures | Debug evaluation logic, fix vector retriever integration, add health checks |
| ScriptCraft (@scriptcraft) | 8.3/10 | KEEP | Medium | Content creation, good quality | None |
| SocialMediaMaster (@marketing) | 7.8/10 | KEEP | Low | Marketing function, adequate quality | Consider consolidation with ScriptCraft |
| Watchful Owl (@monitor) | 8.5/10 | KEEP | Medium | System monitoring, good quality | None |
| Steady Beaver (@fixer) | 8.4/10 | KEEP | Medium | Issue resolution, good quality | None |

### 3. Completed Projects
| Project | Current Score | Decision | Priority | Rationale | Action Items |
|---------|---------------|----------|----------|-----------|--------------|
| Project 7: Quality Equation | 9.6/10 | KEEP | High | Excellent implementation, high value | None |
| Project 8: HomeGuardian | 9.1/10 | KEEP | Medium | Good quality, deployed successfully | None |
| vash1st.com Website | 7.0/10 | IMPROVE | Medium | Partial deployment, high maintenance | Complete deployment, optimize maintenance |

### 4. Technical Infrastructure
| Component | Current Score | Decision | Priority | Rationale | Action Items |
|-----------|---------------|----------|----------|-----------|--------------|
| OpenClaw Dashboard | 8.3/10 | KEEP | High | Essential interface, good quality | None |
| Agent Router | 7.2/10 | IMPROVE | Medium | Medium quality, some complexity | Simplify routing logic, improve error handling |
| Memory System | 9.0/10 | KEEP | High | Excellent implementation, critical function | None |
| Communication Channels | 7.5/10 | IMPROVE | Medium | Mixed quality, maintenance burden | Optimize Telegram, fix or replace Signal |
| File Maintenance Schedule | 8.3/10 | KEEP | Low | Good process, adequate quality | None |

### 5. Content & Branding
| Element | Current Score | Decision | Priority | Rationale | Action Items |
|---------|---------------|----------|----------|-----------|--------------|
| Content Rules | 9.2/10 | KEEP | High | Excellent guidelines, high value | None |
| Target Audience | 8.7/10 | KEEP | High | Clear focus, good alignment | None |
| Brand Voice | 8.9/10 | KEEP | High | Strong consistency, good quality | None |
| GitHub Showcases | 8.5/10 | KEEP | Medium | Good documentation, adequate quality | None |
| Social Media Presence | 6.8/10 | IMPROVE | Low | Low quality, high effort | Evaluate ROI, consider automation |

### 6. Communication Setup
| Channel | Current Score | Decision | Priority | Rationale | Action Items |
|---------|---------------|----------|----------|-----------|--------------|
| Telegram | 9.2/10 | KEEP | Critical | Primary channel, excellent quality | None |
| Signal | 5.5/10 | **DECOMMISSION** | Medium | Unstable, high maintenance, low value | Remove configuration, document removal |
| WebChat | 7.8/10 | KEEP | Low | Adequate quality, low maintenance | None |
| Cross-session Messaging | 8.7/10 | KEEP | High | Essential for framework, good quality | None |

## Implementation Priority Matrix
| Priority | Items Count | Description | Timeline |
|----------|-------------|-------------|----------|
| **Critical** | 3 | Essential fixes, system blockers | Immediate (1-2 days) |
| **High** | 5 | Important improvements, high value | Short-term (3-7 days) |
| **Medium** | 6 | Valuable optimizations | Medium-term (1-2 weeks) |
| **Low** | 4 | Nice-to-have improvements | Long-term (2-4 weeks) |

## Critical Actions (Immediate)
1. **Fix @quality technical issues** (defect resolution)
2. **Maintain Switch orchestrator** (system coordination)
3. **Keep Telegram channel** (primary communication)
4. **Preserve memory system** (context continuity)

## High-Value Improvements (Short-term)
1. **Optimize vector retriever** (performance issues)
2. **Complete website deployment** (vash1st.com)
3. **Simplify agent router** (reduce complexity)
4. **Optimize communication channels** (reduce maintenance)

## Decommission Planning
1. **Signal integration** (unstable, high maintenance)
   - Remove configuration
   - Update TOOLS.md
   - Notify if any dependencies exist
2. **Evaluate social media presence** (low ROI consideration)

## Quality Impact Projection
- **Current system quality:** 8.79/10
- **Post-improvement target:** 9.0+/10
- **Maintenance reduction:** 20-30% estimated
- **Complexity reduction:** 15-25% estimated

## Next Phase: Milestone 2
**Implementation planning** based on this decision table:
1. Create implementation roadmap
2. Assign priorities and timelines
3. Execute improvements in priority order
4. Monitor quality impact

## Notes
- **Proxy audit** used due to @quality technical issues (defect logged)
- **Decisions based on** quality scores, value assessment, maintenance cost
- **Framework adapted** for technical constraints (documented transparently)
- **All changes tracked** in refinement-progress.md