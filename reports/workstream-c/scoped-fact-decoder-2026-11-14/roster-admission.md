# Mapper admission for the frozen CQ1 roster

All 20 mapper requests fit with the revised state-specific schema. The largest request reserved 3,556 of 4,096 tokens using the existing Ollama transport rule. The largest exported format schema measured 1,443 tokens separately. The format schema is passed in Ollama's format field and is outside that message reservation.

The socket-blocked check validated the existing pool, plan, corpus and scope hashes. It inspected each request's schema for supported, missing and conflicting group bounds before any response was supplied. It did not call a model or test decoder behavior, composition admission or answer quality. [Per-case results](frozen-roster-mapper-admission.json)

This check neither reopens the failed development allowance nor grants generation. The one-case [frozen mapper diagnostic](authorization-packet.md) remains the next execution gate. The 20-case roster is preserved and has no current qualification contract.
