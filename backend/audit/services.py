import hashlib
import json
import uuid
from django.db import transaction
from django.utils import timezone
from .models import AuditLog

class AuditService:
    @staticmethod
    @transaction.atomic
    def log_event(covenant_id, agent_id, session_id, tool_name, tool_type, 
                  params, result, result_detail, state_before, state_after, 
                  tokens_delta=0):
        """
        記錄一次合約事件，自動處理 Sequence 與 Hash 鏈。
        """
        # 取得最新的 Log 以決定 sequence 與 prev_log_id
        last_log = AuditLog.objects.filter(covenant_id=covenant_id).order_by('-sequence').first()
        
        sequence = (last_log.sequence + 1) if last_log else 1
        prev_log_id = last_log.log_id if last_log else None
        
        # 準備 log_id (UUID v4)
        log_id = uuid.uuid4()
        timestamp = timezone.now()
        
        # 計算 params_hash 與 params_preview
        # 注意：此處僅為示範，實際 preview 應根據 Tool 各自定義
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.sha256(params_str.encode('utf-8')).hexdigest()
        
        # 簡單的 preview 邏輯：遮蔽敏感資訊
        params_preview = {}
        for k, v in params.items():
            if k in ['content', 'text', 'draft', 'password']:
                params_preview[k] = f"*** (length: {len(str(v))})"
            else:
                params_preview[k] = v

        # 計算本筆 Log 的 Hash
        log_hash = AuditLog.compute_hash(
            prev_log_id=prev_log_id,
            log_id=log_id,
            covenant_id=covenant_id,
            sequence=sequence,
            agent_id=agent_id,
            tool_name=tool_name,
            result=result,
            tokens_delta=tokens_delta,
            state_after=state_after,
            timestamp=timestamp,
            params_hash=params_hash
        )

        # 寫入資料庫
        log_entry = AuditLog.objects.create(
            log_id=log_id,
            covenant_id=covenant_id,
            sequence=sequence,
            agent_id=agent_id,
            session_id=session_id,
            tool_name=tool_name,
            tool_type=tool_type,
            params_hash=params_hash,
            params_preview=params_preview,
            result=result,
            result_detail=result_detail,
            tokens_delta=tokens_delta,
            state_before=state_before,
            state_after=state_after,
            timestamp=timestamp,
            prev_log_id=prev_log_id,
            hash=log_hash
        )
        
        return log_entry

    @staticmethod
    def verify_chain(covenant_id):
        """
        驗證整個 Covenant 的日誌鏈是否完整且未經竄改。
        """
        logs = AuditLog.objects.filter(covenant_id=covenant_id).order_by('sequence')
        violations = []
        
        prev_id = None
        for log in logs:
            # 1. 檢查 prev_log_id
            if log.prev_log_id != prev_id:
                violations.append(f"Sequence {log.sequence}: prev_log_id mismatch")
            
            # 2. 重新計算 Hash 並比對
            recomputed_hash = AuditLog.compute_hash(
                prev_log_id=log.prev_log_id,
                log_id=log.log_id,
                covenant_id=log.covenant_id,
                sequence=log.sequence,
                agent_id=log.agent_id,
                tool_name=log.tool_name,
                result=log.result,
                tokens_delta=log.tokens_delta,
                state_after=log.state_after,
                timestamp=log.timestamp,
                params_hash=log.params_hash
            )
            
            if recomputed_hash != log.hash:
                violations.append(f"Sequence {log.sequence}: hash mismatch (tampered?)")
                
            prev_id = log.log_id
            
        return len(violations) == 0, violations
