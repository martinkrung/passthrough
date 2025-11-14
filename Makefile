all:

start_env:
	# source will not work, but this is for cmd documentation
	source .env
	source .venv/bin/activate

deploy_info:
	ape run scripts/deploy_manager.py info --network arbitrum:mainnet-fork:foundry

get_constructor_abi:
	python  scripts/get_constructor_abi.py

deploy_arbitrum_sepolia:
	ape run scripts/deploy_manager.py deploy --network arbitrum:sepolia:infura

deploy_arbitrum:
	ape run scripts/deploy_manager.py deploy --network arbitrum:mainnet:node

deploy_info_taiko:
	ape run scripts/deploy_manager.py info --network taiko:mainnet:node

deploy_taiko:
	ape run scripts/deploy_manager.py deploy --network taiko:mainnet:node

deploy_many_sonic:
	ape run scripts/deploy_manager.py deploy-many --network sonic:mainnet:node

deploy_optimism:
	ape run scripts/deploy_manager.py deploy --network optimism:mainnet:node

deploy_many_optimism:
	ape run scripts/deploy_manager.py deploy-many --network optimism:mainnet:node

deploy_info_optimism:
	ape run scripts/deploy_manager.py info --network optimism:mainnet:node

deploy_testnet:
	ape run scripts/deploy_manager.py deploy-many --network ethereum:local:test

import_pvk:
	ape accounts import arbideploy

networks_list:
	ape networks list

noisy_test:
	ape test -rP  --capture=no --network ethereum:local:test

test:
	ape test --network ethereum:local:test

# Factory deployment commands
deploy_blueprint_sonic:
	ape run scripts/deploy_factory.py deploy-blueprint --network sonic:mainnet:node

deploy_factory_sonic:
	ape run scripts/deploy_factory.py deploy-factory --blueprint $(BLUEPRINT) --network sonic:mainnet:node

deploy_via_factory_sonic:
	ape run scripts/deploy_factory.py deploy-passthrough-via-factory --factory $(FACTORY) --network sonic:mainnet:node

deploy_many_factory_sonic:
	ape run scripts/deploy_factory.py deploy-many-via-factory --factory $(FACTORY) --reward-token $(REWARD_TOKEN) --network sonic:mainnet:node

factory_info_sonic:
	ape run scripts/deploy_factory.py factory-info --factory $(FACTORY) --network sonic:mainnet:node

test_factory:
	ape test tests/test_factory.py --network ethereum:local:test

test_factory_integration:
	ape test tests/test_factory_integration.py --network ethereum:local:test

test_all:
	ape test --network ethereum:local:test
