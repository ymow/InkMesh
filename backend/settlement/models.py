from django.db import models
import uuid

class SettlementOutput(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    output_id = models.CharField(max_length=50, unique=True, help_text="sout_{uuid_v4}")
    covenant_id = models.CharField(max_length=50, db_index=True)
    
    snapshot_id = models.UUIDField(help_text="對應 ACR-20 的 TokenSnapshot ID")
    calculation_id = models.UUIDField(default=uuid.uuid4)
    
    total_tokens = models.PositiveIntegerField()
    owner_share_pct = models.DecimalField(max_digits=5, decimal_places=2)
    platform_share_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    pool_share_pct = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Recommendations: {agent_id, ink_tokens, pool_share_pct, final_share_pct}
    distributions = models.JSONField(help_text="儲存所有 Agent 的份額建議")
    
    log_id = models.UUIDField(help_text="對應 ACR-300 的 log_id")
    log_hash = models.CharField(max_length=64)
    chain_anchor = models.CharField(max_length=100, blank=True, null=True)
    
    status = models.CharField(max_length=20, default='draft', choices=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('disputed', 'Disputed')
    ])
    
    confirmed_at = models.DateTimeField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

class SettlementDispute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    output = models.ForeignKey(SettlementOutput, related_name='disputes', on_delete=models.CASCADE)
    
    raised_by = models.CharField(max_length=50, help_text="agent_id")
    raised_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    
    disputed_agent = models.CharField(max_length=50, blank=True, null=True)
    resolution = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, default='open', choices=[
        ('open', 'Open'),
        ('resolved', 'Resolved')
    ])
