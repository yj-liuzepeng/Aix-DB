import logging
import traceback
from typing import List, Optional

from openai import AsyncOpenAI

from model.db_connection_pool import get_db_pool
from model.db_models import TAiModel

logger = logging.getLogger(__name__)
pool = get_db_pool()


async def get_default_embedding_model():
    """Get the default embedding model configuration"""
    with pool.get_session() as session:
        # Try to find a default embedding model (model_type=2)
        model = session.query(TAiModel).filter(
            TAiModel.model_type == 2,
            TAiModel.default_model == True
        ).first()

        # If no default, pick the first available embedding model
        if not model:
            model = session.query(TAiModel).filter(TAiModel.model_type == 2).first()
        
        # If still no embedding model, try to use a default LLM (model_type=1) as fallback
        if not model:
            model = session.query(TAiModel).filter(
                TAiModel.model_type == 1,
                TAiModel.default_model == True
            ).first()
            
        # If no default LLM, pick first available LLM
        if not model:
             model = session.query(TAiModel).filter(TAiModel.model_type == 1).first()

        if model:
            # For LLM fallback, we might need to adjust base_model or assume it supports embedding
            # Or we just use it as is, hoping it supports embedding endpoint.
            # Usually LLMs like GPT-4 don't support embedding on same model name, but some do (like Ollama).
            # If using OpenAI LLM for embedding, we should probably switch model name to text-embedding-ada-002 if possible?
            # But requirement says "use LLM as fallback", implying use the LLM config.
            # However, `client.embeddings.create` requires an embedding model name.
            # If it's OpenAI, we might default to `text-embedding-3-small` if not specified?
            # But `model.base_model` will be e.g. `gpt-4`. `gpt-4` cannot do embeddings.
            
            # Let's check supplier. 
            # If supplier=1 (OpenAI), and we are falling back to LLM config, we should probably force a standard embedding model name
            # if the current model name is a chat model.
            
            base_model = model.base_model
            if model.model_type == 1:
                if model.supplier == 1: # OpenAI
                     base_model = "text-embedding-3-small" # Fallback for OpenAI
                # For Ollama (3), usually we need a specific embedding model too, but maybe user has one?
                # If we use LLM config, we just return it. 
                # User said "use large model as fallback".
            
            return {
                "supplier": model.supplier,
                "api_key": model.api_key,
                "api_domain": model.api_domain,
                "base_model": base_model
            }
        return None


async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for the given text"""
    if not text:
        return None

    model = await get_default_embedding_model()
    if not model:
        logger.warning("No embedding model configured. Skipping embedding generation.")
        return None

    try:
        api_key = model["api_key"] or "empty"
        base_url = model["api_domain"]

        # Special handling for Ollama to ensure OpenAI compatibility
        if model["supplier"] == 3:  # Ollama
            if not base_url.endswith("/v1"):
                base_url = f"{base_url.rstrip('/')}/v1"

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        response = await client.embeddings.create(model=model["base_model"], input=text)

        if response.data:
            return response.data[0].embedding

    except Exception as e:
        traceback.print_exc()
        logger.error(f"Failed to generate embedding: {e}")
        return None

    return None
