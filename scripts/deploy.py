import json

from brownie import StrategySushiswapPair, Vault, accounts, rpc, web3, Wei
from click import secho
from eth_utils import is_checksum_address


def get_address(label):
    addr = input(f"{label}: ")
    if is_checksum_address(addr):
        return addr
    resolved = web3.ens.address(addr)
    if resolved:
        print(f"{addr} -> {resolved}")
        return resolved
    raise ValueError("invalid address or ens")


def main():
    # configurations = json.load(open("configurations.json"))
    # for i, config in enumerate(configurations["vaults"]):
    #     print(f"[{i}] {config['name']}")
    # config = configurations["vaults"][int(input("choose configuration to deploy: "))]
    deployer = accounts.load(input("deployer account: "))

    # if input("deploy vault? y/n: ") == "y":
    #     gov = get_address("gov")
    #     rewards = get_address("rewards")
    #     vault = Vault.deploy(
    #         config["want"],
    #         gov,
    #         rewards,
    #         config["name"],
    #         config["symbol"],
    #         {"from": deployer, 'gas_price':Wei("15 gwei")},
    #     )
    # else:
    #     vault = Vault.at(get_address("vault"))

    strategy = StrategySushiswapPair.at(get_address("strat"))
    strategy.harvest({"from": deployer, 'gas_price':Wei("20 gwei")})

    # strategy = StrategySushiswapPair.deploy(vault, config["pid"], {"from": deployer, 'gas_price':Wei("15 gwei")})

    # deposit_limit = Wei('200 ether')
    # vault.setDepositLimit(deposit_limit, {"from": deployer, 'gas_price':Wei("15 gwei")})
    # vault.addStrategy(strategy, deposit_limit, deposit_limit, 50, {"from": deployer, 'gas_price':Wei("15 gwei")})

    # secho(
    #     f"deployed {config['symbol']}\nvault: {vault}\nstrategy: {strategy}\n",
    #     fg="green",
    # )


def migrate():
    assert rpc.is_active()
    vault = Vault.at(get_address("vault"))
    gov = accounts.at(vault.governance(), force=True)
    old_strategy = StrategySushiswapPair.at(get_address("old strategy"))
    new_strategy = StrategySushiswapPair.deploy(
        vault, old_strategy.pid(), {"from": gov}
    )
    print("pricePerShare", vault.pricePerShare().to("ether"))
    print("estimatedTotalAssets", old_strategy.estimatedTotalAssets().to("ether"))
    vault.migrateStrategy(old_strategy, new_strategy, {"from": gov})
    print("pricePerShare", vault.pricePerShare().to("ether"))
    print("estimatedTotalAssets", new_strategy.estimatedTotalAssets().to("ether"))
    keeper = accounts.at(new_strategy.keeper(), force=True)
    for i in range(2):
        new_strategy.harvest({"from": keeper})
        print("pricePerShare", vault.pricePerShare().to("ether"))
        print("estimatedTotalAssets", new_strategy.estimatedTotalAssets().to("ether"))
