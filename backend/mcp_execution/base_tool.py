from django.db import transaction
from django.core.exceptions import ValidationError
from covenants.models import Covenant, CovenantMember, CovenantState
from audit.services import AuditService

class BaseClauseTool:
    """
    實作 ACP Execution Layer v0.1 的 Clause Tool 七步執行流程。
    這是一個抽象基底類別，具體的 Tool 需繼承並實作對應的方法。
    """
    tool_name = "unknown_tool"
    tool_type = "clause"

    def __init__(self, covenant_id, agent_id, session_id):
        self.covenant_id = covenant_id
        self.agent_id = agent_id
        self.session_id = session_id
        self.covenant = None
        self.member = None

    @transaction.atomic
    def execute(self, **params):
        """
        核心的七步執行法 (Seven-Step Execution Flow)
        不可跳步、不可更改順序。
        """
        try:
            # Step 1: 身份驗證
            self._step1_verify_identity()

            # Step 2: 前置條件檢查 (Pre-condition)
            self._step2_check_preconditions(**params)

            # Step 3: 執行 (Execute Core Logic)
            result_data = self._step3_execute_logic(**params)

            # Step 4: 副作用計算 (Side Effects - 只計算不寫入)
            side_effects = self._step4_calculate_side_effects(result_data, **params)

            # Step 5: 寫入 Audit Log (Commit - 最重要的一步)
            log_entry = self._step5_commit_audit_log(params, result_data, side_effects)

            # Step 6: 副作用生效 (Apply - 如: 寫入 Token)
            self._step6_apply_side_effects(log_entry, side_effects, result_data, **params)

            # Step 7: 回傳收據 (Receipt)
            return self._step7_generate_receipt(log_entry, result_data, side_effects)

        except ValidationError as e:
            # 如果在 Step 1-2 失敗，紀錄 Rejected Log
            self._log_rejection(params, str(e))
            raise

    # --- 以下為內部實作與需被子類別覆寫的方法 ---

    def _step1_verify_identity(self):
        try:
            self.covenant = Covenant.objects.get(covenant_id=self.covenant_id)
            self.member = CovenantMember.objects.get(
                covenant=self.covenant, 
                agent_id=self.agent_id
            )
        except (Covenant.DoesNotExist, CovenantMember.DoesNotExist):
            raise ValidationError("Identity verification failed. Agent not in covenant.")

    def _step2_check_preconditions(self, **params):
        """子類別需實作具體的前置檢查，例如狀態、權限、Rate Limit。"""
        if self.covenant.state != CovenantState.ACTIVE:
             raise ValidationError(f"Covenant must be ACTIVE, currently {self.covenant.state}")

    def _step3_execute_logic(self, **params):
        """子類別需實作核心業務邏輯，回傳包含執行結果的字典。"""
        raise NotImplementedError

    def _step4_calculate_side_effects(self, result_data, **params):
        """
        計算會發生什麼改變（但不實際改變資料庫）。
        回傳結構如: {'tokens_delta': 0, 'state_after': 'ACTIVE'}
        """
        return {
            'tokens_delta': 0,
            'state_after': self.covenant.state
        }

    def _step5_commit_audit_log(self, params, result_data, side_effects):
        return AuditService.log_event(
            covenant_id=self.covenant_id,
            agent_id=self.agent_id,
            session_id=self.session_id,
            tool_name=self.tool_name,
            tool_type=self.tool_type,
            params=params,
            result='success',
            result_detail=result_data.get('detail', 'Success'),
            state_before=self.covenant.state,
            state_after=side_effects['state_after'],
            tokens_delta=side_effects['tokens_delta']
        )

    def _step6_apply_side_effects(self, log_entry, side_effects, result_data, **params):
        """子類別可覆寫以應用額外的副作用，例如寫入 Tokens"""
        pass

    def _step7_generate_receipt(self, log_entry, result_data, side_effects):
        return {
            "receipt_id": str(log_entry.log_id),
            "covenant_id": self.covenant_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "status": "accepted" if result_data.get('is_final', True) else "pending",
            "tokens_awarded": side_effects.get('tokens_delta', 0),
            "timestamp": log_entry.timestamp.isoformat(),
            "log_hash": log_entry.hash
        }

    def _log_rejection(self, params, reason):
         """在條件不符時，寫入 Rejected Log"""
         state = self.covenant.state if self.covenant else "UNKNOWN"
         AuditService.log_event(
            covenant_id=self.covenant_id,
            agent_id=self.agent_id,
            session_id=self.session_id,
            tool_name=self.tool_name,
            tool_type=self.tool_type,
            params=params,
            result='rejected',
            result_detail=reason,
            state_before=state,
            state_after=state,
            tokens_delta=0
        )
