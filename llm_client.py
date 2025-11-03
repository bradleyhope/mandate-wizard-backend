"""
Tiered LLM Client for Netflix Mandate Wizard
Supports multiple OpenAI models with intelligent fallback and cost optimization
"""

import os
from typing import Optional, Dict, Any, List
from openai import OpenAI
import time

class TieredLLMClient:
    """
    Intelligent LLM client with tiered model selection for cost optimization

    Model Tiers:
    - FAST: gpt-4o-mini (cheapest, fastest - for simple queries)
    - BALANCED: gpt-4o (good quality/speed balance)
    - PREMIUM: o1-preview or gpt-4-turbo (highest quality for complex queries)
    """

    # Model configurations with cost per 1M tokens (input/output)
    MODELS = {
        'fast': {
            'name': 'gpt-4o-mini',
            'cost_input': 0.15,  # $0.15 per 1M input tokens
            'cost_output': 0.60,  # $0.60 per 1M output tokens
            'max_tokens': 16384,
            'best_for': ['FACTUAL_QUERY', 'CLARIFICATION', 'MARKET_INFO']
        },
        'balanced': {
            'name': 'gpt-4o',
            'cost_input': 2.50,  # $2.50 per 1M input tokens
            'cost_output': 10.00,  # $10.00 per 1M output tokens
            'max_tokens': 16384,
            'best_for': ['ROUTING', 'HYBRID', 'EXAMPLE_QUERY']
        },
        'premium': {
            'name': 'gpt-4-turbo',
            'cost_input': 10.00,  # $10 per 1M input tokens
            'cost_output': 30.00,  # $30 per 1M output tokens
            'max_tokens': 128000,
            'best_for': ['STRATEGIC', 'COMPARATIVE', 'PROCESS_QUERY']
        }
    }

    def __init__(self, api_key: Optional[str] = None, default_tier: str = 'balanced'):
        """
        Initialize the tiered LLM client

        Args:
            api_key: OpenAI API key (reads from env if not provided)
            default_tier: Default model tier ('fast', 'balanced', 'premium')
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set and no API key provided")

        self.client = OpenAI(api_key=self.api_key)
        self.default_tier = default_tier

        # Usage tracking
        self.usage_stats = {
            'requests': 0,
            'tokens_input': 0,
            'tokens_output': 0,
            'cost_usd': 0.0,
            'by_model': {}
        }

    def select_model_for_intent(self, intent: str, force_tier: Optional[str] = None) -> str:
        """
        Intelligently select the best model based on query intent

        Args:
            intent: Query intent (ROUTING, STRATEGIC, FACTUAL_QUERY, etc.)
            force_tier: Force a specific tier ('fast', 'balanced', 'premium')

        Returns:
            Model name to use
        """
        if force_tier:
            return self.MODELS[force_tier]['name']

        # Find best tier for this intent
        for tier, config in self.MODELS.items():
            if intent in config['best_for']:
                return config['name']

        # Default to balanced
        return self.MODELS[self.default_tier]['name']

    def create(
        self,
        prompt: str,
        model: Optional[str] = None,
        intent: str = 'HYBRID',
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        Generate completion with automatic model selection

        Args:
            prompt: Input prompt
            model: Specific model to use (overrides auto-selection)
            intent: Query intent for auto model selection
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            stream: Whether to stream the response

        Returns:
            Generated text
        """
        # Select model
        selected_model = model or self.select_model_for_intent(intent)

        try:
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )

            if stream:
                return response  # Return streaming response

            # Extract text
            text = response.choices[0].message.content

            # Track usage
            self._track_usage(
                model=selected_model,
                tokens_input=response.usage.prompt_tokens,
                tokens_output=response.usage.completion_tokens,
                duration=time.time() - start_time
            )

            return text

        except Exception as e:
            print(f"[ERROR] LLM generation failed with {selected_model}: {e}")

            # Fallback to cheaper model if premium fails
            if selected_model != self.MODELS['fast']['name']:
                print(f"[FALLBACK] Retrying with {self.MODELS['fast']['name']}")
                return self.create(
                    prompt=prompt,
                    model=self.MODELS['fast']['name'],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False
                )

            raise

    def chat_completion_compatible(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        intent: str = 'HYBRID',
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Chat completion interface compatible with existing code

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Specific model to use
            intent: Query intent
            max_tokens: Max tokens
            temperature: Temperature

        Returns:
            OpenAI-compatible response dict
        """
        selected_model = model or self.select_model_for_intent(intent)

        try:
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=selected_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Track usage
            self._track_usage(
                model=selected_model,
                tokens_input=response.usage.prompt_tokens,
                tokens_output=response.usage.completion_tokens,
                duration=time.time() - start_time
            )

            # Return in OpenAI format
            return {
                'choices': [{
                    'message': {
                        'content': response.choices[0].message.content,
                        'role': 'assistant'
                    },
                    'finish_reason': response.choices[0].finish_reason
                }],
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': selected_model
            }

        except Exception as e:
            print(f"[ERROR] Chat completion failed with {selected_model}: {e}")

            # Fallback
            if selected_model != self.MODELS['fast']['name']:
                print(f"[FALLBACK] Retrying with {self.MODELS['fast']['name']}")
                return self.chat_completion_compatible(
                    messages=messages,
                    model=self.MODELS['fast']['name'],
                    max_tokens=max_tokens,
                    temperature=temperature
                )

            raise

    def _track_usage(self, model: str, tokens_input: int, tokens_output: int, duration: float):
        """Track token usage and costs"""
        # Find model tier
        tier_config = None
        for tier, config in self.MODELS.items():
            if config['name'] == model:
                tier_config = config
                break

        if not tier_config:
            return

        # Calculate cost
        cost = (
            (tokens_input / 1_000_000) * tier_config['cost_input'] +
            (tokens_output / 1_000_000) * tier_config['cost_output']
        )

        # Update stats
        self.usage_stats['requests'] += 1
        self.usage_stats['tokens_input'] += tokens_input
        self.usage_stats['tokens_output'] += tokens_output
        self.usage_stats['cost_usd'] += cost

        if model not in self.usage_stats['by_model']:
            self.usage_stats['by_model'][model] = {
                'requests': 0,
                'tokens_input': 0,
                'tokens_output': 0,
                'cost_usd': 0.0,
                'avg_duration': 0.0
            }

        model_stats = self.usage_stats['by_model'][model]
        model_stats['requests'] += 1
        model_stats['tokens_input'] += tokens_input
        model_stats['tokens_output'] += tokens_output
        model_stats['cost_usd'] += cost

        # Update average duration
        prev_avg = model_stats['avg_duration']
        n = model_stats['requests']
        model_stats['avg_duration'] = ((prev_avg * (n - 1)) + duration) / n

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.usage_stats.copy()

    def estimate_cost(self, tokens_input: int, tokens_output: int, tier: str = 'balanced') -> float:
        """
        Estimate cost for a given number of tokens

        Args:
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            tier: Model tier

        Returns:
            Estimated cost in USD
        """
        config = self.MODELS[tier]
        return (
            (tokens_input / 1_000_000) * config['cost_input'] +
            (tokens_output / 1_000_000) * config['cost_output']
        )


# Global instance (for backward compatibility)
_llm_client = None

def get_llm_client(default_tier: str = 'balanced') -> TieredLLMClient:
    """Get or create global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = TieredLLMClient(default_tier=default_tier)
    return _llm_client


# Backward compatibility alias
class GPT5Client(TieredLLMClient):
    """Backward compatibility wrapper"""
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, default_tier='balanced')
