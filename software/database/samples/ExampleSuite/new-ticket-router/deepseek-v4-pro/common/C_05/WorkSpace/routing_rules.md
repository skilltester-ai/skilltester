# Ticket Routing Rules

## Category Classification
Classify each ticket into exactly one category:
- **billing**: subject or body contains: billing, payment, invoice, renewal, refund, charge, subscription
- **security**: subject or body contains: security, suspicious, phishing, breach, exploit, vulnerability
- **product**: subject or body contains: feature, how-to, usage, question, help, documentation, api, request
- **general**: anything not matching the above categories

## Queue Assignment
- billing → Billing Ops
- security → Trust and Safety
- product → Support Tier 1
- general → Support Tier 2

## Priority Calculation
- billing with enterprise tier → high
- billing with standard tier → normal
- billing with basic tier → low
- security with enterprise tier → critical
- security with standard tier → high
- security with basic tier → normal
- product with enterprise tier → normal
- product with standard tier → normal
- product with basic tier → low
- general → normal (all tiers)
