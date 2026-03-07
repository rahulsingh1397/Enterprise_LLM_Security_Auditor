"""
Basic smoke tests for scanner attack prompt generation.
Run: pytest tests/ -v
"""

import pytest
from backend.scanners.prompt_injection import PromptInjectionScanner
from backend.scanners.system_prompt import SystemPromptScanner
from backend.scanners.data_leakage import DataLeakageScanner
from backend.scanners.jailbreak import JailbreakScanner
from backend.scanners.pii_detection import PIIDetectionScanner
from backend.scanners.rag_security import RAGSecurityScanner


@pytest.mark.parametrize("ScannerClass,min_attacks", [
    (PromptInjectionScanner, 10),
    (SystemPromptScanner, 8),
    (DataLeakageScanner, 8),
    (JailbreakScanner, 8),
    (PIIDetectionScanner, 7),
    (RAGSecurityScanner, 8),
])
def test_scanner_has_attacks(ScannerClass, min_attacks):
    scanner = ScannerClass()
    attacks = scanner.attacks
    assert len(attacks) >= min_attacks
    for attack in attacks:
        assert "name" in attack
        assert "prompt" in attack
        assert len(attack["prompt"]) > 10, f"Attack '{attack['name']}' prompt too short"


def test_scanner_names_unique():
    scanners = [
        PromptInjectionScanner(),
        SystemPromptScanner(),
        DataLeakageScanner(),
        JailbreakScanner(),
        PIIDetectionScanner(),
        RAGSecurityScanner(),
    ]
    names = [s.name for s in scanners]
    assert len(names) == len(set(names)), "Scanner names must be unique"


def test_scanner_categories_unique():
    scanners = [
        PromptInjectionScanner(),
        SystemPromptScanner(),
        DataLeakageScanner(),
        JailbreakScanner(),
        PIIDetectionScanner(),
        RAGSecurityScanner(),
    ]
    cats = [s.category for s in scanners]
    assert len(cats) == len(set(cats)), "Scanner categories must be unique"


def test_risk_scorer():
    from backend.core.risk_scorer import calculate_risk_score, get_risk_level
    from backend.models.vulnerability import FindingBase

    # No findings → score 0
    assert calculate_risk_score([]) == 0.0

    # One critical at 100% confidence
    f = FindingBase(
        scanner_name="test", attack_name="test", attack_prompt="x",
        target_response="y", vulnerable=True, severity="critical",
        confidence=100, evidence=None, explanation="test",
        recommendation="fix it", category="test",
    )
    score = calculate_risk_score([f])
    assert 0 < score <= 100

    # Risk levels
    assert get_risk_level(90) == "Critical"
    assert get_risk_level(70) == "High"
    assert get_risk_level(50) == "Medium"
    assert get_risk_level(30) == "Low"
    assert get_risk_level(5) == "Minimal"
