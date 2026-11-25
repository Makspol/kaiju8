from app.modules.workflows import repository
from app.modules.workflows.field_analyzer import infer_node_input_fields
from app.modules.workflows.validator import validate_graph
from app.runtime.engine import WorkflowEngine
from app.modules.executions.service import create_execution
from app.modules.users.service import create_user, get_user


DEV_USER_EMAIL = "dev@kaiju8.local"
DEV_USER_NAME = "Kaiju8 Dev User"


def create_workflow(
    name: str,
    graph: dict | None = None,
    owner_user_id: str | None = None,
) -> dict | None:
    clean_name = name.strip() if name else "Untitled workflow"
    owner_user_id = owner_user_id or _ensure_dev_user()["id"]

    if get_user(owner_user_id) is None:
        return None

    return repository.create_workflow(
        name=clean_name,
        graph=graph,
        owner_user_id=owner_user_id,
    )


def list_workflows(
    owner_user_id: str | None = None,
) -> list[dict]:
    return repository.list_workflows(owner_user_id=owner_user_id)


def get_workflow(
    workflow_id: str,
    owner_user_id: str | None = None,
) -> dict | None:
    workflow = repository.get_workflow(workflow_id)

    if workflow is None:
        return None

    if owner_user_id is None:
        return workflow

    if workflow["owner_user_id"] != owner_user_id:
        return None

    return workflow


def update_workflow(
    workflow_id: str,
    payload: dict,
    owner_user_id: str | None = None,
) -> dict | None:
    workflow = get_workflow(
        workflow_id=workflow_id,
        owner_user_id=owner_user_id,
    )

    if workflow is None:
        return None

    return repository.update_workflow(workflow_id, payload)


def delete_workflow(
    workflow_id: str,
    owner_user_id: str | None = None,
) -> bool:
    workflow = get_workflow(
        workflow_id=workflow_id,
        owner_user_id=owner_user_id,
    )

    if workflow is None:
        return False

    return repository.delete_workflow(
        workflow_id=workflow_id,
        owner_user_id=owner_user_id,
    )


def run_workflow(
    workflow_id: str,
    input_json: dict | None = None,
    owner_user_id: str | None = None,
    trigger_node_id: str | None = None,
) -> dict | None:
    workflow = get_workflow(
        workflow_id=workflow_id,
        owner_user_id=owner_user_id,
    )

    if workflow is None:
        return None

    input_json = input_json or {}
    validation = validate_graph(workflow["graph"])

    if not validation["valid"]:
        result = {
            "status": "failed",
            "output": {},
            "error": "workflow_validation_failed",
            "validation": validation,
            "steps": [],
        }

        execution = create_execution(
            workflow_id=workflow_id,
            input_json=input_json,
            result=result,
        )
        execution["validation"] = validation

        return execution

    engine = WorkflowEngine()

    result = engine.execute(
        graph=workflow["graph"],
        input_json=input_json,
        owner_user_id=owner_user_id,
        trigger_node_id=trigger_node_id,
    )

    return create_execution(
        workflow_id=workflow_id,
        input_json=input_json,
        result=result,
    )


def get_node_input_fields(
    workflow_id: str,
    node_id: str,
    owner_user_id: str | None = None,
) -> dict | None:
    workflow = get_workflow(
        workflow_id=workflow_id,
        owner_user_id=owner_user_id,
    )

    if workflow is None:
        return None

    return infer_node_input_fields(
        graph=workflow["graph"],
        node_id=node_id,
    )


def _ensure_dev_user() -> dict:
    return create_user(
        email=DEV_USER_EMAIL,
        name=DEV_USER_NAME,
    )
