from django.db import models
import uuid

class ContributionType(models.TextChoices):
    PASSAGE = 'passage', '段落貢獻'
    EDIT = 'edit', '段落修改'
    BIBLE = 'bible', '世界觀設定'
    OUTLINE = 'outline', '章節大綱'
    VOTE_REWARD = 'vote_reward', '投票獎勵'
    REVERSAL = 'reversal', '撤銷'

class TokenLedger(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    covenant_id = models.CharField(max_length=50, db_index=True)
    agent_id = models.CharField(max_length=50, db_index=True)
    
    delta = models.IntegerField(help_text="正數為增加，負數為撤銷")
    balance_after = models.PositiveIntegerField()
    
    source_type = models.CharField(max_length=20, choices=ContributionType.choices)
    source_ref = models.CharField(max_length=100, help_text="例如 draft_id")
    
    log_id = models.UUIDField(help_text="對應 ACR-300 的 log_id", unique=True)
    
    status = models.CharField(max_length=20, default='confirmed', choices=[
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('reversed', 'Reversed')
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['covenant_id', 'created_at']

class PendingToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    covenant_id = models.CharField(max_length=50, db_index=True)
    agent_id = models.CharField(max_length=50)
    draft_id = models.CharField(max_length=100, unique=True)
    
    estimated_tokens = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

class TokenSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    covenant_id = models.CharField(max_length=50, unique=True)
    taken_at = models.DateTimeField(auto_now_add=True)
    trigger_log_id = models.UUIDField()
    
    total_tokens = models.PositiveIntegerField()
    balances = models.JSONField(help_text="儲存所有 Agent 的份額快照")
    
    hash = models.CharField(max_length=64, help_text="SHA-256(整個 snapshot JSON)")
    chain_tx_hash = models.CharField(max_length=100, blank=True, null=True)
