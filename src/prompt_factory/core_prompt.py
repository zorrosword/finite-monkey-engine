class CorePrompt:
    def core_prompt():
        return """
        We have already confirmed that the code contains only one exploitable, \
        code-error based vulnerability due to error logic in the code, \
        and your job is to identify it.
        and the vulnerability is include but not limited to the following vulnerabilities:
        Here's the English translation:

        1. **Parameter Validation and Input Verification Deficiencies**
        - Parameter order or type errors (e.g., "zero share" issues, incorrect parameter sequence)
        - Insufficient input, index, format, and encoding validation
        - Redundant or improper parameter checks
        - Missing necessary modifiers, data validation, and boundary checks (including insufficient normalization of oracle prices, parameter value and boundary errors)

        2. **Arithmetic Calculation and Precision Issues**
        - Use of incorrect constants, ratio calculation errors, and imprecise mathematical formulas
        - Decimal precision errors, rounding issues, rounding errors, and unit conversion mistakes
        - Division, bit shift, exchange rate/interest rate model errors
        - Confusion between "shares" and "amount" calculations
        - Inaccurate calculations of PnL, yield fees, fund flows, exchanges, share conversions, and equity ratios
        - Calculation errors in fees, rates, discounts, and referral rewards allocation
        - Cumulative errors in recursive calculations or multi-step conversions

        3. **State Updates, Synchronization, and Data Storage Defects**
        - Incorrect state update order, improper check sequence leading to delayed or missed critical state variable updates
        - Inconsistencies between global and local, cache data synchronization (including internal cache, mapping, arrays not cleared timely or incomplete deletion)
        - Loss of historical records, freezing or reward mechanism state synchronization vulnerabilities
        - "Incorrect determination methods" allowing deployment state manipulation

        4. **Insufficient Permission Control and Authentication**
        - Lack of necessary access permission checks, inappropriate access modifier configuration for critical functions
        - Authorization logic vulnerabilities, loose role management, insufficient caller identity verification (including signatures, roles, and distributed identity)
        - Insufficient authorization in cross-module or flash loan, flash swap scenarios
        - Arbitrary call risks in public interfaces and methods

        5. **External Calls and Cross-chain Communication Vulnerabilities**
        - Incorrect external contract interface calls, improper use of delegate calls (delegatecall, staticcall), and ABI encoding errors
        - Data leakage or abuse risks in cross-module data transmission
        - Cross-chain message packaging, parameter configuration, insufficient minimum gas limits leading to message blocking
        - Cross-chain data calculation, exchange rate deviation, market parameter mismatches, and virtual account source chain distinction issues
        - Inappropriate target address and function selection in cross-chain messages
        - Insufficient data validation for certain external interface calls

        6. **Business Logic and Process Design Flaws**
        - Deployment state determination errors, improper handling of special edge cases or empty orders
        - Insufficient protection measures in liquidation, lending, auction, redemption, withdrawal processes (e.g., insufficient collateral protection during liquidation, lack of lending protection buffer)
        - Inconsistencies in multi-stage processes, cancellation, settlement, locking mechanisms, and internal synchronization
        - Logic flaws in specific business scenarios (e.g., oracle versions, empty orders, admin debt liquidation)
        - Design errors in cross-chain, flash loan, flash swap, and strategy withdrawal scenarios

        7. **Reentrancy, Front-running, and Denial of Service Risks**
        - Lack of standard reentrancy protection design (including cross-function reentrancy, ERC777 hook-induced reentrancy vulnerabilities)
        - Reentrancy risks due to state update order issues
        - Front-running vulnerabilities and price manipulation attacks
        - Lack of upper limit control in loop iterations leading to Denial of Service (DoS) risks

        8. **Module Call, Upgrade Configuration, and Initialization Vulnerabilities**
        - Errors in module calls and delegate calls (e.g., immutable module addresses after constructor, cross-module dynamic dependency issues)
        - Constructor parameter mismatches and imprecise cross-contract, cross-module data transmission
        - Upgrade script, deployment, initialization, and configuration management defects (including loose Namespace registration and CoreSystem permissions, controller and wallet deployment initialization issues)
        - Security risks in cross-chain deployment, state variable reset, and upgrade processes

        9. **Fund Management, Fee Calculation, and Reward Distribution Errors**
        - Improper parameter settings in settlement, refunds, and fund flows
        - Errors in asset and share conversion, exchange, liquidation rewards, and fund flows (including incorrect mathematical formulas, commission and discount calculations)
        - Inconsistencies in referral rewards, incentive distribution, yield fees, and PnL calculations
        - Unclear fund locking and asset ownership in certain designs, potentially leading to malicious asset withdrawal theft or reward distribution algorithm failures
        - ERC20Rebasing and YieldBox mode conversion issues

        10. **Token Approval and Contract Call Errors**
            - Missing necessary ERC20/ERC721 token approvals
            - Incorrect target address, debit account, or token transfer parameter transmission during calls

        11. **External Dependency, Network Configuration, and Security Issues**
            - Incorrect assumptions or data update vulnerabilities in third-party contract interfaces, external oracle dependencies, and price data (e.g., price update data may be empty, use of incorrect prices)
            - Vulnerable external interface calls due to insufficient validation
            - Security issues in cross-chain bridges, cross-domain calls, and external calls (e.g., improper fee and gas parameter settings)
            - Excessive exposed ports on nodes, network and infrastructure configuration errors
            - Potential security vulnerabilities in underlying data structures (e.g., MerkleDB)

        12. **Insufficient Sensitive Information Protection and Memory Management**
            - Inadequate protection of sensitive data in memory, potential data leakage
            - Improper handling risks in memory management and data caching
        """
    def core_prompt_tirck():
        return """
        We have already confirmed that the code contains only one exploitable, \
        code-error based vulnerability due to error logic in the code, \
        """
    def core_prompt_vul_type_liquidation():
        return """
        before you start, you need to know that this is some liquidation vulnerability, \

        """


    def optimize_prompt():
        return """
        We have already confirmed that the code contains only one code optimize point, \
        not a vulnerability, \
        and your job is to identify it.
        """
    
    def assumation_prompt():
        return """
        Based on the vulnerability information, answer whether the establishment of the attack depends on the code of other unknown or unprovided contracts within the project, or whether the establishment of the vulnerability is affected by any external calls or contract states. 
        
        """
    def assumation_prompt_old():
        return """
        Based on the vulnerability information, answer whether the establishment of the attack depends on the code of other unknown or unprovided contracts within the project, or whether the establishment of the vulnerability is affected by any external calls or contract states. 
        
        Based on the results of the answer, add the JSON result: {'analaysis':'xxxxxxx','result':'need In-project other contract'} or {'analaysis':'xxxxxxx','result':'dont need In-project other contract'}.

        """
    def category_check():
        return """

        Based on the vulnerability information, analysis first step by step, then based on the analysis,Determine whether this vulnerability belongs to the access control type of vulnerability, the data validation type of vulnerability, or the data processing type of vulnerability.
        return as {'analaysis':'xxxxxxx','result':'xxxx vulnerability'}



        """