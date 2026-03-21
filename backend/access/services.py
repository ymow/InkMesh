from django.utils import timezone
from covenants.models import Covenant, AccessTier, PlatformIdentity
from .models import AccessGrant
import uuid

class AccessService:
    @staticmethod
    def request_access(covenant_id, platform_id_str, tier_id, tx_ref=None):
        """
        處理准入請求 (e.g., 購書、付費加入)。
        """
        covenant = Covenant.objects.get(covenant_id=covenant_id)
        tier = AccessTier.objects.get(covenant=covenant, tier_id=tier_id)
        
        # 取得或建立平台身份 (PID)
        platform_identity, _ = PlatformIdentity.objects.get_or_create(platform_id=platform_id_str)
        
        # 建立准入紀錄 (Grant)
        grant_id = f"grant_{uuid.uuid4().hex[:8]}"
        grant = AccessGrant.objects.create(
            grant_id=grant_id,
            covenant_id=covenant_id,
            platform_identity=platform_identity,
            tier_id=tier_id,
            transaction_ref=tx_ref,
            status='active'
        )
        
        return grant

    @staticmethod
    def verify_permission(covenant_id, platform_id_str, required_permission):
        """
        核心權限檢查：這是一個 PID 在此 Covenant 是否擁有某權限？
        """
        grants = AccessGrant.objects.filter(
            covenant_id=covenant_id, 
            platform_identity__platform_id=platform_id_str,
            status='active'
        )
        
        for grant in grants:
            # 取得該 Tier 的權限清單
            try:
                tier = AccessTier.objects.get(covenant_id=covenant_id, tier_id=grant.tier_id)
                if required_permission in tier.permissions:
                    return True
            except AccessTier.DoesNotExist:
                continue
                
        # 同時也檢查是否是 CovenantMember (可能是 Contributor/Owner)
        from covenants.models import CovenantMember
        members = CovenantMember.objects.filter(
            covenant__covenant_id=covenant_id,
            platform_identity__platform_id=platform_id_str
        )
        
        for member in members:
            if member.is_owner: # Owner 擁有一切
                return True
            if member.tier and required_permission in member.tier.permissions:
                return True
                
        return False
