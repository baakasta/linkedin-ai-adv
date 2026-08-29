from __future__ import annotations


def build_assistant_placeholder(user_message: str, company_name: str | None = None) -> str:
    """Deterministic assistant reply used when the Java AI service is unavailable."""
    ctx = f" pour {company_name}" if company_name else ""
    return (
        f"[Assistant IA - mode placeholder] Merci pour votre message{ctx} : \"{user_message}\". "
        "Une fois le service IA intégré, je pourrai vous aider à optimiser votre présence "
        "LinkedIn, suggérer des contenus et analyser vos performances en temps réel."
    )
