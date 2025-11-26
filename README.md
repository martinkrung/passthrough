## Passthrough Contract

The Passthrough contract is designed to facilitate reward token distribution on L2 networks acting as an intermediary for depositing reward tokens to authorized gauge contracts.

### Overview

This contract serves as a secure passthrough mechanism that allows authorized distributors and guards to deposit reward tokens to designated gauge contracts.


### Key Features

- **Role-Based Access Control**
  - Guards: Can manage distributors and other guards
  - Distributors: Can deposit reward tokens, Guards are also distributors
  - Non-removable Guards: Special guard addresses that cannot be removed (OWNERSHIP_ADMIN and PARAMETER_ADMIN)
  - OWNERSHIP_ADMIN and PARAMETER_ADMIN are set to the curve agent

### Administrative Functions

- `add_guard`: Add new guard addresses
- `remove_guard`: Remove existing guards (except non-removable ones)
- `add_distributor`: Add new distributor addresses
- `remove_distributor`: Remove existing distributors
- `set_single_reward_receiver`: Set the default gauge for reward deposits

### Security Features

1. Guards cannot remove themselves
2. Core admin addresses are set as non-removable guards
3. Role-based access control for all administrative functions

### Usage

1. Deploy the contract with initial reward receivers (currently not used, set to []), guards, and distributors
2. Guards can manage the system by adding/removing other guards and distributors
3. Set a single reward receiver (gauge) for simplified deposits
4. Authorized distributors or guards can deposit reward tokens either to:
   - The pre-configured single receiver
   - Any specified gauge address

### Events

The contract emits events for all significant actions:
- `PassthroughDeployed`
- `SetSingleRewardReceiver`
- `AddGuard`
- `RemoveGuard`
- `AddDistributor`
- `RemoveDistributor`
- `SentRewardToken`
- `SentRewardTokenWithReceiver`

### Limitations

- Maximum of 10 guards
- Maximum of 10 distributors
- Maximum of 10 reward receivers in the initial array (currently not used)
- Reward receivers must be compatible gauge contracts

## PassthroughFactory Contract

The PassthroughFactory contract implements the Blueprint pattern for efficient deployment of multiple Passthrough contracts.

### Overview

The factory uses Vyper's blueprint pattern to deploy Passthrough contracts with significantly reduced gas costs. A blueprint is deployed once, and then multiple instances can be created from it at a fraction of the cost of normal deployments.

### Key Features

- **Gas Efficient Deployments**: Typically saves 40-60% of deployment gas compared to direct deployments
- **Centralized Management**: Track all deployed passthroughs from a single contract
- **Centralized Admin Management**: Factory stores ownership_admin, parameter_admin, and emergency_admin for all passthroughs
- **Upgradeable Blueprint**: Owner can update the blueprint to deploy new versions
- **Permissionless Deployment**: Anyone can deploy a passthrough via the factory
- **Deployment Tracking**: All deployed passthroughs are tracked and indexed

### Factory Functions

#### Deployment
- `create_passthrough`: Deploy a new Passthrough contract from the blueprint
- `get_passthrough_count`: Get the total number of deployed passthroughs
- `get_passthrough`: Get a passthrough address by index
- `get_all_passthroughs`: Get all deployed passthrough addresses

#### Administration (Owner Only)
- `set_blueprint`: Update the blueprint address to deploy new versions
- `set_ownership_admin`: Update the ownership admin for all passthroughs
- `set_parameter_admin`: Update the parameter admin for all passthroughs
- `set_emergency_admin`: Update the emergency admin for all passthroughs
- `transfer_ownership`: Transfer factory ownership to a new address

### Usage Flow

1. **Deploy Blueprint**: Deploy the Passthrough contract as a blueprint
   ```
   make deploy_blueprint_sonic
   ```

2. **Deploy Factory**: Deploy the factory with the blueprint address
   ```
   make deploy_factory_sonic BLUEPRINT=0x...
   ```

3. **Deploy Passthroughs**: Create passthrough instances via the factory
   ```
   # Single deployment
   make deploy_via_factory_sonic FACTORY=0x...

   # Batch deployment
   make deploy_many_factory_sonic FACTORY=0x... REWARD_TOKEN=0x...
   ```

4. **Check Factory Info**: View deployed passthroughs
   ```
   make factory_info_sonic FACTORY=0x...
   ```

### Testing

Run the comprehensive test suite:
```
# Test factory core functionality
make test_factory

# Test factory integration scenarios
make test_factory_integration

# Run all tests
make test_all
```

### Gas Savings

The blueprint pattern provides significant gas savings:
- **First Deployment**: Higher cost (blueprint deployment)
- **Subsequent Deployments**: 40-60% gas savings per deployment
- **Break-even**: Typically after 2-3 deployments

### Events

- `PassthroughCreated`: Emitted when a new passthrough is deployed
- `BlueprintSet`: Emitted when the blueprint is updated

# Changelog

## Version 0.0.4

* recover token (on normal operation, this contract never holds any tokens, so this function is only used in case of emergency)
* add name to for single_reward_token
* Added PassthroughFactory with Blueprint pattern for gas-efficient deployments
* Centralized admin management in factory

## Version 0.0.3

* Now with L2 Emergency Agent
* init changed to agent as fixed 3 list
* named these L2 agents agents here too
* added more helper function to get each reward_data as single value
* added is_period_active() to see if rewards are still running
* reward_data_with_preset() as reward_data if token and gauge is set
* moved event call in remove_distributor, now only should create event if something is removed
