from langgraph.graph import StateGraph, END

from app.workflows.state import WorkflowState
from app.workflows.nodes.create_task import create_task_node
from app.workflows.nodes.map_fields import map_fields_node
from app.workflows.nodes.resolve_values import resolve_values_node
from app.workflows.nodes.validate import validate_node
from app.workflows.nodes.hitl import hitl_node
from app.workflows.nodes.store_result import store_result_node


def build_autofill_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("create_task", create_task_node)
    graph.add_node("map_fields", map_fields_node)
    graph.add_node("resolve_values", resolve_values_node)
    graph.add_node("validate", validate_node)
    graph.add_node("hitl", hitl_node)
    graph.add_node("store_result", store_result_node)

    graph.set_entry_point("create_task")
    graph.add_edge("create_task", "map_fields")
    graph.add_edge("map_fields", "resolve_values")
    graph.add_edge("resolve_values", "validate")
    graph.add_edge("validate", "hitl")
    graph.add_edge("hitl", "store_result")
    graph.add_edge("store_result", END)

    return graph.compile()


autofill_workflow = build_autofill_graph()
