下面整理了一下文中描述的所有漏洞及其细节，确保不遗漏任何信息。以下每个部分均详细说明了漏洞的成因、攻击过程和潜在影响：

---

## 1. 利用 TWAP 检查缺失导致的流动性部署漏洞

CLM 协议在重新部署 Uniswap V3 的流动性时常常依赖于当前池子的价格（通常来自 `pool.slot0`）来调整价格区间，为了防止价格操控，协议通常会在重大函数中加入 TWAP（时间加权平均价格）的检测。但存在两个函数存在问题，未在调用前后严格执行 TWAP 检查，从而让攻击者能够利用价格操控实施 sandwich 攻击。

### 1.1. 利用 `setPositionWidth` 函数漏洞

- **漏洞代码与流程：**  
  ```solidity
  function setPositionWidth(int24 _width) external onlyOwner {
      emit SetPositionWidth(positionWidth, _width);
      _claimEarnings();
      _removeLiquidity();
      positionWidth = _width;
  
      // @audit 更新 ticks 使用基于 `pool.slot0` 的新数据
      _setTicks();
  
      // @audit 重新部署流动性时，没有调用 `onlyCalmPeriods` TWAP 检查
      _addLiquidity();
  }
  ```
  
- **攻击原理：**  
  - **前置攻击（Front-run）：** 攻击者在合约所有者调用 `setPositionWidth` 前，用大量 USDC 兑换掉流动性的另一资产（例如 WBTC），迫使协议持有的流动性池中 WBTC 被大量买出，从而将池内价格向上推高。  
  - **流程细节：**
    1. 用户存入流动性，CLM 协议建立初始 Uniswap V3 LP 头寸。
    2. 攻击者在所有者调用 `setPositionWidth` 前，利用大量 USDC 来前置交易（front-run），使得池内 WBTC 数量急剧减少，同时 WBTC 价格被人为撑高。
    3. 所有者调用 `setPositionWidth`，合约根据被操纵后的 `pool.slot0` 更新 ticks，并直接重新部署流动性，未进行 TWAP 检查。
    4. **后置攻击（Back-run）：** 攻击者在该交易后，再次发起交易，将手中的 WBTC 以高价卖给刚刚重新部署流动性的协议，迫使协议以不利的价格买入 WBTC，从而损失惨重。
  
- **后果：**  
  协议大部分资产（包括 WBTC 与 USDC）会被攻击者通过大幅套利消耗殆尽，最终导致协议资金几乎被“榨干”。

### 1.2. 利用 `unpause` 函数漏洞

- **漏洞代码与流程：**  
  ```solidity
  // 已暂停时流动性已被移除
  function unpause() external onlyManager {
      _giveAllowances();
      _unpause();
      _setTicks();
      _addLiquidity();
  }
  ```
  
- **攻击原理：**  
  - **前置攻击：** 当协议处于暂停状态且流动性已被移除时，攻击者利用大量 USDC 交易来购买池内的 WBTC，从而迅速将价格推高。
  - **流程细节：**
    1. 用户存入资金并建立单边或不平衡的流动性头寸（例如只有 USDC，无 WBTC）。
    2. 协议由于市场波动或其他原因暂停操作，流动性被提前全部移除。
    3. 攻击者在所有者调用 `unpause` 前，通过前置交易用大量 USDC 购买 WBTC，迫使 WBTC 价格暴涨。
    4. 所有者调用 `unpause`，合约在重新部署流动性时，根据操纵后的价格用 USDC 布置新的流动性头寸，未执行 TWAP 检查。
    5. 攻击者随后后置交易，以更高价格将其 WBTC 卖给该新建的高价流动性头寸。
  
- **后果：**  
  特别是在单边或不平衡流动性头寸下，协议将大量 USDC 以极不划算的价格交付给攻击者，导致协议主要资产被不合理地转移。

---

## 2. 通过设置无效 TWAP 参数实施 Owner Rug-Pull 的风险

- **背景：**  
  为了防范短期价格操控，协议引入了 TWAP 检查，其中两个关键参数是 `maxDeviation`（最大价格偏差）和 `twapInterval`（TWAP 时间区间）。
  
- **漏洞描述：**  
  - 协议允许合约所有者随意更新这两个参数。  
  - 如果所有者将参数调整到极端值（例如设置一个很大的偏差或过于短的时间间隔），那么 TWAP 检查可能会失效，从而无法有效防止价格操控攻击。
  
- **潜在风险：**
  - **Owner Rug-Pull（所有者跑路）：** 通过操控 TWAP 参数，所有者可以在不受到防护机制约束的情况下，重新部署流动性并利用 retrospective fee 的机制窃取用户未领取的奖励。
  - **费用的追溯调整：** 因为管理费在 harvest 调用时才计算，如果在 harvest 之前所有者提升费用，则之前在低费用下累积的奖励将按照更高费率扣费，进一步加剧对流动性提供者的不公。

- **潜在解决方案：**
  - 将所有关键的所有者操作（例如更新 TWAP 参数）置于一个多签或时间锁（Time-Locked）的机制后面，防止滥用。
  - 对关键参数设置最小值和最大值限制，防止其被设置为任意不合理的值。

---

## 3. 代币因数字舍入问题永久滞留在协议中

- **背景与漏洞代码：**  
  在分配原生奖励（nativeEarned）时，按照各自的比例计算各个角色（call fee、beefy fee、strategist fee）的份额，由于整数除法的舍入误差，可能会有少量代币始终未分配：
  ```solidity
  uint256 callFeeAmount = nativeEarned * fees.call / DIVISOR;
  IERC20Metadata(native).safeTransfer(_callFeeRecipient, callFeeAmount);
  
  uint256 beefyFeeAmount = nativeEarned * fees.beefy / DIVISOR;
  IERC20Metadata(native).safeTransfer(beefyFeeRecipient, beefyFeeAmount);
  
  uint256 strategistFeeAmount = nativeEarned * fees.strategist / DIVISOR;
  IERC20Metadata(native).safeTransfer(strategist, strategistFeeAmount);
  ```
  
- **问题细节：**  
  - 每次分配后由于除法舍入可能存在微小剩余，这部分代币不会被进一步分配或回收，长期运作后累积成较大金额。
  
- **建议的改进方案：**  
  - 在分发完 callFeeAmount 和 strategistFeeAmount 后，让 beefyFeeAmount 使用剩余的所有代币：
    ```solidity
    uint256 callFeeAmount = nativeEarned * fees.call / DIVISOR;
    IERC20Metadata(native).safeTransfer(_callFeeRecipient, callFeeAmount);
    
    uint256 strategistFeeAmount = nativeEarned * fees.strategist / DIVISOR;
    IERC20Metadata(native).safeTransfer(strategist, strategistFeeAmount);
    
    uint256 beefyFeeAmount = nativeEarned - callFeeAmount - strategistFeeAmount;
    IERC20Metadata(native).safeTransfer(beefyFeeRecipient, beefyFeeAmount);
    ```
  - 确保所有应分配的代币均被正确分发，防止小额代币滞留。

---

## 4. 更新 Router 地址时代币授权（Token Approvals）未被撤销问题

- **背景：**  
  CLM 协议通常会为关键的 Router 授予无限额代币授权，以便后续操作（见 _giveAllowances 函数）：
  ```solidity
  function _giveAllowances() private {
      IERC20Metadata(lpToken0).forceApprove(unirouter, type(uint256).max);
      IERC20Metadata(lpToken1).forceApprove(unirouter, type(uint256).max);
  }
  ```
- **漏洞描述：**  
  - 当通过简单函数更新 unirouter 地址时：
    ```solidity
    function setUnirouter(address _unirouter) external onlyOwner {
        unirouter = _unirouter;
        emit SetUnirouter(_unirouter);
    }
    ```
  - 协议没有先撤销（revoke）原有 Router 的授权，导致旧的 Router 依然拥有无限授权，可以随时操作协议中的代币。
  
- **风险后果：**  
  - 如果旧的 Router 存在安全漏洞或者被攻击者控制，协议资产可能因此被恶意转移。
  
- **建议的改进措施：**  
  - 在更新 Router 地址前，先撤销对原先 Router 的所有授权，确保新地址生效后旧授权不再有效。

---

## 5. 更新协议费用导致待领取 LP 奖励被追溯性收取高费

- **背景：**  
  CLM 协议通过收取管理费来从 LP 奖励中抽成，而 LP 奖励是在 harvest 函数调用时才结算的。
  
- **漏洞描述：**  
  - 合约所有者可以随时修改管理费比例。  
  - 如果所有者在 harvest 调用前上调费用，则之前已累积但尚未收取的 LP 奖励，会按照更高的费用比率扣除。
  
- **风险点：**  
  - **追溯性应用新费用：** 用户在先前低费率期内获取的奖励，在 harvest 时却被新费用率抽成，这对 LP 提供者非常不公平，类似于所有者利用操作费率实现 rug-pull。
  
- **审计建议：**  
  - 在更新费用结构前，优先对待领取奖励（pending rewards）进行结算，确保新的费用不会倒逼性适用于之前已累积的奖励。
  
---

## 6. 其他需要关注的 CLM 协议不变量（Invariants）

在 CLM 协议中，还存在一些额外的不变量需要确保正确执行，避免系统漏洞：

- 协议在有效的 `sqrtPriceX96` 范围内不应因溢出（overflow）而 revert。
- 当销毁一定数量的 LP 份额时，withdraw 操作必须返还大于 0 的代币。
- 当存入资金时，deposit 操作须返回大于 0 的 LP 份额。
- 协议中代币不应永远滞留在某个合约内（例如由于小额残留问题）。
- 审计过程中可采用状态性 fuzz 测试（例如 Echidna invariant 测试）以验证如下面的示例：
  ```solidity
  // 不变量示例：Strategy 合约内不能滞留 native 代币
  function property_strategy_native_tokens_balance_zero() public returns(bool) {
      uint256 bal = IERC20(native).balanceOf(address(strategy));
      emit TestDebugUIntOutput(bal);
      return bal == 0;
  }
  ```

---
