"""
Scope Enforcement & Target Safety
The "Kill Switch" - Ensures agents NEVER scan unauthorized targets

This is a CRITICAL security layer that prevents:
1. Scanning targets outside the defined scope
2. Accidentally pivoting to external domains (e.g., google.com links)
3. Hitting sensitive infrastructure (government, healthcare, critical infra)
"""
import re
import socket
import ipaddress
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse
from enum import Enum
import asyncio


class ScopeDecision(Enum):
    """Result of scope check"""
    ALLOWED = "allowed"
    DENIED_OUT_OF_SCOPE = "denied_out_of_scope"
    DENIED_EXCLUDED = "denied_excluded"
    DENIED_SENSITIVE = "denied_sensitive"
    DENIED_PRIVATE_IP = "denied_private_ip"


@dataclass
class ScopeConfig:
    """
    Scope configuration for a security assessment.
    Defines what targets are allowed and forbidden.
    """
    # Allowed patterns (wildcards supported)
    # e.g., ["*.example.com", "192.168.1.0/24", "api.target.io"]
    allowed_domains: List[str] = field(default_factory=list)
    allowed_ips: List[str] = field(default_factory=list)  # CIDR notation supported
    
    # Explicitly excluded (takes precedence over allowed)
    # e.g., ["prod.example.com", "admin.example.com"]
    excluded_domains: List[str] = field(default_factory=list)
    excluded_ips: List[str] = field(default_factory=list)
    
    # Safety settings
    allow_private_ips: bool = False  # 10.x, 172.16.x, 192.168.x
    allow_localhost: bool = False    # 127.0.0.1, localhost
    
    # Global blocklist (NEVER scan these)
    # These are always blocked regardless of scope
    sensitive_patterns: List[str] = field(default_factory=lambda: [
        # Government
        "*.gov", "*.gov.*", "*.mil",
        # Healthcare  
        "*.nhs.uk", "*.va.gov",
        # Critical Infrastructure
        "*.edu", "*.bank", "*.fin",
        # Major platforms (avoid accidents)
        "*.google.com", "*.googleapis.com",
        "*.microsoft.com", "*.azure.com",
        "*.amazon.com", "*.aws.amazon.com",
        "*.cloudflare.com",
        "*.github.com", "*.githubusercontent.com",
        # Social media
        "*.facebook.com", "*.twitter.com", "*.linkedin.com",
    ])


class ScopeEnforcer:
    """
    Enforces target scope restrictions.
    MUST be called before ANY tool execution.
    """
    
    def __init__(self, config: ScopeConfig):
        self.config = config
        self._compile_patterns()
        self._audit_log: List[Tuple[str, ScopeDecision, str]] = []
    
    def _compile_patterns(self):
        """Compile wildcard patterns to regex for efficient matching"""
        def wildcard_to_regex(pattern: str) -> re.Pattern:
            # Escape special chars, then convert * to .*
            escaped = re.escape(pattern)
            regex = escaped.replace(r'\*', '.*')
            return re.compile(f'^{regex}$', re.IGNORECASE)
        
        self._allowed_domain_patterns = [
            wildcard_to_regex(p) for p in self.config.allowed_domains
        ]
        self._excluded_domain_patterns = [
            wildcard_to_regex(p) for p in self.config.excluded_domains
        ]
        self._sensitive_patterns = [
            wildcard_to_regex(p) for p in self.config.sensitive_patterns
        ]
        
        # Parse IP networks
        self._allowed_networks = []
        for ip_spec in self.config.allowed_ips:
            try:
                self._allowed_networks.append(ipaddress.ip_network(ip_spec, strict=False))
            except ValueError:
                pass  # Invalid network, skip
        
        self._excluded_networks = []
        for ip_spec in self.config.excluded_ips:
            try:
                self._excluded_networks.append(ipaddress.ip_network(ip_spec, strict=False))
            except ValueError:
                pass
    
    def check_target(self, target: str) -> Tuple[ScopeDecision, str]:
        """
        Check if a target is within scope.
        
        Args:
            target: Domain, IP, URL, or hostname to check
            
        Returns:
            Tuple of (decision, reason)
        """
        # Normalize the target
        normalized = self._normalize_target(target)
        
        if not normalized:
            return ScopeDecision.DENIED_OUT_OF_SCOPE, "Invalid target format"
        
        domain, ip = normalized
        
        # Check 1: Sensitive patterns (ALWAYS blocked)
        if domain:
            for pattern in self._sensitive_patterns:
                if pattern.match(domain):
                    decision = ScopeDecision.DENIED_SENSITIVE
                    reason = f"Target matches sensitive pattern (protected infrastructure)"
                    self._log_decision(target, decision, reason)
                    return decision, reason
        
        # Check 2: Explicit exclusions
        if domain:
            for pattern in self._excluded_domain_patterns:
                if pattern.match(domain):
                    decision = ScopeDecision.DENIED_EXCLUDED
                    reason = f"Domain explicitly excluded from scope"
                    self._log_decision(target, decision, reason)
                    return decision, reason
        
        if ip:
            ip_obj = ipaddress.ip_address(ip)
            for network in self._excluded_networks:
                if ip_obj in network:
                    decision = ScopeDecision.DENIED_EXCLUDED
                    reason = f"IP explicitly excluded from scope"
                    self._log_decision(target, decision, reason)
                    return decision, reason
        
        # Check 3: Private/localhost IPs
        if ip:
            ip_obj = ipaddress.ip_address(ip)
            
            if ip_obj.is_loopback and not self.config.allow_localhost:
                decision = ScopeDecision.DENIED_PRIVATE_IP
                reason = "Localhost addresses not allowed"
                self._log_decision(target, decision, reason)
                return decision, reason
            
            if ip_obj.is_private and not self.config.allow_private_ips:
                decision = ScopeDecision.DENIED_PRIVATE_IP
                reason = "Private IP addresses not allowed"
                self._log_decision(target, decision, reason)
                return decision, reason
        
        # Check 4: Allowed patterns
        allowed = False
        
        if domain:
            for pattern in self._allowed_domain_patterns:
                if pattern.match(domain):
                    allowed = True
                    break
        
        if ip and not allowed:
            ip_obj = ipaddress.ip_address(ip)
            for network in self._allowed_networks:
                if ip_obj in network:
                    allowed = True
                    break
        
        if allowed:
            decision = ScopeDecision.ALLOWED
            reason = "Target is within defined scope"
            self._log_decision(target, decision, reason)
            return decision, reason
        
        # Default: Deny if not explicitly allowed
        decision = ScopeDecision.DENIED_OUT_OF_SCOPE
        reason = "Target not in allowed scope"
        self._log_decision(target, decision, reason)
        return decision, reason
    
    def _normalize_target(self, target: str) -> Optional[Tuple[Optional[str], Optional[str]]]:
        """
        Normalize target to (domain, ip) tuple.
        Returns None if target is invalid.
        """
        target = target.strip()
        
        # Handle URLs
        if '://' in target:
            parsed = urlparse(target)
            target = parsed.netloc or parsed.path
        
        # Remove port if present
        if ':' in target and not target.startswith('['):
            target = target.split(':')[0]
        
        # Handle IPv6
        if target.startswith('[') and ']' in target:
            target = target[1:target.index(']')]
        
        # Check if it's an IP
        try:
            ip = ipaddress.ip_address(target)
            return (None, str(ip))
        except ValueError:
            pass
        
        # It's a domain
        if self._is_valid_domain(target):
            return (target.lower(), None)
        
        return None
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Check if string is a valid domain name"""
        if not domain or len(domain) > 255:
            return False
        
        # Basic domain validation
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
    
    def _log_decision(self, target: str, decision: ScopeDecision, reason: str):
        """Log scope decision for auditing"""
        self._audit_log.append((target, decision, reason))
        
        # Keep only last 1000 entries
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]
    
    def get_audit_log(self) -> List[Tuple[str, ScopeDecision, str]]:
        """Get the audit log of all scope decisions"""
        return self._audit_log.copy()
    
    def validate_tool_call(self, tool_name: str, arguments: dict) -> Tuple[bool, str]:
        """
        Validate a tool call before execution.
        Extracts targets from various argument formats.
        """
        # Common target argument names
        target_keys = ['target', 'host', 'domain', 'url', 'ip', 'hosts', 'domains', 'urls']
        
        targets_to_check = []
        
        for key in target_keys:
            if key in arguments:
                value = arguments[key]
                if isinstance(value, str):
                    targets_to_check.append(value)
                elif isinstance(value, list):
                    targets_to_check.extend(value)
        
        if not targets_to_check:
            return False, f"No target found in tool arguments for {tool_name}"
        
        # Check all targets
        denied_targets = []
        for target in targets_to_check:
            decision, reason = self.check_target(target)
            if decision != ScopeDecision.ALLOWED:
                denied_targets.append(f"{target}: {reason}")
        
        if denied_targets:
            return False, f"Scope violation: {'; '.join(denied_targets)}"
        
        return True, "All targets within scope"


class ScopeMiddleware:
    """
    Middleware that wraps tool execution with scope enforcement.
    Use this to ensure NO tool can ever execute against out-of-scope targets.
    """
    
    def __init__(self, enforcer: ScopeEnforcer):
        self.enforcer = enforcer
        self.blocked_count = 0
        self.allowed_count = 0
    
    async def execute_with_scope_check(
        self,
        tool_executor,  # Callable that actually runs the tool
        tool_name: str,
        arguments: dict
    ):
        """
        Execute a tool ONLY if it passes scope validation.
        
        Raises:
            ScopeViolationError: If target is out of scope
        """
        is_valid, message = self.enforcer.validate_tool_call(tool_name, arguments)
        
        if not is_valid:
            self.blocked_count += 1
            raise ScopeViolationError(message)
        
        self.allowed_count += 1
        return await tool_executor(tool_name, arguments)
    
    def get_stats(self) -> dict:
        """Get middleware statistics"""
        return {
            "allowed": self.allowed_count,
            "blocked": self.blocked_count,
            "block_rate": self.blocked_count / max(1, self.allowed_count + self.blocked_count)
        }


class ScopeViolationError(Exception):
    """Raised when a tool attempts to execute against an out-of-scope target"""
    pass


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_scope_config_from_db(project_config: dict) -> ScopeConfig:
    """
    Create ScopeConfig from database project configuration.
    """
    return ScopeConfig(
        allowed_domains=project_config.get("allowed_domains", []),
        allowed_ips=project_config.get("allowed_ips", []),
        excluded_domains=project_config.get("excluded_domains", []),
        excluded_ips=project_config.get("excluded_ips", []),
        allow_private_ips=project_config.get("allow_private_ips", False),
        allow_localhost=project_config.get("allow_localhost", False),
    )


def create_strict_scope(domains: List[str], exclude: List[str] = None) -> ScopeEnforcer:
    """
    Create a strict scope enforcer for the given domains.
    Convenience function for common use case.
    """
    config = ScopeConfig(
        allowed_domains=domains,
        excluded_domains=exclude or [],
        allow_private_ips=False,
        allow_localhost=False,
    )
    return ScopeEnforcer(config)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Configure scope for example.com assessment
    config = ScopeConfig(
        allowed_domains=["*.example.com", "api.example.io"],
        allowed_ips=["192.168.1.0/24"],
        excluded_domains=["admin.example.com", "prod.example.com"],
        excluded_ips=["192.168.1.1"],
        allow_private_ips=True,
    )
    
    enforcer = ScopeEnforcer(config)
    
    # Test various targets
    test_targets = [
        "www.example.com",        # Should: ALLOWED
        "api.example.com",        # Should: ALLOWED
        "admin.example.com",      # Should: DENIED (excluded)
        "google.com",             # Should: DENIED (sensitive)
        "192.168.1.50",           # Should: ALLOWED
        "192.168.1.1",            # Should: DENIED (excluded IP)
        "10.0.0.1",               # Should: ALLOWED (private IPs enabled)
        "random.com",             # Should: DENIED (not in scope)
    ]
    
    for target in test_targets:
        decision, reason = enforcer.check_target(target)
        print(f"{target}: {decision.value} - {reason}")

