class VulPrompt:
    def vul_prompt_common():
        return """

1. **Parameter Validation and Input Verification Deficiencies**  
   - Checks for parameter order or type errors (e.g., “zero share” issues, incorrect parameter sequencing).  
   - Insufficient validation of input length, indices, format, and encoding.  
   - Redundant or improper parameter checks that may allow unexpected values into the system.  
   - Missing necessary modifiers, data validation, and boundary checks (including insufficient normalization of oracle prices and parameter/boundary value errors).  
   - In certain trade and minting functions, validation for slippage parameters and transaction deadlines is neglected, which increases the risk of adverse execution.

2. **Arithmetic Calculation and Precision Issues**  
   - Use of incorrect constants, ratio calculation errors, and imprecise mathematical formulas.  
   - Decimal precision errors, rounding problems, and unit conversion mistakes (for instance, using a fixed 6-decimal precision when the target token might have 18 decimals).  
   - Division, bit shift, exchange rate, or interest rate model miscalculations.  
   - Confusion between “shares” and “amount” calculations leading to misrepresentations of user balances or collateral values.  
   - Inaccuracies in calculating PnL, yield fees, fund flows, conversion rates, share conversions, and equity ratios.  
   - Cumulative errors in recursive or multi-step conversions that can amplify small rounding issues.  
   - In inline assembly, using operations like add, sub, or mul without Solidity’s overflow/underflow protection can lead to unnoticed overflows—even issues where uint128 arithmetic is performed in a 256‑bit environment.  
   - Fixed-point (e.g., Q96) multiplications without proper full‑width intermediate storage may result in overflow; similarly, LP reward distribution using integer division can leave remainders that become permanently locked.

3. **State Updates, Synchronization, and Data Storage Defects**  
   - Incorrect ordering of state updates or improper check sequences that delay or miss critical updates.  
   - Inconsistent synchronization between global and local (cache) data—including situations where mappings, arrays, or internal caches are not cleared in a timely or complete manner.  
   - Loss of historical records and vulnerabilities within freezing or reward mechanisms due to unsynchronized state updates.  
   - “Incorrect determination methods” that can be manipulated to alter the deployment state.  
   - In inline assembly, failure to update the Free Memory Pointer (FMPA) on time or allocating insufficient memory (for example, missing a 32‑byte offset) leads to memory corruption and data overwrites.  
   - In DAO implementations, unsynchronized snapshots and NFT voting power updates may result in inaccurate governance state records.

4. **Insufficient Permission Control and Authentication**  
   - Lack of necessary access permission checks or inappropriate access modifier configurations for critical functions.  
   - Vulnerabilities in authorization logic, loose role management, and insufficient caller identity verification (including issues with signatures, roles, and distributed identity schemes).  
   - In cross‑module, flash loan, or flash swap scenarios, insufficient authorization controls can open attack vectors.  
   - Public interfaces and functions may be exploited by arbitrary calls.  
   - Signature/replay vulnerabilities occur when signed messages lack a nonce, chain_id, or other key parameters—allowing replay attacks even after a user’s status or KYC changes.  
   - Failure to properly check the result of ecrecover (e.g., a returned zero address) or address signature malleability can permit unauthorized operations.  
   - For example, updating a router address without revoking old unlimited approvals leaves the previous address with perpetual control over token transfers.

5. **External Calls and Cross‑chain Communication Vulnerabilities**  
   - Incorrect external contract interface calls, misuse of delegatecall or staticcall, and ABI encoding errors.  
   - Data leakage or abuse risks during cross‑module or external data transmissions.  
   - Problems with cross‑chain message packaging, insufficient parameter configuration, or inadequate minimum gas limits that can lead to message blocking.  
   - In cross‑chain scenarios, issues include exchange rate deviations, market parameter mismatches, and unclear distinctions of virtual account source chains.  
   - Choosing inappropriate target addresses or functions for cross‑chain messages can lead to unwanted side effects.  
   - Insufficient data validation for certain external interface calls may allow erroneous or malicious data to enter the system.  
   - In inline assembly, for instance, when making an external call (using staticcall), failing to check that the target has valid code deployed can cause logic errors and misinterpretations of data returned.

6. **Business Logic and Process Design Flaws**  
   - Errors in deployment state determination and improper handling of special edge cases or empty orders.  
   - Insufficient protection measures in critical processes such as liquidation, lending, auction, redemption, and withdrawal—leading to inadequate collateral protection or weak lending buffers.  
   - Inconsistencies in multi‑stage processes (including cancellation, settlement, or locking mechanisms) and flawed internal synchronization.  
   - Specific DAO governance flaws include:  
     • Flash loans used to temporarily inflate voting power, enabling rapid proposal approval and lock‑in within a single transaction.  
     • Inconsistent NFT voting power calculation functions that can be exploited to set vote weight to zero or artificially reduce the total voting power (thus amplifying individual influence).  
     • Unsynchronized vote snapshots, duplicate voting via token transfers, bypass of direct voting restrictions via delegation, and proposals that either remain open indefinitely or get approved before tokens exist.  
     • Decimal conversion issues in token sales and circumvention of per‑user purchase limits by splitting transactions.  
   - In lending protocols:  
     • Liquidation may be triggered prematurely (for example, using an accepted timestamp instead of the last repayment timestamp) or might fail to liquidate a borrower due to errors in managing collateral records.  
     • Debt closures without real repayments, misdirected repayments (even to the zero address), and infinite loan rollovers can all lead to systemic risk.  
     • Repayments might be applied only to the current outstanding loan, causing misallocations.  
   - In liquidation processes:  
     • Lack of sufficient liquidation incentives (especially for small positions) can let bad debt accumulate.  
     • Users might over‑withdraw collateral, leaving too little to cover adverse movements.  
     • Partial liquidations can bypass bad debt handling if certain thresholds (like remaining margin) are not re‑evaluated correctly.  
     • Other issues include disrupted collateral priority, repayment misallocation when borrower identities change, an overly narrow gap between borrow LTV and liquidation thresholds, and improper handling of accrued yield and positive PnL.

7. **Reentrancy, Front‑running, and Denial of Service Risks**  
   - Absence of standard reentrancy protection designs (including protection against cross‑function reentrancy and ERC777 hook-induced vulnerabilities).  
   - State update order issues that provide windows for reentrant calls.  
   - Front‑running vulnerabilities that enable attackers to manipulate prices or state (for example, by using a manipulated TWAP or sandwich attacks).  
   - Unbounded iterations in loops that may cause Denial of Service (DoS) conditions.  
   - In Uniswap V3 swap callbacks (UniswapV3SwapCallback), sending output tokens before completing the callback routine may allow reentrancy and state manipulation.  
   - In lending and liquidity deployment, insufficient TWAP protection or sole reliance on a single price source further expose the system to front‑running and sandwich attacks.

8. **Module Call, Upgrade Configuration, and Initialization Vulnerabilities**  
   - Errors in module calls and delegatecalls—for example, setting immutable module addresses in the constructor or failing to verify cross‑module dependencies adequately.  
   - Mismatched or misconfigured constructor parameters and imprecise cross‑contract or cross‑module data transmissions.  
   - Defects in upgrade scripts, deployment, initialization, and configuration management (including loose Namespace registration and weak core system permissions, as well as controller or wallet initialization mistakes).  
   - Cross‑chain deployment, state variable resets, and upgrade processes may introduce security risks if not handled with strict controls.  
   - In liquidity management, failure to revoke old router approvals during updates or overly lax TWAP parameter configurations can be exploited for rug‑pulls or retroactive fee increases.

9. **Fund Management, Fee Calculation, and Reward Distribution Errors**  
   - Improper parameter settings in settlements, refunds, and overall fund flows.  
   - Errors in asset and share conversion, exchange operations, liquidation reward distribution, and related fund flows (including miscalculations in commissions, discounts, and referral rewards).  
   - Inconsistencies in calculating referral rewards, incentive distributions, yield fees, and overall PnL.  
   - Unclear rules for fund locking or asset ownership may result in malicious asset extractions or faulty reward distribution (notably in systems using ERC20 rebasing or YieldBox conversions).  
   - In liquidity management, for example, native reward distributions may leave small remainders permanently locked due to integer arithmetic, and retroactive adjustments to management fees on pending LP rewards can unjustly reduce provider rewards.

10. **Token Approval and Contract Call Errors**  
    - Missing necessary ERC20/ERC721 token approvals.  
    - Errors in specifying target addresses, debit accounts, or token transfer parameters during contract calls.  
    - When updating critical contract addresses (such as routers) or swapping dependencies, failure to revoke old unlimited approvals leaves tokens vulnerable to unauthorized transfers.

11. **External Dependency, Network Configuration, and Security Issues**  
    - Incorrect assumptions about third‑party contract interfaces, external oracle dependencies, or price data (for example, returning empty or stale data, or employing incorrect price values in calculations).  
    - Insufficient validation in external interface calls, which can lead to dangerous reliance on inaccurate data.  
    - In cross‑chain bridges and cross‑domain calls, misconfigured fee or gas parameters—and even overly exposed node ports—can lead to security vulnerabilities.  
    - Underlying data structures (such as MerkleDB) may have inherent security issues.  
    - For external oracles like Chainlink, specific concerns include:  
      • Not checking for stale prices by overlooking the updatedAt timestamp.  
      • Failing to verify L2 sequencer status on L2 chains.  
      • Assuming a uniform heartbeat across different feeds instead of using feed‑specific data.  
      • Not validating that price feeds update frequently or correctly handle decimal precision.  
      • Inadequate request confirmations vis‑à‑vis chain re‑org depths, use of incorrect oracle addresses, potential for front‑running oracle updates, and unhandled oracle call reverts or depegging events.  
      • For randomness oracles, allowing bets after the randomness request or permitting re‑requests can undermine fairness.

12. **Language‑specific and Low‑level Implementation Vulnerabilities**  
    - Issues unique to Solidity inline assembly and low‑level EVM code.  
    - Memory corruption caused by not updating the Free Memory Pointer (FMPA) promptly, or by using incorrect memory offsets (as seen in buffer initialization problems).  
    - Using assembly instructions (e.g., add, sub, mul) without proper overflow/underflow detection; also, using 256‑bit arithmetic to perform operations intended for smaller types (such as uint128) may bypass expected safety checks.

13. **Trade Execution and Slippage Vulnerabilities**  
    - Swap functions that do not allow users to specify a minimum acceptable output (minTokensOut) or that hard‑code the slippage parameter (e.g., 0), leaving trades vulnerable to sandwich attacks and adverse execution.  
    - Not providing a user‑defined deadline, which can result in trades executing under unfavorable conditions if delayed.  
    - Incorrect slippage calculations—for example, computing slippage based on internal LP token values instead of the actual user‑provided amounts—or applying slippage protection only to intermediate steps while leaving the final output unprotected.  
    - Mismatches in fixed precision (such as returning a 6‑decimal value) against the target token’s actual decimals can cause the slippage protection to fail.  
    - In minting operations, calculating synthetic token amounts from asset reserves without allowing users to set an acceptable slippage range exposes users to infinite slippage risk.  
    - On‑chain slippage calculations (e.g., using on‑chain estimations) can be manipulated by adversaries, so user‑calculated values (often performed off‑chain) should be used in transactions.  
    - Hard‑coded fee tiers in systems like Uniswap V3 or zero slippage requirements (demanding exact outputs) can lead to transaction reversions, DoS conditions, or severe losses under volatile market conditions.
        """
    def vul_prompt_common_new():
        return """
# Smart Contract Security Checklist

1. **Parameter Validation and Input Verification Deficiencies**  
   - Checks for parameter order or type errors (e.g., "zero share" issues, incorrect parameter sequencing).  
   - Insufficient validation of input length, indices, format, and encoding.  
   - Redundant or improper parameter checks that may allow unexpected values into the system.  
   - Missing necessary modifiers, data validation, and boundary checks (including insufficient normalization of oracle prices and parameter/boundary value errors).  
   - In certain trade and minting functions, validation for slippage parameters and transaction deadlines is neglected, which increases the risk of adverse execution.
   - Missing validation of fund-related parameters allowing manipulation of funds.
   - Incorrect parameter order leading to unauthorized access.
   - Failure to validate transaction parameters in cross-chain communications.
   - Failure to check codehash against keccak256("") for non-existent contracts.
   - ETH value parameters not properly validated in payable functions.

2. **Arithmetic Calculation and Precision Issues**  
   - Use of incorrect constants, ratio calculation errors, and imprecise mathematical formulas.  
   - Decimal precision errors, rounding problems, and unit conversion mistakes (for instance, using a fixed 6-decimal precision when the target token might have 18 decimals).  
   - Division, bit shift, exchange rate, or interest rate model miscalculations.  
   - Confusion between "shares" and "amount" calculations leading to misrepresentations of user balances or collateral values.  
   - Inaccuracies in calculating PnL, yield fees, fund flows, conversion rates, share conversions, and equity ratios.  
   - Cumulative errors in recursive or multi-step conversions that can amplify small rounding issues.  
   - In inline assembly, using operations like add, sub, or mul without Solidity's overflow/underflow protection can lead to unnoticed overflows--even issues where uint128 arithmetic is performed in a 256‑bit environment.  
   - Fixed-point (e.g., Q96) multiplications without proper full‑width intermediate storage may result in overflow; similarly, LP reward distribution using integer division can leave remainders that become permanently locked.
   - Insufficient precision in mathematical utilities (e.g., MathUtils) causing calculation errors.
   - Using collateralShare instead of amount for liquidation threshold calculations, causing inaccurate liquidation checks.
   - Calculation overflows when handling large numbers.
   - Variable type errors causing insufficient fund burning.
   - Incorrect reward calculations leading to double-counting of rewards.
   - Insufficient precision when comparing accumulated fees with total pool value, making reinvestment vulnerable to flash loan attacks.
   - Failure to account for price differences between ETH and staked ETH2.

3. **State Updates, Synchronization, and Data Storage Defects**  
   - Incorrect ordering of state updates or improper check sequences that delay or miss critical updates.  
   - Inconsistent synchronization between global and local (cache) data--including situations where mappings, arrays, or internal caches are not cleared in a timely or complete manner.  
   - Loss of historical records and vulnerabilities within freezing or reward mechanisms due to unsynchronized state updates.  
   - "Incorrect determination methods" that can be manipulated to alter the deployment state.  
   - In inline assembly, failure to update the Free Memory Pointer (FMPA) on time or allocating insufficient memory (for example, missing a 32‑byte offset) leads to memory corruption and data overwrites.  
   - In DAO implementations, unsynchronized snapshots and NFT voting power updates may result in inaccurate governance state records.
   - State variables are prematurely updated before asset transfers, leading to improper transaction sequencing.
   - Asynchronous reserve and balance updates causing double counting of funds.
   - Incorrect state reset handling due to time-related inconsistencies.
   - Allowing voting rights to be transferred, harming the weight of other participants.
   - Not destroying tokens after liquidation procedures.
   - System shutdowns that stop updating user reward data, allowing new users to steal rewards.

4. **Consistency and Double-counting Issues**
   - Inconsistencies between token accounting systems leading to double counting.
   - Reward calculations double-counting unsettled reserves.
   - Reserve and balance not updated in real-time synchronization leading to double calculations.
   - Fee double-counting due to inconsistent fee accounting mechanisms.
   - Inconsistent time reset handling across different contract components.
   - Inconsistent application of penalty calculations (e.g., grace period penalties not included in market exit penalties).
   - Elasticity amount variables incorrectly applied in liquidation asset calculations.
   - Inconsistent handling of price data between different components.
   - Inconsistent validation processes across similar functions.
   - Inconsistent initialization of time_weight when adding new gauges.
   - Inconsistent behavior between original and wrapper contracts for the same assets.

5. **Insufficient Permission Control and Authentication**  
   - Lack of necessary access permission checks or inappropriate access modifier configurations for critical functions.  
   - Vulnerabilities in authorization logic, loose role management, and insufficient caller identity verification (including issues with signatures, roles, and distributed identity schemes).  
   - In cross‑module, flash loan, or flash swap scenarios, insufficient authorization controls can open attack vectors.  
   - Public interfaces and functions may be exploited by arbitrary calls.  
   - Signature/replay vulnerabilities occur when signed messages lack a nonce, chain_id, or other key parameters--allowing replay attacks even after a user's status or KYC changes.  
   - Failure to properly check the result of ecrecover (e.g., a returned zero address) or address signature malleability can permit unauthorized operations.  
   - For example, updating a router address without revoking old unlimited approvals leaves the previous address with perpetual control over token transfers.
   - Cross-chain entity address forgery due to inadequate verification.
   - Borrowers unable to update market's maxTotalSupply or close markets due to insufficient permissions.
   - Blacklisted users bypassing sanctions by transferring funds in parts within the system.

6. **Business Logic and Process Design Flaws**  
   - Errors in deployment state determination and improper handling of special edge cases or empty orders.  
   - Insufficient protection measures in critical processes such as liquidation, lending, auction, redemption, and withdrawal--leading to inadequate collateral protection or weak lending buffers.  
   - Inconsistencies in multi‑stage processes (including cancellation, settlement, or locking mechanisms) and flawed internal synchronization.  
   - Specific DAO governance flaws include:  
     • Flash loans used to temporarily inflate voting power, enabling rapid proposal approval and lock‑in within a single transaction.  
     • Inconsistent NFT voting power calculation functions that can be exploited to set vote weight to zero or artificially reduce the total voting power (thus amplifying individual influence).  
     • Unsynchronized vote snapshots, duplicate voting via token transfers, bypass of direct voting restrictions via delegation, and proposals that either remain open indefinitely or get approved before tokens exist.  
     • Decimal conversion issues in token sales and circumvention of per‑user purchase limits by splitting transactions.  
   - In lending protocols:  
     • Liquidation may be triggered prematurely (for example, using an accepted timestamp instead of the last repayment timestamp) or might fail to liquidate a borrower due to errors in managing collateral records.  
     • Debt closures without real repayments, misdirected repayments (even to the zero address), and infinite loan rollovers can all lead to systemic risk.  
     • Repayments might be applied only to the current outstanding loan, causing misallocations.  
   - In liquidation processes:  
     • Lack of sufficient liquidation incentives (especially for small positions) can let bad debt accumulate.  
     • Users might over‑withdraw collateral, leaving too little to cover adverse movements.  
     • Partial liquidations can bypass bad debt handling if certain thresholds (like remaining margin) are not re‑evaluated correctly.  
     • Other issues include disrupted collateral priority, repayment misallocation when borrower identities change, an overly narrow gap between borrow LTV and liquidation thresholds, and improper handling of accrued yield and positive PnL.
   - Bad debt incorrectly preserved in the system.
   - Liquidation debt removal values exceeding actual user collateral value.
   - First deposit/donation attack vulnerabilities where initial small deposits establish manipulated exchange rates.
   - Variables that can be set to zero, limiting withdrawals to only already-paid assets in batches.
   - Reward distribution mechanisms ignoring the actual duration of user deposits.
   - User scores can be manipulated back and forth to game the system.
   - Lack of constraints allowing users to delegate voting rights and then vote again, manipulating weight.
   - Voting rights calculated from current time rather than fixed historical blocks.
   - Expired vote staking lock periods without timely delegation revocation causing tokens to be permanently locked.
   - Missing ratio checks between pool y and x values using existing functions.
   - Failure to reset voting power when gauges are removed.
   - Lock period extensions that are excessively long.

7. **Reentrancy, Front‑running, and Denial of Service Risks**  
   - Absence of standard reentrancy protection designs (including protection against cross‑function reentrancy and ERC777 hook-induced vulnerabilities).  
   - State update order issues that provide windows for reentrant calls.  
   - Front‑running vulnerabilities that enable attackers to manipulate prices or state (for example, by using a manipulated TWAP or sandwich attacks).  
   - Unbounded iterations in loops that may cause Denial of Service (DoS) conditions.  
   - In Uniswap V3 swap callbacks (UniswapV3SwapCallback), sending output tokens before completing the callback routine may allow reentrancy and state manipulation.  
   - In lending and liquidity deployment, insufficient TWAP protection or sole reliance on a single price source further expose the system to front‑running and sandwich attacks.
   - Array length increases leading to DoS attacks due to gas limits.
   - Message path blocking due to insufficient minimum remaining gas verification for storing failure messages.
   - State modifications in staticcall contexts causing reverts.
   - Flash loans creating abnormal pool states leading to irregular fund dumps.

8. **Module Call, Upgrade Configuration, and Initialization Vulnerabilities**  
   - Errors in module calls and delegatecalls--for example, setting immutable module addresses in the constructor or failing to verify cross‑module dependencies adequately.  
   - Mismatched or misconfigured constructor parameters and imprecise cross‑contract or cross‑module data transmissions.  
   - Defects in upgrade scripts, deployment, initialization, and configuration management (including loose Namespace registration and weak core system permissions, as well as controller or wallet initialization mistakes).  
   - Cross‑chain deployment, state variable resets, and upgrade processes may introduce security risks if not handled with strict controls.  
   - In liquidity management, failure to revoke old router approvals during updates or overly lax TWAP parameter configurations can be exploited for rug‑pulls or retroactive fee increases.
   - Delegation of funds not considering zero address cases.
   - Lack of state validation checks after complex operations.
   - Incompatibilities between vaults and vaults not fully compliant with ERC4626 standards.

9. **Fund Management, Fee Calculation, and Reward Distribution Errors**  
   - Improper parameter settings in settlements, refunds, and overall fund flows.  
   - Errors in asset and share conversion, exchange operations, liquidation reward distribution, and related fund flows (including miscalculations in commissions, discounts, and referral rewards).  
   - Inconsistencies in calculating referral rewards, incentive distributions, yield fees, and overall PnL.  
   - Unclear rules for fund locking or asset ownership may result in malicious asset extractions or faulty reward distribution (notably in systems using ERC20 rebasing or YieldBox conversions).  
   - In liquidity management, for example, native reward distributions may leave small remainders permanently locked due to integer arithmetic, and retroactive adjustments to management fees on pending LP rewards can unjustly reduce provider rewards.
   - Input parameters being used for different fund purposes than intended.
   - Vault exchange rates that can only increase but never decrease.
   - Unbalanced deposits into UniV3 pools where unused tokens are neither returned nor accounted for.
   - Token exchange contracts not accurately calculating and returning expected vs. actual differences.
   - Inaccurate weight processing affecting distributions.
   - addCollateral function not properly validating parameters, enabling unlimited borrowing and user fund theft.

10. **Token Approval and Contract Call Errors**  
    - Missing necessary ERC20/ERC721 token approvals.  
    - Errors in specifying target addresses, debit accounts, or token transfer parameters during contract calls.  
    - When updating critical contract addresses (such as routers) or swapping dependencies, failure to revoke old unlimited approvals leaves tokens vulnerable to unauthorized transfers.
    - Ignoring non-standard ERC20 transfer return values.

11. **External Dependency, Network Configuration, and Security Issues**  
    - Incorrect assumptions about third‑party contract interfaces, external oracle dependencies, or price data (for example, returning empty or stale data, or employing incorrect price values in calculations).  
    - Insufficient validation in external interface calls, which can lead to dangerous reliance on inaccurate data.  
    - In cross‑chain bridges and cross‑domain calls, misconfigured fee or gas parameters--and even overly exposed node ports--can lead to security vulnerabilities.  
    - Underlying data structures (such as MerkleDB) may have inherent security issues.  
    - For external oracles like Chainlink, specific concerns include:  
      • Not checking for stale prices by overlooking the updatedAt timestamp.  
      • Failing to verify L2 sequencer status on L2 chains.  
      • Assuming a uniform heartbeat across different feeds instead of using feed‑specific data.  
      • Not validating that price feeds update frequently or correctly handle decimal precision.  
      • Inadequate request confirmations vis‑à‑vis chain re‑org depths, use of incorrect oracle addresses, potential for front‑running oracle updates, and unhandled oracle call reverts or depegging events.  
      • For randomness oracles, allowing bets after the randomness request or permitting re‑requests can undermine fairness.
    - Ignoring oracle update timestamps leading to using stale data.
    - Relying on Curve pool instant prices which are easily manipulable.
    - Using single-sided valuations, allowing cached value manipulation for excessive borrowing or unfair liquidations.

12. **Language‑specific and Low‑level Implementation Vulnerabilities**  
    - Issues unique to Solidity inline assembly and low‑level EVM code.  
    - Memory corruption caused by not updating the Free Memory Pointer (FMPA) promptly, or by using incorrect memory offsets (as seen in buffer initialization problems).  
    - Using assembly instructions (e.g., add, sub, mul) without proper overflow/underflow detection; also, using 256‑bit arithmetic to perform operations intended for smaller types (such as uint128) may bypass expected safety checks.

13. **Trade Execution and Slippage Vulnerabilities**  
    - Swap functions that do not allow users to specify a minimum acceptable output (minTokensOut) or that hard‑code the slippage parameter (e.g., 0), leaving trades vulnerable to sandwich attacks and adverse execution.  
    - Not providing a user‑defined deadline, which can result in trades executing under unfavorable conditions if delayed.  
    - Incorrect slippage calculations--for example, computing slippage based on internal LP token values instead of the actual user‑provided amounts--or applying slippage protection only to intermediate steps while leaving the final output unprotected.  
    - Mismatches in fixed precision (such as returning a 6‑decimal value) against the target token's actual decimals can cause the slippage protection to fail.  
    - In minting operations, calculating synthetic token amounts from asset reserves without allowing users to set an acceptable slippage range exposes users to infinite slippage risk.  
    - On‑chain slippage calculations (e.g., using on‑chain estimations) can be manipulated by adversaries, so user‑calculated values (often performed off‑chain) should be used in transactions.  
    - Hard‑coded fee tiers in systems like Uniswap V3 or zero slippage requirements (demanding exact outputs) can lead to transaction reversions, DoS conditions, or severe losses under volatile market conditions.
    - Accepting high slippage, allowing attackers to manipulate pool imbalances and cause losses for all depositors.        """
    def vul_prompt_inline_assembly():
        return """
        1. **Memory Corruption from External Calls**  
        When saving data using inline assembly, if the Solidity Free Memory Pointer (FMPA) isn't updated promptly, data returned from external calls may write to the current FMPA location, overwriting existing data. For example, in the HasherImpl contract, after writing variables a and b to memory without updating FMPA, infoRetriever.getVal()'s return data overwrites a stored at 0x80, causing incorrect hash calculation.

        2. **Assuming Unchanged Free Memory Pointer Address**  
        In inline assembly, the first segment retrieves FMPA and assumes it remains constant as the starting point for hash calculation. However, Solidity automatically updates FMPA during external calls, causing keccak256 to operate on incorrect memory addresses and ranges. This incorrect assumption leads to hash operations computing wrong data or incorrect ranges.

        3. **Memory Corruption Due to Insufficient Allocation**  
        In ENS's Buffer contract, if insufficient memory is reserved during buffer initialization (e.g., omitting 32-byte offset), subsequent data writes (like append operations) may overwrite adjacent variables. For instance, Buffer.init function only uses mstore(0x40, add(ptr, capacity)) to update FMPA, whereas it should reserve an additional 32 bytes for buffer data to prevent overwriting adjacent variable foo's length.

        4. **External Call to Non-Existent Contract**  
        When using low-level calls (like staticcall) to addresses without deployed code (e.g., regular EOAs), the call might succeed but return unexpected data. For example, the WalletVerifier contract doesn't check extcodesize, leading to successful calls with incorrectly interpreted return data when given EOA addresses, causing signature verification errors.

        5. **Overflow/Underflow During Inline Assembly**  
        When using add, mul, sub instructions in inline assembly, extreme value calculations can easily overflow without detection due to the lack of Solidity's built-in overflow/underflow protection. For instance, in DexPair contract's getSwapQuote function, adding 1 to type(uint256).max may overflow (returning 0) without triggering checks.

        6. **Uint128 Overflow Evades Detection Due to Inline Assembly Using 256 Bits**  
        When function parameters use uint128 but inline assembly performs arithmetic operations in 256 bits, overflow detection becomes ineffective. For example, in DexPair's getSwapQuoteUint128 function, even with addition and comparison checks, passing maximum uint128 value won't trigger lt check due to internal 256-bit operations, resulting in incorrect values. Solutions include using addmod to limit operation range or additional checking of return values outside assembly.
        """
    def vul_prompt_chainlink():
        return """
        1. **Not Checking For Stale Prices**  
        Smart contracts that call Chainlink’s latestRoundData() without verifying the updatedAt timestamp (e.g., omitting the check “if (updatedAt < block.timestamp - 3600)” as shown in the error snippet) risk using outdated prices and must enforce a freshness check per the feed’s heartbeat.

        2. **Not Checking For Down L2 Sequencer**  
        When using Chainlink data on L2 chains (like Arbitrum), failing to check the L2 Sequencer status may result in using data that appears fresh but is untrustworthy; thus, contracts should validate the sequencer’s status before relying on the feed, as advised in Chainlink’s official documentation.

        3. **Same Heartbeat Used For Multiple Price Feeds**  
        Assuming a uniform heartbeat interval across multiple price feeds (e.g., using a 1-hour check for one and a 24-hour check for another, as seen in JOJO’s audit example) can lead to errors, so each feed must be validated against its own heartbeat value from Chainlink’s listing.

        4. **Oracle Price Feeds Not Updated Frequently**  
        Selecting a price feed with infrequent updates can disconnect contract computations from actual market prices, hence developers and auditors should prioritize feeds with high update frequency, low heartbeat intervals, and small deviation thresholds to ensure timely data.

        5. **Request Confirmation < Depth of Chain Re-Orgs**  
        Using a REQUEST_CONFIRMATIONS value that is lower than the common chain re-org depth (e.g., a default of 3 on Polygon, where re-orgs may exceed 3 blocks) exposes randomness requests (like VRF) to manipulation, so the confirmation count must be adjusted based on the chain’s characteristics.

        6. **Assuming Oracle Price Precision**  
        Contracts that assume a uniform decimal precision across oracles (noting differences, for instance, between non-ETH feeds using 8 decimals and certain ETH feeds or exceptions like AMPL/USD using 18 decimals) risk miscalculations; developers should dynamically retrieve the precision via the decimals() method.

        7. **Incorrect Oracle Price Feed Address**  
        Hardcoding or misconfiguring oracle addresses (for example, documenting BTC/USD correctly but mistakenly initializing with an ETH/USD address) leads to incorrect data retrieval; auditing all addresses against Chainlink’s official lists and considering chain-specific differences is essential.

        8. **Oracle Price Updates Can Be Front-Run**  
        When Oracle updates are delayed (triggered only after significant price deviations), attackers might front-run price feed updates in operations like mint or burn by monitoring pending transactions, so measures such as small fees, deposit delays, and off-chain monitoring should be implemented to reduce such risks.

        9. **Unhandled Oracle Revert Denial Of Service**  
        If a Chainlink oracle call reverts (due to issues like multisig-feed shutdowns) and is not wrapped in try/catch, the contract may become DoSed or permanently frozen; thus, developers should handle exceptions and allow switching or updating of oracle addresses when necessary.

        10. **Unhandled Depeg Of Bridged Assets**  
        For bridged assets like WBTC priced solely via BTC/USD feeds, a depeg event may result in significant value discrepancies exploited by attackers (buying low and borrowing against inflated valuations), which necessitates additional feeds (such as WBTC/BTC) or depeg detection mechanisms to safeguard valuation.

        11. **Oracle Returns Incorrect Price During Flash Crashes**  
        In flash crash scenarios, Chainlink oracles might return a floor value (minAnswer) that does not reflect the true market price, allowing attackers to exploit mispricing in protocol operations; therefore, contracts should enforce that returned prices lie within the [minAnswer, maxAnswer] range and be paired with off-chain, multi-source monitoring.

        12. **Placing Bets After Randomness Request**  
        Allowing users to place bets or transactions after a randomness request (as in lottery applications) enables attackers to use the revealed randomness information for profitable, front-run betting, so betting actions should be frozen until the random number is delivered.

        13. **Re-requesting Randomness**  
        Permitting re-requesting of randomness opens the door for VRF providers to delay or alter the initial unfavorable result (by rejecting the first and returning a favorable random number later), thereby compromising fairness; contracts must restrict re-requests in line with Chainlink VRF’s security best practices.

        """
    def vul_prompt_dao():
        return """
1. **Flash Loan Manipulation of Proposal Decisions**  
   An attacker can use flash loans to borrow a large amount of voting tokens, deposit them in the governance pool, delegate the voting power to a slave contract, cast votes to hit quorum and lock the proposal in a single transaction (as shown in the example where deposit, delegate, vote, then immediate withdrawal occur), and then retract the delegation to repay the loan; to mitigate, restrict withdrawals or undelegations after proposals lock and prevent multiple critical state transitions in the same block.

2. **Attacker Sabotaging User Voting Power**  
   Due to inconsistent behavior between getNftPower (which returns 0 when block.timestamp is at or below powerCalcStartTimestamp) and recalculateNftPower (which recalculates using the 0 value at the threshold), an attacker can repeatedly call recalculateNftPower to erroneously set NFT voting power to 0 and drastically reduce totalPower, thereby disrupting vote distribution; ensuring both functions behave consistently at the boundary and that NFT configurations are properly initialized is essential.

3. **Amplifying Individual Voting Power by Reducing Total Vote Weight**  
   When non-existent tokenIds trigger getNftPower to return near-maximum power and recalculateNftPower subtracts a full maximum value then adds a lower new value, repeated calls can gradually decrease totalPower, unintentionally amplifying individual vote shares (as demonstrated in the provided Solidity snippet); validate tokenId existence and tighten the “first update” logic to prevent abuse.

4. **Incorrect Snapshot of Total Voting Power at Proposal Creation**  
   If snapshots are taken without updating NFT voting power (e.g., via updateNftPowers), the recorded totalPower (as seen in the createNftPowerSnapshot example reading nftContract.totalPower()) may be outdated, resulting in misrepresentation of individual voting weights; ensure that all NFT voting powers are updated before snapshotting or automate state updates during snapshot creation.

5. **Failure to Reach Quorum Due to Miscalculated Vote Totals**  
   In DAOs combining ERC20 and ERC721 voting, if the NFT component’s vote power (ERC721Power.totalPower) drops to 0 while a fixed totalPowerInTokens remains unchanged, the ERC20 votes can become diluted, making quorum unreachable; dynamically adjust the NFT vote total rather than relying on a static number to reflect current voting power accurately.

6. **Exploiting Delegated Treasury Voting Power for Extra Influence**  
   Some DAOs delegate treasury (library) vote power to expert users, but if this delegated power is transferable or further delegable, attackers could accumulate extra influence beyond what was intended; restrict further transfers or redelegations of treasury voting rights and explicitly define boundaries for their use in proposals.

7. **Bypassing Voting Restrictions Through Delegation**  
   Even if proposals restrict direct voting by specific users, attackers can delegate their voting power to another address (or use multiple addresses), thereby circumventing the restrictions—as illustrated by a scenario where a banned user (SECOND) delegates to SLAVE who casts the vote; incorporate delegation relationship checks and record original voter identities to enforce vote restrictions.

8. **Repeated Voting Using the Same Tokens (Vote Duplication)**  
   When voting is permitted on an address basis, users may transfer tokens among multiple addresses and vote repeatedly, thereby exploiting a loophole despite token lock mechanisms (as shown in the code snippet that only checks msg.sender, not the source of tokens); implement voting snapshots or ensure locked tokens cannot be reused for additional votes across different addresses.

9. **Indefinite Proposals Leading to Permanently Locked Tokens**  
   Proposals without a clear deadline can remain active indefinitely, causing tokens locked during voting to never be released for other uses; establish fixed proposal deadlines or timeout mechanisms that force an automatic transition to a failed state, coupled with periodic cleanup of expired proposals.

10. **Proposal Approval Before Voting Tokens Are Issued**  
   In early DAO stages, when no voting tokens exist and both individual balances and total supplies are 0, validations based on token holdings can malfunction (as shown by conditions improperly passing due to 0 comparison), enabling proposals to pass without genuine backing; disable governance operations until tokens are issued and add explicit checks to handle 0-supply states.

11. **Decimal Conversion Vulnerability in Token Sales**  
   In token sale proposals, if different tokens have varying decimals (e.g., 18 vs. 6) and the conversion function (from18) incorrectly converts an amount to 0—illustrated in the _sendFunds example—an attacker can exploit this to bypass payment requirements and illicitly receive DAO tokens; enforce strict validation during decimal conversion and allow payments in the token's native decimal format.

12. **Circumventing Per-User Purchase Limits with Multiple Small Transactions**  
   If purchase checks only enforce limits on individual transactions (ignoring cumulative totals), an attacker can bypass the maxAllocationPerUser by executing several smaller buys, as the purchase total is not aggregated over the sale period; track cumulative purchases per user and, if necessary, impose limits based on daily or total aggregated amounts.

13. **Heuristic Issues in Identifying Vulnerabilities**  
   Auditors should consider whether cumulative effects of multiple small transactions equate to a single large one, inspect for subtle differences in conditional checks (such as "<" versus "<="), verify that the total stored value always matches the sum of individual contributions, and test edge cases like non-existent identifiers or minimal value operations to identify rounding or overflow errors; comprehensive testing and cross-checks of inter-contract interactions are advised to ensure no inconsistencies remain.
        """
    def vul_prompt_lending():
        return """
1. **Liquidation Before Default:** Liquidation should only occur after a genuine default (e.g., overdue repayment or insufficient collateral), yet in cases like Sherlock’s TellerV2—where the function returns the loan’s accepted timestamp instead of the last repayment timestamp—and Hats Finance Tempus Raft—where an unchecked collateralToken parameter permits price miscalculation—the conditions enable premature liquidation before the due repayment date.  

2. **Borrower Can't Be Liquidated:** In certain implementations such as Sherlock TellerV2, neglecting to check the return value of OpenZeppelin’s EnumerableSetUpgradeable.AddressSet.add() allows the borrower to overwrite existing collateral records (even with a zero amount), thereby preventing proper liquidation on default.  

3. **Debt Closed Without Repayment:** Some systems, as seen in a DebtDAO audit, allow borrowers to call the close() function with a non-existent credit ID that returns a default Credit structure (with principal 0), bypassing repayment validations and erroneously marking the loan as repaid while decrementing an internal counter.  

4. **Repayments Paused While Liquidations Enabled:** In platforms like Sherlock’s Blueberry example, repay() enforces an isRepayAllowed() check while liquidate() does not, which permits liquidation operations even when repayments are deliberately paused, placing borrowers at an unfair disadvantage.  

5. **Token Disallow Stops Existing Repayment & Liquidation:** When governance changes disallow a previously permitted token (as seen in BlueBerry updates), loans using that token for repayment or as collateral might become incapable of proper repayment or liquidation, creating inconsistencies that jeopardize both borrowers and lenders.  

6. **Borrower Immediately Liquidated After Repayments Resume:** If market conditions deteriorate during a pause in repayments, then—as soon as repayments are re-enabled without a grace period—the unchanged liquidation thresholds can trigger immediate liquidation, leaving borrowers with little to no opportunity to recover.  

7. **Liquidator Takes Collateral With Insufficient Repayment:** Partial liquidation calculations that rely solely on the ratio from a specific debt position—for instance, using share/oldShare in Blueberry—can let liquidators pay a minimal portion of the debt while unjustifiably seizing a disproportionately large amount of collateral, ignoring the borrower’s entire debt profile.  

8. **Infinite Loan Rollover:** Allowing borrowers to extend (roll over) their loans indefinitely without imposing strict limits exposes lenders to prolonged credit risk and potential non-repayment, underscoring the need for capping the number or duration of rollovers.  

9. **Repayment Sent to Zero Address:** In examples like Cooler’s Sherlock audit, deleting loan records before executing the repayment transfer can reset critical fields (such as loan.lender) to the zero address, resulting in repayment funds being sent to (0) and permanently lost.  

10. **Borrower Permanently Unable To Repay Loan:** System logic errors or token disallowances that prevent the successful execution of a repay() call can leave borrowers incapable of repaying—forcing them into liquidation while also preventing lenders from recovering their funds.  

11. **Borrower Repayment Only Partially Credited:** When a borrower makes a lump-sum repayment covering multiple loans, if the system credits only the current loan without applying any overpayment to subsequent loans, it leads to partial repayments, excessive interest accrual, or misinterpreted default statuses.  

12. **No Incentive To Liquidate Small Positions:** With rising gas fees, liquidation fees for small underwater positions may be economically unattractive; consequently, liquidators might avoid these positions, allowing them to accumulate risk and threaten the platform’s overall solvency.  

13. **Liquidation Leaves Traders Unhealthier:** Certain liquidation algorithms may inadvertently worsen a borrower’s health by prioritizing the removal of lower-risk collateral, thereby leaving behind riskier positions and potentially setting the stage for subsequent, compounding liquidations.
        """
    def vul_prompt_liquidation():
        return """
Below is an extremely compressed list of the 35 liquidation code vulnerabilities in English—each described in 1–2 sentences without losing any original information (including descriptions and examples):

1. **Lack of Liquidation Incentive**  
   If the protocol does not offer sufficient rewards (e.g. bonus covering gas fees) for trustless liquidators, positions that are liquidatable may not be cleared in time, allowing them to worsen into insolvency.

2. **Small Positions with No Liquidation Incentive**  
   Without a minimum position size, numerous tiny positions yield low rewards, discouraging liquidators and causing an accumulation of small positions that increase bad debt risk.

3. **Profitable Users Withdrawing All Collateral**  
   Users with significant positive PNL may withdraw nearly all collateral—leaving minimal deposits such that if their PNL reverses, the remaining collateral is insufficient for liquidation and may even trigger panic reverts.

4. **Lack of a Bad Debt Handling Mechanism**  
   When liquidatable positions deteriorate into insolvent states, if the system does not enforce trusted liquidators, use an insurance fund, or share bad debt among users, liquidators have no economic incentive to act, potentially resulting in unrecoverable liabilities.

5. **Partial Liquidation Bypassing Bad Debt Handling**  
   In partial liquidations, a liquidator may choose not to close the entire position—bypassing a check (e.g. only triggered when remaining margin < 0) and thereby letting residual bad debt accumulate.

6. **No Support for Partial Liquidation of Large Positions**  
   If the protocol only allows full liquidation, a single liquidator might be unable to supply enough debt tokens to clear large (whale) positions, making them unfeasible to liquidate without relying on limited flash loans.

7. **Liquidation DoS via Iteration and Array Reordering**  
   (a) Malicious users can flood the system with many small (dust) positions, exhausting gas in for-loop iterations, and (b) using "swap and pop" for removals can reorder arrays and cause out-of-bound errors when the loop relies on the original ordering.  
   
8. **Front-Running to Prevent Liquidation**  
   If key variables (e.g. position state, cooldown, nonce) are user-controlled, an attacker can front-run the liquidation transaction by adjusting them, causing a liquidatable position to appear safe before the liquidation is finalized.

9. **Blocking Liquidation with Pending Withdrawals**  
   A user who creates pending withdrawal actions can reduce their effective balance to zero, ensuring that any subsequent liquidation attempt reverts due to insufficient funds, thereby obstructing the liquidation process.

10. **Malicious ERC721/ERC20 Callback Interference**  
   When using a "push" method to send tokens during liquidation, an attacker’s contract can deliberately revert in onERC721Received (or the ERC20 hook), forcing the entire liquidation to revert; using a "pull" or safe transfer method prevents this.

11. **Exploiting Yield Vaults to Block Collateral Seizure**  
   If the liquidation logic fails to account for assets deposited (and yield accrued) in a yield vault, an attacker can withdraw vault assets post-loan, leaving inadequate collateral during liquidation.

12. **Bad Debt Exceeding the Insurance Fund**  
   If the bad debt from a liquidation exceeds the size of the insurance fund, the liquidation may revert, leaving insolvent positions uncleared and accumulating systemic risk.

13. **Fixed Liquidation Reward Causing Reverts**  
   When a fixed bonus (e.g. 10%) is applied regardless of collateral amount, positions barely above the liquidation threshold (e.g. 110% collateral ratio) might cause insufficient funds for the bonus, leading to transaction reversion; dynamic adjustment or reward capping is necessary.

14. **Non-18 Decimal Collateral Issues**  
   Assuming 18 decimals for all tokens can miscompute values for tokens like USDC (6 decimals), potentially returning 0 or causing calculation errors during liquidation; therefore, proper normalization and conversion for token decimals is essential.

15. **Multiple nonReentrancy Locks Causing Reverts**  
   When liquidation logic spans multiple calls each guarded by nonReentrant modifiers, overlapping locks may trigger a revert—thus, the call flow must be carefully planned to avoid multiple simultaneous nonReentrancy invocations.

16. **Zero-Value Transfers Leading to Reverts**  
   Rounding errors or calculations that yield a transfer amount of 0 may cause tokens that disallow zero-value transfers to revert the whole transaction; pre-checking for a nonzero value before transfers can prevent this issue.

17. **Token Deny List Restrictions Interfering with Liquidation**  
   If the protocol "pushes" tokens (e.g. USDC) to an address that is on a deny list (frozen), the transfer will fail and revert the liquidation, so a "pull" model or pre-transfer checks for the recipient’s status are recommended.

18. **Inability to Liquidate When Only One Borrower Exists**  
   Some liquidation routines trigger only if multiple borrowers exist; if only a single borrower is present, the clearing loop never starts, leaving an otherwise liquidatable position uncleared.

19. **Liquidation Calculation Errors**  
   (a) Incorrectly using debt token amounts with differing decimals (e.g. using USDC’s value to compute a WETH reward) can misprice the liquidator bonus, and (b) faulty protocol fee calculations based on seized collateral can disrupt incentives; both require precise unit conversion and fee structure handling.

20. **Excluding Liquidation Fees from Minimum Collateral Requirement**  
   Failure to account for future liquidation fees when checking a position’s collateral may result in insufficient actual collateral during liquidation, triggering errors or bad debt—thus, fee obligations must be incorporated into safety checks.

21. **Not Counting Earned Yield in Collateral Valuation**  
   If accrued yield on deposited collateral is omitted from the total collateral value during liquidation calculation, positions may be unfairly liquidated prematurely, so all earned yield must be included.

22. **Positive PNL Not Added to Collateral Value**  
   Omitting the offset of positive PNL from the debt by not incorporating it into collateral value can cause profitable positions to be liquidated, effectively stripping users of gains; liquidation logic should factor in a user’s PNL.

23. **No Grace Period after L2 Sequencer Recovery**  
   Without a grace period after a failed L2 sequencer comes back online, stale or rapidly changing oracle prices may trigger immediate liquidations before users can act to remedy their positions.

24. **Accruing Interest During Protocol Pause**  
   If the protocol continues to accrue borrowing interest during a pause (when repayments are halted), borrowers may be unfairly pushed over the liquidation threshold once the pause ends, so interest accrual should be suspended.

25. **Liquidation Proceeds While Repayments Are Paused**  
   Continuing liquidation operations during periods when repayments are paused can force borrowers into liquidation due to unchecked debt accumulation, creating a misalignment between repayment and liquidation conditions.

26. **Delayed Liquidation from Stale Fee and Yield Data**  
   When the isLiquidatable check does not refresh interest, funding, and yield data prior to evaluation, liquidations may be delayed despite deteriorating position conditions; timely data updates are critical to accurate liquidation triggers.

27. **Losing Unrealized Gains and Rewards in Liquidation**  
   Liquidation processes that fail to first settle an account’s positive PNL, accrued yield, or pending rewards effectively strip the user of those benefits, leading to an unfair loss upon liquidation.

28. **Omitting Internal Swap Fees during Liquidation**  
   If an internal asset swap during liquidation does not implement minimum price expectations (slippage settings) or charge swap fees, the liquidator and protocol may receive far less than anticipated, upsetting the intended incentive balance.

29. **Oracle Sandwich Exploits Enabling Cheap Self-Liquidation**  
   Attackers can deploy flash loans to inflate borrowing, trigger an oracle update, and then quickly self-liquidate at a favorable mid-update price—akin to a sandwich attack—thus paying less debt for full collateral recovery; this necessitates sufficient fees, risk limits, and conservative oracle designs.

30. **Deterioration of Borrower Health Score Post-Liquidation**  
   If, after liquidation, the remaining position is left with a worse health ratio—possibly because the liquidator selectively seizes higher-quality collateral—the borrower becomes prone to repeated liquidations, so post-liquidation health must improve relative to pre-liquidation levels.

31. **Disrupted Collateral Liquidation Priority**  
   Allowing dynamic modification or unguarded reordering of collateral priorities (e.g. for high-volatility assets) can break the intended order of liquidation, leading to improper collateral seizure; priority order functions must ensure strict data consistency and integrity.

32. **Repayment Misallocation from Borrower Replacement**  
   In scenarios where a liquidatable position is replaced (or bought out) by a healthier borrower, repayments might be erroneously credited to the original borrower instead of the new owner, reducing debt incorrectly; repayment flows must strictly match the current borrower’s address.

33. **No Gap Between Borrow LTV and Liquidation Threshold**  
   A narrow gap between the initial borrowing LTV and the strict liquidation LTV leaves little room for market fluctuations, potentially forcing immediate liquidation upon opening a position; maintaining a clear safety buffer is crucial.

34. **Interest Accumulation During Auction Periods**  
   If interest continues to accrue while a liquidatable position is in auction, the additional debt can distort auction outcomes and unfairly penalize the borrower, so interest accrual must be halted once the auction starts.

35. **Lack of Slippage Controls in Liquidation Swaps**  
   Without allowing liquidators to set minimum expected return amounts, market swings or MEV attacks during internal swaps may result in considerably lower rewards than anticipated, thus configurable slippage settings are needed during such exchanges.
        """
    def vul_prompt_liquidity_manager():
        return """
1. **TWAP Check Omission in Liquidity Deployment via setPositionWidth**  
   In the setPositionWidth function, after claiming earnings and removing liquidity, the contract updates ticks based on the current pool.slot0 and redeploys liquidity with _addLiquidity()—without a TWAP check—allowing an attacker to front-run by using large USDC trades to deplete WBTC from the pool (manipulating the price) and then back-run by selling WBTC at an inflated price, which drains the protocol's assets.

2. **TWAP Check Omission in Liquidity Deployment via unpause**  
   In the unpause function, when the protocol is reactivated and liquidity is re-added without a TWAP check, an attacker can front-run by using USDC to purchase WBTC (driving up its price) while the protocol is paused and then back-run after unpause to offload WBTC at an exaggerated price, causing significant losses to the protocol.

3. **Owner Rug-Pull Risk Through Invalid TWAP Parameter Settings**  
   The protocol permits the owner to arbitrarily adjust TWAP parameters (maxDeviation and twapInterval); if set to extreme values, these parameters render TWAP checks ineffective, enabling the owner to re-deploy liquidity and trigger retrospective fee mechanisms that unfairly deduct higher fees from pre-accumulated rewards, effectively executing a rug-pull.

4. **Permanent Token Lock Due to Rounding Errors in Reward Distribution**  
   During native reward distribution, fees for call, beefy, and strategist are calculated via integer division that may leave a small remainder unallocated (as shown in the code splitting nativeEarned), causing tokens to be permanently retained in the contract; this can be remedied by computing beefyFeeAmount as the leftover balance after subtracting the other fees.

5. **Risk of Unrevoked Token Approvals When Updating Router Address**  
   When the owner updates the unirouter address via the setUnirouter function, the protocol fails to revoke the unlimited token approvals previously granted to the old router (as set in _giveAllowances()), leaving the old router with perpetual access to protocol tokens and risking asset compromise if that router becomes insecure.

6. **Retroactive Fee Increase on Pending LP Rewards**  
   Since LP rewards are settled only at harvest, an owner can increase the management fee before harvest occurs, thereby applying the new, higher fee retroactively to rewards accumulated under a lower fee regime—effectively siphoning extra value from liquidity providers; the fix is to settle pending rewards before any fee updates occur.

7. **Maintaining Critical CLM Invariants**  
   The protocol must enforce invariants such as ensuring sqrtPriceX96 stays within valid ranges, deposits return >0 LP shares, withdrawals return >0 tokens, and tokens don't become permanently trapped due to rounding errors—all of which can be verified via invariant-based fuzz testing (e.g., an Echidna test ensuring a strategy’s native token balance remains zero).
        """
    def vul_prompt_signature_replay():
        return """
1. **Missing Nonce Replay:** The signature is generated solely from fixed parameters (e.g., kycRequirementGroup, user, deadline) without a nonce, so if a user’s KYC status is later revoked, an attacker can replay the previously valid signature (as shown in the addKYCAddressViaSignature example); to mitigate, include a nonce in the signed message and update it on use (see ERC20Permit’s _useNonce implementation).  

2. **Cross Chain Replay:** The signature mechanism is vulnerable because the message hash (e.g., of a UserOperation) does not include the chain_id—allowing a valid signature on one chain to be replayed on another; mitigation requires adding the chain_id in the signed message and employing EIP-712 for chain-specific verification.  

3. **Missing Parameter:** Critical parameters (such as tokenGasPriceFactor) are omitted from the signed data, letting attackers manipulate these parameters (for example, altering gas refund calculations in the encodeTransactionData and handlePaymentRevert examples); the fix is to ensure all key execution parameters are included in the signed message before execution.  

4. **No Expiration:** Signatures without an explicit expiration time remain valid indefinitely (as seen in NFTPort’s call function example), which can lead to replay attacks or unauthorized long-term actions; the remedy is to include an expiration timestamp in the signed data and check it during execution (e.g., in the updated _hash and RequestMetadata examples).  

5. **Unchecked ecrecover() Return:** Since Solidity’s ecrecover() returns the zero address on an invalid signature (illustrated in the validOrderHash example), failing to verify that the recovered address is non-zero allows attackers to bypass signature checks; therefore, explicitly check that ecrecover() does not return the zero address before proceeding.  

6. **Signature Malleability:** Due to the properties of elliptic curve cryptography, an original signature’s [v, r, s] values can be altered into an equivalent valid signature (as demonstrated in the 65-byte signature example), enabling attackers to forge alternative signatures; using libraries like OpenZeppelin’s ECDSA.sol with proper s-value range checks and tryRecover functions prevents this malleability issue.
        """
    def vul_prompt_univ3():
        return """
1. **DOS Vulnerability in Pool Initialization:**  
   Attackers can pass extreme or harmful initialization parameters (e.g. far-future timestamps or unreachable tick constraints) to lock the pool in an unusable state, preventing liquidity provision and swaps until unrealistic conditions are met; the pool initialization function must validate all parameters to prompt secure operations.

2. **Missing Slippage and Deadline Protection:**  
   Without user-defined slippage limits and deadlines, attackers can sandwich trades or indefinitely delay transactions in the mempool, forcing users into manipulated and unfavorable exchange rates; swap functions must enforce maximum price deviation and transaction expiry to protect users.

3. **Reading Price Directly from slot0:**  
   Relying solely on the instantaneous pool state from slot0 makes the protocol vulnerable to front-running, as a single large trade can drastically skew the reported price; instead, the price lookup must incorporate smoothing methods like time-weighted averages to mitigate manipulation.

4. **TWAP Oracle Stale Observation:**  
   By injecting uninitialized or malicious data into the observation array, attackers can corrupt the time-weighted average price (TWAP) oracle with fake historical values, resulting in distorted average prices; the oracle must validate each observation before using it in the TWAP calculation.

5. **UniswapV3SwapCallback() Reentrancy Risks:**  
   In a two-step swap process, sending output tokens before the caller’s UniswapV3SwapCallback() can allow attackers to reenter and manipulate state or drain balances; reentrancy guard mechanisms and rigorous state checks must be applied to secure the external callback.

6. **Low Liquidity Pool Price Manipulation:**  
   Aggregating prices from multiple pools that include low-liquidity markets lets an attacker manipulate a thin market with a small trade, skewing the aggregated price and impacting critical operations; the oracle should filter or weight pools to prevent low liquidity from disproportionately influencing the final price.

7. **SplitSwapper Oracle Manipulation via Fake Pool Deployment:**  
   If the oracle uses a default fee tier to look up a Uniswap V3 pool and no legitimate pool exists, an attacker can deploy a fake pool with extreme price parameters, leading to highly skewed swap calculations; the oracle must verify that any looked-up pool is genuine and sufficiently liquid before using its price data.

8. **Fee Growth Underflow Handling in tick::get_fee_growth_inside():**  
   Using checked subtraction instead of wrapping arithmetic in fee growth computations causes legitimate underflows to revert, potentially locking positions and stopping fee updates; the function must use wrapping subtraction (or equivalent logic) to correctly calculate fee growth as intended.

9. **Misconfigured sqrtPriceLimitX96 in Dual Swap Execution:**  
   Reusing the same sqrtPriceLimitX96 parameter across swaps on different pools—with distinct liquidity and acceptable price ranges—can trigger reverts or misapply slippage constraints; each swap should employ its own correctly configured price limit or rely on alternative checks like amountOutMinimum.

10. **Q96 Fixed-Point Multiplication Overflow:**  
    Multiplying two Q96 fixed-point numbers without utilizing full-width (e.g. 256- or 512-bit) intermediate storage and proper shifting can cause an overflow since the product may require up to 192 bits; therefore, dedicated math libraries (like Uniswap’s FullMath) must be used to handle full-width multiplication and maintain precision.
        """
    def vul_prompt_slippage():
        return """
Below is an extremely compressed summary of the slippage-related vulnerabilities in 1–2 sentences each, preserving all original details, examples, and recommendations:

1. **No Slippage Parameter:**  
   When a swap function (e.g. using swapExactTokensForTokens with a hardcoded 0 for minTokensOut) does not allow users to specify a minimum acceptable output, it exposes them to sandwich attacks in volatile or low-liquidity scenarios; developers must let users set a safe, adjustable minTokensOut (or use a sensible default).

2. **No Expiration Deadline:**  
   Not providing a user-defined deadline—opting instead for a hardcoded maximum (such as type(uint256).max or block.timestamp)—can cause trades to be executed after adverse price movements (as shown by the example lacking slippage control), so a deadline parameter is critical to prevent delayed execution risks.

3. **Incorrect Slippage Calculation:**  
   Calculating slippage from internal LP token values (as seen in the OpenZeppelin Origin Dollar example) rather than using the directly provided user amount can lead to erroneous outputs and insufficient token returns; the logic must properly convert units and use the user-specified minimum output directly.

4. **Mismatched Slippage Precision:**  
   Using a fixed precision (like returning a 6-decimal value for minTokenOut) without adjusting for the target token’s decimals can render slippage protection ineffective when tokens differ in decimal places; hence, the computed slippage must be scaled according to the output token’s precision.

5. **Minting Operation Leading to Infinite Slippage Risk:**  
   In minting functions (e.g. mintSynth) that calculate synthetic token amounts from asset reserves without a slippage parameter, attackers can manipulate reserve values to create infinite slippage risk; such swap-like operations must allow users to define an acceptable slippage range to secure the minting process.

6. **Slippage Parameter for Intermediate Steps Only, Not Final Output:**  
   In multi-step operations (like the Olympus update where liquidity is first exited with a minTokensOut check but later adjusted for treasury extraction), enforcing slippage only on intermediate steps may leave the final output below expectations; therefore, slippage protection must be applied and verified in every step, including at the final output stage.

7. **On-Chain Slippage Calculation Can Be Manipulated:**  
   Relying on on-chain estimations (e.g. via Quoter.quoteExactInput) to compute minTokensOut is vulnerable to manipulation (such as by sandwich attacks) since the simulated trade can be preempted, so users should calculate their required slippage off-chain and supply that value in the transaction.

8. **Hard-coded Slippage May Freeze User Funds:**  
   Hard-coding a very low slippage tolerance (e.g. requiring a 99.00% minimum return as in strict require checks) can cause transactions to perpetually revert during high volatility, effectively freezing user funds; therefore, default slippage limits must be flexible and user-adjustable.

9. **Hard-coded Fee Tier in UniswapV3 Swap:**  
   Hardcoding a fee tier for UniswapV3 swaps risks selecting a pool with insufficient liquidity—even when other fee tiers are better—which can lead to unexpectedly high slippage; thus, the fee tier should either be passed as a parameter by the user or determined dynamically based on liquidity conditions.

10. **Zero Slippage Required:**  
    Requiring an exact (zero slippage) output—with no allowance for market fluctuations—inevitably leads to transaction reverts and forms a DoS condition in volatile circumstances; users must be permitted to set a reasonable non-zero slippage tolerance to successfully execute trades.
        """
    