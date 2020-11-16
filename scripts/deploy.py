import json

from brownie import StrategyBalancerLP, Vault, accounts, rpc, web3, Wei
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
    deployer = accounts.load(input("deployer account: "))

    if input("deploy vault? y/n: ") == "y":
        gov = get_address("gov")
        rewards = get_address("rewards")
        vault = Vault.deploy(
            "0x59A19D8c652FA0284f44113D0ff9aBa70bd46fB4",
            gov,
            rewards,
            "Balancer BAL-WETH 80-20 Pool yVault",
            "yvBal-BAL-WETH-80-20",
            {"from": deployer},
        )
    else:
        vault = Vault.at(get_address("vault"))

    strategy = StrategyBalancerLP.deploy(vault, {"from": deployer})

    deposit_limit = Wei('50 ether')
    vault.setDepositLimit(deposit_limit, {"from": deployer})
    vault.addStrategy(strategy, deposit_limit, deposit_limit, 0, {"from": deployer})

    secho(
        f"deployed {config['symbol']}\nvault: {vault}\nstrategy: {strategy}\n",
        fg="green",
    )


def migrate():
    assert rpc.is_active()
    vault = Vault.at(get_address("vault"))
    gov = accounts.at(vault.governance(), force=True)
    old_strategy = StrategyBalancerLP.at(get_address("old strategy"))
    new_strategy = StrategyBalancerLP.deploy(
        vault, {"from": gov}
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
