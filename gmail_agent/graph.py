from langgraph.graph import StateGraph, END
from .state import AgentState
from .agents.strategist import strategist_node
from .agents.executor import executor_node

def define_graph():
    # Initialize Graph
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("executor", executor_node)
    
    # Define Entry Point
    workflow.set_entry_point("strategist")
    
    # Conditional Edge Logic
    def route_after_strategist(state):
        if state.get("is_lead"):
            return "executor"
        else:
            return END
            
    # Add Edges
    workflow.add_conditional_edges(
        "strategist",
        route_after_strategist,
        {
            "executor": "executor",
            END: END
        }
    )
    
    workflow.add_edge("executor", END)
    
    # Compile
    app = workflow.compile()
    return app

# Expose the runnable graph
agent_graph = define_graph()
