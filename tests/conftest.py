import pytest
from unittest.mock import patch


@pytest.fixture(scope="session", autouse=True)
def mock_etherscan():
    """Mock Etherscan to avoid API calls during tests"""
    with patch('ape_etherscan.explorer.Etherscan.supports_chain', return_value=False):
        with patch('ape_etherscan.client.get_supported_chains', return_value=[]):
            yield


@pytest.fixture(scope="session")
def accounts():
    """Provide test accounts"""
    from ape import accounts as ape_accounts
    return ape_accounts.test_accounts


def get_passthrough_at(address):
    """
    Helper to get a Passthrough contract instance at an address.
    This works around Ape's contract verification issues in test environment.
    """
    from ape import project, chain

    # Use chain's contract cache to create instance with known contract type
    contract_type = project.Passthrough.contract_type
    return chain.contracts.instance_at(address, contract_type=contract_type)


def deploy_blueprint(contract_container, sender):
    """
    Deploy a contract as a Vyper blueprint.

    A blueprint is a special contract deployment that stores the contract's
    runtime bytecode in a way that can be used with create_from_blueprint.

    Vyper blueprint format (EIP-5202):
    - 0xFE: EIP-5202 identifier
    - 0x71: Vyper version marker
    - 0x00: Reserved byte
    - Then the actual runtime bytecode
    """
    from eth_utils import to_checksum_address

    # Get the deployment bytecode (initcode) from the contract
    contract_type = contract_container.contract_type
    web3 = sender.provider.web3

    # Get deployment bytecode (this is what gets deployed to create new instances)
    init_code = contract_type.deployment_bytecode.bytecode
    if not init_code.startswith('0x'):
        init_code = '0x' + init_code

    # Convert to bytes
    init_code_bytes = bytes.fromhex(init_code[2:])

    # Build blueprint: EIP-5202 preamble (0xFE7100) + deployment bytecode
    # code_offset=3 means skip first 3 bytes when using create_from_blueprint
    preamble = bytes.fromhex('FE7100')  # EIP-5202 marker + Vyper marker + reserved
    blueprint_code = preamble + init_code_bytes

    # Create deployment code that returns the blueprint code
    # PUSH<n> <blueprint_code> PUSH1 0 MSTORE PUSH1 <size> PUSH1 0 RETURN
    blueprint_size = len(blueprint_code)

    # Simple deployment bytecode that returns our blueprint code
    # This uses a different approach: we'll build initcode that returns blueprint_code
    deploy_code = (
        '0x61' + hex(blueprint_size)[2:].zfill(4) +  # PUSH2 <size>
        '80' +                                         # DUP1
        '600b' +                                       # PUSH1 0x0b (offset where blueprint starts)
        '6000' +                                       # PUSH1 0x00 (dest memory)
        '39' +                                         # CODECOPY
        '6000' +                                       # PUSH1 0x00 (memory offset)
        'f3' +                                         # RETURN
        blueprint_code.hex()
    )

    # Deploy the blueprint
    nonce = web3.eth.get_transaction_count(sender.address)
    tx_dict = {
        'from': sender.address,
        'data': deploy_code,
        'value': 0,
        'gas': 3000000,
        'nonce': nonce,
        'gasPrice': web3.eth.gas_price,
    }

    tx_hash = web3.eth.send_transaction(tx_dict)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    # Get blueprint address
    blueprint_address = receipt.get('contractAddress') or receipt.get('contract_address')
    if not blueprint_address:
        from eth_utils import keccak
        import rlp
        rlp_encoded = rlp.encode([bytes.fromhex(sender.address[2:]), nonce])
        blueprint_address = '0x' + keccak(rlp_encoded)[-20:].hex()

    # Return a mock contract object with the address
    class BlueprintMock:
        def __init__(self, address):
            self.address = to_checksum_address(address)

        def __str__(self):
            return self.address

    return BlueprintMock(blueprint_address)
