from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.settings import get_settings
from app.core.logging import setup_logging
from app.schemas.agent_chat_request import AgentChatRequest
from app.schemas.agent_chat_response import AgentChatResponse
from app.services.bedrock_llm_service import BedrockLLMService
from app.services.llm_service import LLMService, MockLLMService
from app.services.orchestrator import AgentOrchestrator
from app.services.prompt_builder import PromptBuilder
from app.services.retrieval_service import RetrievalService

router = APIRouter()
logger = setup_logging()
settings = get_settings()

retrieval_service = RetrievalService()
prompt_builder = PromptBuilder()
llm_service: LLMService = MockLLMService() if settings.use_mock_llm else BedrockLLMService()
agent_orchestrator = AgentOrchestrator(
    retrieval_service=retrieval_service,
    prompt_builder=prompt_builder,
    llm_service=llm_service,
    multi_agent_enabled=settings.multi_agent_enabled,
    multi_agent_threshold=settings.multi_agent_threshold,
)


def get_agent_orchestrator() -> AgentOrchestrator:
    return agent_orchestrator


@router.post(
    "/agent-chat",
    response_model=AgentChatResponse,
    tags=["Agent Chat"],
)
async def agent_chat(
    request: AgentChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> AgentChatResponse:
    """Route a question to the appropriate enterprise agent and return a grounded answer."""

    logger.info("Incoming agent-chat request: question=%s", request.question)

    try:
        result = orchestrator.handle(question=request.question)
        response = AgentChatResponse(
            selected_agents=result.selected_agents,
            question=result.question,
            answer=result.answer,
            sources=[
                {
                    "document_id": source.document_id,
                    "chunk_number": source.chunk_number,
                    "similarity_score": source.similarity_score,
                }
                for source in result.sources
            ],
        )
        logger.info(
            "Response returned: endpoint=/agent-chat selected_agents=%s sources=%s",
            response.selected_agents,
            len(response.sources),
        )
        logger.info("Agent chat completed: question=%s selected_agents=%s", request.question, response.selected_agents)
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected failure in agent-chat endpoint for question=%s", request.question)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete agent chat request.",
        ) from exc
