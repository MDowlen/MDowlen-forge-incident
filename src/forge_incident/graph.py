from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .models import WorkflowState
from .nodes import (
    context_agent,
    correlation_agent,
    diagnosis_agent,
    normalize_agent,
    remediation_agent,
    report_agent,
)


def build_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("normalize", normalize_agent)
    graph.add_node("correlate", correlation_agent)
    graph.add_node("context", context_agent)
    graph.add_node("diagnose", diagnosis_agent)
    graph.add_node("remediate", remediation_agent)
    graph.add_node("report", report_agent)

    graph.add_edge(START, "normalize")
    graph.add_edge("normalize", "correlate")
    graph.add_edge("correlate", "context")
    graph.add_edge("context", "diagnose")
    graph.add_edge("diagnose", "remediate")
    graph.add_edge("remediate", "report")
    graph.add_edge("report", END)
    return graph.compile()
