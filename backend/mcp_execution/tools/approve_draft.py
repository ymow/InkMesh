from mcp_execution.base_tool import BaseClauseTool
from tokens.models import PendingToken
from tokens.services import TokenService
from covenants.models import CovenantMember
from django.core.exceptions import ValidationError

class ApproveDraftTool(BaseClauseTool):
    tool_name = "approve_draft"
    
    def _step2_check_preconditions(self, **params):
        super()._step2_check_preconditions(**params)
        
        # 必須是 Owner 或有權限的人才能 Approve
        if not self.member.is_owner:
            raise ValidationError("Only Covenant Owner can approve drafts.")
            
        draft_id = params.get('draft_id')
        if not draft_id:
            raise ValidationError("draft_id is required")
            
        try:
            self.pending_token = PendingToken.objects.get(
                covenant_id=self.covenant_id, 
                draft_id=draft_id
            )
        except PendingToken.DoesNotExist:
            raise ValidationError(f"Draft {draft_id} not found or already processed.")

    def _step3_execute_logic(self, **params):
        acceptance_ratio = params.get('acceptance_ratio', 1.0)
        word_count = params.get('word_count', 0) # 由 Editor 確認最終字數
        
        if word_count <= 0:
             raise ValidationError("word_count must be provided for approval.")
        
        return {
            'draft_id': params['draft_id'],
            'proposer_agent_id': self.pending_token.agent_id,
            'acceptance_ratio': acceptance_ratio,
            'word_count': word_count,
            'detail': f"Draft {params['draft_id']} approved with {acceptance_ratio*100}% ratio.",
            'is_final': True
        }
        
    def _step4_calculate_side_effects(self, result_data, **params):
        # 先計算預計會發多少 Token
        proposer = CovenantMember.objects.get(
            covenant=self.covenant, 
            agent_id=result_data['proposer_agent_id']
        )
        multiplier = proposer.tier.token_multiplier if proposer.tier else 1.0
        
        tokens_delta = TokenService.calculate_tokens(
            word_count=result_data['word_count'],
            tier_multiplier=multiplier,
            acceptance_ratio=result_data['acceptance_ratio']
        )
        
        return {
            'tokens_delta': tokens_delta,
            'state_after': self.covenant.state
        }

    def _step6_apply_side_effects(self, log_entry, side_effects, result_data, **params):
        # 1. 寫入帳本
        TokenService.confirm_contribution(
            covenant_id=self.covenant_id,
            agent_id=result_data['proposer_agent_id'],
            log_id=log_entry.log_id,
            word_count=result_data['word_count'],
            source_ref=result_data['draft_id'],
            acceptance_ratio=result_data['acceptance_ratio']
        )
        
        # 2. 清除 PendingToken
        self.pending_token.delete()
