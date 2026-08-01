import pytest

from farmers_chatbot.auth import IdentityError, identity_from_claims


def test_non_google_oidc_issuer_is_rejected():
    with pytest.raises(IdentityError):
        identity_from_claims(
            {
                "iss": "https://identity.example.org",
                "sub": "subject",
                "email": "tester@example.org",
                "email_verified": True,
            }
        )
