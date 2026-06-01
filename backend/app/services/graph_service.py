from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.evidence import Evidence
from app.models.event import Event
from app.schemas.graph import CaseGraph, GraphEdge, GraphNode
from app.services.contradiction_service import detect_case_contradictions


def add_node_once(
    nodes: dict[str, GraphNode],
    node_id: str,
    label: str,
    node_type: str,
    metadata: dict | None = None,
) -> None:
    if node_id in nodes:
        return

    nodes[node_id] = GraphNode(
        id=node_id,
        label=label,
        type=node_type,
        metadata=metadata or {},
    )


def add_edge_once(
    edges: dict[str, GraphEdge],
    edge_id: str,
    source: str,
    target: str,
    label: str,
    edge_type: str,
    metadata: dict | None = None,
) -> None:
    if edge_id in edges:
        return

    edges[edge_id] = GraphEdge(
        id=edge_id,
        source=source,
        target=target,
        label=label,
        type=edge_type,
        metadata=metadata or {},
    )


def build_case_graph(db: Session, case_id: int) -> CaseGraph:
    case = db.query(Case).filter(Case.id == case_id).first()

    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}

    if not case:
        return CaseGraph(
            case_id=case_id,
            total_nodes=0,
            total_edges=0,
            nodes=[],
            edges=[],
        )

    case_node_id = f"case:{case.id}"

    add_node_once(
        nodes=nodes,
        node_id=case_node_id,
        label=case.title,
        node_type="case",
        metadata={
            "status": case.status,
            "priority": case.priority,
            "case_type": case.case_type,
            "location": case.location,
        },
    )

    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .all()
    )

    events = (
        db.query(Event)
        .filter(Event.case_id == case_id)
        .all()
    )

    for evidence in evidence_items:
        evidence_node_id = f"evidence:{evidence.id}"

        add_node_once(
            nodes=nodes,
            node_id=evidence_node_id,
            label=evidence.title,
            node_type="evidence",
            metadata={
                "evidence_type": evidence.evidence_type,
                "source_name": evidence.source_name,
                "status": evidence.status,
                "confidence_score": evidence.confidence_score,
            },
        )

        add_edge_once(
            edges=edges,
            edge_id=f"{case_node_id}->evidence:{evidence.id}",
            source=case_node_id,
            target=evidence_node_id,
            label="contains evidence",
            edge_type="contains",
        )

    for event in events:
        event_node_id = f"event:{event.id}"

        add_node_once(
            nodes=nodes,
            node_id=event_node_id,
            label=f"{event.event_time or 'Unknown time'} — Event {event.id}",
            node_type="event",
            metadata={
                "event_time": event.event_time,
                "location": event.location,
                "confidence_score": event.confidence_score,
                "status": event.status,
                "description": event.description,
            },
        )

        add_edge_once(
            edges=edges,
            edge_id=f"{case_node_id}->event:{event.id}",
            source=case_node_id,
            target=event_node_id,
            label="has event",
            edge_type="has_event",
        )

        if event.evidence_id:
            add_edge_once(
                edges=edges,
                edge_id=f"evidence:{event.evidence_id}->event:{event.id}",
                source=f"evidence:{event.evidence_id}",
                target=event_node_id,
                label="supports event",
                edge_type="supports",
            )

        for person in event.participants or []:
            person_node_id = f"person:{person.lower().replace(' ', '_')}"

            add_node_once(
                nodes=nodes,
                node_id=person_node_id,
                label=person,
                node_type="person",
            )

            add_edge_once(
                edges=edges,
                edge_id=f"{person_node_id}->event:{event.id}",
                source=person_node_id,
                target=event_node_id,
                label="involved in",
                edge_type="involved_in",
            )

        if event.location:
            location_node_id = f"location:{event.location.lower().replace(' ', '_')}"

            add_node_once(
                nodes=nodes,
                node_id=location_node_id,
                label=event.location,
                node_type="location",
            )

            add_edge_once(
                edges=edges,
                edge_id=f"event:{event.id}->location:{event.location.lower().replace(' ', '_')}",
                source=event_node_id,
                target=location_node_id,
                label="occurred at",
                edge_type="occurred_at",
            )

        for object_name in event.objects or []:
            object_node_id = f"object:{object_name.lower().replace(' ', '_')}"

            add_node_once(
                nodes=nodes,
                node_id=object_node_id,
                label=object_name,
                node_type="object",
            )

            add_edge_once(
                edges=edges,
                edge_id=f"event:{event.id}->object:{object_name.lower().replace(' ', '_')}",
                source=event_node_id,
                target=object_node_id,
                label="mentions object",
                edge_type="mentions_object",
            )

    contradiction_summary = detect_case_contradictions(db=db, case_id=case_id)

    for index, finding in enumerate(contradiction_summary.findings, start=1):
        contradiction_node_id = f"contradiction:{index}"

        add_node_once(
            nodes=nodes,
            node_id=contradiction_node_id,
            label=f"{finding.severity.upper()} contradiction",
            node_type="contradiction",
            metadata={
                "contradiction_type": finding.contradiction_type,
                "severity": finding.severity,
                "description": finding.description,
                "confidence_score": finding.confidence_score,
            },
        )

        for event_id in finding.involved_event_ids:
            add_edge_once(
                edges=edges,
                edge_id=f"contradiction:{index}->event:{event_id}",
                source=contradiction_node_id,
                target=f"event:{event_id}",
                label="flags",
                edge_type="flags",
            )

    return CaseGraph(
        case_id=case_id,
        total_nodes=len(nodes),
        total_edges=len(edges),
        nodes=list(nodes.values()),
        edges=list(edges.values()),
    )