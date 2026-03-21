import os
import django
import sys
import uuid

# Setup Django environment
sys.path.append('/Users/ymow/projects/inkmesh/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inkmesh_backend.settings')
django.setup()

from covenants.services import CovenantService
from covenants.models import AccessTier, CovenantState
from mcp_execution.tools.propose_passage import ProposePassageTool
from mcp_execution.tools.approve_draft import ApproveDraftTool
from audit.services import AuditService
from tokens.models import PendingToken, TokenLedger

def test_execution_layer():
    print("1. Creating Covenant and Members...")
    # Owner
    owner_pid = f"pid_owner_{uuid.uuid4().hex[:8]}"
    covenant = CovenantService.create_covenant(
        title="Execution Layer Test Book",
        space_type="book",
        owner_platform_id=owner_pid
    )
    covenant_id = covenant.covenant_id
    owner_agent_id = covenant.members.first().agent_id
    
    # Create a Tier
    tier = AccessTier.objects.create(
        covenant=covenant,
        tier_id="contributor",
        display_name="Contributor",
        token_multiplier=1.2
    )
    
    # Open Covenant
    CovenantService.transition_to_open(covenant_id)
    
    # Agent joins
    agent_pid = f"pid_agent_{uuid.uuid4().hex[:8]}"
    agent_member = CovenantService.join_covenant(covenant_id, agent_pid, "contributor")
    agent_id = agent_member.agent_id
    
    # Active Covenant
    CovenantService.transition_to_active(covenant_id)
    
    print("2. Testing ProposePassageTool...")
    propose_tool = ProposePassageTool(
        covenant_id=covenant_id,
        agent_id=agent_id,
        session_id=f"sess_{uuid.uuid4().hex[:8]}"
    )
    
    receipt1 = propose_tool.execute(word_count=500, content="This is a test passage.")
    print("Receipt 1:", receipt1)
    
    # Verify Pending Token
    pending = PendingToken.objects.filter(draft_id=receipt1['tool_name']).first() # Use receipt tool name just to debug output
    pending_list = PendingToken.objects.filter(covenant_id=covenant_id)
    print(f"Pending Tokens count: {pending_list.count()}")
    draft_id = pending_list.first().draft_id
    
    print("3. Testing ApproveDraftTool...")
    approve_tool = ApproveDraftTool(
        covenant_id=covenant_id,
        agent_id=owner_agent_id, # Must be owner
        session_id=f"sess_{uuid.uuid4().hex[:8]}"
    )
    
    receipt2 = approve_tool.execute(
        draft_id=draft_id,
        word_count=450, # Partially accepted
        acceptance_ratio=0.9
    )
    print("Receipt 2:", receipt2)
    
    # Verify Token Ledger
    ledger = TokenLedger.objects.filter(covenant_id=covenant_id, agent_id=agent_id).first()
    print(f"Tokens awarded: {ledger.delta}, Balance: {ledger.balance_after}")
    
    print("4. Verifying Audit Chain...")
    is_valid, violations = AuditService.verify_chain(covenant_id)
    print(f"Chain Valid: {is_valid}")
    if not is_valid:
        print("Violations:", violations)

if __name__ == "__main__":
    test_execution_layer()
