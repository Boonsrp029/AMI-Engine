"""Test exact fact-slot accounting with independently declared synthetic evidence."""
import json


def project(required, direct_sources, context_sources, selections):
    """Return exact evidence IDs and unresolved slots within the declared scope."""
    if set(selections) != set(required):
        raise ValueError("Each requested fact requires a decision")
    retained = set()
    unresolved = []
    for fact in required:
        selected = selections[fact]
        if selected is None:
            unresolved.append(fact)
            continue
        if selected not in direct_sources.get(fact, ()):
            raise ValueError("Selected span is not direct evidence for this fact")
        retained.add(selected)
        retained.update(context_sources.get((fact, selected), ()))
    return {"retained": sorted(retained), "unresolved": unresolved}


def main():
    # Independent synthetic source records. The allowed associations below are
    # fixture judgments, not facts inferred by the accounting function.
    harbor = {
        "history": "Earlier harbor transmitters operated in manual and automated modes.",
        "direct": "In automated mode, the transmitters could send berth vacancies weekly to the port clerk.",
        "background": "The port office also kept a log of vessel arrivals.",
    }
    district = {
        "installation": "The district paid 24,000 baht for installation in 2021.",
        "maintenance": "The annual maintenance fee was 3,500 baht in 2021.",
        "forecast": "The vendor forecast annual fees of 4,000 baht for 2023.",
    }
    harbor_facts = ("reported_item", "recipient")
    harbor_direct = {fact: {"direct"} for fact in harbor_facts}
    harbor_context = {(fact, "direct"): {"history"} for fact in harbor_facts}
    district_facts = ("installation_cost", "annual_maintenance_cost")
    district_direct = {fact: {span} for fact, span in zip(district_facts, ("installation", "maintenance"), strict=True)}
    history = project(harbor_facts, harbor_direct, harbor_context,
                      {"reported_item": "direct", "recipient": "direct"})
    assert history == {"retained": ["direct", "history"], "unresolved": []}
    assert "could send" in harbor["direct"]
    costs = project(district_facts, district_direct, {},
                    {"installation_cost": "installation", "annual_maintenance_cost": "maintenance"})
    assert costs == {"retained": ["installation", "maintenance"], "unresolved": []}
    partial = project(district_facts, district_direct, {},
                      {"installation_cost": "installation", "annual_maintenance_cost": None})
    assert partial == {"retained": ["installation"], "unresolved": ["annual_maintenance_cost"]}
    failures = {
        "silent fact omission": (district_facts, district_direct, {}, {"installation_cost": "installation"}),
        "wrong measure": (district_facts, district_direct, {},
                          {"installation_cost": "installation", "annual_maintenance_cost": "installation"}),
        "forecast substitution": (district_facts, district_direct, {},
                                  {"installation_cost": "installation", "annual_maintenance_cost": "forecast"}),
        "background as a response": (harbor_facts, harbor_direct, harbor_context,
                                     {"reported_item": "direct", "recipient": "background"}),
    }
    for name, args in failures.items():
        try:
            project(*args)
        except ValueError:
            continue
        raise AssertionError(name)
    print(json.dumps({"sources": [harbor, district], "historical_capability": history,
                      "distinct_costs": costs, "explicit_partial": partial, "rejected": list(failures),
                      "synthetic_checks_passed": 7, "model_calls": 0, "runtime_activated": False}, indent=2))


if __name__ == "__main__":
    main()
