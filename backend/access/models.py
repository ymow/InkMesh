from django.db import models
from django.utils import timezone
import uuid

class AccessGrant(models.Model):
    """
    實作 ACR-50: 讀者准入與權限管理。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grant_id = models.CharField(max_length=50, unique=True, help_text="grant_{uuid_v4}")
    
    covenant_id = models.CharField(max_length=50, db_index=True)
    platform_identity = models.ForeignKey('covenants.PlatformIdentity', on_delete=models.CASCADE)
    
    tier_id = models.CharField(max_length=50) # e.g., 'observer', 'reader'
    
    status = models.CharField(max_length=20, default='active', choices=[
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked')
    ])
    
    # 外部交易參考 (Stripe / 鏈上交易)
    transaction_ref = models.CharField(max_length=100, blank=True, null=True)
    
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-granted_at']
        unique_together = ('covenant_id', 'platform_identity', 'tier_id')

    def __str__(self):
        return f"Grant {self.grant_id} for {self.platform_identity.platform_id} on {self.covenant_id}"
