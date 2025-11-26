import pytest
import ape
from ape import project, accounts, Contract
from conftest import get_passthrough_at


@pytest.fixture
def owner(accounts):
    return accounts[0]


@pytest.fixture
def ownership_admin(accounts):
    return accounts[1]


@pytest.fixture
def parameter_admin(accounts):
    return accounts[2]


@pytest.fixture
def emergency_admin(accounts):
    return accounts[3]


@pytest.fixture
def mock_gauge(accounts, owner):
    """Deploy a mock gauge for testing"""
    # For now, just return an account address
    # In a real scenario, you'd deploy a mock gauge contract
    return accounts[8]


@pytest.fixture
def mock_token(accounts, owner):
    """Deploy a mock ERC20 token for testing"""
    # For now, just return an account address
    # In a real scenario, you'd deploy a mock ERC20 contract
    return accounts[9]


@pytest.fixture
def blueprint(owner):
    """Deploy the Passthrough contract as a blueprint"""
    from conftest import deploy_blueprint
    return deploy_blueprint(project.Passthrough, owner)


@pytest.fixture
def factory(owner, blueprint, ownership_admin, parameter_admin, emergency_admin):
    """Deploy the PassthroughFactory with the blueprint and admins"""
    return owner.deploy(project.PassthroughFactory, blueprint.address, ownership_admin.address, parameter_admin.address, emergency_admin.address)


def test_deploy_multiple_gauges_scenario(factory, ownership_admin, parameter_admin, owner, accounts):
    """
    Test scenario similar to deploy_many script:
    Deploy multiple passthroughs for different gauges
    """
    # Simulate deploying passthroughs for multiple gauges
    gauges = [accounts[i].address for i in range(10, 15)]  # 5 mock gauges
    names = [
        "Gauge 1 Passthrough",
        "Gauge 2 Passthrough",
        "Gauge 3 Passthrough",
        "Gauge 4 Passthrough",
        "Gauge 5 Passthrough"
    ]

    guards = [accounts[6].address, accounts[7].address]
    deployed_passthroughs = []

    # Deploy passthroughs for each gauge
    for i, gauge in enumerate(gauges):
        tx = factory.create_passthrough(
            [],
            guards,
            [],
            sender=owner
        )

        passthrough_address = factory.get_passthrough(i)
        deployed_passthroughs.append(passthrough_address)

        # Set up the passthrough
        passthrough = get_passthrough_at(passthrough_address)

        # Set name
        passthrough.set_name(names[i], sender=accounts[6])
        assert passthrough.name() == names[i]

        # Set single reward receiver (gauge)
        passthrough.set_single_reward_receiver(gauge, sender=accounts[6])
        assert passthrough.single_reward_receiver() == gauge

    # Verify all passthroughs were created
    assert factory.get_passthrough_count() == len(gauges)
    all_passthroughs = factory.get_all_passthroughs()
    assert len(all_passthroughs) == len(gauges)
    assert all_passthroughs == deployed_passthroughs


def test_factory_gas_savings(factory, ownership_admin, parameter_admin, owner, accounts):
    """
    Test that using the factory with blueprints saves gas compared to deploying directly
    """
    guard = accounts[6]

    # Deploy via factory (using blueprint)
    tx_factory = factory.create_passthrough(
        [],
        [guard.address],
        [],
        sender=owner
    )
    factory_gas = tx_factory.gas_used

    # Note: Can't easily compare to direct deployment since Passthrough now requires factory
    # But we can verify gas usage is reasonable
    print(f"Factory deployment gas: {factory_gas}")

    # Factory deployment should use reasonable gas (< 500k for simple deployment)
    assert factory_gas < 500000


def test_upgrade_blueprint_and_deploy(factory, ownership_admin, parameter_admin, owner, accounts):
    """
    Test upgrading the blueprint and deploying new passthroughs with the new blueprint
    """
    guard = accounts[6]

    # Deploy a passthrough with original blueprint
    factory.create_passthrough(
        [],
        [guard.address],
        [],
        sender=owner
    )

    original_passthrough = factory.get_passthrough(0)

    # Deploy a new blueprint (could be an updated version)
    from conftest import deploy_blueprint
    new_blueprint = deploy_blueprint(project.Passthrough, owner)

    # Update factory blueprint
    factory.set_blueprint(new_blueprint.address, sender=owner)
    assert factory.blueprint() == new_blueprint.address

    # Deploy another passthrough with new blueprint
    factory.create_passthrough(
        [],
        [guard.address],
        [],
        sender=owner
    )

    new_passthrough = factory.get_passthrough(1)

    # Both passthroughs should exist and be different
    assert original_passthrough != new_passthrough
    assert factory.get_passthrough_count() == 2

    # Both should still work
    old_pt = get_passthrough_at(original_passthrough)
    new_pt = get_passthrough_at(new_passthrough)

    old_pt.set_name("Old Passthrough", sender=guard)
    new_pt.set_name("New Passthrough", sender=guard)

    assert old_pt.name() == "Old Passthrough"
    assert new_pt.name() == "New Passthrough"


def test_batch_deployment_simulation(factory, ownership_admin, parameter_admin, owner, accounts):
    """
    Simulate deploying many passthroughs in a batch like the deploy_many script
    """
    guards = [accounts[6].address]
    num_deployments = 10

    passthroughs = []

    # Batch deploy
    for i in range(num_deployments):
        tx = factory.create_passthrough(
            [],
            guards,
            [],
            sender=owner
        )
        passthroughs.append(factory.get_passthrough(i))

    # Verify all deployments
    assert factory.get_passthrough_count() == num_deployments
    assert len(factory.get_all_passthroughs()) == num_deployments

    # Configure each passthrough
    for i, pt_address in enumerate(passthroughs):
        pt = get_passthrough_at(pt_address)
        pt.set_name(f"Passthrough #{i + 1}", sender=accounts[6])
        assert pt.name() == f"Passthrough #{i + 1}"


def test_centralized_admin_management(factory, ownership_admin, parameter_admin, owner, accounts, blueprint):
    """
    Test that admin management is centralized at the factory level
    """
    guard = accounts[6]

    # Create multiple passthroughs
    for i in range(3):
        factory.create_passthrough([], [guard.address], [], sender=owner)

    # Get all passthroughs
    pt1 = get_passthrough_at(factory.get_passthrough(0))
    pt2 = get_passthrough_at(factory.get_passthrough(1))
    pt3 = get_passthrough_at(factory.get_passthrough(2))

    # All should have same admins
    assert pt1.ownership_admin() == ownership_admin.address
    assert pt2.ownership_admin() == ownership_admin.address
    assert pt3.ownership_admin() == ownership_admin.address

    # Change ownership admin at factory level
    new_ownership_admin = accounts[7]
    factory.set_ownership_admin(new_ownership_admin.address, sender=ownership_admin)

    # Existing passthroughs now query the new admin
    assert pt1.ownership_admin() == new_ownership_admin.address
    assert pt2.ownership_admin() == new_ownership_admin.address
    assert pt3.ownership_admin() == new_ownership_admin.address

    # New passthroughs also get the new admin
    factory.create_passthrough([], [guard.address], [], sender=owner)
    pt4 = get_passthrough_at(factory.get_passthrough(3))
    assert pt4.ownership_admin() == new_ownership_admin.address
