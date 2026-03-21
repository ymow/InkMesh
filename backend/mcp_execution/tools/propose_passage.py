import uuid
from django.utils import timezone
from datetime import timedelta
from mcp_execution.base_tool import BaseClauseTool
from tokens.models import PendingToken
from django.core.exceptions import ValidationError

class ProposePassageTool(BaseClauseTool):
    tool_name = "propose_passage"
    
    def _step2_check_preconditions(self, **params):
        super()._step2_check_preconditions(**params)
        
        # 檢查必填參數
        word_count = params.get('word_count')
        if not word_count or word_count <= 0:
            raise ValidationError("word_count must be greater than 0")
            
        # Optional: Rate Limit Check 可以加在這裡

    def _step3_execute_logic(self, **params):
        # 因為 InkMesh 是 Zero Knowledge，我們不儲存原始內容 (params['content'])
        # 我們只產生一個 draft_id 代表這次的提交
        draft_id = f"draft_{uuid.uuid4().hex[:8]}"
        
        return {
            'draft_id': draft_id,
            'word_count': params.get('word_count'),
            'detail': f"Draft {draft_id} proposed with {params.get('word_count')} words.",
            'is_final': False # 代表這是 Pending 狀態，還沒拿到 Token
        }

    def _step6_apply_side_effects(self, log_entry, side_effects, result_data, **params):
        # 建立 Pending Token (因為觸發條件是 on_approve)
        PendingToken.objects.create(
            covenant_id=self.covenant_id,
            agent_id=self.agent_id,
            draft_id=result_data['draft_id'],
            estimated_tokens=0, # 實際數量等 Approve 才算
            expires_at=timezone.now() + timedelta(days=30)
        )
