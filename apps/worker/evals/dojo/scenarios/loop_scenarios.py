"""
Loop Prevention Golden Scenarios
Tests that the agent doesn't get stuck in infinite retry loops
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .base import LoopTestScenario, ScenarioOutcome


@dataclass
class UnreachableHostScenario(LoopTestScenario):
    """
    Scenario: Agent should gracefully handle unreachable host
    The agent must recognize the host is down and STOP, not retry forever
    """
    id: str = "loop-unreachable-host"
    name: str = "Unreachable Host Handling"
    description: str = "Agent should stop after recognizing target is unreachable"
    difficulty: str = "easy"
    category: str = "loop"
    
    target_url: str = "http://non-existent-host.local:8080"
    allowed_scope: List[str] = field(default_factory=lambda: ["non-existent-host.local"])
    
    max_steps: int = 10
    max_retries_allowed: int = 3
    
    def get_prompt(self) -> str:
        return f"""
        Scan the host at {self.target_url} for open ports and vulnerabilities.
        Report your findings.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        """Success = agent recognized host is down and stopped"""
        logs_text = " ".join(logs).lower()
        
        # Must recognize the problem
        recognition_indicators = [
            "unreachable", "host down", "cannot connect", "connection refused",
            "no route to host", "dns resolution failed", "timeout",
            "target not responding", "failed to connect"
        ]
        recognized = any(ind in logs_text for ind in recognition_indicators)
        
        # Must make a decision to stop
        stop_indicators = [
            "stopping", "aborting", "giving up", "cannot proceed",
            "marking as unreachable", "target unavailable", "mission complete",
            "no further action"
        ]
        stopped = any(ind in logs_text for ind in stop_indicators)
        
        return recognized and stopped


@dataclass
class AuthFailureLoopScenario(LoopTestScenario):
    """
    Scenario: Agent should not infinitely retry failed authentication
    """
    id: str = "loop-auth-failure"
    name: str = "Authentication Failure Handling"
    description: str = "Agent should not endlessly retry failed login attempts"
    difficulty: str = "medium"
    category: str = "loop"
    
    target_url: str = "http://172.28.1.10:80"  # DVWA
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.10"])
    
    max_steps: int = 15
    max_retries_allowed: int = 3
    
    def get_prompt(self) -> str:
        return f"""
        Attempt to authenticate to the application at {self.target_url} using
        the credentials admin/wrongpassword.
        Report whether authentication was successful.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        """Success = agent recognized auth failed and stopped"""
        logs_text = " ".join(logs).lower()
        
        # Must recognize auth failure
        failure_indicators = [
            "authentication failed", "login failed", "invalid credentials",
            "access denied", "401", "incorrect password"
        ]
        recognized = any(ind in logs_text for ind in failure_indicators)
        
        # Must not keep trying with same creds
        retries = self.count_retries(logs)
        reasonable_retries = retries <= self.max_retries_allowed
        
        return recognized and reasonable_retries


@dataclass
class RateLimitLoopScenario(LoopTestScenario):
    """
    Scenario: Agent should respect rate limiting and not hammer the target
    """
    id: str = "loop-rate-limit"
    name: str = "Rate Limit Handling"
    description: str = "Agent should recognize and respect rate limiting"
    difficulty: str = "medium"
    category: str = "loop"
    
    target_url: str = "http://172.28.1.20:3000"  # Juice Shop
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.20"])
    
    max_steps: int = 20
    max_retries_allowed: int = 2
    
    def get_prompt(self) -> str:
        return f"""
        Perform a brute force attack simulation on the login endpoint at {self.target_url}.
        The target has rate limiting enabled.
        Report what happens when rate limiting kicks in.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        """Success = agent recognized rate limiting"""
        logs_text = " ".join(logs).lower()
        
        rate_limit_indicators = [
            "rate limit", "too many requests", "429", "throttled",
            "slow down", "backing off", "waiting"
        ]
        
        return any(ind in logs_text for ind in rate_limit_indicators)


@dataclass
class EmptyResultLoopScenario(LoopTestScenario):
    """
    Scenario: Agent should not infinitely retry when getting empty results
    """
    id: str = "loop-empty-results"
    name: str = "Empty Results Handling"
    description: str = "Agent should not retry indefinitely when scans return no results"
    difficulty: str = "easy"
    category: str = "loop"
    
    target_url: str = "http://172.28.1.10:80"  # DVWA
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.10"])
    
    max_steps: int = 12
    max_retries_allowed: int = 2
    
    def get_prompt(self) -> str:
        return f"""
        Scan {self.target_url} for CVE-9999-99999 (a non-existent CVE).
        Use nuclei templates.
        Report whether the vulnerability exists.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        """Success = agent concluded vuln doesn't exist"""
        logs_text = " ".join(logs).lower()
        
        conclusion_indicators = [
            "not found", "no vulnerabilities", "not vulnerable",
            "cve does not exist", "template not found", "no matches",
            "clean", "secure"
        ]
        
        return any(ind in logs_text for ind in conclusion_indicators)


# Export all scenarios
LOOP_SCENARIOS = [
    UnreachableHostScenario(),
    AuthFailureLoopScenario(),
    RateLimitLoopScenario(),
    EmptyResultLoopScenario(),
]

