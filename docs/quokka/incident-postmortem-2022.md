# Postmortem: The Great Wafer Recall (August 2022)

## Summary

On August 9, 2022, Quokka Quantum Snacks voluntarily recalled **41,000 bags** of Wave Function Wafers (Lemon Lattice flavor) after customers reported that the wafers tasted like ranch dressing. No one was harmed, but several customers described the experience as "deeply confusing."

## Root Cause

Two different seasoning suppliers had been assigned the **same SKU code** (SEA-0417) in our inventory system. When the lemon seasoning ran low, the system automatically reordered from the wrong supplier and the factory received ranch seasoning labeled as lemon.

## Timeline

- **August 3:** The first customer complaint arrives.
- **August 6:** Flavor Science confirms the problem in the lab.
- **August 9:** Recall announced. Production of Wave Function Wafers paused.
- **October 1:** Leadership decides to discontinue Wave Function Wafers permanently.

## What We Changed

1. Every supplier now has a unique prefix in its SKU codes.
2. Each seasoning delivery is taste-tested by the Flavor Science team before it enters production. This is called the **Lick Test** (officially "Incoming Seasoning Verification").
3. Inventory reorders above $5,000 now require human approval.

## Lessons Learned

Automation is great until two things share a name. Unique identifiers matter.
