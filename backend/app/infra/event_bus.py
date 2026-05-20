"""Event bus implementation using Redis Pub/Sub."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Optional

import redis.asyncio as aioredis
import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class EventBusBackend(ABC):
    """Abstract base class for event bus backends."""

    @abstractmethod
    async def publish(self, channel: str, message: dict) -> None:
        """Publish a message to a channel."""
        pass

    @abstractmethod
    async def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a channel."""
        pass

    @abstractmethod
    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel."""
        pass


class RedisEventBusBackend(EventBusBackend):
    """Redis Pub/Sub based event bus implementation."""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._sync_client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._channel_prefix = "strix:events:"

    @property
    def sync_client(self) -> redis.Redis:
        """Get or create synchronous Redis client."""
        if self._sync_client is None:
            self._sync_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return self._sync_client

    async def publish(self, channel: str, message: dict) -> None:
        """Publish a message to a channel."""
        full_channel = f"{self._channel_prefix}{channel}"
        message_str = json.dumps(message, ensure_ascii=False, default=str)
        self.sync_client.publish(full_channel, message_str)
        logger.debug(f"Published to {full_channel}: {message.get('type', 'unknown')}")

    async def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a channel."""
        full_channel = f"{self._channel_prefix}{channel}"
        pubsub = self.sync_client.pubsub()
        await pubsub.subscribe(full_channel)

        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await callback(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in message: {message['data']}")

    def get_pubsub(self, channels: list[str]):
        """Get a pubsub instance for multiple channels."""
        full_channels = [f"{self._channel_prefix}{ch}" for ch in channels]
        pubsub = self.sync_client.pubsub()
        pubsub.subscribe(*full_channels)
        return pubsub

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel."""
        pass


class InMemoryEventBusBackend(EventBusBackend):
    """In-memory event bus for testing or single-instance deployment."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def publish(self, channel: str, message: dict) -> None:
        """Publish a message to local subscribers."""
        if channel in self._subscribers:
            for callback in self._subscribers[channel]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")

    async def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a channel."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)
        logger.debug(f"Subscribed to channel: {channel}")

    async def unsubscribe(self, channel: str, callback: Callable = None) -> None:
        """Unsubscribe from a channel."""
        if channel in self._subscribers:
            if callback:
                self._subscribers[channel].remove(callback)
            else:
                self._subscribers[channel].clear()


class EventBus:
    """Event bus for publishing and subscribing to run events.

    Uses Redis Pub/Sub for distributed deployments, with in-memory fallback.
    """

    def __init__(self, backend: EventBusBackend = None):
        """Initialize event bus.

        Args:
            backend: Event bus backend to use
        """
        if backend is None:
            if settings.event_bus_backend == "redis":
                self._backend = RedisEventBusBackend()
            else:
                self._backend = InMemoryEventBusBackend()
        else:
            self._backend = backend

        self._pubsub: Optional[redis.client.PubSub] = None
        self._running = False

    async def publish_run_event(
        self,
        run_id: str,
        event_type: str,
        data: dict,
        seq: int = None,
    ) -> None:
        """Publish a run event.

        Args:
            run_id: Run ID
            event_type: Event type (e.g., 'status_change', 'progress')
            data: Event data payload
            seq: Optional sequence number
        """
        message = {
            "type": event_type,
            "run_id": run_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if seq is not None:
            message["seq"] = seq

        channel = f"run:{run_id}"
        await self._backend.publish(channel, message)

    async def publish_status_change(
        self,
        run_id: str,
        task_id: str,
        status: str,
        extra: dict = None,
    ) -> None:
        """Publish a status change event."""
        data = {
            "task_id": task_id,
            "status": status,
        }
        if extra:
            data.update(extra)

        await self.publish_run_event(run_id, "status_change", data)

    async def publish_event(self, run_id: str, event: dict) -> None:
        """Publish a raw event from STRIX."""
        await self.publish_run_event(
            run_id,
            "strix_event",
            event,
            seq=event.get("_seq"),
        )

    def subscribe_to_run(self, run_id: str) -> redis.client.PubSub:
        """Subscribe to events for a specific run.

        Args:
            run_id: Run ID to subscribe to

        Returns:
            PubSub instance for listening
        """
        channel = f"run:{run_id}"
        if isinstance(self._backend, RedisEventBusBackend):
            self._pubsub = self._backend.get_pubsub([channel])
            return self._pubsub
        return None

    def unsubscribe_from_run(self, run_id: str) -> None:
        """Unsubscribe from a run."""
        if self._pubsub:
            channel = f"strix:events:run:{run_id}"
            self._pubsub.unsubscribe(channel)

    async def close(self) -> None:
        """Close the event bus."""
        self._running = False
        if self._pubsub:
            self._pubsub.close()


def get_event_bus() -> EventBus:
    """Get the configured event bus instance."""
    if settings.event_bus_backend == "redis":
        return EventBus(RedisEventBusBackend())
    return EventBus(InMemoryEventBusBackend())
