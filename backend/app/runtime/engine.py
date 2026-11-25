from app.runtime.registry import NodeRegistry
from app.runtime.limits import ExecutionLimitExceeded
from app.runtime.types import ExecutionContext


class WorkflowEngine:
    def __init__(self):
        self.registry = NodeRegistry()

    def execute(
        self,
        graph: dict,
        input_json: dict,
        owner_user_id: str | None = None,
        trigger_node_id: str | None = None,
    ) -> dict:
        nodes = {node["id"]: node for node in graph["nodes"]}
        edges = graph.get("edges", [])
        settings = graph.get("settings", {})

        max_steps = settings.get("max_steps", 20)
        timeout_seconds = settings.get("timeout_seconds")
        budget = settings.get("budget")
        max_llm_calls = settings.get("max_llm_calls")
        max_tokens = settings.get("max_tokens")
        ai_limits = settings.get("ai_limits")

        start_node_id = self._find_start_node_id(
            nodes=graph["nodes"],
            trigger_node_id=trigger_node_id,
        )
        trigger_node = nodes[start_node_id]
        active_node_ids = {start_node_id}
        executed_node_ids = set()
        current_data = input_json
        context = ExecutionContext(
            initial_input=input_json,
            owner_user_id=owner_user_id,
            trigger_node_id=start_node_id,
            trigger_node_type=trigger_node["type"],
            max_steps=max_steps,
            timeout_seconds=timeout_seconds,
            budget=budget,
            max_llm_calls=max_llm_calls,
            max_tokens=max_tokens,
            ai_limits=ai_limits if isinstance(ai_limits, dict) else {},
        )
        steps = []

        for _ in range(max_steps):
            ready_node_ids = self._ready_node_ids(
                graph["nodes"],
                edges,
                active_node_ids,
                executed_node_ids,
            )

            if not ready_node_ids:
                if active_node_ids - executed_node_ids:
                    return {
                        "status": "failed",
                        "output": current_data,
                        "error": "waiting_for_inputs",
                        "steps": steps,
                        "usage": context.usage.as_dict(),
                    }

                return {
                    "status": "success",
                    "output": current_data,
                    "error": None,
                    "steps": steps,
                    "usage": context.usage.as_dict(),
                }

            current_node_id = ready_node_ids[0]

            try:
                context.ensure_not_timed_out()
            except ExecutionLimitExceeded as error:
                return {
                    "status": "failed",
                    "output": current_data,
                    "error": error.code,
                    "steps": steps,
                    "usage": context.usage.as_dict(),
                }

            node = nodes[current_node_id]
            executor = self.registry.get(node["type"])

            if executor is None:
                return {
                    "status": "failed",
                    "output": current_data,
                    "error": f"Unknown node type: {node['type']}",
                    "steps": steps,
                }

            node_input = (
                self._node_input(
                    node_id=current_node_id,
                    edges=edges,
                    active_node_ids=active_node_ids,
                    node_outputs=context.node_outputs,
                )
                if executor.has_input
                else {}
            )

            try:
                result = executor.execute(
                    config=node.get("config", {}),
                    input_data=node_input,
                    context=context,
                )
            except ExecutionLimitExceeded as error:
                return {
                    "status": "failed",
                    "output": current_data,
                    "error": error.code,
                    "steps": steps,
                    "usage": context.usage.as_dict(),
                }

            steps.append({
                "node_id": current_node_id,
                "node_type": node["type"],
                "status": "success",
                "input": node_input,
                "output": result.output,
            })

            context.node_outputs[current_node_id] = result.output
            executed_node_ids.add(current_node_id)
            current_data = result.output

            if result.final:
                return {
                    "status": "success",
                    "output": current_data,
                    "error": None,
                    "steps": steps,
                    "usage": context.usage.as_dict(),
                }

            route = result.output.get("route") if isinstance(result.output, dict) else None
            for edge in self._selected_outgoing_edges(edges, current_node_id, route):
                target_node_id = edge["target"]

                if target_node_id in executed_node_ids:
                    return {
                        "status": "failed",
                        "output": current_data,
                        "error": "max_steps_exceeded",
                        "steps": steps,
                        "usage": context.usage.as_dict(),
                    }

                active_node_ids.add(target_node_id)

        return {
            "status": "failed",
            "output": current_data,
            "error": "max_steps_exceeded",
            "steps": steps,
            "usage": context.usage.as_dict(),
        }

    def _find_start_node_id(
        self,
        nodes: list[dict],
        trigger_node_id: str | None = None,
    ) -> str:
        registry = self.registry

        if trigger_node_id:
            for node in nodes:
                if node.get("id") != trigger_node_id:
                    continue

                executor = registry.get(node.get("type"))

                if executor and executor.category == "trigger":
                    return node["id"]

                raise ValueError("Workflow start node must be a trigger.")

            raise ValueError("Workflow trigger was not found.")

        for node in nodes:
            executor = registry.get(node["type"])

            if executor and executor.category == "trigger":
                return node["id"]

        raise ValueError("Workflow has no trigger.")

    def _selected_outgoing_edges(
        self,
        edges: list[dict],
        current_node_id: str,
        route: str | None = None,
    ) -> list[dict]:
        outgoing_edges = [
            edge
            for edge in edges
            if edge["source"] == current_node_id
        ]

        if not outgoing_edges:
            return []

        if route is not None:
            route = str(route).lower()
            matching_edges = []

            for edge in outgoing_edges:
                edge_route = self._edge_route(edge)

                if edge_route is not None and str(edge_route).lower() == route:
                    matching_edges.append(edge)

            if matching_edges:
                return matching_edges

            if len(outgoing_edges) > 1:
                return []

        return outgoing_edges

    def _ready_node_ids(
        self,
        nodes: list[dict],
        edges: list[dict],
        active_node_ids: set[str],
        executed_node_ids: set[str],
    ) -> list[str]:
        return [
            node["id"]
            for node in nodes
            if self._node_is_ready(
                node=node,
                edges=edges,
                active_node_ids=active_node_ids,
                executed_node_ids=executed_node_ids,
            )
        ]

    def _node_is_ready(
        self,
        node: dict,
        edges: list[dict],
        active_node_ids: set[str],
        executed_node_ids: set[str],
    ) -> bool:
        node_id = node["id"]

        if node_id not in active_node_ids or node_id in executed_node_ids:
            return False

        executor = self.registry.get(node["type"])

        if executor is None or not executor.has_input:
            return True

        return self._active_upstream_sources_done(
            node_id=node_id,
            edges=edges,
            active_node_ids=active_node_ids,
            executed_node_ids=executed_node_ids,
        )

    def _active_upstream_sources_done(
        self,
        node_id: str,
        edges: list[dict],
        active_node_ids: set[str],
        executed_node_ids: set[str],
    ) -> bool:
        incoming_sources = [
            edge["source"]
            for edge in edges
            if edge["target"] == node_id
        ]

        for source_id in incoming_sources:
            if source_id in active_node_ids:
                if source_id not in executed_node_ids:
                    return False
                continue

            if self._can_still_reach(
                target_id=source_id,
                edges=edges,
                active_node_ids=active_node_ids,
                executed_node_ids=executed_node_ids,
            ):
                return False

        return True

    def _can_still_reach(
        self,
        target_id: str,
        edges: list[dict],
        active_node_ids: set[str],
        executed_node_ids: set[str],
    ) -> bool:
        frontier = [
            node_id
            for node_id in active_node_ids
            if node_id not in executed_node_ids
        ]
        seen = set(frontier)

        while frontier:
            current_id = frontier.pop(0)

            if current_id == target_id:
                return True

            for edge in edges:
                if edge["source"] != current_id:
                    continue

                next_id = edge["target"]

                if next_id in seen or next_id in executed_node_ids:
                    continue

                seen.add(next_id)
                frontier.append(next_id)

        return False

    def _node_input(
        self,
        node_id: str,
        edges: list[dict],
        active_node_ids: set[str],
        node_outputs: dict[str, dict],
    ) -> dict:
        predecessor_ids = [
            edge["source"]
            for edge in edges
            if edge["target"] == node_id
            and edge["source"] in active_node_ids
            and edge["source"] in node_outputs
        ]

        if not predecessor_ids:
            return {}

        if len(predecessor_ids) == 1:
            return node_outputs[predecessor_ids[0]]

        merged = {}
        branches = {}

        for predecessor_id in predecessor_ids:
            output = node_outputs[predecessor_id]
            branches[predecessor_id] = output
            merged = self._deep_merge(merged, output)

        merged["_branches"] = branches
        return merged

    def _deep_merge(self, left: dict, right: dict) -> dict:
        merged = dict(left)

        for key, value in right.items():
            current = merged.get(key)

            if isinstance(current, dict) and isinstance(value, dict):
                merged[key] = self._deep_merge(current, value)
            else:
                merged[key] = value

        return merged

    def _edge_route(self, edge: dict) -> str | None:
        return edge.get("label") or edge.get("branch") or edge.get("condition")
