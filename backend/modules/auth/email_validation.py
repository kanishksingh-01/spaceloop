"""
SpaceLoop Email Validation & Disposable Domain Defense Module
Follows Rule 5: Deterministic core business logic.
Integrates RFC 5322 validation, Unicode/punycode normalization,
and comprehensive disposable/temporary email provider blocking with subdomain evasion defense.
"""
import os
import re
import logging
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger("spaceloop.email_validation")

# Fallback built-in list in case file is absent
_FALLBACK_DISPOSABLE_DOMAINS = {
    "mailinator.com", "mailinator.net", "mailinator.org", "mailinator2.com", "mailin8r.com",
    "10minutemail.com", "10minutemail.net", "10minutemail.org", "10minutenmail.de",
    "guerrillamail.com", "guerrillamail.net", "guerrillamail.biz", "guerrillamail.org",
    "sharklasers.com", "grr.la", "guerrillamailblock.com", "pokemail.net", "spam4.me",
    "tempmail.com", "tempmail.net", "tempmail.org", "temp-mail.org", "temp-mail.io", "temp-mail.ru",
    "yopmail.com", "yopmail.fr", "yopmail.net", "cool.fr.nf", "jetable.fr.nf",
    "dispostable.com", "throwawaymail.com", "getairmail.com", "fakeinbox.com",
    "trashmail.com", "trashmail.net", "trashmail.me", "trashmail.at", "trashmail.de",
    "mytemp.email", "generator.email", "emailondeck.com", "minuteinbox.com",
    "burnermail.io", "mohmal.com", "mohmal.im", "mohmal.in", "discard.email",
    "discardmail.com", "crazymailing.com", "maildrop.cc", "getnada.com",
    "inboxbear.com", "inboxkitten.com", "tempr.email", "binkmail.com",
    "safetymail.info", "trashemail.net", "zillamail.com", "mailnesia.com",
    "tempinbox.com", "incognitomail.com", "tmail.ws", "mytrashmail.com",
    "armyspy.com", "cuvox.de", "dayrep.com", "einrot.com", "fambit.com",
    "fleexy.tv", "gustr.com", "jourrapide.com", "rhyta.com", "superrito.com", "teleworm.us"
}


def _load_disposable_domains() -> set[str]:
    """Loads disposable domains from disk or falls back to built-in set."""
    domains = set(_FALLBACK_DISPOSABLE_DOMAINS)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "disposable_domains.txt")

    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip().lower()
                    if line and not line.startswith("#"):
                        domains.add(line)
            logger.debug(f"Loaded {len(domains)} disposable domains.")
        except Exception as e:
            logger.warning(f"Could not load disposable_domains.txt: {e}. Using fallback set.")
    return domains


DISPOSABLE_DOMAINS: set[str] = _load_disposable_domains()


def is_disposable_domain(domain: str) -> bool:
    """
    Checks if a domain or any of its parent domains is a known disposable provider.
    Protects against evasion tricks such as subdomains (e.g., test@sub.mailinator.com).
    """
    if not domain:
        return False

    clean_domain = domain.strip().lower().rstrip(".")
    if clean_domain in DISPOSABLE_DOMAINS:
        return True

    # Check parent domain hierarchies (e.g. foo.bar.mailinator.com -> bar.mailinator.com -> mailinator.com)
    parts = clean_domain.split(".")
    for i in range(1, len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in DISPOSABLE_DOMAINS:
            return True

    return False


def validate_email_address(email: str, check_disposable: bool = True) -> tuple[bool, str, str]:
    """
    Performs comprehensive validation of an email address:
    1. Rejects non-string, empty, or whitespace-only inputs.
    2. Validates RFC 5322 syntax, length, character set, and punycode normalization.
    3. Blocks IP-literal domains and domains without valid TLDs.
    4. Evaluates disposable/temporary provider blocklists and subdomain variations.

    Returns:
        tuple[bool, str, str]: (is_valid, normalized_email, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "", "Email address is required."

    raw_email = email.strip()
    if not raw_email:
        return False, "", "Email address cannot be empty."

    if len(raw_email) > 254:
        return False, "", "Email address exceeds maximum length of 254 characters."

    # Validate syntax and normalize (Unicode NFC, punycode, case folding)
    try:
        valid_info = validate_email(raw_email, check_deliverability=False)
        normalized = valid_info.normalized
        domain = valid_info.domain.lower()
    except EmailNotValidError as e:
        return False, "", f"Invalid email format: {str(e)}"
    except Exception as e:
        return False, "", f"Invalid email format: {str(e)}"

    # Protect against IP-literal addresses (e.g. user@[192.168.1.1])
    if domain.startswith("[") and domain.endswith("]"):
        return False, "", "IP address domain literals are not permitted."

    # Check for valid TLD structure (at least one dot and non-numeric TLD of length >= 2)
    parts = domain.split(".")
    if len(parts) < 2 or len(parts[-1]) < 2 or parts[-1].isdigit():
        return False, "", "Invalid email domain structure."

    # Check disposable / temporary domain blocklist
    if check_disposable and is_disposable_domain(domain):
        return (
            False,
            normalized,
            "Disposable or temporary email addresses are not permitted. Please use a permanent email address."
        )

    return True, normalized, ""
