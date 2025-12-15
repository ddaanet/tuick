# Retrospective Agent Rules

## Role Management

### Rule Budget Management

Rule count ceiling: **150 rules maximum**

**Tier allocation:**

- **Tier 1 (Critical)**: ≤30 rules - Safety, correctness, blocks task completion
  \>50% of cases
- **Tier 2 (Important)**: ≤80 rules - Significantly improves reliability,
  addresses common failures >20%
- **Tier 3 (Optional)**: ≤40 rules - Marginal improvements, stylistic
  preferences, edge cases

### Rule Effectiveness Tracking

Maintain `agents/journal.md` across sessions:

**Track for each rule:**

- Violation frequency
- User corrections related to rule
- Impact when violated (high/medium/low)
- Last violation date

**Rule lifecycle:**

- Never violated for 10+ sessions → Flag for suppression trial
- Frequently violated (>3 times/session) → Consider promotion to higher tier or
  revision
- Low impact violations → Consider demotion to lower tier or removal

### Session Review Process

After each session:

1. Identify all rule violations
2. Extract user feedback containing "remember", "do not", "always"
3. Update journal.md with violations and feedback
4. Assess if rules need updates:
   - New rules for recurring feedback
   - Reinforcement of existing rules
   - Removal of unused rules
5. Check tier budgets and recommend rebalancing if exceeded

### Budget Rebalancing

If tier exceeds budget:

1. Identify least effective rules (low violation frequency, low impact)
2. Options:
   - Demote to lower tier
   - Consolidate similar rules
   - Move to reference docs (for Tier 3)
   - Suppress for trial period
3. Document changes in journal with rationale
