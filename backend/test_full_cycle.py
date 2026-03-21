import os
import django
import sys
import uuid
import json

# Setup Django environment
sys.path.append('/Users/ymow/projects/inkmesh/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inkmesh_backend.settings')
django.setup()

from covenants.services import CovenantService
from covenants.models import AccessTier, CovenantState
from mcp_execution.tools.propose_passage import ProposePassageTool
from mcp_execution.tools.approve_draft import ApproveDraftTool
from mcp_execution.tools.generate_settlement import GenerateSettlementTool
from audit.services import AuditService
from tokens.models import PendingToken, TokenLedger
from settlement.models import SettlementOutput

def test_full_cycle():
    print("=== Step 1: Initialization ===")
    owner_pid = f"pid_owner_{uuid.uuid4().hex[:8]}"
    covenant = CovenantService.create_covenant(
        title="Royalty Settlement Test",
        space_type="book",
        owner_platform_id=owner_pid
    )
    covenant_id = covenant.covenant_id
    owner_agent_id = covenant.members.first().agent_id
    
    tier = AccessTier.objects.create(
        covenant=covenant,
        tier_id="contributor",
        display_name="Contributor",
        token_multiplier=1.0
    )
    
    CovenantService.transition_to_open(covenant_id)
    
    # Two agents join
    agent1_pid = "pid_agent_1"
    agent1 = CovenantService.join_covenant(covenant_id, agent1_pid, "contributor")
    agent2_pid = "pid_agent_2"
    agent2 = CovenantService.join_covenant(covenant_id, agent2_pid, "contributor")
    
    CovenantService.transition_to_active(covenant_id)
    
    print("=== Step 2: Contributions ===")
    # Agent 1 proposes 1000 words
    pt1 = ProposePassageTool(covenant_id, agent1.agent_id, "sess1")
    r1 = pt1.execute(word_count=1000)
    draft1_id = PendingToken.objects.filter(covenant_id=covenant_id, agent_id=agent1.agent_id).first().draft_id
    
    # Agent 2 proposes 500 words
    pt2 = ProposePassageTool(covenant_id, agent2.agent_id, "sess2")
    r2 = pt2.execute(word_count=500)
    draft2_id = PendingToken.objects.filter(covenant_id=covenant_id, agent_id=agent2.agent_id).first().draft_id
    
    print("=== Step 3: Approvals ===")
    at = ApproveDraftTool(covenant_id, owner_agent_id, "sess_admin")
    at.execute(draft_id=draft1_id, word_count=1000, acceptance_ratio=1.0) # 1000 tokens
    at.execute(draft_id=draft2_id, word_count=500, acceptance_ratio=1.0)  # 500 tokens
    
    print("=== Step 4: Settlement ===")
    # Transition to LOCKED
    CovenantService.transition_to_locked(covenant_id)
    
    st = GenerateSettlementTool(covenant_id, owner_agent_id, "sess_admin_settle")
    r_settle = st.execute()
    
    output = SettlementOutput.objects.get(output_id=r_settle['output_id'])
    print(f"Settlement Generated: {output.output_id}")
    print(f"Total Tokens: {output.total_tokens}")
    print("Distributions:")
    for dist in output.distributions:
        print(f"  Agent {dist['agent_id']}: Tokens={dist['ink_tokens']}, Final Share={dist['final_share_pct']}%")

    print("=== Step 5: Verification ===")
    is_valid, _ = AuditService.verify_chain(covenant_id)
    print(f"Audit Chain Valid: {is_valid}")

if __name__ == "__main__":
    test_full_cycle()
