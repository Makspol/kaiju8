from fastapi import APIRouter

from app.modules.workflow_templates.service import list_workflow_templates


router = APIRouter()


@router.get("")
def list_workflow_templates_route():
    return list_workflow_templates()
