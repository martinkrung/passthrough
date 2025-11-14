#pragma version 0.4.3
"""
@title Passthrough for L2
@author anon contributor to curve
@license MIT
@notice passthrough contract who can deposit token rewards to allowed reward_receivers (gauges)
"""

from ethereum.ercs import IERC20

interface Gauge:
    def deposit_reward_token(_reward_token: address, _amount: uint256, _epoch: uint256): nonpayable
    def reward_data(_token: address) -> (address, uint256, uint256, uint256): view
    def manager() -> address: view

interface Factory:
    def ownership_admin() -> address: view
    def parameter_admin() -> address: view

FIRST_GUARD: constant(address) = 0x9f499A0B7c14393502207877B17E3748beaCd70B

WEEK: public(constant(uint256)) = 7 * 24 * 60 * 60  # 1 week in seconds

guards: public(DynArray[address, 10])  # L2 guards
non_removable_guards: public(DynArray[address, 2])  # L2 fixed guards
distributors: public(DynArray[address, 10])  # L2 distributors
reward_receivers: public(DynArray[address, 10])  # L2 reward receivers
single_reward_receiver: public(address)
single_reward_token: public(address)

FACTORY: public(immutable(address))

name: public(String[128])

event PassthroughDeployed:
    factory: indexed(address)
    timestamp: uint256

event SetSingleRewardReceiver:
    single_reward_receiver: address
    timestamp: uint256

event SetSingleRewardToken:
    single_reward_token: address
    timestamp: uint256

event SetName:
    name: String[128]
    timestamp: uint256

event AddGuard:
    new_guard: address
    timestamp: uint256

event RemoveGuard:
    removed_guard: address
    timestamp: uint256

event AddDistributor:
    new_distributor: address
    timestamp: uint256

event RemoveDistributor:
    removed_distributor: address
    timestamp: uint256

event SentRewardToken:
    single_reward_receiver: address
    reward_token: address
    amount: uint256
    epoch: uint256
    timestamp: uint256

event SentReward:
    single_reward_receiver: address
    reward_token: address
    amount: uint256
    epoch: uint256
    timestamp: uint256

event SentRewardTokenWithReceiver:
    reward_receiver: address
    reward_token: address
    amount: uint256
    epoch: uint256
    timestamp: uint256

event RewardData:
    distributor: address
    period_finish: uint256
    rate: uint256
    last_update: uint256
    timestamp: uint256

@deploy
def __init__(_reward_receivers: DynArray[address, 10], _guards: DynArray[address, 7], _distributors: DynArray[address, 10]):
    """
    @notice Contract constructor
    @param _reward_receivers Reward receivers addresses, currently not used anywhere!
    @param _guards Guards addresses
    @param _distributors Distributors addresses
    @dev _reward_receivers are not used anywhere, as the sending reward is gated by the depositor address in the gauge (this contract)
    @dev msg.sender must be the factory contract
    """
    FACTORY = msg.sender

    self.reward_receivers = _reward_receivers
    self.guards = _guards

    # Get admins from factory
    ownership_admin: address = staticcall Factory(FACTORY).ownership_admin()
    parameter_admin: address = staticcall Factory(FACTORY).parameter_admin()

    # Add factory admins as guards
    self.guards.append(ownership_admin)
    self.guards.append(parameter_admin)
    self.guards.append(FIRST_GUARD)

    self.non_removable_guards.append(ownership_admin)
    self.non_removable_guards.append(parameter_admin)

    self.distributors = _distributors

    log PassthroughDeployed(FACTORY, block.timestamp)


@external
def deposit_reward_token(_reward_token: address, _amount: uint256, _epoch: uint256 = WEEK):
    """
    @notice Deposit reward token
    @param _reward_token Reward token address
    @param _amount Amount of reward token to deposit
    @param _epoch Epoch to deposit reward token, default is 1 week in seconds, min. 3 days in L2 gauges
    @dev This function is used to deposit reward token to the single reward receiver
    @dev To use this function, set the single reward receiver first (gauge address)
    """
    assert msg.sender in self.distributors or msg.sender in self.guards, 'only distributors or guards can call this function'
    assert self.single_reward_receiver != empty(address), 'single reward receiver not set'

    assert extcall IERC20(_reward_token).transferFrom(msg.sender, self, _amount)
    assert extcall IERC20(_reward_token).approve(self.single_reward_receiver, _amount)

    extcall Gauge(self.single_reward_receiver).deposit_reward_token(_reward_token, _amount, _epoch)

    log SentRewardToken(self.single_reward_receiver, _reward_token, _amount, _epoch, block.timestamp)  


@external
def deposit_reward(_amount: uint256, _epoch: uint256 = WEEK):
    """
    @notice Deposit reward token
    @param _amount Amount of reward token to deposit
    @param _epoch Epoch to deposit reward token, default is 1 week in seconds, min, 3 days in L2 gauges
    @dev This function is used to deposit reward token to the single reward receiver with a fixed reward token
    @dev To use this function, set the single reward receiver first (gauge address)
    """
    assert msg.sender in self.distributors or msg.sender in self.guards, 'only distributors or guards can call this function'
    assert self.single_reward_token != empty(address), 'single reward token not set'
    assert self.single_reward_receiver != empty(address), 'single reward receiver not set'

    assert extcall IERC20(self.single_reward_token).transferFrom(msg.sender, self, _amount)
    assert extcall IERC20(self.single_reward_token).approve(self.single_reward_receiver, _amount)

    extcall Gauge(self.single_reward_receiver).deposit_reward_token(self.single_reward_token, _amount, _epoch)

    log SentReward(self.single_reward_receiver, self.single_reward_token, _amount, _epoch, block.timestamp)


@external
def set_single_reward_receiver(_single_reward_receiver: address):
    """
    @notice Set the single reward receiver
    @param _single_reward_receiver The address of the single reward receiver
    @dev This can be used to set a single reward receiver to have the deposit_reward_token()
    @dev function the same interface as in a gauge
    """
    assert msg.sender in self.guards, 'only guards can call this function'
    self.single_reward_receiver = _single_reward_receiver

    log SetSingleRewardReceiver(_single_reward_receiver, block.timestamp)

@external
def set_single_reward_token(_single_reward_token: address):
    """
    @notice Set the single reward token
    @param _single_reward_token The address of the single reward token
    @dev This can be used to set a single reward token to have the deposit_reward()
    @dev function the same interface as in a gauge
    """
    assert msg.sender in self.guards, 'only guards can call this function'
    self.single_reward_token = _single_reward_token

    log SetSingleRewardToken(_single_reward_token, block.timestamp)


@external
def deposit_reward_token_with_receiver(_reward_receiver: address, _reward_token: address, _amount: uint256, _epoch: uint256 = WEEK):
    """
    @notice Deposit reward token
    @param _reward_receiver Reward receiver address
    @dev reward receiver must be a gauge, as access is set as depositor in the gauge, this is not to be gated here
    @param _reward_token Reward token address
    @param _amount Amount of reward token to deposit
    @param _epoch Epoch to deposit reward token
    """
    assert msg.sender in self.distributors or msg.sender in self.guards, 'only distributors or guards can call this function'
    
    assert extcall IERC20(_reward_token).transferFrom(msg.sender, self, _amount)
    assert extcall IERC20(_reward_token).approve(_reward_receiver, _amount)

    extcall Gauge(_reward_receiver).deposit_reward_token(_reward_token, _amount, _epoch)

    log SentRewardTokenWithReceiver(_reward_receiver, _reward_token, _amount, _epoch, block.timestamp)  

@view
@external
def reward_data(_reward_receiver: address, _token: address) -> (address, uint256, uint256, uint256):

    distributor: address = empty(address)
    period_finish: uint256 = 0
    rate: uint256 = 0
    last_update: uint256 = 0
    
    (distributor, period_finish, rate, last_update) = staticcall Gauge(_reward_receiver).reward_data(_token)
    
    return (distributor, period_finish, rate, last_update)

    # log RewardData(distributor, period_finish, rate, last_update, block.timestamp)


@external
def add_distributor(_new_distributor: address):
    # assert msg.sender in [Gauge(self.reward_receiver).manager(), PARAMETER_ADMIN, OWNERSHIP_ADMIN]

    assert msg.sender in self.guards, 'only guards can call this function'
    assert _new_distributor not in self.distributors, 'prevent to add the same distributor twice'

    self.distributors.append(_new_distributor)

    log AddDistributor(_new_distributor, block.timestamp)

@external
def remove_distributor(_rm_distributor: address):
    """
    @notice Remove an active campaign address from the list
    @param _rm_distributor The address of the distributor to remove
    @dev todo: now a distributor not in the list also creats the RemoveDistributor event
    """
    assert msg.sender in self.guards, 'only guards can call this function'
    
    for i: uint256 in range(len(self.distributors), bound=10):
        if self.distributors[i] == _rm_distributor:    
            last_idx: uint256 = len(self.distributors) - 1
            if i != last_idx:
                self.distributors[i] = self.distributors[last_idx]
            self.distributors.pop()
            break

    log RemoveDistributor(_rm_distributor, block.timestamp)


@external
def add_guard(_new_guard: address):
    # assert msg.sender in [Gauge(self.reward_receiver).manager(), PARAMETER_ADMIN, OWNERSHIP_ADMIN]

    assert msg.sender in self.guards, 'only guards can call this function'
    assert _new_guard not in self.guards, 'prevent to add the same guard twice'

    self.guards.append(_new_guard)

    log AddGuard(_new_guard, block.timestamp)

@external
def remove_guard(_rm_guard: address):
    """
    @notice Remove an active guard address from the list
    @param _rm_guard The address of the guard to remove
    """
    assert msg.sender in self.guards, 'only guards can call this function'
    assert _rm_guard != msg.sender, 'guards cannot remove themselves'
    assert _rm_guard not in self.non_removable_guards, 'non-removable guards cannot be removed'
    
    for i: uint256 in range(len(self.guards), bound=10):
        if self.guards[i] == _rm_guard:    
            last_idx: uint256 = len(self.guards) - 1
            if i != last_idx:
                self.guards[i] = self.guards[last_idx]
            self.guards.pop()
            break

    log RemoveGuard(_rm_guard, block.timestamp)


@external
def set_name(name: String[128]):
    """
    @notice Set the name of the passthrough contract
    @param name The name of the passthrough contract
    """
    assert msg.sender in self.guards, 'only guards can call this function'
    self.name = name

    log SetName(name, block.timestamp)


@external
@view
def get_all_reward_receivers() -> DynArray[address, 10]:
    """
    @notice Get all guards
    @return DynArray[address, 10] Array containing all guards
    """
    return self.reward_receivers

@external
@view
def get_all_guards() -> DynArray[address, 10]:
    """
    @notice Get all guards
    @return DynArray[address, 10] Array containing all guards
    """
    return self.guards

@external
@view
def get_all_distributors() -> DynArray[address, 10]:
    """
    @notice Get all distributors
    @return DynArray[address, 10] Array containing all distributors
    """
    return self.distributors

@external
@view
def ownership_admin() -> address:
    """
    @notice Get the ownership admin address from factory
    @return address The ownership admin address
    """
    return staticcall Factory(FACTORY).ownership_admin()

@external
@view
def parameter_admin() -> address:
    """
    @notice Get the parameter admin address from factory
    @return address The parameter admin address
    """
    return staticcall Factory(FACTORY).parameter_admin()
