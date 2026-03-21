from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Covenant, CovenantState, AccessTier, CovenantMember, PlatformIdentity

class CovenantService:
    @staticmethod
    @transaction.atomic
    def create_covenant(title, space_type, owner_platform_id, description="", language=None):
        """建立新的 Covenant (DRAFT 狀態)"""
        import uuid
        covenant_id = f"cvnt_{uuid.uuid4()}"
        
        covenant = Covenant.objects.create(
            covenant_id=covenant_id,
            title=title,
            space_type=space_type,
            description=description,
            language=language or ["zh-TW"],
            state=CovenantState.DRAFT
        )
        
        # 取得或建立平台身份
        platform_id, _ = PlatformIdentity.objects.get_or_create(platform_id=owner_platform_id)
        
        # 建立 Owner 假名
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        CovenantMember.objects.create(
            covenant=covenant,
            platform_identity=platform_id,
            agent_id=agent_id,
            is_owner=True
        )
        
        return covenant

    @staticmethod
    def transition_to_open(covenant_id):
        """DRAFT -> OPEN: 開始允許 Agent 加入"""
        covenant = Covenant.objects.get(covenant_id=covenant_id)
        if covenant.state != CovenantState.DRAFT:
            raise ValidationError(f"Cannot transition from {covenant.state} to OPEN")
        
        # 檢查是否已定義 AccessTiers
        if not covenant.access_tiers.exists():
            raise ValidationError("Covenant must have at least one AccessTier before opening")
            
        covenant.state = CovenantState.OPEN
        covenant.save()
        return covenant

    @staticmethod
    def transition_to_active(covenant_id):
        """OPEN -> ACTIVE: 正式開始協作"""
        covenant = Covenant.objects.get(covenant_id=covenant_id)
        if covenant.state != CovenantState.OPEN:
            raise ValidationError(f"Cannot transition from {covenant.state} to ACTIVE")
            
        covenant.state = CovenantState.ACTIVE
        covenant.save()
        return covenant

    @staticmethod
    def transition_to_locked(covenant_id):
        """ACTIVE -> LOCKED: 創作完成，凍結 Token 帳本"""
        covenant = Covenant.objects.get(covenant_id=covenant_id)
        if covenant.state != CovenantState.ACTIVE:
            raise ValidationError(f"Cannot transition from {covenant.state} to LOCKED")
            
        # TODO: 觸發 ACR-20 Token 快照
        covenant.state = CovenantState.LOCKED
        covenant.save()
        return covenant

    @staticmethod
    def transition_to_settled(covenant_id):
        """LOCKED -> SETTLED: 結算完成，永久封存"""
        covenant = Covenant.objects.get(covenant_id=covenant_id)
        if covenant.state != CovenantState.LOCKED:
            raise ValidationError(f"Cannot transition from {covenant.state} to SETTLED")
            
        # TODO: 檢查是否已產生 SettlementOutput
        covenant.state = CovenantState.SETTLED
        covenant.save()
        return covenant

    @staticmethod
    @transaction.atomic
    def join_covenant(covenant_id, platform_id_str, tier_id):
        """Agent 加入 Covenant"""
        covenant = Covenant.objects.get(covenant_id=covenant_id)
        if covenant.state != CovenantState.OPEN:
            raise ValidationError("Covenant is not open for new members")
            
        tier = AccessTier.objects.get(covenant=covenant, tier_id=tier_id)
        
        # 檢查席位限制
        if tier.max_slots is not None:
            current_count = CovenantMember.objects.filter(covenant=covenant, tier=tier).count()
            if current_count >= tier.max_slots:
                raise ValidationError(f"Access tier {tier_id} is full")
        
        platform_id, _ = PlatformIdentity.objects.get_or_create(platform_id=platform_id_str)
        
        # 檢查是否已加入
        if CovenantMember.objects.filter(covenant=covenant, platform_identity=platform_id).exists():
            raise ValidationError("Platform identity already has an agent in this covenant")
            
        import uuid
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        member = CovenantMember.objects.create(
            covenant=covenant,
            platform_identity=platform_id,
            agent_id=agent_id,
            tier=tier
        )
        
        return member
