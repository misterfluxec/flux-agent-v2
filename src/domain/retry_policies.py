from pydantic import BaseModel, Field
from typing import List, Type, Any
import logging

class RetryPolicy(BaseModel):
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    backoff_strategy: str = Field(default="exponential", description="exponential, linear, fixed")
    base_delay_seconds: float = Field(default=2.0)
    max_delay_seconds: float = Field(default=300.0)
    # A list of exception class names or error types that should trigger a retry
    retryable_error_types: List[str] = Field(default=["TimeoutError", "ConnectionError", "RateLimitError"])

    def should_retry(self, current_attempt: int, error_type: str) -> bool:
        """Determines if a retry should be attempted based on current state."""
        if current_attempt >= self.max_retries:
            return False
            
        # If it's not in the allowed list, do not retry (fail fast to DLQ)
        # We use a broad match for simplicity here. In production, this can match Exception.__class__.__name__
        if error_type not in self.retryable_error_types and "all" not in self.retryable_error_types:
            return False
            
        return True

    def calculate_delay(self, current_attempt: int) -> float:
        """Calculates the delay before the next attempt based on the strategy."""
        if self.backoff_strategy == "fixed":
            delay = self.base_delay_seconds
        elif self.backoff_strategy == "linear":
            delay = self.base_delay_seconds * (current_attempt + 1)
        elif self.backoff_strategy == "exponential":
            delay = self.base_delay_seconds * (2 ** current_attempt)
        else:
            delay = self.base_delay_seconds
            
        return min(delay, self.max_delay_seconds)

# Pre-defined enterprise standard policies
DEFAULT_RETRY_POLICY = RetryPolicy(
    max_retries=3,
    backoff_strategy="exponential",
    retryable_error_types=["TimeoutError", "ConnectionError", "RateLimitError", "ServerDisconnect"]
)

CRITICAL_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_strategy="exponential",
    base_delay_seconds=5.0,
    max_delay_seconds=600.0,
    retryable_error_types=["TimeoutError", "ConnectionError", "RateLimitError", "ServerDisconnect", "TransientError"]
)

NO_RETRY_POLICY = RetryPolicy(
    max_retries=0,
    retryable_error_types=[]
)
