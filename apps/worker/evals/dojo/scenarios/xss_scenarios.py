"""
XSS (Cross-Site Scripting) Golden Scenarios
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .base import GoldenScenario


@dataclass
class DVWAReflectedXSSScenario(GoldenScenario):
    """
    Scenario: Find Reflected XSS in DVWA
    Target: DVWA
    Difficulty: Easy
    """
    id: str = "xss-dvwa-reflected"
    name: str = "DVWA Reflected XSS"
    description: str = "Find the reflected XSS vulnerability in DVWA"
    difficulty: str = "easy"
    category: str = "xss"
    
    target_url: str = "http://172.28.1.10:80"
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.10"])
    
    expected_vuln_type: str = "xss"
    expected_location: str = "/vulnerabilities/xss_r/"
    
    max_steps: int = 10
    
    def get_prompt(self) -> str:
        return f"""
        Test the web application at {self.target_url} for Cross-Site Scripting (XSS) vulnerabilities.
        Focus on reflected XSS in user input fields.
        Provide proof of concept and evidence.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        for finding in findings:
            vuln_type = finding.get("type", "").lower()
            if "xss" in vuln_type or "cross-site" in vuln_type:
                return True
        
        logs_text = " ".join(logs).lower()
        return "xss" in logs_text and ("reflected" in logs_text or "found" in logs_text)


@dataclass
class JuiceShopDOMXSSScenario(GoldenScenario):
    """
    Scenario: Find DOM-based XSS in Juice Shop search
    Target: OWASP Juice Shop
    Difficulty: Medium
    """
    id: str = "xss-juice-dom"
    name: str = "Juice Shop DOM XSS"
    description: str = "Find the DOM-based XSS in the search functionality"
    difficulty: str = "medium"
    category: str = "xss"
    
    target_url: str = "http://172.28.1.20:3000"
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.20"])
    
    expected_vuln_type: str = "xss"
    expected_location: str = "/search"
    
    max_steps: int = 15
    
    def get_prompt(self) -> str:
        return f"""
        The target at {self.target_url} is a modern JavaScript-heavy application.
        Find any DOM-based XSS vulnerabilities.
        Pay attention to client-side rendering and search functionality.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        for finding in findings:
            vuln_type = finding.get("type", "").lower()
            location = finding.get("location", "").lower()
            
            if "xss" in vuln_type and "search" in location:
                return True
        
        logs_text = " ".join(logs).lower()
        return "dom" in logs_text and "xss" in logs_text


@dataclass
class StoredXSSScenario(GoldenScenario):
    """
    Scenario: Find Stored XSS in a comments/feedback form
    Target: DVWA or Juice Shop
    Difficulty: Medium
    """
    id: str = "xss-stored-feedback"
    name: str = "Stored XSS in Feedback"
    description: str = "Find stored XSS in the feedback/comments functionality"
    difficulty: str = "medium"
    category: str = "xss"
    
    target_url: str = "http://172.28.1.20:3000"
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.20"])
    
    expected_vuln_type: str = "xss"
    expected_location: str = "/feedback"
    
    max_steps: int = 20
    
    def get_prompt(self) -> str:
        return f"""
        Test {self.target_url} for stored XSS vulnerabilities.
        Look for places where user input is stored and displayed to other users,
        such as comments, feedback forms, or user profiles.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        for finding in findings:
            vuln_type = finding.get("type", "").lower()
            
            if "xss" in vuln_type and "stored" in finding.get("title", "").lower():
                return True
        
        logs_text = " ".join(logs).lower()
        return "stored xss" in logs_text or ("xss" in logs_text and "feedback" in logs_text)


# Export all scenarios
XSS_SCENARIOS = [
    DVWAReflectedXSSScenario(),
    JuiceShopDOMXSSScenario(),
    StoredXSSScenario(),
]

