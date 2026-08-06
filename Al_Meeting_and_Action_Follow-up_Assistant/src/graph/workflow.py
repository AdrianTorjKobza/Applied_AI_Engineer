"""
Assembles the LangGraph StateGraph for the Local AI Meeting Assistant.
Configures MemorySaver checkpointer and HITL interrupt_before on write_eml_node.
"""

from typing import Any, Dict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.graph.nodes import (
    chunk_transcript_node,
    draft_email_node,
    map_summarize_node,
    reduce_synthesize_node,
    write_eml_node,
    write_markdown_node,
)
from src.graph.state import MeetingState


def build_meeting_assistant_graph() -> Any:
    """
    Constructs and compiles the Meeting Assistant LangGraph workflow.
    
    Graph Topology:
      [START] 
         -> chunk_transcript_node
         -> map_summarize_node
         -> reduce_synthesize_node
         -> write_markdown_node (Automated .md output)
         -> draft_email_node
         -> [HITL INTERRUPT]
         -> write_eml_node (Conditional .eml output)
         -> [END]
    """
    builder = StateGraph(MeetingState)

    # 1. Register Graph Nodes
    builder.add_node("chunk_transcript_node", chunk_transcript_node)
    builder.add_node("map_summarize_node", map_summarize_node)
    builder.add_node("reduce_synthesize_node", reduce_synthesize_node)
    builder.add_node("write_markdown_node", write_markdown_node)
    builder.add_node("draft_email_node", draft_email_node)
    builder.add_node("write_eml_node", write_eml_node)

    # 2. Define Sequential & Conditional Edges
    builder.add_edge(START, "chunk_transcript_node")
    builder.add_edge("chunk_transcript_node", "map_summarize_node")
    builder.add_edge("map_summarize_node", "reduce_synthesize_node")
    builder.add_edge("reduce_synthesize_node", "write_markdown_node")
    builder.add_edge("write_markdown_node", "draft_email_node")
    
    # Execution halts AFTER draft_email_node finishes, right BEFORE write_eml_node starts
    builder.add_edge("draft_email_node", "write_eml_node")
    builder.add_edge("write_eml_node", END)

    # 3. Attach Checkpointer & Specify HITL Interruption Boundary
    checkpointer = MemorySaver()
    
    compiled_graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["write_eml_node"],
    )

    return compiled_graph


# Shared singleton compiled graph
meeting_graph = build_meeting_assistant_graph()