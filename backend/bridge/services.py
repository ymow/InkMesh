import hashlib
import json
import uuid
from django.utils import timezone
from audit.models import AuditLog, ChainAnchor
from django.db import transaction

class BridgeService:
    @staticmethod
    def normalize_event(log_entry):
        """
        ACP Bridge - Event Normalizer (事件正規化器)
        把 MCP Tool 呼叫翻譯成 ACP 標準事件格式 (EIP 相容)。
        """
        # 這是 ACR-300 Log -> Standard Event 的對應
        standard_event = {
            "event": f"{log_entry.tool_name.capitalize()}Executed",
            "version": "ACR-20@1.0", # 或從日誌讀取
            "covenant_id": log_entry.covenant_id,
            "agent_id": log_entry.agent_id,
            "amount": log_entry.tokens_delta,
            "reason": f"{log_entry.tool_name}:{log_entry.log_id}",
            "timestamp": log_entry.timestamp.isoformat(),
            "hash": log_entry.hash
        }
        return standard_event

    @staticmethod
    @transaction.atomic
    def anchor_log_range(covenant_id, from_seq, to_seq, anchor_type="periodic"):
        """
        ACP Bridge - Chain Router & Proof Writer
        把 Log 範圍的 Range Hash 寫入 L2 (Base)。
        """
        logs = AuditLog.objects.filter(
            covenant_id=covenant_id, 
            sequence__range=(from_seq, to_seq)
        ).order_by('sequence')
        
        if not logs.exists():
            return None
            
        # 1. 計算 Range Hash (所有 entry.hash 串接後的 SHA-256)
        all_hashes = "".join([log.hash for log in logs])
        range_hash = hashlib.sha256(all_hashes.encode('utf-8')).hexdigest()
        
        # 2. 建立待處理的 Anchor 記錄
        anchor = ChainAnchor.objects.create(
            covenant_id=covenant_id,
            anchor_type=anchor_type,
            from_sequence=from_seq,
            to_sequence=to_seq,
            entry_count=logs.count(),
            range_hash=range_hash,
            chain='base',
            status='pending'
        )
        
        # 3. 模擬發送到 L2 (未來此處會呼叫 Web3.py 或 RPC)
        # Mocking a Base L2 TX Hash
        tx_hash = f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}"[:66]
        
        # 4. 更新狀態 (模擬非同步回傳)
        anchor.tx_hash = tx_hash
        anchor.status = 'confirmed'
        anchor.anchored_at = timezone.now()
        anchor.save()
        
        return anchor

    @staticmethod
    def get_audit_proof(covenant_id, target_log_id):
        """
        為特定 Log 產生一個「存證證明」。
        包含該 Log、前後日誌鏈摘要、以及對應的鏈上錨定。
        """
        log = AuditLog.objects.get(log_id=target_log_id)
        
        # 尋找包含此 Log 的 Anchor
        anchor = ChainAnchor.objects.filter(
            covenant_id=covenant_id,
            from_sequence__lte=log.sequence,
            to_sequence__gte=log.sequence,
            status='confirmed'
        ).first()
        
        return {
            "log": {
                "id": str(log.log_id),
                "sequence": log.sequence,
                "hash": log.hash,
                "timestamp": log.timestamp.isoformat()
            },
            "chain_anchor": {
                "tx_hash": anchor.tx_hash if anchor else None,
                "chain": anchor.chain if anchor else None,
                "range_hash": anchor.range_hash if anchor else None
            },
            "verified": anchor is not None
        }
