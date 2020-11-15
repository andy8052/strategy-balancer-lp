import json
import pytest

@pytest.fixture
def vault(Vault, gov, rewards, guardian, token, bptWhale):
    vault = Vault.deploy(
        token,
        gov,
        rewards,
        "Balancer Pool Vault",
        "yvBLP BAL/WETH 80/20",
        {"from": guardian},
    )
    vault.setManagementFee(0, {"from": gov})
    deposit = token.balanceOf(bptWhale) / 2
    token.approve(vault, token.balanceOf(bptWhale), {"from": bptWhale})
    vault.deposit(deposit, {"from": bptWhale})
    assert token.balanceOf(vault) == vault.balanceOf(bptWhale) == deposit
    assert vault.totalDebt() == 0  # No connected strategies yet
    return vault


@pytest.fixture
def strategy(StrategyBalancerLP, vault, strategist, token, keeper, gov):
    strategy = StrategyBalancerLP.deploy(vault, {"from": strategist})
    strategy.setKeeper(keeper, {"from": strategist})
    vault.addStrategy(
        strategy,
        token.totalSupply() / 2,  # Debt limit of 50% total supply
        token.totalSupply() // 1000,  # Rate limt of 0.1% of token supply per block
        50,  # 0.5% performance fee for Strategist
        {"from": gov},
    )
    return strategy

@pytest.fixture
def succ_strategy(StrategyBalancerLP, vault, strategist, keeper):
    strategy = StrategyBalancerLP.deploy(vault, {"from": strategist})
    strategy.setKeeper(keeper, {"from": strategist})
    return strategy

@pytest.fixture
def token(interface):
    return interface.ERC20("0x59A19D8c652FA0284f44113D0ff9aBa70bd46fB4")

@pytest.fixture
def balancer(interface):
    return interface.ERC20("0xba100000625a3754423978a60c9317c58a424e3D")

@pytest.fixture
def gov(accounts):
    return accounts[1]

@pytest.fixture
def rewards(gov):
    return gov

@pytest.fixture
def guardian(accounts):
    return accounts[2]

@pytest.fixture
def strategist(accounts):
    return accounts[3]

@pytest.fixture
def keeper(accounts):
    return accounts[4]

@pytest.fixture
def bptWhale(accounts):
    # BPT whale
    return accounts.at("0xfF052381092420B7F24cc97FDEd9C0c17b2cbbB9", force=True)

@pytest.fixture
def balWhale(accounts):
    # BAL whale
    return accounts.at("0xb618F903ad1d00d6F7b92f5b0954DcdC056fC533", force=True)