from django.db import models
import uuid

class SpaceType(models.TextChoices):
    BOOK = 'book', '書籍創作'
    CODE = 'code', '程式碼協作'
    MUSIC = 'music', '音樂創作'
    CUSTOM = 'custom', '自定義'

class CovenantState(models.TextChoices):
    DRAFT = 'DRAFT', '草稿'
    OPEN = 'OPEN', '開放加入'
    ACTIVE = 'ACTIVE', '執行中'
    LOCKED = 'LOCKED', '已鎖定'
    SETTLED = 'SETTLED', '已結算'

class Covenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    covenant_id = models.CharField(max_length=50, unique=True, help_text="格式：cvnt_{uuid_v4}")
    version = models.CharField(max_length=20, default="ACP@1.0")
    space_type = models.CharField(max_length=20, choices=SpaceType.choices, default=SpaceType.BOOK)
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    language = models.JSONField(default=list, help_text="語言列表，例如 ['zh-TW', 'en']")
    
    state = models.CharField(
        max_length=20, 
        choices=CovenantState.choices, 
        default=CovenantState.DRAFT
    )
    
    # Metadata
    cover_url = models.URLField(max_length=500, blank=True, null=True)
    external_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Economics (from ACR-100 v0.2)
    owner_share_pct = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    platform_share_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    contributor_pool_pct = models.DecimalField(max_digits=5, decimal_places=2, default=70.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.covenant_id})"

    class Meta:
        ordering = ['-created_at']

class AccessTier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    covenant = models.ForeignKey(Covenant, related_name='access_tiers', on_delete=models.CASCADE)
    tier_id = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    token_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    max_slots = models.IntegerField(null=True, blank=True)
    permissions = models.JSONField(default=list)

    class Meta:
        unique_together = ('covenant', 'tier_id')

class PlatformIdentity(models.Model):
    platform_id = models.CharField(max_length=50, primary_key=True, help_text="pid_{uuid_v4}")
    kyc_status = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('pending', 'Pending'),
        ('verified', 'Verified')
    ], default='none')
    kyc_ref = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.platform_id

class CovenantMember(models.Model):
    covenant = models.ForeignKey(Covenant, related_name='members', on_delete=models.CASCADE)
    platform_identity = models.ForeignKey(PlatformIdentity, on_delete=models.CASCADE)
    agent_id = models.CharField(max_length=50, help_text="agent_{random_8chars}")
    tier = models.ForeignKey(AccessTier, on_delete=models.SET_NULL, null=True)
    
    is_owner = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('covenant', 'agent_id')
