"""
SQL Injection Golden Scenarios
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .base import GoldenScenario, ContextScenario


@dataclass
class DVWASQLiScenario(GoldenScenario):
    """
    Scenario: Find SQL Injection in DVWA login form
    Target: DVWA (vulnerables/web-dvwa)
    Difficulty: Easy
    """
    id: str = "sqli-dvwa-login"
    name: str = "DVWA Login SQL Injection"
    description: str = "Find the SQL injection vulnerability in the DVWA login form"
    difficulty: str = "easy"
    category: str = "sqli"
    
    target_url: str = "http://172.28.1.10:80"
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.10", "*.dvwa.local"])
    
    expected_vuln_type: str = "sqli"
    expected_location: str = "/vulnerabilities/sqli/"
    
    max_steps: int = 10
    
    def get_prompt(self) -> str:
        return f"""
        Audit the web application at {self.target_url} for SQL injection vulnerabilities.
        Focus on the login functionality and any user input forms.
        Report any SQLi vulnerabilities you find with evidence.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        # Check if any finding mentions SQL injection
        for finding in findings:
            vuln_type = finding.get("type", "").lower()
            if "sql" in vuln_type or "sqli" in vuln_type:
                return True
        
        # Also check logs for SQLi detection
        logs_text = " ".join(logs).lower()
        sqli_indicators = [
            "sql injection", "sqli", "' or '1'='1",
            "union select", "error-based", "blind sql"
        ]
        return any(indicator in logs_text for indicator in sqli_indicators)


@dataclass
class JuiceShopSQLiScenario(GoldenScenario):
    """
    Scenario: Find SQL Injection in Juice Shop search
    Target: OWASP Juice Shop
    Difficulty: Medium
    """
    id: str = "sqli-juice-search"
    name: str = "Juice Shop Search SQL Injection"
    description: str = "Find the SQL injection in the product search endpoint"
    difficulty: str = "medium"
    category: str = "sqli"
    
    target_url: str = "http://172.28.1.20:3000"
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.20", "*.juice-shop.local"])
    
    expected_vuln_type: str = "sqli"
    expected_location: str = "/rest/products/search"
    
    max_steps: int = 15
    
    def get_prompt(self) -> str:
        return f"""
        The target is a modern e-commerce application at {self.target_url}.
        Your objective is to find SQL injection vulnerabilities in the API endpoints.
        Pay special attention to search functionality and product queries.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        for finding in findings:
            vuln_type = finding.get("type", "").lower()
            location = finding.get("location", "").lower()
            
            if "sql" in vuln_type and ("search" in location or "product" in location):
                return True
        
        # Check logs
        logs_text = " ".join(logs).lower()
        return "sql injection" in logs_text and "search" in logs_text


@dataclass  
class ContextAwareSQLiScenario(ContextScenario):
    """
    Scenario: Use uploaded API spec to find SQLi
    This tests RAG capabilities - agent must read the spec to know where to look
    Difficulty: Hard
    """
    id: str = "sqli-context-idor"
    name: str = "Context-Aware SQLi Discovery"
    description: str = "Use the uploaded API documentation to find the SQLi in the billing endpoint"
    difficulty: str = "hard"
    category: str = "sqli"
    
    target_url: str = "http://172.28.1.20:3000"
    allowed_scope: List[str] = field(default_factory=lambda: ["172.28.1.20"])
    
    expected_vuln_type: str = "sqli"
    expected_location: str = "/api/v1/billing/invoice"
    
    max_steps: int = 20
    
    # The "uploaded" API spec that hints at the vulnerability
    context_documents: List[str] = field(default_factory=lambda: [
        """
        API Specification: Billing Service v2.1
        
        Endpoint: GET /api/v1/billing/invoice/{id}
        Description: Retrieves invoice details by ID
        
        Parameters:
        - id: Invoice identifier (WARNING: This endpoint uses raw SQL queries 
              for legacy compatibility. The 'id' parameter is concatenated 
              directly into the query string.)
        
        Example: GET /api/v1/billing/invoice/12345
        
        Known Issues:
        - SEC-2023-001: Input validation not implemented for 'id' parameter
        """
    ])
    
    def get_prompt(self) -> str:
        return f"""
        I just uploaded the API specification for our billing service.
        The spec mentions a security issue in the getInvoice endpoint.
        Please audit {self.target_url} and find the SQL injection vulnerability 
        described in the documentation.
        """
    
    def check_success(self, findings: List[Dict], logs: List[str]) -> bool:
        # Must find SQLi AND must have used context
        found_sqli = False
        used_context = self.check_context_usage(logs)
        
        for finding in findings:
            vuln_type = finding.get("type", "").lower()
            location = finding.get("location", "").lower()
            
            if "sql" in vuln_type and ("invoice" in location or "billing" in location):
                found_sqli = True
                break
        
        # Full success requires both
        return found_sqli and used_context


# Export all scenarios
SQLI_SCENARIOS = [
    DVWASQLiScenario(),
    JuiceShopSQLiScenario(),
    ContextAwareSQLiScenario(),
]

