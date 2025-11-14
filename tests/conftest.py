import pytest


@pytest.fixture(scope="session")
def accounts():
    """Provide test accounts"""
    from ape import accounts as ape_accounts
    return ape_accounts.test_accounts
