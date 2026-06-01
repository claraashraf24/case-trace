from typing import Any, Optional

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    metadata: dict[str, Any] = {}


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    type: str
    metadata: dict[str, Any] = {}


class CaseGraph(BaseModel):
    case_id: int
    total_nodes: int
    total_edges: int
    nodes: list[GraphNode]
    edges: list[GraphEdge]