from __future__ import annotations

import uuid
from django.db import models


class OutboxStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    PUBLISHED = "published", "Published"
    FAILED = "failed", "Failed"


class OutboxEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aggregate_type = models.CharField(max_length=64)
    aggregate_id = models.UUIDField()
    event_type = models.CharField(max_length=128)
    payload = models.JSONField()
    status = models.CharField(max_length=16, choices=OutboxStatus.choices, default=OutboxStatus.PENDING)
    available_at = models.DateTimeField(db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "platform_outbox_event"
        indexes = [models.Index(fields=["status", "available_at"]) ]
