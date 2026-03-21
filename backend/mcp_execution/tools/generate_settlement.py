from mcp_execution.base_tool import BaseClauseTool
from settlement.services import SettlementService
from covenants.models import CovenantState
from django.core.exceptions import ValidationError

class GenerateSettlementTool(BaseClauseTool):
    """
    實作 ACR-100: 產生結算建議報告的 Admin Tool。
    """
    tool_name = "generate_settlement_output"
    tool_type = "admin" # 結算報告屬於管理行為
    
    def _step2_check_preconditions(self, **params):
        # 注意：雖然繼承 BaseClauseTool，但我們覆寫 check，因為此處狀態必須是 LOCKED 或 SETTLED
        # 但有些 Covenant 可能在 ACTIVE 階段每季結算，因此我們保留一點彈性
        self.covenant = self._get_covenant()
        self.member = self._get_member()
        
        if not self.member.is_owner:
            raise ValidationError("Only Covenant Owner can trigger settlement.")
            
        if self.covenant.state not in [CovenantState.ACTIVE, CovenantState.LOCKED]:
            raise ValidationError(f"Covenant must be ACTIVE or LOCKED to settle. Current: {self.covenant.state}")

    def _get_covenant(self):
        from covenants.models import Covenant
        return Covenant.objects.get(covenant_id=self.covenant_id)

    def _get_member(self):
        from covenants.models import CovenantMember
        return CovenantMember.objects.get(covenant=self.covenant, agent_id=self.agent_id)

    def _step3_execute_logic(self, **params):
        # 邏輯主要在 Step 6 之前需要先知道 log_id，因此我們在 base_tool 的流程中執行
        return {
            'detail': "Settlement output generation triggered.",
            'is_final': True
        }
        
    def _step6_apply_side_effects(self, log_entry, side_effects, result_data, **params):
        # 實際產生報告
        settlement_output = SettlementService.generate_output(
            covenant_id=self.covenant_id,
            log_id=log_entry.log_id,
            log_hash=log_entry.hash
        )
        # 把 output_id 存入結果方便 Step 7 讀取
        result_data['output_id'] = settlement_output.output_id

    def _step7_generate_receipt(self, log_entry, result_data, side_effects):
        receipt = super()._step7_generate_receipt(log_entry, result_data, side_effects)
        receipt['output_id'] = result_data.get('output_id')
        return receipt
