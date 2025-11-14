#pragma version ^0.4.3
"""
@title PassthroughFactory
@author anon contributor to curve
@license MIT
@notice Factory contract for deploying Passthrough contracts using the Blueprint pattern
"""

event PassthroughCreated:
    passthrough: indexed(address)
    ownership_admin: indexed(address)
    parameter_admin: indexed(address)
    deployer: indexed(address)
    timestamp: uint256

event BlueprintSet:
    blueprint: indexed(address)
    timestamp: uint256

blueprint: public(address)
owner: public(address)
passthroughs: public(DynArray[address, 1000])

@deploy
def __init__(_blueprint: address):
    """
    @notice Contract constructor
    @param _blueprint The blueprint contract address for Passthrough
    """
    self.blueprint = _blueprint
    self.owner = msg.sender
    log BlueprintSet(_blueprint, block.timestamp)

@external
def create_passthrough(
    _ownership_admin: address,
    _parameter_admin: address,
    _reward_receivers: DynArray[address, 10],
    _guards: DynArray[address, 7],
    _distributors: DynArray[address, 10]
) -> address:
    """
    @notice Deploy a new Passthrough contract from the blueprint
    @param _ownership_admin Ownership admin address
    @param _parameter_admin Parameter admin address
    @param _reward_receivers Reward receivers addresses
    @param _guards Guards addresses
    @param _distributors Distributors addresses
    @return The address of the newly deployed Passthrough contract
    """
    passthrough: address = create_from_blueprint(
        self.blueprint,
        _ownership_admin,
        _parameter_admin,
        _reward_receivers,
        _guards,
        _distributors,
        code_offset=3
    )

    self.passthroughs.append(passthrough)

    log PassthroughCreated(passthrough, _ownership_admin, _parameter_admin, msg.sender, block.timestamp)

    return passthrough

@external
def set_blueprint(_new_blueprint: address):
    """
    @notice Set a new blueprint address
    @param _new_blueprint The new blueprint contract address
    @dev Only the owner can set a new blueprint
    """
    assert msg.sender == self.owner, "only owner can set blueprint"
    self.blueprint = _new_blueprint
    log BlueprintSet(_new_blueprint, block.timestamp)

@external
def transfer_ownership(_new_owner: address):
    """
    @notice Transfer ownership to a new owner
    @param _new_owner The new owner address
    @dev Only the current owner can transfer ownership
    """
    assert msg.sender == self.owner, "only owner can transfer ownership"
    assert _new_owner != empty(address), "new owner cannot be zero address"
    self.owner = _new_owner

@external
@view
def get_passthrough_count() -> uint256:
    """
    @notice Get the total number of deployed passthroughs
    @return The count of deployed passthroughs
    """
    return len(self.passthroughs)

@external
@view
def get_passthrough(index: uint256) -> address:
    """
    @notice Get a passthrough address by index
    @param index The index in the passthroughs array
    @return The passthrough address
    """
    assert index < len(self.passthroughs), "index out of bounds"
    return self.passthroughs[index]

@external
@view
def get_all_passthroughs() -> DynArray[address, 1000]:
    """
    @notice Get all deployed passthrough addresses
    @return Array of all passthrough addresses
    """
    return self.passthroughs
