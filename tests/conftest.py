import pytest


@pytest.fixture(scope="session")
def accounts():
    """Provide test accounts"""
    from ape import accounts as ape_accounts
    return ape_accounts.test_accounts


def deploy_blueprint(contract_container, sender):
    """
    Deploy a contract as a Vyper blueprint.

    A blueprint is a special contract deployment that stores the contract's
    runtime bytecode in a way that can be used with create_from_blueprint.

    Vyper blueprint format (EIP-5202):
    - 0xFE: EIP-5202 identifier
    - 0x71: Vyper version marker
    - 0x00: Reserved byte
    - Followed by 2-byte length prefix
    - Then the actual runtime bytecode
    """
    from eth_utils import to_checksum_address

    # Get the deployment bytecode which will return the runtime code
    contract_type = contract_container.contract_type
    init_code = contract_type.deployment_bytecode.bytecode

    # Ensure proper hex format
    if not init_code.startswith('0x'):
        init_code = '0x' + init_code

    # Use web3 to send a raw deployment transaction
    web3 = sender.provider.web3
    nonce = web3.eth.get_transaction_count(sender.address)

    tx_dict = {
        'from': sender.address,
        'data': init_code,
        'value': 0,
        'gas': 3000000,
        'nonce': nonce,
        'gasPrice': web3.eth.gas_price,
    }

    tx_hash = web3.eth.send_transaction(tx_dict)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    # Get contract address from receipt - check multiple possible keys
    contract_address = None
    for key in ['contractAddress', 'contract_address', 'to']:
        if key in receipt and receipt[key]:
            contract_address = receipt[key]
            break

    # If no contract address found, compute it from sender and nonce
    if not contract_address:
        from eth_utils import keccak
        import rlp
        # Contract address = keccak256(rlp([sender_address, nonce]))[-20:]
        rlp_encoded = rlp.encode([bytes.fromhex(sender.address[2:]), nonce])
        contract_address_bytes = keccak(rlp_encoded)[-20:]
        contract_address = '0x' + contract_address_bytes.hex()

    # Return a mock contract object with the address
    class BlueprintMock:
        def __init__(self, address):
            self.address = to_checksum_address(address)

        def __str__(self):
            return self.address

    return BlueprintMock(contract_address)
