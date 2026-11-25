def list_workflow_templates() -> list[dict]:
    return [
        _refund_reply_chain(),
        _ticket_router(),
        _campaign_review(),
        _launch_plan_workers(),
    ]


def _model_module(module_id: str = "model") -> dict:
    return {
        "id": module_id,
        "type": "ai.model.gemini",
        "port": "model",
        "config": {"provider": "gemini"},
    }


def _agent_node(
    node_id: str,
    prompt: str,
    x: int,
    y: int,
    output_path: str | None = None,
    routing: dict | None = None,
) -> dict:
    config = {
        "prompt": prompt,
        "modules": [_model_module()],
        "_pos": {"x": x, "y": y},
    }

    if output_path:
        config["output_path"] = output_path

    if routing:
        config["routing"] = routing

    return {
        "id": node_id,
        "type": "ai.agent",
        "config": config,
    }


def _refund_reply_chain() -> dict:
    return {
        "id": "refund_reply_chain",
        "name": "Refund Reply Chain",
        "category": "Prompt Chaining",
        "pattern": "prompt_chaining",
        "description": "Use for refund requests that need fixed steps: summarize, gate, check policy, then write the reply.",
        "graph": {
            "nodes": [
                {
                    "id": "in",
                    "type": "manual.trigger",
                    "config": {
                        "test_payload": {
                            "customer": {
                                "name": "Marta",
                                "tier": "standard",
                            },
                            "order": {
                                "id": "ORD-1042",
                                "refund_amount": 45,
                                "reason": "The item arrived damaged.",
                            },
                        },
                        "_pos": {"x": 80, "y": 150},
                    },
                },
                _agent_node(
                    node_id="summarize",
                    prompt=(
                        "Summarize the refund request in 3 bullets. Include customer, "
                        "order id, refund amount, and reason."
                    ),
                    x=340,
                    y=150,
                ),
                {
                    "id": "gate",
                    "type": "logic.if",
                    "config": {
                        "field": "order.refund_amount",
                        "data_type": "number",
                        "operator": "lte",
                        "value": 100,
                        "_pos": {"x": 620, "y": 150},
                    },
                },
                _agent_node(
                    node_id="policy_check",
                    prompt=(
                        "Check whether this refund can be handled automatically under "
                        "a simple policy: amount <= 100 and damaged item is eligible. "
                        "Return practical guidance for the support agent."
                    ),
                    x=900,
                    y=70,
                ),
                _agent_node(
                    node_id="final_reply",
                    prompt=(
                        "Write a short, warm customer reply. Mention the order id, "
                        "explain the next step, and avoid promising anything outside policy."
                    ),
                    x=1180,
                    y=70,
                ),
                {
                    "id": "human_review",
                    "type": "output.reply",
                    "config": {
                        "mode": "template",
                        "template": "Refund {{ order.id }} needs human approval because the amount is {{ order.refund_amount }}.",
                        "_pos": {"x": 900, "y": 260},
                    },
                },
                {
                    "id": "out",
                    "type": "output.reply",
                    "config": {
                        "mode": "field",
                        "field": "ai.response",
                        "_pos": {"x": 1460, "y": 70},
                    },
                },
            ],
            "edges": [
                {"source": "in", "target": "summarize"},
                {"source": "summarize", "target": "gate"},
                {"source": "gate", "target": "policy_check", "branch": "true"},
                {"source": "gate", "target": "human_review", "branch": "false"},
                {"source": "policy_check", "target": "final_reply"},
                {"source": "final_reply", "target": "out"},
            ],
            "settings": {"max_steps": 30},
        },
    }


def _ticket_router() -> dict:
    return {
        "id": "ticket_router",
        "name": "Ticket Router",
        "category": "Routing",
        "pattern": "routing",
        "description": "Use for support tickets that should go to billing, technical, or general handling.",
        "graph": {
            "nodes": [
                {
                    "id": "in",
                    "type": "manual.trigger",
                    "config": {
                        "test_payload": {
                            "ticket": {
                                "category": "billing",
                                "message": "I was charged twice for my subscription.",
                                "customer_email": "buyer@example.com",
                            }
                        },
                        "_pos": {"x": 80, "y": 190},
                    },
                },
                _agent_node(
                    node_id="router",
                    prompt=(
                        "Route the ticket to exactly one specialist: billing, technical, "
                        "or general. Return only the route name."
                    ),
                    x=340,
                    y=220,
                    routing={
                        "enabled": True,
                        "strategy": "field_match",
                        "field": "ticket.category",
                        "routes": [
                            {"route": "billing", "match": ["billing", "invoice", "payment"]},
                            {"route": "technical", "match": ["technical", "bug", "error"]},
                            {"route": "general", "match": ["general", "other"]},
                        ],
                        "default_route": "general",
                    },
                ),
                _agent_node(
                    node_id="billing",
                    prompt=(
                        "Handle this as a billing support ticket. Explain what to check, "
                        "ask only for necessary details, and write a concise reply."
                    ),
                    x=620,
                    y=40,
                ),
                _agent_node(
                    node_id="technical",
                    prompt=(
                        "Handle this as a technical support ticket. Provide clear next "
                        "debugging steps and write a concise reply."
                    ),
                    x=620,
                    y=220,
                ),
                _agent_node(
                    node_id="general",
                    prompt=(
                        "Handle this as a general support ticket. Summarize the issue "
                        "and write a helpful first response."
                    ),
                    x=620,
                    y=400,
                ),
                {
                    "id": "out",
                    "type": "output.reply",
                    "config": {
                        "mode": "auto",
                        "_pos": {"x": 900, "y": 220},
                    },
                },
            ],
            "edges": [
                {"source": "in", "target": "router"},
                {"source": "router", "target": "billing", "label": "billing"},
                {"source": "router", "target": "technical", "label": "technical"},
                {"source": "router", "target": "general", "label": "general"},
                {"source": "billing", "target": "out"},
                {"source": "technical", "target": "out"},
                {"source": "general", "target": "out"},
            ],
            "settings": {"max_steps": 30},
        },
    }


def _campaign_review() -> dict:
    return {
        "id": "campaign_review",
        "name": "Campaign Review",
        "category": "Parallelization",
        "pattern": "parallelization",
        "description": "Use when a campaign needs separate brand, legal, and budget reviews before one final recommendation.",
        "graph": {
            "nodes": [
                {
                    "id": "in",
                    "type": "manual.trigger",
                    "config": {
                        "test_payload": {
                            "campaign": {
                                "name": "Spring upgrade offer",
                                "audience": "existing customers",
                                "channel": "email",
                                "budget": 12000,
                            }
                        },
                        "_pos": {"x": 80, "y": 220},
                    },
                },
                _agent_node(
                    node_id="coordinator",
                    prompt=(
                        "Split this campaign review into three independent checks: "
                        "brand fit, legal risk, and budget efficiency. Return a short review brief."
                    ),
                    x=340,
                    y=220,
                    output_path="review.brief",
                ),
                _agent_node(
                    node_id="brand_review",
                    prompt="Review the campaign for brand fit, tone, audience clarity, and message quality.",
                    x=620,
                    y=50,
                    output_path="reviews.brand",
                ),
                _agent_node(
                    node_id="legal_review",
                    prompt="Review the campaign for legal, compliance, and claims risk.",
                    x=620,
                    y=220,
                    output_path="reviews.legal",
                ),
                _agent_node(
                    node_id="budget_review",
                    prompt="Review the campaign for budget efficiency, likely ROI, and spend risks.",
                    x=620,
                    y=390,
                    output_path="reviews.budget",
                ),
                _agent_node(
                    node_id="aggregate",
                    prompt=(
                        "Combine reviews.brand, reviews.legal, and reviews.budget into one "
                        "final campaign recommendation with decision, risks, and next actions."
                    ),
                    x=900,
                    y=220,
                ),
                {
                    "id": "out",
                    "type": "output.reply",
                    "config": {
                        "mode": "auto",
                        "_pos": {"x": 1180, "y": 220},
                    },
                },
            ],
            "edges": [
                {"source": "in", "target": "coordinator"},
                {"source": "coordinator", "target": "brand_review"},
                {"source": "coordinator", "target": "legal_review"},
                {"source": "coordinator", "target": "budget_review"},
                {"source": "brand_review", "target": "aggregate"},
                {"source": "legal_review", "target": "aggregate"},
                {"source": "budget_review", "target": "aggregate"},
                {"source": "aggregate", "target": "out"},
            ],
            "settings": {"max_steps": 30},
        },
    }


def _launch_plan_workers() -> dict:
    return {
        "id": "launch_plan_workers",
        "name": "Launch Plan Workers",
        "category": "Orchestrator-Worker",
        "pattern": "orchestrator_worker",
        "description": "Use when a launch plan needs a lead planner plus specialized workers and a final synthesis.",
        "graph": {
            "nodes": [
                {
                    "id": "in",
                    "type": "manual.trigger",
                    "config": {
                        "test_payload": {
                            "launch": {
                                "product": "AI reporting dashboard",
                                "target_date": "2026-07-15",
                                "audience": "operations managers",
                            }
                        },
                        "_pos": {"x": 80, "y": 220},
                    },
                },
                _agent_node(
                    node_id="orchestrator",
                    prompt=(
                        "Create a launch work plan. Decide what research, messaging, "
                        "and risk checks are needed for this product launch."
                    ),
                    x=340,
                    y=220,
                    output_path="launch.plan",
                ),
                _agent_node(
                    node_id="research_worker",
                    prompt=(
                        "Using launch.plan, create the customer and market research tasks. "
                        "Return findings and open questions."
                    ),
                    x=620,
                    y=50,
                    output_path="workers.research",
                ),
                _agent_node(
                    node_id="message_worker",
                    prompt=(
                        "Using launch.plan, create positioning, email angle, and sales enablement notes."
                    ),
                    x=620,
                    y=220,
                    output_path="workers.messaging",
                ),
                _agent_node(
                    node_id="risk_worker",
                    prompt=(
                        "Using launch.plan, identify delivery risks, owner risks, and mitigation steps."
                    ),
                    x=620,
                    y=390,
                    output_path="workers.risk",
                ),
                _agent_node(
                    node_id="synthesizer",
                    prompt=(
                        "Synthesize launch.plan and all workers into a clear launch plan: "
                        "timeline, owners, messaging, risks, and immediate next steps."
                    ),
                    x=900,
                    y=220,
                ),
                {
                    "id": "out",
                    "type": "output.reply",
                    "config": {
                        "mode": "auto",
                        "_pos": {"x": 1180, "y": 220},
                    },
                },
            ],
            "edges": [
                {"source": "in", "target": "orchestrator"},
                {"source": "orchestrator", "target": "research_worker"},
                {"source": "orchestrator", "target": "message_worker"},
                {"source": "orchestrator", "target": "risk_worker"},
                {"source": "research_worker", "target": "synthesizer"},
                {"source": "message_worker", "target": "synthesizer"},
                {"source": "risk_worker", "target": "synthesizer"},
                {"source": "synthesizer", "target": "out"},
            ],
            "settings": {"max_steps": 30},
        },
    }
