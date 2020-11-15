blocks_per_year = 6525 * 365
seconds_per_block = (86400 * 365) / blocks_per_year
sample = 200


def sleep(chain):
    chain.mine(sample)
    chain.sleep(int(sample * seconds_per_block))


def test_vault_deposit(vault, token, bptWhale):
    token.approve(vault, token.balanceOf(bptWhale), {"from": bptWhale})
    before = vault.balanceOf(bptWhale)
    deposit = token.balanceOf(bptWhale)
    vault.deposit(deposit, {"from": bptWhale})
    assert vault.balanceOf(bptWhale) == before + deposit
    assert token.balanceOf(vault) == before + deposit
    assert vault.totalDebt() == 0
    assert vault.pricePerShare() == 10 ** token.decimals()  # 1:1 price
    vault.withdraw(vault.balanceOf(bptWhale), {"from": bptWhale})

def test_vault_withdraw(vault, token, bptWhale):
    balance = token.balanceOf(bptWhale) + vault.balanceOf(bptWhale)
    vault.withdraw(vault.balanceOf(bptWhale), {"from": bptWhale})
    assert vault.totalSupply() == token.balanceOf(vault) == 0
    assert vault.totalDebt() == 0
    assert token.balanceOf(bptWhale) == balance

def test_strategy_harvest(strategy, vault, token, balancer, bptWhale, balWhale, chain):
    print("vault:", vault.name())
    user_before = token.balanceOf(bptWhale) + vault.balanceOf(bptWhale)
    print("BLP whale balance:", user_before.to("ether"))
    print("BAL whale balance:", balancer.balanceOf(balWhale).to("ether"))

    # token.approve(vault, token.balanceOf(bptWhale), {"from": bptWhale})
    vault.deposit(token.balanceOf(bptWhale), {"from": bptWhale})
    sleep(chain)
    print("share price before:", vault.pricePerShare().to("ether"))
    assert vault.creditAvailable(strategy) > 0
    # give the strategy some debt
    strategy.harvest()
    before = strategy.estimatedTotalAssets()
    print("Est total assets:", before.to("ether"))
    # run strategy for some time
    sleep(chain)
    print("Want balance|strategy:", token.balanceOf(strategy).to("ether"))
    print("Want balance|vault:", token.balanceOf(vault).to("ether"))
    print("Balancer balance|strategy:", balancer.balanceOf(strategy).to("ether"))
    print("Debt outstanding:", vault.debtOutstanding().to("ether"))
    balancer.transfer(strategy, balancer.balanceOf(balWhale) / 10, {"from": balWhale})
    strategy.harvest()
    sleep(chain)
    strategy.harvest()
    print("Want balance|strategy:", token.balanceOf(strategy).to("ether"))
    print("Want balance|vault:", token.balanceOf(vault).to("ether"))
    print("Balancer balance|strategy:", balancer.balanceOf(strategy).to("ether"))
    print("debt outstanding:", vault.debtOutstanding().to("ether"))
    after = strategy.estimatedTotalAssets()
    assert after > before
    print("share price after: ", vault.pricePerShare().to("ether"))
    # print(f"implied apy: {(after / before - 1) / (sample / blocks_per_year):.5%}")
    # user withdraws all funds
    vault.withdraw(vault.balanceOf(bptWhale), {"from": bptWhale})
    assert token.balanceOf(bptWhale) >= user_before


def test_strategy_withdraw(strategy, vault, token, bptWhale, balWhale, gov, chain):
    user_before = token.balanceOf(bptWhale) + vault.balanceOf(bptWhale)
    token.approve(vault, token.balanceOf(bptWhale), {"from": bptWhale})
    vault.deposit(token.balanceOf(bptWhale), {"from": bptWhale})
    # first harvest adds initial deposits
    sleep(chain)
    strategy.harvest()
    initial_deposits = strategy.estimatedTotalAssets().to("ether")
    # second harvest secures some profits
    sleep(chain)
    token.transfer(strategy, token.balanceOf(balWhale) / 10, {"from": balWhale})
    strategy.harvest()
    sleep(chain)
    strategy.harvest()
    deposits_after_savings = strategy.estimatedTotalAssets().to("ether")
    assert deposits_after_savings > initial_deposits
    # user withdraws funds
    vault.withdraw(vault.balanceOf(bptWhale), {"from": bptWhale})
    assert token.balanceOf(bptWhale) >= user_before
