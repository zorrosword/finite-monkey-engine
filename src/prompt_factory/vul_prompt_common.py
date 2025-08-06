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

        # 组合后的检查列表 (3+3+3+2)
        permission_reentrancy_list = permission_control_list + reentrancy_list
        module_call_fund_list = module_call_list + fund_management_list
        external_dependency_trade_list = external_dependency_list + trade_execution_list

        # 将所有检查列表组织成一个有序字典
        all_checklists = {
            # "parameter_validation": parameter_validation_list,
            # "arithmetic_calculation": arithmetic_calculation_list,
            # "state_updates": state_updates_list,
            "consistency": consistency_list,
            # "permission_reentrancy": permission_reentrancy_list,
            # "business_logic": business_logic_list,
            # "module_call_fund": module_call_fund_list,
            # "external_dependency_trade": external_dependency_trade_list,
            
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