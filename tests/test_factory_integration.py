import pytest
import ape
from ape import project, accounts, Contract


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
    return project.Passthrough.deploy_as_blueprint(sender=owner)


@pytest.fixture
def factory(owner, blueprint):
    """Deploy the PassthroughFactory with the blueprint"""
    return owner.deploy(project.PassthroughFactory, blueprint.address)


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
            ownership_admin.address,
            parameter_admin.address,
            [],
            guards,
            [],
            sender=owner
        )

        passthrough_address = factory.get_passthrough(i)
        deployed_passthroughs.append(passthrough_address)

        # Set up the passthrough
        passthrough = Contract(passthrough_address, abi=project.Passthrough.contract_type.abi)

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
        ownership_admin.address,
        parameter_admin.address,
        [],
        [guard.address],
        [],
        sender=owner
    )
    factory_gas = tx_factory.gas_used

    # Deploy directly
    tx_direct = owner.deploy(
        project.Passthrough,
        ownership_admin.address,
        parameter_admin.address,
        [],
        [guard.address],
        []
    )
    direct_gas = tx_direct.gas_used

    # Factory deployment should use less gas
    # Blueprint pattern typically saves 40-60% of deployment gas
    print(f"Factory deployment gas: {factory_gas}")
    print(f"Direct deployment gas: {direct_gas}")
    print(f"Gas saved: {direct_gas - factory_gas} ({((direct_gas - factory_gas) / direct_gas * 100):.2f}%)")

    # Factory should use significantly less gas
    assert factory_gas < direct_gas


def test_upgrade_blueprint_and_deploy(factory, ownership_admin, parameter_admin, owner, accounts):
    """
    Test upgrading the blueprint and deploying new passthroughs with the new blueprint
    """
    guard = accounts[6]

    # Deploy a passthrough with original blueprint
    factory.create_passthrough(
        ownership_admin.address,
        parameter_admin.address,
        [],
        [guard.address],
        [],
        sender=owner
    )

    original_passthrough = factory.get_passthrough(0)

    # Deploy a new blueprint (could be an updated version)
    new_blueprint = project.Passthrough.deploy_as_blueprint(sender=owner)

    # Update factory blueprint
    factory.set_blueprint(new_blueprint.address, sender=owner)
    assert factory.blueprint() == new_blueprint.address

    # Deploy another passthrough with new blueprint
    factory.create_passthrough(
        ownership_admin.address,
        parameter_admin.address,
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
    old_pt = Contract(original_passthrough, abi=project.Passthrough.contract_type.abi)
    new_pt = Contract(new_passthrough, abi=project.Passthrough.contract_type.abi)

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
            ownership_admin.address,
            parameter_admin.address,
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
        pt = Contract(pt_address, abi=project.Passthrough.contract_type.abi)
        pt.set_name(f"Passthrough #{i + 1}", sender=accounts[6])
        assert pt.name() == f"Passthrough #{i + 1}"
