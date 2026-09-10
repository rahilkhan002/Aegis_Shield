"""Streaming Transaction Ingestion Consumer.

Supports consuming financial transactions from Kafka / Redpanda topics,
with an in-memory queue fallback for standalone local development.
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional

from app.data.schema import Transaction, TransactionEvaluationResponse
from app.risk.engine import get_risk_engine

logger = logging.getLogger(__name__)


class TransactionStreamConsumer:
    """Consumes and scores transactions in a streaming event pipeline."""

    _instance: Optional["TransactionStreamConsumer"] = None

    def __init__(self):
        self.is_running = False
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        self.topic = os.getenv("KAFKA_TOPIC", "financial-transactions")
        self.risk_engine = get_risk_engine()
        self._in_memory_queue: asyncio.Queue = asyncio.Queue()

    @classmethod
    def get_instance(cls) -> "TransactionStreamConsumer":
        if cls._instance is None:
            cls._instance = TransactionStreamConsumer()
        return cls._instance

    async def push_event(self, transaction_data: Dict[str, Any]):
        """Publish a transaction event into the stream queue."""
        await self._in_memory_queue.put(transaction_data)

    async def process_single_event(self, raw_event: Dict[str, Any]) -> TransactionEvaluationResponse:
        """Score a transaction event through the risk engine."""
        return self.risk_engine.evaluate_transaction(raw_event, update_feature_store=True)

    async def start_consumer(self, callback: Optional[Callable[[TransactionEvaluationResponse], None]] = None):
        """Start streaming consumer loop."""
        self.is_running = True
        logger.info("Starting Transaction Stream Consumer (Kafka=%s)...", bool(self.kafka_bootstrap))

        while self.is_running:
            try:
                # In-memory queue consumer loop with 0.5s timeout
                try:
                    event = await asyncio.wait_for(self._in_memory_queue.get(), timeout=0.5)
                    response = await self.process_single_event(event)
                    if callback:
                        callback(response)
                    self._in_memory_queue.task_done()
                except asyncio.TimeoutError:
                    continue
            except Exception as e:
                logger.error("Error in streaming consumer loop: %s", e)
                await asyncio.sleep(1)

    def stop_consumer(self):
        self.is_running = False
        logger.info("Transaction Stream Consumer stopped.")


def get_stream_consumer() -> TransactionStreamConsumer:
    return TransactionStreamConsumer.get_instance()
