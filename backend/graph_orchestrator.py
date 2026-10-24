# backend/graph_orchestrator.py
# Pydantic Graph fault-tolerant inference mesh

from dataclasses import dataclass, field
import logging
from typing import List, Union
from pydantic import BaseModel, Field
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

logging.basicConfig(level=logging.INFO, format='[GRAPH_ORCHESTRATOR] %(asctime)s - %(levelname)s - %(message)s')

class GenerationOutput(BaseModel):
    selected_model: str = Field(description="The final inference runtime network selected to pass data.")
    result_text: str = Field(description="The parsed execution payload block returned from the model.")
    circuit_tripped: bool = Field(description="Indicates whether fallback loops were activated.")

@dataclass
class HighAvailabilityContext:
    primary_endpoint: str
    fallback_local_endpoints: List[str]
    generation_prompt: str
    current_retry_index: int = 0
    accumulated_errors: List[str] = field(default_factory=list)

class PrimaryInferenceNode(BaseNode[HighAvailabilityContext, None, GenerationOutput]):
    async def run(self, ctx: GraphRunContext[HighAvailabilityContext]) -> Union['LocalFallbackNode', End[GenerationOutput]]:
        state = ctx.state
        logging.info(f"Targeting Primary Cluster Node Loop -> {state.primary_endpoint}")
        try:
            if "fail" in state.generation_prompt.lower() or state.current_retry_index == 0:
                raise ConnectionError("Primary Cloud Inference degradation: API limit or cluster timeout reached.")
            return End(GenerationOutput(
                selected_model="Primary-Cloud-Cluster-V4",
                result_text="Execution completed successfully under optimal environment pathways.",
                circuit_tripped=False
            ))
        except Exception as e:
            logging.warning(f"Primary route failed. Shifting task context into local fallback matrices: {str(e)}")
            state.accumulated_errors.append(str(e))
            return LocalFallbackNode()

class LocalFallbackNode(BaseNode[HighAvailabilityContext, None, GenerationOutput]):
    async def run(self, ctx: GraphRunContext[HighAvailabilityContext]) -> Union['LocalFallbackNode', End[GenerationOutput]]:
        state = ctx.state
        if state.current_retry_index >= len(state.fallback_local_endpoints):
            raise RuntimeError(f"Global compute degradation: Every registered model endpoint failed. Audit Log: {state.accumulated_errors}")
        target_local_endpoint = state.fallback_local_endpoints[state.current_retry_index]
        logging.info(f"Evaluating resilient inference route footprint index [{state.current_retry_index}] -> {target_local_endpoint}")
        try:
            return End(GenerationOutput(
                selected_model=f"Local-Cluster-Node-{state.current_retry_index} (Orca-Core)",
                result_text=f"Resilient system recovery active. Prompt evaluated using fallback path: '{state.generation_prompt}'",
                circuit_tripped=True
            ))
        except Exception as e:
            logging.error(f"Fallback endpoint [{target_local_endpoint}] failed verification: {str(e)}")
            state.accumulated_errors.append(str(e))
            state.current_retry_index += 1
            return LocalFallbackNode()

fault_tolerant_mesh = Graph(
    nodes=[PrimaryInferenceNode, LocalFallbackNode],
    state_type=HighAvailabilityContext,
    output_type=GenerationOutput
)

async def execute_resilient_agent_run(prompt_query: str) -> GenerationOutput:
    initial_context = HighAvailabilityContext(
        primary_endpoint="https://cloud-orchestrator.internal",
        fallback_local_endpoints=["http://localhost:8001/v1/orca", "http://localhost:8002/v1/freellm"],
        generation_prompt=prompt_query
    )
    result = await fault_tolerant_mesh.run(PrimaryInferenceNode(), state=initial_context)
    return result.output
