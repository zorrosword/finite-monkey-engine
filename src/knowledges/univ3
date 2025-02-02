
## 1. DOS Vulnerability in Pool Initialization

- **Vulnerability Title:** DOS Vulnerability in Pool Initialization  
- **Vulnerability Description:**  
  Attackers can render newly created liquidity pools unusable by passing extreme or harmful initialization parameters—such as setting far-future timestamps or unreachable tick constraints—during pool creation. Such values lock the pool in a blocked state, preventing normal operations until the unrealistic conditions are met.
- **Key Concept:**  
  When a system allows arbitrary pool setup parameters without sufficient validation, an attacker can front-run or misuse the initialization. By setting the pool’s operational parameters to unachievable or extremely distant values, the attacker effectively locks the pool, causing a Denial of Service (DoS) for all market participants.
- **Functionality:**  
  The pool initialization function is designed to establish base trading parameters and set an operational timeline. Once initialized, market participants should be able to add liquidity and perform token swaps. The vulnerability undermines this by freezing the pool right at its start.
- **Prompt Ask (Functionality Context):**  
  The function should be prompt in initializing a pool with validated parameters so that normal liquidity provision and token exchanges can commence immediately.

---

## 2. Missing Slippage and Deadline Protection

- **Vulnerability Title:** Missing Slippage and Deadline Protection  
- **Vulnerability Description:**  
  Without limits on acceptable price movement (slippage) or a set transaction expiry (deadline), attackers can sandwich swaps or delay them indefinitely in the mempool. This can cause extreme and manipulated price changes that force users into unfavorable exchange rates.
- **Key Concept:**  
  If a system fails to impose boundaries on price deviations or enforce timing constraints, it becomes vulnerable to front-running or prolonged pending states. Malicious actors might deliberately manipulate the price feed or hold transactions indefinitely.
- **Functionality:**  
  The swap function accepts a swap request and completes a token exchange by looking up the current price. However, it does not enforce a maximum tolerable price change or a deadline after which the transaction will fail, thereby exposing users to manipulated or delayed transactions.
- **Prompt Ask (Functionality Context):**  
  The exchange functionality should include mechanisms to protect users by limiting slippage and requiring deadlines, ensuring that if market conditions change too much or if the transaction is delayed, the swap will revert or be adjusted suitably.

---

## 3. Reading Price Directly from slot0

- **Vulnerability Title:** Reading Price Directly from slot0  
- **Vulnerability Description:**  
  The protocol reads the current live pool price directly from the storage slot (slot0) instead of using a historical or averaged value. As a result, a single large trade or a temporary state change can drastically skew the reported price. 
- **Key Concept:**  
  By relying on the immediate pool state instead of a time-weighted average, the system becomes vulnerable to front-running. An attacker can execute a large, sudden trade to distort the pool state and then benefit from the manipulated price.
- **Functionality:**  
  The functionality is meant to retrieve a real-time exchange rate from the pool’s current state and calculate token conversion results. Without an averaging mechanism, this real-time price is easily manipulated by instantaneous trades.
- **Prompt Ask (Functionality Context):**  
  The price lookup function should incorporate methods to smooth out short-term fluctuations (for example, using time-weighted averages) instead of relying solely on the current slot0 value.

---

## 4. TWAP Oracle Stale Observation

- **Vulnerability Title:** TWAP Oracle Stale Observation  
- **Vulnerability Description:**  
  Attackers can manipulate the time-weighted average price (TWAP) oracle by exploiting its observation array. By injecting invalid or uninitialized entries (for example, using a manipulated index or seed), the oracle may incorporate fake historical data, resulting in distorted average prices.
- **Key Concept:**  
  When a circular log (observation array) contains uninitialized or malicious data and no legitimacy checks are performed before using it in time-weighted calculations, the computed average price becomes unreliable.
- **Functionality:**  
  The purpose is to compute a time-adjusted exchange rate by aggregating and averaging past pool states stored in a circular ledger. If uninitialized readings are used, the combined rate will be artificially skewed.
- **Prompt Ask (Functionality Context):**  
  The oracle computation functionality should validate each observation entry before using it in the TWAP calculation to ensure that only genuine historical values contribute.

---

## 5. UniswapV3SwapCallback() Reentrancy Risks

- **Vulnerability Title:** UniswapV3SwapCallback() Reentrancy Risks  
- **Vulnerability Description:**  
  In a two-step swap process, the protocol first sends out output tokens and then calls an external callback (UniswapV3SwapCallback()) expecting the caller to supply input tokens. An attacker can abuse this flow by intervening during the callback, potentially reentering or redirecting control flow to drain approved balances or bypass proper state changes.
- **Key Concept:**  
  Delivering assets before verifying the return of input tokens opens the door for reentrancy. External contracts can exploit the callback to execute unintended operations if not properly protected.
- **Functionality:**  
  The swap functionality is intended to complete a token exchange by first dispensing one asset and then receiving payment (input tokens) through the callback. Correctly managing this callback is essential to ensure that the exchange completes in full and without side effects.
- **Prompt Ask (Functionality Context):**  
  The callback should be designed so that external calls cannot reenter the critical sections of the swap logic or modify state in unexpected ways. Additional reentrancy guards or state checks should be in place.

---

## 6. Low Liquidity Pool Price Manipulation

- **Vulnerability Title:** Low Liquidity Pool Price Manipulation  
- **Vulnerability Description:**  
  When an oracle aggregates prices from multiple pools, including those with very low liquidity, attackers can execute small trades in these thin markets to push the price far from the fair market. The outlier then skews the aggregated or averaged price, leading to mispriced swaps or liquidations.
- **Key Concept:**  
  Including markets with inadequate liquidity in a combined price feed lets an adversary manipulate the final aggregated price with minimal capital. This can distort the reference price used for critical decisions.
- **Functionality:**  
  The system surveys multiple venues (pools) for an exchange rate, collects the quotes, and blends them into a single representative price for downstream use. Thinly traded pools may provide easily manipulable quotes.
- **Prompt Ask (Functionality Context):**  
  The oracle aggregation functionality should filter out markets below a minimum liquidity threshold or weight the pools appropriately so that low liquidity pools cannot disproportionately affect the final price.

---

## 7. SplitSwapper Oracle Manipulation via Fake Pool Deployment

- **Vulnerability Title:** SplitSwapper Oracle Manipulation via Fake Pool Deployment  
- **Vulnerability Description:**  
  The Oracle for the SplitSwapper looks up a Uniswap V3 pool using the token pair and a default fee tier (for example, 0.05%). If no such pool exists, an attacker can deploy and initialize a new pool at that fee tier with extreme price parameters (such as an absurdly low or high price). Once deployed, the Oracle fetches price data from this manipulated pool, resulting in highly skewed swap calculations.
- **Key Concept:**  
  The default fee tier is trusted. Without verification of pool existence or sanity (such as liquidity checks), the Oracle may use data from an attacker-controlled pool. This allows the attacker to distort prices and potentially secure arbitrage advantages or cause zero-cost swaps.
- **Functionality:**  
  The oracle functionality looks for an existing Uniswap V3 pool by (tokenA, tokenB, feeTier) and returns its price data for use in swaps. It must verify that the pool is a genuine and active market before relying on its price.
- **Recommendations:**  
  - Validate that the pool already exists and has adequate liquidity.
  - Reject or ignore price data from newly deployed or “empty” pools.
  - Consider using explicit overrides or ensuring owner/config sanity when setting the default fee tier.
- **Prompt Ask (Functionality Context):**  
  When the oracle library looks up the pool, it should ensure that the pool is legitimately deployed and active; if not, it must not use that pool’s price for critical operations.

---

## 8. Fee Growth Underflow Handling in tick::get_fee_growth_inside()

- **Vulnerability Title:** Fee Growth Underflow Handling in tick::get_fee_growth_inside()  
- **Vulnerability Description:**  
  In Uniswap V3’s fee calculations, the protocol relies on wraparound (underflow) behavior to compute correct fee growth inside a tick range. Seawater’s Rust implementation, however, uses `checked_sub`, which throws an error (or returns None) on underflow. This means that legitimate underflows (which indicate fee accumulation from the opposite direction) cause the code to revert, potentially locking positions and preventing fee updates.
- **Key Concept:**  
  Uniswap V3’s original Solidity code relies on implicit wraparound for underflow. When using Rust, failing to mimic this behavior by using a checked subtraction results in errors, making valid fee computations fail.
- **Impact:**  
  Positions that depend on these calculations may become unmodifiable or stuck, leading to users being unable to add or remove liquidity or collect accrued fees.
- **Recommended Fix:**  
  Use arithmetic that allows wrapping (e.g., `wrapping_sub`) so the computation can proceed as expected.
- **Functionality:**  
  The function `tick::get_fee_growth_inside()` calculates fee growth by subtracting fee counters at the tick boundaries. It must account for natural underflow that represents accumulated fees correctly.

---

## 9. Misconfigured sqrtPriceLimitX96 in Dual Swap Execution

- **Vulnerability Title:** Misconfigured sqrtPriceLimitX96 in Dual Swap Execution  
- **Vulnerability Description:**  
  In the PerpDepository contract, the function `_rebalanceNegativePnlWithSwap()` calls two distinct swap functions: one interacting with the protocol’s internal Uniswap V3 pool and another via a separate Uniswap instance (spotSwapper). Both calls reuse the same `sqrtPriceLimitX96` parameter, although each pool can have different liquidity distributions and acceptable price ranges. This misuse can result in unexpected reverts or incorrect price constraints.
- **Key Concept:**  
  Each Uniswap V3 pool has its own characteristics, and a slippage boundary (sqrtPriceLimitX96) suited for one pool may not apply to another. Reusing the same limit inadvertently forces one of the swaps into an incorrect execution pathway.
- **Impact:**  
  The entire transaction may fail if the limit is invalid for the second pool, or swaps may execute with unintended slippage protections.
- **Recommended Fix:**  
  Apply `sqrtPriceLimitX96` only to the pool for which it was specifically configured. For the second swap, either set a distinct limit or rely solely on alternative checks (like `amountOutMinimum`).
- **Functionality:**  
  The contract performs two swap operations as part of rebalancing negative PNL. Each swap needs its own properly configured slippage or price limit to ensure correct exchange rates and avoid excessive reversion.

---

## 10. Q96 Fixed-Point Multiplication Overflow

- **Vulnerability Title:** Q96 Fixed-Point Multiplication Overflow  
- **Vulnerability Description:**  
  In Uniswap V3 and similar protocols, numbers are represented in fixed-point format (commonly Q96). When two Q96 values are multiplied, the true mathematical result can require up to 192 bits. If the multiplication is performed in an environment that does not use sufficiently wide intermediate storage—or if proper shifting and rounding are not applied—the intermediate result may overflow or produce an incorrect result.
- **Key Concept:**  
  Simple multiplication of Q96 numbers without employing specialized libraries (such as Uniswap’s FullMath) that handle 256-bit or even 512-bit intermediate values can cause overflows. The proper approach requires managing wide bit-width results and then shifting the product back to a Q96 representation.
- **Recommended Practice:**  
  Use dedicated math libraries that implement full-width multiplication and proper shifting to prevent overflow. Ensure that the intermediate arithmetic can handle up to 192 bits of fractional data before converting back to Q96.
- **Functionality:**  
  The fixed-point multiplication operations are fundamental in calculating exchange rates, fee accumulations, and other financial parameters. They must accurately handle overflow and shifting to maintain precision and correctness.

