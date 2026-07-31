"""Policy-governed execution pipeline with audit trail and hash chain integrity."""
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ecnyss.kernel import permission_model
from ecnyss.memory import episodic_store
from ecnyss.protocol import hash_chain
from ecnyss.util import results


@dataclass
class PolicyRule:
    """A single policy rule with predicate, effect, and optional obligation."""
    predicate: Callable[[Dict], bool]
    effect: permission_model.Decision
    obligation: Optional[Callable[[Dict], None]] = None


def key_equals(key: str, value: Any) -> Callable[[Dict], bool]:
    """Create a predicate that checks if context[key] == value."""
    def predicate(ctx: Dict) -> bool:
        return ctx.get(key) == value
    return predicate


def hash_obj(obj: Any) -> bytes:
    """Create a deterministic hash of an object."""
    serialized = json.dumps(obj, sort_keys=True, default=str).encode('utf-8')
    return hashlib.sha256(serialized).digest()


@dataclass
class ExecutionRecord:
    """Record of a single execution for the hash chain."""
    input_hash: bytes
    output_hash: Optional[bytes]
    decision: permission_model.Decision
    action_name: str


class PolicyEngine:
    """Policy-governed execution engine with audit trail and integrity verification."""
    
    def __init__(self, rules: Tuple[PolicyRule, ...] = ()):
        """Initialize the policy engine with optional rules."""
        self.rules = rules
        self.store = episodic_store.EpisodicStore()
        self.chain = hash_chain.HashChain()
    
    def _evaluate_policy(self, ctx: Dict) -> Tuple[permission_model.Decision, Optional[Callable]]:
        """Evaluate all rules and return the first matching decision and obligation."""
        for rule in self.rules:
            try:
                if rule.predicate(ctx):
                    return rule.effect, rule.obligation
            except Exception:
                continue
        # Default deny if no rules match
        return permission_model.Decision.DENY, None
    
    def _record_episode(self, ctx: Dict, decision: permission_model.Decision, 
                       action_name: str, output: Any = None) -> None:
        """Record an execution episode in the store and hash chain."""
        input_hash = hash_obj(ctx)
        output_hash = hash_obj(output) if output is not None else None
        
        # Create execution record for hash chain
        record = ExecutionRecord(
            input_hash=input_hash,
            output_hash=output_hash,
            decision=decision,
            action_name=action_name
        )
        self.chain.append(record)
        
        # Store episode in episodic store
        episode = episodic_store.Episode(
            actor=ctx.get("actor", "unknown"),
            decision=decision,
            provenance=episodic_store.Provenance(
                action=action_name,
                input_hash=input_hash,
                output_hash=output_hash
            ),
            context=ctx
        )
        self.store.add(episode)
    
    def execute(self, action: Callable, ctx: Dict) -> results.Result:
        """Execute an action under policy governance."""
        action_name = getattr(action, "__name__", "action")
        
        # Evaluate policy
        decision, obligation = self._evaluate_policy(ctx)
        
        # Record episode with decision
        self._record_episode(ctx, decision, action_name)
        
        if decision is permission_model.Decision.DENY:
            return results.Result.failure("policy_denied")
        
        # Run obligation if present
        if obligation is not None:
            try:
                obligation(ctx)
            except Exception:
                pass  # Obligation failures don't block execution
        
        # Execute the action
        try:
            output = action(ctx)
            return results.Result.success(output)
        except Exception as e:
            return results.Result.failure(type(e).__name__)