from django.db import models
from django.utils import timezone
import hashlib
import json
import uuid

class AuditLog(models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    covenant_id = models.CharField(max_length=50, db_index=True)
    sequence = models.PositiveIntegerField()
    
    agent_id = models.CharField(max_length=50)
    session_id = models.CharField(max_length=50)
    
    tool_name = models.CharField(max_length=100)
    tool_type = models.CharField(max_length=20, choices=[
        ('clause', 'Clause Tool'),
        ('query', 'Query Tool'),
        ('admin', 'Admin Tool')
    ])
    
    params_hash = models.CharField(max_length=64)
    params_preview = models.JSONField()
    
    result = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('rejected', 'Rejected'),
        ('error', 'Error')
    ])
    result_detail = models.TextField(blank=True)
    
    tokens_delta = models.IntegerField(default=0)
    state_before = models.CharField(max_length=20)
    state_after = models.CharField(max_length=20)
    
    timestamp = models.DateTimeField(default=timezone.now)
    prev_log_id = models.UUIDField(null=True, blank=True)
    hash = models.CharField(max_length=64)

    class Meta:
        unique_together = ('covenant_id', 'sequence')
        ordering = ['covenant_id', 'sequence']

    @staticmethod
    def compute_hash(prev_log_id, log_id, covenant_id, sequence, agent_id, 
                     tool_name, result, tokens_delta, state_after, timestamp, params_hash):
        """實作 ACR-300 v0.1 的 Hash 計算公式"""
        components = [
            str(prev_log_id) if prev_log_id else "None",
            str(log_id),
            str(covenant_id),
            str(sequence),
            str(agent_id),
            str(tool_name),
            str(result),
            str(tokens_delta),
            str(state_after),
            timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            str(params_hash)
        ]
        payload = "|".join(components)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        # 如果 self._state.adding 為 True，代表是 CREATE 操作
        if self._state.adding:
            super().save(*args, **kwargs)
        else:
            raise PermissionError("Audit Log is immutable and cannot be updated.")

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit Log is immutable and cannot be deleted.")

class ChainAnchor(models.Model):
    anchor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    covenant_id = models.CharField(max_length=50, db_index=True)
    anchor_type = models.CharField(max_length=50)
    
    from_sequence = models.PositiveIntegerField()
    to_sequence = models.PositiveIntegerField()
    entry_count = models.PositiveIntegerField()
    
    range_hash = models.CharField(max_length=64)
    chain = models.CharField(max_length=20, default='base')
    tx_hash = models.CharField(max_length=100, blank=True, null=True)
    
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    anchored_at = models.DateTimeField(null=True, blank=True)
