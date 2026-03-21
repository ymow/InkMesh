from django.db import transaction, models
from django.utils import timezone
from .models import TokenLedger, PendingToken, TokenSnapshot, ContributionType
from covenants.models import Covenant, CovenantMember
import hashlib
import json

class TokenService:
    @staticmethod
    def calculate_tokens(word_count, tier_multiplier, base_rate=100, acceptance_ratio=1.0):
        """實作 ACR-20 v0.1 的 Formula 語法"""
        # "floor(word_count * acceptance_ratio / 100) * base_rate * tier_multiplier"
        from math import floor
        effective_words = word_count * float(acceptance_ratio)
        tokens = floor(effective_words / 100) * int(base_rate) * float(tier_multiplier)
        return int(tokens)

    @staticmethod
    @transaction.atomic
    def confirm_contribution(covenant_id, agent_id, log_id, word_count, source_ref, 
                             source_type=ContributionType.PASSAGE, acceptance_ratio=1.0):
        """將貢獻轉化為 Token 並寫入帳本"""
        # 取得 Agent 的 multiplier
        member = CovenantMember.objects.get(covenant__covenant_id=covenant_id, agent_id=agent_id)
        multiplier = member.tier.token_multiplier if member.tier else 1.0
        
        tokens_delta = TokenService.calculate_tokens(
            word_count=word_count,
            tier_multiplier=multiplier,
            acceptance_ratio=acceptance_ratio
        )
        
        # 取得當前餘額
        last_entry = TokenLedger.objects.filter(
            covenant_id=covenant_id, 
            agent_id=agent_id
        ).order_by('-created_at').first()
        
        current_balance = last_entry.balance_after if last_entry else 0
        new_balance = current_balance + tokens_delta
        
        # 寫入帳本
        entry = TokenLedger.objects.create(
            covenant_id=covenant_id,
            agent_id=agent_id,
            delta=tokens_delta,
            balance_after=new_balance,
            source_type=source_type,
            source_ref=source_ref,
            log_id=log_id,
            status='confirmed'
        )
        
        return entry

    @staticmethod
    @transaction.atomic
    def create_snapshot(covenant_id, trigger_log_id):
        """當 Covenant 進入 LOCKED 時產生快照"""
        # 聚合所有 Agent 的餘額
        # 由於 TokenLedger 是 INSERT-only，我們需要每個 agent_id 的最新一筆記錄
        from django.db.models import Max
        
        # 取得每個 Agent 最新的 Ledger ID
        latest_ids = TokenLedger.objects.filter(covenant_id=covenant_id).values('agent_id').annotate(
            latest_id=Max('id')
        ).values_list('latest_id', flat=True)
        
        latest_entries = TokenLedger.objects.filter(id__in=latest_ids)
        
        balances = []
        total_tokens = 0
        for entry in latest_entries:
            balances.append({
                'agent_id': entry.agent_id,
                'tokens': entry.balance_after
            })
            total_tokens += entry.balance_after
            
        # 計算 share_pct
        for b in balances:
            b['share_pct'] = (b['tokens'] / total_tokens * 100) if total_tokens > 0 else 0
            
        snapshot_data = {
            'covenant_id': covenant_id,
            'total_tokens': total_tokens,
            'balances': balances,
            'taken_at': timezone.now().isoformat()
        }
        
        # 計算快照 Hash
        snapshot_json = json.dumps(snapshot_data, sort_keys=True)
        snapshot_hash = hashlib.sha256(snapshot_json.encode('utf-8')).hexdigest()
        
        snapshot = TokenSnapshot.objects.create(
            covenant_id=covenant_id,
            trigger_log_id=trigger_log_id,
            total_tokens=total_tokens,
            balances=balances,
            hash=snapshot_hash
        )
        
        return snapshot
