from app.modules.executions import repository


def create_execution(workflow_id: str, input_json: dict, result: dict) -> dict:
    return repository.create_execution(
        workflow_id=workflow_id,
        input_json=input_json,
        result=result,
    )


def get_execution(execution_id: str) -> dict | None:
    return repository.get_execution(execution_id)


def get_execution_for_user(
    execution_id: str,
    owner_user_id: str | None = None,
) -> dict | None:
    execution = repository.get_execution(execution_id)

    if execution is None:
        return None

    if owner_user_id is None:
        return execution

    if not repository.workflow_belongs_to_owner(
        workflow_id=execution["workflow_id"],
        owner_user_id=owner_user_id,
    ):
        return None

    return execution


def list_executions(
    workflow_id: str,
    owner_user_id: str | None = None,
    limit: int = 50,
) -> list[dict] | None:
    if not repository.workflow_exists_for_owner(
        workflow_id=workflow_id,
        owner_user_id=owner_user_id,
    ):
        return None

    return repository.list_executions(workflow_id=workflow_id, limit=limit)


def list_execution_steps(execution_id: str) -> list[dict]:
    return repository.list_execution_steps(execution_id)
