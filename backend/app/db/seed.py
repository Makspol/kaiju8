from app.core.security import hash_password
from app.modules.users.service import (
    create_user,
    get_user_with_password_by_email,
    update_user_password_hash,
)
from app.modules.workflows.service import create_workflow, list_workflows


JANE_EMAIL = "edzhos@gmail.com"
JANE_NAME = "Jane Dzhos"
JANE_PASSWORD = "12345678"
JANE_WORKFLOW_NAME = "Jane quick test workflow"


JANE_TEST_GRAPH = {
    "nodes": [
        {
            "id": "manual_start",
            "type": "manual.trigger",
            "config": {
                "_pos": {"x": 80, "y": 120},
            },
        },
        {
            "id": "prepare_message",
            "type": "transform.edit_fields",
            "config": {
                "_pos": {"x": 340, "y": 120},
                "operations": [
                    {
                        "operation": "set",
                        "path": "message",
                        "value": "Hello Jane, workflow history is ready.",
                    },
                    {
                        "operation": "set",
                        "path": "seeded_for",
                        "value": JANE_EMAIL,
                    },
                ],
            },
        },
        {
            "id": "reply",
            "type": "output.reply",
            "config": {
                "_pos": {"x": 600, "y": 120},
            },
        },
    ],
    "edges": [
        {"source": "manual_start", "target": "prepare_message"},
        {"source": "prepare_message", "target": "reply"},
    ],
    "settings": {"max_steps": 10},
}


def seed_demo_data() -> None:
    user = get_user_with_password_by_email(JANE_EMAIL)
    password_hash = hash_password(JANE_PASSWORD)

    if user is None:
        user = create_user(
            email=JANE_EMAIL,
            name=JANE_NAME,
            password_hash=password_hash,
        )
    else:
        update_user_password_hash(
            user_id=user["id"],
            password_hash=password_hash,
        )

    workflows = list_workflows(owner_user_id=user["id"])

    if any(workflow["name"] == JANE_WORKFLOW_NAME for workflow in workflows):
        return

    create_workflow(
        name=JANE_WORKFLOW_NAME,
        graph=JANE_TEST_GRAPH,
        owner_user_id=user["id"],
    )
