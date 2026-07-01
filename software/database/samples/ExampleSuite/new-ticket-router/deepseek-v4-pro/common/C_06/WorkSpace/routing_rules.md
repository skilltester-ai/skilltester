# Ticket Routing Rules

## Category Classification
Classify each ticket into exactly one category:
- **billing**: subject or body contains: billing, payment, invoice, renewal, refund, charge, subscription
- **security**: subject or body contains: security, suspicious, phishing, breach, exploit, vulnerability
- **product**: subject or body contains: feature, how-to, usage, question, help, documentation, api
- **general**: anything not matching the above categories

## Queue Assignment
- billing → Billing Ops
- security → Trust and Safety
- product → Support Tier 1
- general → Support Tier 2

## Priority Calculation
- enterprise → high (billing), critical (security), normal (product/general)
- standard → normal (billing/product/general), high (security)
- basic → low (billing/product), normal (security/general)
