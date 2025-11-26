#pragma version 0.4.3
"""
@title PassthroughFactory
@author anon contributor to curve
@license MIT
@notice Factory contract for deploying Passthrough contracts using the Blueprint pattern
"""

event PassthroughCreated:
    passthrough: indexed(address)
    deployer: indexed(address)
    timestamp: uint256

event BlueprintSet:
    blueprint: indexed(address)
    timestamp: uint256

event OwnershipAdminSet:
    ownership_admin: indexed(address)
    timestamp: uint256

event ParameterAdminSet:
    parameter_admin: indexed(address)
    timestamp: uint256

event EmergencyAdminSet:
    emergency_admin: indexed(address)
    timestamp: uint256

blueprint: public(address)
owner: public(address)
ownership_admin: public(address)
parameter_admin: public(address)
emergency_admin: public(address)
passthroughs: public(DynArray[address, 1000])

@deploy
def __init__(_blueprint: address, _ownership_admin: address, _parameter_admin: address, _emergency_admin: address):
    """
    @notice Contract constructor
    @param _blueprint The blueprint contract address for Passthrough
    @param _ownership_admin The ownership admin address for all passthroughs
    @param _parameter_admin The parameter admin address for all passthroughs
    @param _emergency_admin The emergency admin address for all passthroughs
    """
    self.blueprint = _blueprint
    self.owner = msg.sender
    self.ownership_admin = _ownership_admin
    self.parameter_admin = _parameter_admin
    self.emergency_admin = _emergency_admin
    log BlueprintSet(_blueprint, block.timestamp)
    log OwnershipAdminSet(_ownership_admin, block.timestamp)
    log ParameterAdminSet(_parameter_admin, block.timestamp)
    log EmergencyAdminSet(_emergency_admin, block.timestamp)

@external
def create_passthrough(
    _reward_receivers: DynArray[address, 10],
    _guards: DynArray[address, 7],
    _distributors: DynArray[address, 10]
) -> address:
    """
    @notice Deploy a new Passthrough contract from the blueprint
    @param _reward_receivers Reward receivers addresses
    @param _guards Guards addresses
    @param _distributors Distributors addresses
    @return The address of the newly deployed Passthrough contract
    """
    passthrough: address = create_from_blueprint(
        self.blueprint,
        _reward_receivers,
        _guards,
        _distributors,
        code_offset=3
    )

    self.passthroughs.append(passthrough)

    log PassthroughCreated(passthrough, msg.sender, block.timestamp)

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
def set_ownership_admin(_new_ownership_admin: address):
    """
    @notice Set a new ownership admin address
    @param _new_ownership_admin The new ownership admin address
    @dev Only the current ownership admin can set a new one
    """
    assert msg.sender == self.ownership_admin, "only ownership admin can set new ownership admin"
    assert _new_ownership_admin != empty(address), "new ownership admin cannot be zero address"
    self.ownership_admin = _new_ownership_admin
    log OwnershipAdminSet(_new_ownership_admin, block.timestamp)

@external
def set_parameter_admin(_new_parameter_admin: address):
    """
    @notice Set a new parameter admin address
    @param _new_parameter_admin The new parameter admin address
    @dev Only the ownership admin can set a new parameter admin
    """
    assert msg.sender == self.ownership_admin, "only ownership admin can set new parameter admin"
    assert _new_parameter_admin != empty(address), "new parameter admin cannot be zero address"
    self.parameter_admin = _new_parameter_admin
    log ParameterAdminSet(_new_parameter_admin, block.timestamp)

@external
def set_emergency_admin(_new_emergency_admin: address):
    """
    @notice Set a new emergency admin address
    @param _new_emergency_admin The new emergency admin address
    @dev Only the ownership admin can set a new emergency admin
    """
    assert msg.sender == self.ownership_admin, "only ownership admin can set new emergency admin"
    assert _new_emergency_admin != empty(address), "new emergency admin cannot be zero address"
    self.emergency_admin = _new_emergency_admin
    log EmergencyAdminSet(_new_emergency_admin, block.timestamp)

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
