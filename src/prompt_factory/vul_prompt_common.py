class VulPromptCommon:
    @staticmethod
    def vul_prompt_common_new(prompt_index=None):
        parameter_validation_list = [
            "Checks for parameter order or type errors (e.g., 'zero share' issues, incorrect parameter sequencing)",
            "Insufficient validation of input length, indices, format, and encoding",
            "Redundant or improper parameter checks that may allow unexpected values into the system",
            "Missing necessary modifiers, data validation, and boundary checks",
            "In certain trade and minting functions, validation for slippage parameters and transaction deadlines is neglected",
            "Missing validation of fund-related parameters allowing manipulation of funds",
            "Incorrect parameter order leading to unauthorized access",
            "Failure to validate transaction parameters in cross-chain communications",
            "Failure to check codehash against keccak256('') for non-existent contracts",
            "ETH value parameters not properly validated in payable functions",
            "Missing necessary ERC20/ERC721 token approvals",
            "Errors in specifying target addresses, debit accounts, or token transfer parameters",
            "When updating critical contract addresses, failure to revoke old unlimited approvals",
            "Ignoring non-standard ERC20 transfer return values"
            "Missing length consistency check when input consists of two arrays"
        ]

        arithmetic_calculation_list = [
            "Use of incorrect constants, ratio calculation errors, and imprecise mathematical formulas",
            "Decimal precision errors, rounding problems, and unit conversion mistakes",
            "Division, bit shift, exchange rate, or interest rate model miscalculations",
            "Confusion between 'shares' and 'amount' calculations",
            "Inaccuracies in calculating PnL, yield fees, fund flows, conversion rates",
            "Cumulative errors in recursive or multi-step conversions",
            "In inline assembly, using operations without Solidity's overflow/underflow protection",
            "Fixed-point multiplications without proper full-width intermediate storage",
            "Insufficient precision in mathematical utilities",
            "Using collateralShare instead of amount for liquidation threshold calculations",
            "Calculation overflows when handling large numbers",
            "Variable type errors causing insufficient fund burning",
            "Incorrect reward calculations leading to double-counting",
            "Insufficient precision when comparing accumulated fees",
            "Failure to account for price differences between ETH and staked ETH2"
        ]

        state_updates_list = [
            "Incorrect ordering of state updates or improper check sequences",
            "Inconsistent synchronization between global and local data",
            "Loss of historical records and vulnerabilities within freezing or reward mechanisms",
            "'Incorrect determination methods' that can be manipulated",
            "In inline assembly, failure to update the Free Memory Pointer",
            "In DAO implementations, unsynchronized snapshots and NFT voting power updates",
            "State variables are prematurely updated before asset transfers",
            "Asynchronous reserve and balance updates causing double counting",
            "Incorrect state reset handling due to time-related inconsistencies",
            "Allowing voting rights to be transferred, harming other participants",
            "Not destroying tokens after liquidation procedures",
            "System shutdowns that stop updating user reward data"
        ]

        consistency_list = [
            "Inconsistencies between token accounting systems leading to double counting",
            "Reward calculations double-counting unsettled reserves",
            "Reserve and balance not updated in real-time synchronization",
            "Fee double-counting due to inconsistent fee accounting mechanisms",
            "Inconsistent time reset handling across different contract components",
            "Inconsistent application of penalty calculations",
            "Elasticity amount variables incorrectly applied in liquidation",
            "Inconsistent handling of price data between different components",
            "Inconsistent validation processes across similar functions",
            "Inconsistent initialization of time_weight when adding new gauges",
            "Inconsistent behavior between original and wrapper contracts",
            "Variable states lack business-level endpoint/phase validation, leading to state inconsistencies"
        ]

        permission_control_list = [
            "Lack of necessary access permission checks",
            "Vulnerabilities in authorization logic and role management",
            "In cross-module scenarios, insufficient authorization controls",
            "Public interfaces and functions may be exploited by arbitrary calls",
            "Signature/replay vulnerabilities due to lacking nonce or chain_id",
            "Failure to properly check the result of ecrecover",
            "Updating router address without revoking old unlimited approvals",
            "Cross-chain entity address forgery due to inadequate verification",
            "Borrowers unable to update market parameters due to insufficient permissions",
            "Blacklisted users bypassing sanctions by transferring funds in parts"
        ]

        business_logic_list = [
            "Errors in deployment state determination and edge case handling",
            "Insufficient protection measures in critical processes",
            "Inconsistencies in multi-stage processes",
            "Bad debt incorrectly preserved in the system",
            "Liquidation debt removal values exceeding actual collateral value",
            "First deposit/donation attack vulnerabilities",
            "Variables that can be set to zero limiting withdrawals",
            "Reward distribution mechanisms ignoring deposit duration",
            "User scores can be manipulated back and forth",
            "Lack of constraints in voting rights delegation",
            "Voting rights calculated from current time rather than fixed blocks",
            "Expired vote staking lock periods without revocation",
            "Missing ratio checks between pool values",
            "Failure to reset voting power when gauges are removed",
            "Lock period extensions that are excessively long"
        ]

        reentrancy_list = [
            "Absence of standard reentrancy protection designs",
            "State update order issues enabling reentrant calls",
            "Front-running vulnerabilities enabling price manipulation",
            "Unbounded iterations causing Denial of Service",
            "Uniswap V3 swap callback vulnerabilities",
            "Insufficient TWAP protection",
            "Array length increases leading to DoS attacks",
            "Message path blocking due to insufficient gas verification",
            "State modifications in staticcall contexts",
            "Flash loans creating abnormal pool states"
        ]

        module_call_list = [
            "Errors in module calls and delegatecalls",
            "Mismatched constructor parameters",
            "Defects in upgrade scripts and initialization",
            "Cross-chain deployment risks",
            "Failure to revoke old router approvals",
            "Delegation of funds not considering zero address cases",
            "Lack of state validation checks",
            "Incompatibilities between vaults and ERC4626 standards"
        ]

        fund_management_list = [
            "Improper parameter settings in settlements",
            "Errors in asset and share conversion",
            "Inconsistencies in calculating rewards and fees",
            "Unclear rules for fund locking or asset ownership",
            "Input parameters used for unintended purposes",
            "Vault exchange rates that can only increase",
            "Unbalanced deposits into UniV3 pools",
            "Inaccurate token exchange calculations",
            "Inaccurate weight processing affecting distributions",
            "Improper validation in addCollateral function"
        ]

        external_dependency_list = [
            "Incorrect assumptions about third-party interfaces",
            "Insufficient validation in external interface calls",
            "Misconfigured fee or gas parameters in cross-chain bridges",
            "Underlying data structure security issues",
            "Ignoring oracle update timestamps",
            "Relying on easily manipulable Curve pool prices",
            "Using single-sided valuations"
        ]

        trade_execution_list = [
            "Swap functions without minimum acceptable output",
            "Missing user-defined deadlines",
            "Incorrect slippage calculations",
            "Mismatches in fixed precision",
            "Unprotected minting operations",
            "Manipulatable on-chain slippage calculations",
            "Hard-coded fee tiers causing transaction issues",
            "Accepting high slippage allowing pool manipulation"
        ]

        erc4626_security_list_1 = [
            "Check if balance differences are recorded correctly instead of using expected transfer amounts",
            "Verify all token operations support tokens that revert on zero transfers like LEND",
            "Confirm system correctly handles precision conversion for tokens with different decimals",
            "Check compatibility handling for rebasing tokens and fee-on-transfer tokens",
            "Verify special handling for potentially blacklisted tokens like USDT",
            "Check if first deposit has minimum value requirements or pre-minted share protection",
            "Verify use of virtual share offset to prevent rate manipulation through donations",
            "Confirm rounding direction in deposit and mint functions favors the protocol",
            "Check consistency between preview functions and actual operation function rounding",
            "Verify all external calls execute after state updates following CEI pattern",
            "Check protection against reentrancy from ERC777 and tokens with hooks",
            "Confirm comprehensive protection measures against cross-function reentrancy attacks",
            "Check all sensitive functions have correct access control modifiers",
            "Verify proxy withdrawal operations check correct authorized addresses"
        ]

        erc4626_security_list_2 = [
            "Confirm admin functions cannot be bypassed by regular users",
            "Check correct implementation of multisig or timelock controls",
            "Verify Oracle prices check timeliness and reasonable boundary limits",
            "Check validation for L2 sequencer downtime",
            "Confirm price calculations use correct base and quote token order",
            "Verify protection against Oracle manipulation with TWAP or other measures",
            "Check if division executes before multiplication causing precision loss",
            "Verify correct precision scaling when mixing different decimal tokens",
            "Confirm critical calculations use rounding direction favoring protocol",
            "Check liquidation only executes after actual default not premature liquidation",
            "Verify liquidation incentive mechanisms are sufficient without enabling self-liquidation arbitrage",
            "Confirm liquidation collateral calculations include correct token scaling",
            "Check partial liquidations correctly handle bad debt and health improvement",
            "Verify deposit/withdrawal limit checks consider actual underlying vault limits"
        ]

        erc4626_security_list_3 = [
            "Check asset allocation and redemption logic completeness in multi-vault systems",
            "Confirm user funds can be normally withdrawn when vault is paused",
            "Check fee calculations use actual exchange amounts not input parameter amounts",
            "Verify total supply syncs before fee minting during reward distribution",
            "Confirm protocol fee collection cannot be bypassed or manipulated by users",
            "Verify cross-chain messages validate sender and chain ID validity",
            "Check Layer2 bridge operations use lock-unlock instead of mint-burn pattern",
            "Confirm upgradeable contracts have storage gaps to prevent conflicts",
            "Check critical parameter changes have timelocks or require rebalancing",
            "Verify user operations have sufficient slippage protection parameters",
            "Check automated operations like compounding prevent MEV arbitrage attacks",
            "Confirm all division by zero underflow overflow and array bounds are handled",
        ]

        # Category 1: Testing and Code Quality (Vulnerability #0)
        solana_testing_quality_list = [
            "Programs completely missing test suite with no unit, integration or mainnet fork tests",
            "Missing negative test cases for unauthorized access attempts and error conditions",
            "Missing edge case tests for boundary values, zero amounts, and maximum values",
            "No access control verification tests to ensure only authorized users can execute functions",
            "Tests not asserting state changes and protocol invariants after operations",
            "Unimplemented test functions marked with placeholders like '-' or 'todo!'",
            "Missing fuzz testing for financial calculations prone to precision or overflow errors",
            "No integration tests simulating full user workflows and cross-contract interactions"
        ]
        
        # Category 2: Account Validation and PDA Issues (Vulnerabilities #1, #2, #3, #9, #19, #32)
        solana_account_validation_list = [
            "PDA accounts missing seeds constraint allowing attacker to supply PDA belonging to different authority",
            "PDA seeds missing authority/signer parameter enabling cross-authority data manipulation",
            "PDA seeds missing governing state/context account enabling privilege escalation across contexts",
            "Receipt PDAs derived without sale/event address allowing redemption across different sales",
            "Token accounts validated only by owner and mint without enforcing deterministic canonical address",
            "Non-deterministic vault addresses allowing phantom vault attacks to drain legitimate vaults",
            "Missing Signer<'info> requirement for authority accounts allowing unauthorized operations",
            "Unchecked accounts (UncheckedAccount) used without proper validation in instruction handlers",
            "Account existence not checked before CPI creation attempts causing preemptive creation DoS",
            "Missing init_if_needed causing failures when expected PDA already exists",
            "Owner validation missing for accounts that should be owned by specific programs"
        ]
        
        # Category 3: Arithmetic and Calculation Issues (Vulnerabilities #4, #6, #34, #35, #36)
        solana_arithmetic_calculation_list = [
            "Arithmetic operations using +, -, *, / instead of checked_add, checked_sub, checked_mul, checked_div",
            "Division before multiplication causing precision loss in multi-step financial calculations",
            "Multiple sequential divisions compounding precision loss in fee or conversion calculations",
            "Fee calculations performed before final amount determination causing incorrect fee collection",
            "Last buy adjusting price but fees already calculated on wrong amount",
            "Interval-based pricing with partial final interval causing users to overpay beyond maximum",
            "Price calculation not capping at advertised maximum when duration not evenly divisible",
            "Fee formula discontinuities at phase boundaries creating abrupt jumps (e.g., 8.76% to 1%)",
            "Account balance comparisons including rent-exempt reserve against values excluding rent",
            "Invariant checks comparing account.lamports() directly without subtracting rent exemption",
            "Converting between shares and amounts without proper precision scaling"
        ]
        
        # Category 4: State Management Issues (Vulnerabilities #5, #10, #14, #15, #17, #33, #38)
        solana_state_management_list = [
            "State variables not updated after refunds causing stale values in subsequent calculations",
            "Temporary state variables like last_total_shares_minted not decremented when reversing operations",
            "State variable updates in update_settings function missing certain fields from input parameters",
            "Critical fields like migration_token_allocation provided in params but never assigned",
            "Price updates between withdrawal request and execution causing amount recalculation mismatches",
            "Withdrawal amounts locked at request price but recalculated at execution with different price",
            "Single failed operation in loop (e.g., closed pool) causing all subsequent operations to fail",
            "One error blocking entire collection update instead of skipping failed items gracefully",
            "State updates (balance -= amount) after external calls (transfer) enabling reentrancy attacks",
            "Checks-Effects-Interactions pattern violated with effects happening after interactions",
            "Input validation comparing self.field < self.other_field instead of input_param < self.field",
            "Validation always checking current stored value instead of validating the new input parameter",
            "Global state variables like claimed_supply not updated in refund/withdrawal functions",
            "Tokens not returned to authority when users withdraw, leaving them permanently locked"
        ]
        
        # Category 5: Token and Payment Handling (Vulnerabilities #7, #8, #13, #20, #21, #22, #23)
        solana_token_payment_list = [
            "Token account space hard-coded to 165 bytes failing for Token-2022 with extensions",
            "Dynamic space calculation missing for Token-2022 requiring ExtensionType::try_calculate_account_len",
            "Rent recipient accounts missing mut marker preventing account closure operations",
            "Native SOL vs SPL token handling inconsistent with fees in SPL but payments in SOL",
            "Fee collection using transfer_checked for SPL tokens when native_dst_asset flag indicates SOL payment",
            "Token transfer amount using calculated value like calculate_cost(amount) instead of parameter amount_to_deposit",
            "Base tokens not transferred from window to pair account when restaking expired withdrawals",
            "LST tokens minted but corresponding base tokens remain locked in window account",
            "Payment funds collected into Sale PDA or ATA with no withdraw_payments instruction",
            "Organizers unable to retrieve collected SOL/SPL payments after sale ends",
            "CPI transfer authority set to buyer.to_account_info() for sale's token account",
            "Wrong authority used when sale PDA should be authority with signer seeds"
        ]
        
        # Category 6: Fee and Economic Logic (Vulnerabilities #11, #12, #30)
        solana_fee_economic_list = [
            "Protocol fee and integrator fee parameters fully controlled by maker during order creation",
            "Maker can set protocol_fee = 0 and integrator_fee = 0 to bypass all fees",
            "Fee recipient accounts provided by user without validation against protocol fee wallet",
            "No enforcement of minimum protocol fee allowing makers to bypass protocol revenue",
            "Surplus fee condition bypassable by setting estimated_dst_amount to u64::MAX",
            "Actual amount never exceeds user-inflated estimate preventing surplus fee trigger",
            "Estimated amount parameters not validated for realism against oracle prices or min amounts",
            "Oracle-based dynamic pricing without user max_payment parameter exposing to price volatility",
            "Missing slippage protection allowing users to pay significantly more than expected"
        ]
        
        # Category 7: Access Control and Authorization (Vulnerabilities #16, #24, #25, #31, #39)
        solana_access_control_list = [
            "Signature verification without expiry timestamp allowing indefinite signature reuse",
            "DepositMetadata signatures missing nonce check enabling replay attacks",
            "Signatures not bound to specific user pubkey allowing sharing between users",
            "Admin claim_revenue function callable even when below min_threshold blocking user withdrawals",
            "Admin front-running user withdrawal transactions by changing protocol state",
            "Sale parameter updates (price, mint, etc.) allowed after sale start_time affecting pending transactions",
            "Guardian can end_sale before official end_time preventing legitimate purchases",
            "No end_time check in termination allowing premature sale ending",
            "Sale creation with no restrictions, fees, or deposits enabling spam and ID exhaustion DoS",
            "Global sale ID space exhaustible by attacker creating thousands of spam sales"
        ]
        
        # Category 8: Input Validation and Parameter Issues (Vulnerabilities #17, #27, #30)
        solana_input_validation_list = [
            "Validation checking if self.capacity_amount < self.accumulated instead of capacity_amount (parameter) < self.accumulated",
            "Always validating against current stored value instead of validating new input before assignment",
            "Sale initialization accepting max_tokens_per_user > max_tokens_total creating impossible conditions",
            "Sale accepting end_time < start_time or start_time in the past",
            "Max_price_feed_age allowed to be 0 making all purchases impossible",
            "Time validation missing minimum duration check (end_time - start_time >= MIN_DURATION)",
            "Token price and amounts allowed to be zero causing division errors",
            "Mint accounts not checked for initialization before using in operations",
            "Array length consistency not validated when input has multiple parallel arrays"
        ]
        
        # Category 9: Operational Continuity Issues (Vulnerabilities #18, #26, #29, #37, #40)
        solana_operational_continuity_list = [
            "Single withdrawal_enabled_flag checked in both request_withdrawal and withdraw (claim) operations",
            "Disabling new requests inadvertently blocks claiming of already-approved withdrawals",
            "Freeze state checks present (require!(!sale.is_frozen())) but no freeze_sale/unfreeze_sale instructions",
            "Dead code creating false sense of security without actual pause mechanism",
            "Account closure requiring amount == 0 allowing dust attack DoS by sending 1 token",
            "Strict zero-balance check prevents legitimate closures when tiny amounts present",
            "Proportional token distribution based on claimed_supply < sale_supply locking unclaimed difference",
            "No recovery mechanism for tokens between sale_supply and claimed_supply",
            "claim_tokens allowed without min_threshold check while withdraw_payment requires revenue < min_threshold",
            "Inconsistent threshold enforcement allowing both claims and withdrawals in same state"
        ]
        
        # Category 10: Space and Memory Management (Vulnerability #28)
        solana_space_memory_list = [
            "Account space calculation using size_of::<Data>() without adding 8-byte Anchor discriminator",
            "PDA init with space = std::mem::size_of::<SaleData>() missing the required 8-byte prefix",
            "Missing Data::LEN constant pattern where const LEN: usize = 8 + std::mem::size_of::<Self>()",
            "Token-2022 space calculation not using ExtensionType::try_calculate_account_len for extensions",
            "Hard-coded 165 bytes used instead of dynamic calculation based on mint's extension requirements"
        ]

        # 组合后的检查列表 (3+3+3+2)
        permission_reentrancy_list = permission_control_list + reentrancy_list
        # module_call_fund_list = module_call_list + fund_management_list
        external_dependency_trade_list = external_dependency_list + trade_execution_list

        # 将所有检查列表组织成一个有序字典
        all_checklists = {
            "parameter_validation": parameter_validation_list,
            # "arithmetic_calculation": arithmetic_calculation_list,
            "state_updates": state_updates_list,
            "consistency": consistency_list,
            # "permission_reentrancy": permission_reentrancy_list,
            "business_logic": business_logic_list,
            "fund_management": fund_management_list,
            # "solana_testing_quality": solana_testing_quality_list,
            "solana_account_validation": solana_account_validation_list,
            "solana_arithmetic_calculation": solana_arithmetic_calculation_list,
            "solana_state_management": solana_state_management_list,
            "solana_token_payment": solana_token_payment_list,
            "solana_fee_economic": solana_fee_economic_list,
            "solana_access_control": solana_access_control_list,
            # "external_dependency_trade": external_dependency_trade_list,
            # "erc4626_security_1": erc4626_security_list_1,
            # "erc4626_security_2": erc4626_security_list_2,
            # "erc4626_security_3": erc4626_security_list_3,
            
        }

        # 如果提供了 prompt_index，返回特定的检查列表
        if prompt_index is not None:
            checklist_keys = list(all_checklists.keys())
            if 0 <= prompt_index < len(checklist_keys):
                # print(f"[DEBUG] Returning checklist for index {prompt_index}: {checklist_keys[prompt_index]}")
                key = checklist_keys[prompt_index]
                return {key: all_checklists[key]}
            else:
                print(f"[WARNING] Invalid prompt_index {prompt_index}, returning all checklists")
                return all_checklists
        
        # 如果没有提供 prompt_index，返回所有检查列表
        return all_checklists