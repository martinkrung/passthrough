import os
import click
import time
from ape import project, Contract
from ape.cli import ConnectedProviderCommand, account_option

from scripts.get_constructor_abi_passthrough import get_constructor_args
from scripts.deploy_manager import setup

OWNERSHIP_ADMIN = os.getenv('OWNERSHIP_ADMIN')
PARAMETER_ADMIN = os.getenv('PARAMETER_ADMIN')


@click.group()
def cli():
    pass


@click.command(cls=ConnectedProviderCommand)
@account_option()
def deploy_blueprint(ecosystem, network, provider, account):
    """Deploy the Passthrough contract as a blueprint"""
    account.set_autosign(True)
    max_fee, blockexplorer = setup(ecosystem, network)

    click.echo("Deploying Passthrough blueprint...")
    blueprint = project.Passthrough.deploy_as_blueprint(
        sender=account,
        max_priority_fee="10 wei",
        max_fee=max_fee,
        gas_limit="600000"
    )

    click.echo(f"Blueprint deployed at: {blueprint.address}")
    click.echo(f"Explorer: {blockexplorer}/address/{blueprint.address}")

    # Log deployment
    chainname = ecosystem.name
    with open(f"deployments/deploy_blueprint_{chainname}.log", "a+") as f:
        f.write(f"Passthrough Blueprint: {blueprint.address}\n")
        f.write(f"Link: {blockexplorer}/address/{blueprint.address}\n")
        f.write("-" * 80 + "\n\n")

    return blueprint.address


cli.add_command(deploy_blueprint)


@click.command(cls=ConnectedProviderCommand)
@account_option()
@click.option('--blueprint', required=True, help='Blueprint contract address')
def deploy_factory(ecosystem, network, provider, account, blueprint):
    """Deploy the PassthroughFactory with a blueprint address"""
    account.set_autosign(True)
    max_fee, blockexplorer = setup(ecosystem, network)

    click.echo(f"Deploying PassthroughFactory with blueprint: {blueprint}")
    factory = account.deploy(
        project.PassthroughFactory,
        blueprint,
        max_priority_fee="10 wei",
        max_fee=max_fee,
        gas_limit="400000"
    )

    click.echo(f"Factory deployed at: {factory.address}")
    click.echo(f"Explorer: {blockexplorer}/address/{factory.address}")

    # Log deployment
    chainname = ecosystem.name
    with open(f"deployments/deploy_factory_{chainname}.log", "a+") as f:
        f.write(f"PassthroughFactory: {factory.address}\n")
        f.write(f"Blueprint: {blueprint}\n")
        f.write(f"Owner: {account.address}\n")
        f.write(f"Link: {blockexplorer}/address/{factory.address}\n")
        f.write("-" * 80 + "\n\n")

    return factory.address


cli.add_command(deploy_factory)


@click.command(cls=ConnectedProviderCommand)
@account_option()
@click.option('--factory', required=True, help='Factory contract address')
def deploy_passthrough_via_factory(ecosystem, network, provider, account, factory):
    """Deploy a single Passthrough using the factory"""
    account.set_autosign(True)
    max_fee, blockexplorer = setup(ecosystem, network)

    factory_contract = Contract(factory)

    reward_receivers = []
    guards = ["0x84bC1fC6204b959470BF8A00d871ff8988a3914A"]
    distributors = []

    click.echo(f"Creating Passthrough via factory at {factory}")
    tx = factory_contract.create_passthrough(
        OWNERSHIP_ADMIN,
        PARAMETER_ADMIN,
        reward_receivers,
        guards,
        distributors,
        sender=account,
        max_priority_fee="10 wei",
        max_fee=max_fee,
        gas_limit="400000"
    )

    # Get the newly created passthrough address from events
    events = list(tx.decode_logs(factory_contract.PassthroughCreated))
    if events:
        passthrough_address = events[0].passthrough
        click.echo(f"Passthrough created at: {passthrough_address}")
        click.echo(f"Explorer: {blockexplorer}/address/{passthrough_address}")

        # Log deployment
        chainname = ecosystem.name
        with open(f"deployments/deploy_via_factory_{chainname}.log", "a+") as f:
            f.write(f"Passthrough: {passthrough_address}\n")
            f.write(f"Factory: {factory}\n")
            f.write(f"Ownership Admin: {OWNERSHIP_ADMIN}\n")
            f.write(f"Parameter Admin: {PARAMETER_ADMIN}\n")
            f.write(f"Link: {blockexplorer}/address/{passthrough_address}\n")
            f.write("-" * 80 + "\n\n")

        return passthrough_address
    else:
        click.echo("Failed to create passthrough - no event emitted")


cli.add_command(deploy_passthrough_via_factory)


@click.command(cls=ConnectedProviderCommand)
@account_option()
@click.option('--factory', required=True, help='Factory contract address')
@click.option('--reward-token', required=True, help='Reward token address')
def deploy_many_via_factory(ecosystem, network, provider, account, factory, reward_token):
    """Deploy multiple Passthroughs using the factory (similar to deploy_many)"""
    account.set_autosign(True)
    max_fee, blockexplorer = setup(ecosystem, network)

    factory_contract = Contract(factory)
    guards = ["0x84bC1fC6204b959470BF8A00d871ff8988a3914A", "0xf7Bd34Dd44B92fB2f9C3D2e31aAAd06570a853A6"]
    chainname = ecosystem.name

    # Load gauge list based on network (same as deploy_manager.py)
    gauges, names = get_gauges_for_network(chainname)

    sleep_time = 2

    with open("contracts/abi/ChildLiquidityGauge.json", "r") as f:
        contract_abi = f.read()

    for i, gauge in enumerate(gauges):
        click.echo(f"Deploying {names[i]}")

        # Create passthrough via factory
        tx = factory_contract.create_passthrough(
            OWNERSHIP_ADMIN,
            PARAMETER_ADMIN,
            [],
            guards,
            [],
            sender=account,
            max_priority_fee="10 wei",
            max_fee=max_fee,
            gas_limit="400000"
        )

        # Get passthrough address
        events = list(tx.decode_logs(factory_contract.PassthroughCreated))
        passthrough_address = events[0].passthrough if events else None

        if not passthrough_address:
            click.echo(f"Failed to create passthrough for {names[i]}")
            continue

        passthrough = Contract(passthrough_address, abi=project.Passthrough.contract_type.abi)

        time.sleep(sleep_time)

        # Configure passthrough
        passthrough.set_name(names[i], sender=account)
        time.sleep(sleep_time)

        passthrough.set_single_reward_receiver(gauge, sender=account)
        time.sleep(sleep_time)

        passthrough.set_single_reward_token(reward_token, sender=account)

        # Get gauge manager
        gauge_contract = Contract(gauge, abi=contract_abi)
        manager = gauge_contract.manager()

        # Log deployment
        with open(f"deployments/deploy_factory_many_{chainname}.log", "a+") as f:
            f.write(f"Passthrough Contract: {passthrough_address}\n")
            f.write(f"Name: {names[i]}\n")
            f.write(f"Reward Receiver/Gauge: {gauge}\n")
            f.write(f"Reward Token: {reward_token}\n")
            f.write(f"Gauge Manager: {manager}\n")
            f.write(f"Link: {blockexplorer}/address/{passthrough_address}\n")
            f.write("-" * 20 + "\n")
            f.write(f"Done with {names[i]} Passthrough\n")
            f.write("-" * 80 + "\n\n")

        time.sleep(sleep_time)

    click.echo("All passthroughs deployed successfully!")


cli.add_command(deploy_many_via_factory)


def get_gauges_for_network(chainname):
    """Get gauges and names for a specific network"""
    if chainname == 'optimism':
        # Load from env
        gauges = [os.getenv('GAUGE_SCRVUSD')]
        names = ["crvUSD/scrvUSD"]
    elif chainname == 'taiko':
        gauges = [os.getenv('GAUGE_CRVUSD_USDC')]
        names = ["crvUSD/USDC"]
    elif chainname == 'sonic':
        GAUGE_LEND_WS_LONG = os.getenv('GAUGE_LEND_WS_LONG')
        gauges = [GAUGE_LEND_WS_LONG]
        names = ["LLama Lend wraped sonic (wS)"]
    else:
        gauges = []
        names = []

    return gauges, names


@click.command(cls=ConnectedProviderCommand)
@account_option()
@click.option('--factory', required=True, help='Factory contract address')
def factory_info(ecosystem, network, provider, account, factory):
    """Get info about the factory and deployed passthroughs"""
    factory_contract = Contract(factory)

    click.echo(f"Factory: {factory}")
    click.echo(f"Blueprint: {factory_contract.blueprint()}")
    click.echo(f"Owner: {factory_contract.owner()}")
    click.echo(f"Passthrough Count: {factory_contract.get_passthrough_count()}")

    count = factory_contract.get_passthrough_count()
    if count > 0:
        click.echo("\nDeployed Passthroughs:")
        for i in range(count):
            pt = factory_contract.get_passthrough(i)
            click.echo(f"  [{i}] {pt}")


cli.add_command(factory_info)
