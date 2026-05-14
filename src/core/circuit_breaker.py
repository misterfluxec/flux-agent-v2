import asyncio
import time
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"   # Normal operation, requests pass through
    OPEN = "open"       # Failing, requests immediately rejected
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreakerError(Exception):
    pass

class CircuitBreaker:
    """
    Enterprise Circuit Breaker to prevent cascading failures.
    Protects the runtime from external providers (OpenAI, Shopify, etc.) going down.
    """
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout_sec: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    async def call(self, func, *args, **kwargs):
        """
        Wraps a function call with circuit breaker logic.
        """
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout_sec:
                logger.info(f"[CircuitBreaker] {self.name} entering HALF-OPEN state.")
                self.state = CircuitState.HALF_OPEN
            else:
                logger.warning(f"[CircuitBreaker] {self.name} is OPEN. Request rejected immediately.")
                raise CircuitBreakerError(f"Circuit {self.name} is OPEN.")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
            
        except Exception as e:
            self._record_failure()
            raise e

    def _record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"[CircuitBreaker] {self.name} recovered. State is now CLOSED.")
            self.state = CircuitState.CLOSED
        
        self.failure_count = 0

    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.error(f"[CircuitBreaker] {self.name} threshold reached! State is now OPEN.")
            self.state = CircuitState.OPEN
