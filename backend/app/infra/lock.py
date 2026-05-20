"""Distributed lock implementation using Redis."""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional

import redis
from redis.lock import Lock

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class LockBackend(ABC):
    """Abstract base class for lock backends."""

    @abstractmethod
    def acquire(self, key: str, timeout: int = 10) -> bool:
        """Acquire a lock."""
        pass

    @abstractmethod
    def release(self, key: str) -> bool:
        """Release a lock."""
        pass

    @abstractmethod
    def is_locked(self, key: str) -> bool:
        """Check if a key is locked."""
        pass


class RedisLockBackend(LockBackend):
    """Redis-based distributed lock implementation."""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._client: Optional[redis.Redis] = None
        self._lock_prefix = "strix:lock:"

    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return self._client

    def acquire(self, key: str, timeout: int = 10) -> bool:
        """Acquire a distributed lock using Redis SET NX.

        Args:
            key: Lock key (without prefix)
            timeout: Lock timeout in seconds

        Returns:
            bool: True if lock acquired, False otherwise
        """
        lock_key = f"{self._lock_prefix}{key}"
        lock_value = str(uuid.uuid4())

        acquired = self.client.set(
            lock_key,
            lock_value,
            nx=True,
            ex=timeout,
        )

        if acquired:
            logger.debug(f"Lock acquired: {key}")
            return True
        else:
            logger.debug(f"Lock not available: {key}")
            return False

    def release(self, key: str) -> bool:
        """Release a distributed lock.

        Args:
            key: Lock key (without prefix)

        Returns:
            bool: True if lock released, False otherwise
        """
        lock_key = f"{self._lock_prefix}{key}"
        self.client.delete(lock_key)
        logger.debug(f"Lock released: {key}")
        return True

    def is_locked(self, key: str) -> bool:
        """Check if a key is currently locked.

        Args:
            key: Lock key (without prefix)

        Returns:
            bool: True if locked, False otherwise
        """
        lock_key = f"{self._lock_prefix}{key}"
        return self.client.exists(lock_key) > 0

    def extend(self, key: str, timeout: int = 10) -> bool:
        """Extend lock timeout.

        Args:
            key: Lock key (without prefix)
            timeout: New timeout in seconds

        Returns:
            bool: True if extended, False otherwise
        """
        lock_key = f"{self._lock_prefix}{key}"
        return self.client.expire(lock_key, timeout)


class InMemoryLockBackend(LockBackend):
    """In-memory lock implementation for testing or single-instance deployment."""

    def __init__(self):
        self._locks: dict[str, str] = {}

    def acquire(self, key: str, timeout: int = 10) -> bool:
        """Acquire an in-memory lock."""
        if key not in self._locks:
            self._locks[key] = str(uuid.uuid4())
            logger.debug(f"In-memory lock acquired: {key}")
            return True
        return False

    def release(self, key: str) -> bool:
        """Release an in-memory lock."""
        if key in self._locks:
            del self._locks[key]
            logger.debug(f"In-memory lock released: {key}")
            return True
        return False

    def is_locked(self, key: str) -> bool:
        """Check if key is locked."""
        return key in self._locks


class DistributedLock:
    """Distributed lock wrapper with context manager support."""

    def __init__(
        self,
        backend: LockBackend = None,
        key: str = None,
        timeout: int = 10,
        retry_times: int = 3,
        retry_delay: float = 0.1,
    ):
        """Initialize distributed lock.

        Args:
            backend: Lock backend to use
            key: Lock key
            timeout: Lock timeout in seconds
            retry_times: Number of times to retry acquiring lock
            retry_delay: Delay between retries in seconds
        """
        if backend is None:
            if settings.lock_backend == "redis":
                self._backend = RedisLockBackend()
            else:
                self._backend = InMemoryLockBackend()
        else:
            self._backend = backend

        self.key = key
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self._acquired = False

    def acquire(self) -> bool:
        """Acquire the lock with retries."""
        for i in range(self.retry_times):
            if self._backend.acquire(self.key, self.timeout):
                self._acquired = True
                return True

            if i < self.retry_times - 1:
                time.sleep(self.retry_delay)

        return False

    def release(self) -> bool:
        """Release the lock."""
        if self._acquired:
            result = self._backend.release(self.key)
            self._acquired = False
            return result
        return False

    def __enter__(self) -> "DistributedLock":
        """Context manager entry."""
        if not self.acquire():
            raise RuntimeError(f"Failed to acquire lock: {self.key}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()


def get_lock_backend() -> LockBackend:
    """Get the configured lock backend."""
    if settings.lock_backend == "redis":
        return RedisLockBackend()
    return InMemoryLockBackend()
