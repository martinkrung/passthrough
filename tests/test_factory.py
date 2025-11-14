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
def guard(accounts):
    return accounts[3]


@pytest.fixture
def distributor(accounts):
    return accounts[4]


@pytest.fixture
def user(accounts):
    return accounts[5]


@pytest.fixture
def blueprint(owner):
    """Deploy the Passthrough contract as a blueprint"""
    # Deploy as a blueprint using the special blueprint deployment
    return project.Passthrough.deploy_as_blueprint(sender=owner)


@pytest.fixture
def factory(owner, blueprint):
    """Deploy the PassthroughFactory with the blueprint"""
    return owner.deploy(project.PassthroughFactory, blueprint.address)


def test_factory_deployment(factory, blueprint, owner):
    """Test that the factory deploys correctly"""
    assert factory.blueprint() == blueprint.address
    assert factory.owner() == owner.address
    assert factory.get_passthrough_count() == 0


def test_create_passthrough(factory, ownership_admin, parameter_admin, guard, distributor, owner):
    """Test creating a passthrough from the factory"""
    reward_receivers = []
    guards = [guard.address]
    distributors = [distributor.address]

    # Create passthrough
    tx = factory.create_passthrough(
        ownership_admin.address,
        parameter_admin.address,
        reward_receivers,
        guards,
        distributors,
        sender=owner
    )

    # Check event was emitted
    events = list(tx.decode_logs(factory.PassthroughCreated))
    assert len(events) == 1
    event = events[0]
    assert event.ownership_admin == ownership_admin.address
    assert event.parameter_admin == parameter_admin.address
    assert event.deployer == owner.address

    # Check factory state
    assert factory.get_passthrough_count() == 1
    passthrough_address = factory.get_passthrough(0)
    assert passthrough_address == event.passthrough

    # Verify the passthrough contract works
    passthrough = Contract(passthrough_address, abi=project.Passthrough.contract_type.abi)
    assert passthrough.OWNERSHIP_ADMIN() == ownership_admin.address
    assert passthrough.PARAMETER_ADMIN() == parameter_admin.address


def test_multiple_passthroughs(factory, ownership_admin, parameter_admin, guard, distributor, owner, accounts):
    """Test creating multiple passthroughs"""
    num_passthroughs = 3

    for i in range(num_passthroughs):
        factory.create_passthrough(
            ownership_admin.address,
            parameter_admin.address,
            [],
            [guard.address],
            [distributor.address],
            sender=owner
        )

    assert factory.get_passthrough_count() == num_passthroughs

    # Get all passthroughs
    all_passthroughs = factory.get_all_passthroughs()
    assert len(all_passthroughs) == num_passthroughs

    # Verify each passthrough is unique
    assert len(set(all_passthroughs)) == num_passthroughs

    # Verify each can be retrieved by index
    for i in range(num_passthroughs):
        assert factory.get_passthrough(i) == all_passthroughs[i]


def test_passthrough_functionality(factory, ownership_admin, parameter_admin, guard, distributor, owner):
    """Test that created passthroughs have full functionality"""
    # Create passthrough
    tx = factory.create_passthrough(
        ownership_admin.address,
        parameter_admin.address,
        [],
        [guard.address],
        [distributor.address],
        sender=owner
    )

    passthrough_address = factory.get_passthrough(0)
    passthrough = Contract(passthrough_address, abi=project.Passthrough.contract_type.abi)

    # Test that guards can perform admin actions
    test_name = "Test Passthrough"
    passthrough.set_name(test_name, sender=guard)
    assert passthrough.name() == test_name

    # Verify guards list
    all_guards = passthrough.get_all_guards()
    assert guard.address in all_guards
    assert ownership_admin.address in all_guards
    assert parameter_admin.address in all_guards

    # Verify distributors list
    all_distributors = passthrough.get_all_distributors()
    assert distributor.address in all_distributors


def test_set_blueprint(factory, owner, user):
    """Test setting a new blueprint"""
    new_blueprint = project.Passthrough.deploy_as_blueprint(sender=owner)

    # Owner can set new blueprint
    tx = factory.set_blueprint(new_blueprint.address, sender=owner)

    # Check event
    events = list(tx.decode_logs(factory.BlueprintSet))
    assert len(events) == 1
    assert events[0].blueprint == new_blueprint.address

    assert factory.blueprint() == new_blueprint.address

    # Non-owner cannot set blueprint
    with ape.reverts("only owner can set blueprint"):
        factory.set_blueprint(new_blueprint.address, sender=user)


def test_transfer_ownership(factory, owner, user, accounts):
    """Test transferring factory ownership"""
    new_owner = accounts[6]

    # Transfer ownership
    factory.transfer_ownership(new_owner.address, sender=owner)
    assert factory.owner() == new_owner.address

    # Old owner cannot set blueprint anymore
    new_blueprint = project.Passthrough.deploy_as_blueprint(sender=owner)
    with ape.reverts("only owner can set blueprint"):
        factory.set_blueprint(new_blueprint.address, sender=owner)

    # New owner can set blueprint
    factory.set_blueprint(new_blueprint.address, sender=new_owner)
    assert factory.blueprint() == new_blueprint.address


def test_transfer_ownership_access_control(factory, owner, user):
    """Test that only owner can transfer ownership"""
    with ape.reverts("only owner can transfer ownership"):
        factory.transfer_ownership(user.address, sender=user)


def test_transfer_ownership_zero_address(factory, owner):
    """Test that ownership cannot be transferred to zero address"""
    zero_address = "0x0000000000000000000000000000000000000000"
    with ape.reverts("new owner cannot be zero address"):
        factory.transfer_ownership(zero_address, sender=owner)


def test_get_passthrough_out_of_bounds(factory, owner):
    """Test that getting a passthrough with invalid index reverts"""
    with ape.reverts("index out of bounds"):
        factory.get_passthrough(0)

    # Create one passthrough
    factory.create_passthrough(
        owner.address,
        owner.address,
        [],
        [owner.address],
        [],
        sender=owner
    )

    # Index 0 should work
    factory.get_passthrough(0)

    # Index 1 should fail
    with ape.reverts("index out of bounds"):
        factory.get_passthrough(1)


def test_anyone_can_create_passthrough(factory, ownership_admin, parameter_admin, guard, distributor, user):
    """Test that anyone can create a passthrough (permissionless deployment)"""
    # User (non-owner) can create passthrough
    tx = factory.create_passthrough(
        ownership_admin.address,
        parameter_admin.address,
        [],
        [guard.address],
        [distributor.address],
        sender=user
    )

    # Check event shows correct deployer
    events = list(tx.decode_logs(factory.PassthroughCreated))
    assert len(events) == 1
    assert events[0].deployer == user.address

    assert factory.get_passthrough_count() == 1


def test_passthrough_independent_configs(factory, ownership_admin, parameter_admin, guard, distributor, owner, accounts):
    """Test that each passthrough has independent configuration"""
    admin1 = accounts[6]
    admin2 = accounts[7]

    # Create two passthroughs with different admins
    factory.create_passthrough(
        admin1.address,
        parameter_admin.address,
        [],
        [guard.address],
        [],
        sender=owner
    )

    factory.create_passthrough(
        admin2.address,
        parameter_admin.address,
        [],
        [guard.address],
        [],
        sender=owner
    )

    # Get contracts
    passthrough1 = Contract(factory.get_passthrough(0), abi=project.Passthrough.contract_type.abi)
    passthrough2 = Contract(factory.get_passthrough(1), abi=project.Passthrough.contract_type.abi)

    # Verify different ownership
    assert passthrough1.OWNERSHIP_ADMIN() == admin1.address
    assert passthrough2.OWNERSHIP_ADMIN() == admin2.address
    assert passthrough1.OWNERSHIP_ADMIN() != passthrough2.OWNERSHIP_ADMIN()

    # Set different names
    passthrough1.set_name("Passthrough 1", sender=guard)
    passthrough2.set_name("Passthrough 2", sender=guard)

    assert passthrough1.name() == "Passthrough 1"
    assert passthrough2.name() == "Passthrough 2"
