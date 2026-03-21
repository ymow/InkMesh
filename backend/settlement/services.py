from django.db import transaction
from django.core.exceptions import ValidationError
from tokens.services import TokenService
from tokens.models import TokenSnapshot
from covenants.models import Covenant
from .models import SettlementOutput
import uuid
import json
import hashlib

class SettlementService:
    @staticmethod
    @transaction.atomic
    def generate_output(covenant_id, log_id, log_hash):
        """
        實作 ACR-100 v0.2: 產生結算建議報告。
        """
        covenant = Covenant.objects.get(covenant_id=covenant_id)
        
        # 1. 取得或產生 Token 快照 (ACR-20)
        snapshot = TokenSnapshot.objects.filter(covenant_id=covenant_id).first()
        if not snapshot:
            # 如果還沒有快照，則在目前狀態下產生一個 (通常在 LOCKED 狀態呼叫)
            snapshot = TokenService.create_snapshot(covenant_id, log_id)
            
        # 2. 三層分配計算 (Owner / Platform / Pool)
        owner_share = float(covenant.owner_share_pct)
        platform_share = float(covenant.platform_share_pct)
        pool_share = float(covenant.contributor_pool_pct)
        
        if abs(owner_share + platform_share + pool_share - 100.0) > 0.01:
            raise ValidationError("Covenant shares do not add up to 100%")
            
        # 3. 計算 Agent 貢獻池分配
        total_tokens = snapshot.total_tokens
        agent_distributions = []
        
        for balance in snapshot.balances:
            agent_id = balance['agent_id']
            ink_tokens = balance['tokens']
            
            # 在池子裡的比例 (e.g., 40%)
            pool_share_pct = (ink_tokens / total_tokens * 100) if total_tokens > 0 else 0
            
            # 最終版稅比例 (e.g., 70% * 40% = 28%)
            final_share_pct = pool_share * (pool_share_pct / 100)
            
            agent_distributions.append({
                'agent_id': agent_id,
                'ink_tokens': ink_tokens,
                'pool_share_pct': round(pool_share_pct, 4),
                'final_share_pct': round(final_share_pct, 4)
            })
            
        # 4. 儲存報告
        output_id = f"sout_{uuid.uuid4().hex[:8]}"
        settlement_output = SettlementOutput.objects.create(
            output_id=output_id,
            covenant_id=covenant_id,
            snapshot_id=snapshot.id,
            total_tokens=total_tokens,
            owner_share_pct=owner_share,
            platform_share_pct=platform_share,
            pool_share_pct=pool_share,
            distributions=agent_distributions,
            log_id=log_id,
            log_hash=log_hash
        )
        
        # 5. [ACP Bridge] 觸發鏈上錨定 (ACR-100 要求)
        from bridge.services import BridgeService
        # 錨定此次結算及其之前的 Log (假設從 1 開始到當前 log_id 的 sequence)
        from audit.models import AuditLog
        current_log = AuditLog.objects.get(log_id=log_id)
        anchor = BridgeService.anchor_log_range(
            covenant_id=covenant_id,
            from_seq=1, # 或前一次錨定點
            to_seq=current_log.sequence,
            anchor_type="settlement"
        )
        
        if anchor:
            settlement_output.chain_anchor = anchor.tx_hash
            settlement_output.save()
            
        return settlement_output

    @staticmethod
    def get_latest_output(covenant_id):
        return SettlementOutput.objects.filter(covenant_id=covenant_id).order_by('-generated_at').first()
