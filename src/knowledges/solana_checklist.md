---
alwaysApply: true
---
# Solana Security Primer

## Purpose

This primer documents critical security vulnerabilities in Solana programs discovered through real-world audits. It provides systematic bug-hunting methodologies for identifying security issues in production Solana codebases, with a focus on Anchor framework patterns and common anti-patterns that lead to exploitable vulnerabilities.

## Key Concepts

### Program Derived Addresses (PDAs)
- Deterministic addresses derived from seeds and program ID
- Do not have private keys, controlled entirely by the program
- Critical for state isolation between different authorities/users
- Must include ALL context-defining parameters in seeds

### Account Model
- All data stored in accounts owned by programs
- Accounts have lamports (SOL balance) and data
- Account ownership determines which program can modify
- Rent exemption required to prevent garbage collection

### Cross-Program Invocations (CPI)
- Programs calling other programs
- Requires careful validation of accounts passed
- Can enable reentrancy if state updates occur after CPI

### Token Accounts
- SPL Token and Token-2022 standards
- Associated Token Accounts (ATAs) vs arbitrary token accounts
- Token-2022 extensions require dynamic space calculation

## Common Vulnerability Patterns

### 0. Missing Test Suite

**Description**: Programs without comprehensive test suites are at high risk of bugs that impact security and functionality. Audits complement but don't replace thorough testing.

**Example Issues**:
- Early Purchase program completely missing test suite
- Liquid Staking program with unimplemented tests marked with "-"
- No unit tests, integration tests, or mainnet fork testing
- Missing negative test cases and edge cases
- No access control verification
- Lack of state change and invariant assertions

**Secure Implementation**:
```rust
// Test suite should include:
#[cfg(test)]
mod tests {
    // Unit tests for each function
    #[test]
    fn test_happy_path() { /* ... */ }
    
    #[test]
    fn test_negative_cases() { /* ... */ }
    
    #[test]
    fn test_edge_cases() { /* ... */ }
    
    #[test]
    fn test_access_control() { /* ... */ }
    
    // Integration tests with mainnet fork
    #[test]
    fn test_full_workflow() { /* ... */ }
    
    // Fuzz testing
    #[test]
    fn fuzz_test_calculations() { /* ... */ }
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - Both Early Purchase and Liquid Staking programs lacked proper test coverage.

### 1. Missing PDA Seeds Validation

**Description**: When account constraints fail to properly derive PDAs using all required seeds (especially authority/signer), attackers can supply PDAs belonging to different authorities.

**Example Vulnerable Code**:
```rust
// VULNERABLE: No PDA derivation constraint
pub struct AppendDataBitmap<'info> {
    #[account(mut)]  // Missing seeds constraint!
    pub sandwich_validators: AccountLoader<'info, SandwichValidators>,
    #[account(mut)]
    pub multisig_authority: Signer<'info>,
}
```

**Attack Scenario**:
1. Authority A creates PDA for their data
2. Attacker (Authority B) calls instruction with their signature but Authority A's PDA
3. Instruction accepts foreign PDA due to missing validation
4. Attacker modifies Authority A's data

**Secure Implementation**:
```rust
// SECURE: Proper PDA derivation enforced
pub struct AppendDataBitmap<'info> {
    #[account(
        mut,
        seeds = [
            SandwichValidators::SEED_PREFIX, 
            multisig_authority.key().as_ref(), 
            &epoch_arg.to_le_bytes()
        ],
        bump
    )]
    pub sandwich_validators: AccountLoader<'info, SandwichValidators>,
    #[account(mut)]
    pub multisig_authority: Signer<'info>,
}
```

**Real-World Impact**: Found in Pashov audit of Saguaro Gatekeeper - allowed cross-authority bitmap corruption.

### 2. Cross-Context Privilege Escalation

**Description**: PDAs missing governing state/context in seeds allow attackers with authority in one context to affect resources in another context.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Missing state context in PDA seeds
pub struct AddToAllowlistEntry<'info> {
    #[account(
        init_if_needed,
        seeds = [
            b"allow_list_entry", 
            args.stake_pool.as_ref(),    
            args.user_account.as_ref()   
            // MISSING: state.key() to bind to specific context!
        ],
        bump
    )]
    pub allow_list_entry: Account<'info, AllowListEntry>,
    
    #[account(mut, address = state.allower)]
    pub allower: Signer<'info>,
    pub state: Account<'info, State>,
}
```

**Attack Scenario**:
1. Legitimate protocol has State1 with trusted allower
2. Attacker creates State2 with themselves as allower
3. Attacker uses their allower status to add themselves to State1's pools
4. Complete bypass of intended access control

**Secure Implementation**:
```rust
// SECURE: State included in PDA seeds
#[account(
    init_if_needed,
    seeds = [
        b"allow_list_entry",
        state.key().as_ref(),     // CRITICAL: Bind to specific state
        args.stake_pool.as_ref(),
        args.user_account.as_ref()
    ],
    bump
)]
```

**Real-World Impact**: Found in Quantstamp audit of Liquid Collective - allowed unauthorized allowlist manipulation.

### 3. Non-Deterministic Token Account (Phantom Vaults)

**Description**: Accepting any token account with matching owner/mint without verifying canonical address allows attackers to create "phantom" vaults.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Only checks owner and mint, not canonical address!
#[account(
    mut,
    constraint = vault_account.owner == state.key(),
    constraint = vault_account.mint == state.belo_mint
)]
pub vault_account: Account<'info, TokenAccount>,
```

**Attack Scenario**:
1. Alice deposits 100 tokens to official vault
2. Bob creates phantom vault with same owner/mint but different address
3. Bob deposits 50 tokens to phantom vault
4. Bob withdraws from OFFICIAL vault, draining Alice's funds
5. Protocol becomes insolvent

**Secure Implementation**:
```rust
// SECURE: Enforce deterministic vault address
let (vault_key, _bump) = Pubkey::find_program_address(
    &[b"vault", state.belo_mint.as_ref()],
    program_id,
);
require!(vault_account.key() == vault_key, Error::InvalidVault);
```

**Real-World Impact**: Found in Cyfrin audit of Doryoku - enabled draining legitimate vault through phantom vaults.

### 4. Integer Arithmetic Vulnerabilities

**Description**: Unchecked arithmetic operations can overflow/underflow, and division before multiplication causes precision loss.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Multiple divisions cause compounding precision loss
let time_fraction = seconds_elapsed
    .checked_mul(precision)?
    .checked_div(SECONDS_IN_YEAR)?;  // First division

let fee_pct = time_fraction
    .checked_mul(fee_rate)?
    .checked_div(10000)?;  // Second division - more precision lost
```

**Attack/Impact**: 
- Systematic undercharging of fees over time
- Small errors compound over thousands of transactions
- Steady value leak from protocol

**Secure Implementation**:
```rust
// SECURE: All multiplications first, single division at end
let numerator = shares
    .checked_mul(seconds_elapsed)?
    .checked_mul(fee_bps as u128)?;

let denominator = SECONDS_IN_YEAR
    .checked_mul(10000)?;

let fee = numerator.checked_div(denominator)?;  // Only ONE division
```

**Real-World Impact**: Found in Quantstamp audit of Neutral Trade - caused systematic undercharging of management fees.

### 5. Stale State Variables

**Description**: State variables not updated after operations in multi-step processes cause cascading calculation errors.

**Example Vulnerable Code**:
```rust
// VULNERABLE: State variable not updated after each refund
pub fn refund_deposit(ctx: Context<RefundDeposit>) -> Result<()> {
    let shares_to_revert = user_share * 
        bundle_temp_data.last_total_shares_minted / PRECISION;
    
    cumulative_pending_deposits -= deposit_amount;
    // BUG: last_total_shares_minted NOT decreased!
}
```

**Attack/Impact**:
- First refund calculates correctly
- Subsequent refunds use stale value, cancel too many shares
- Share price distortion affects all future operations

**Secure Implementation**:
```rust
// SECURE: Update all related state variables
cumulative_pending_deposits -= deposit_amount;
bundle_temp_data.last_total_shares_minted -= shares_to_revert;  // CRITICAL!
```

**Real-World Impact**: Found in Quantstamp audit of Neutral Trade - caused share price distortion.

### 6. Edge Cases in Interval-Based Pricing

**Description**: When duration isn't evenly divisible by price intervals, partial intervals at the end cause users to overpay beyond intended maximum.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Partial intervals not handled
let number_of_intervals = total_duration / price_fix_duration;  // Integer division!
let current_interval = elapsed_time / price_fix_duration;

// Users in partial interval pay more than max price!
let price = start_price + (price_per_interval * (current_interval + 1));
```

**Attack/Impact**:
- Duration: 2.5 days, Interval: 1 day
- Day 1: Users pay 15 (correct)
- Day 2: Users pay 20 (intended max)
- Day 2.5: Users pay 25 (OVERPAYMENT!)

**Secure Implementation**:
```rust
// SECURE: Cap at maximum price
let calculated_price = /* calculation */;
let final_price = calculated_price.min(max_price);
```

**Real-World Impact**: Found in Quantstamp audit of ONRE - caused users to pay more than advertised maximum.

### 7. Hard-coded Account Sizes for Token-2022

**Description**: Using legacy SPL Token size (165 bytes) for Token-2022 accounts with extensions causes initialization failures.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Hard-coded 165 bytes for legacy SPL Token
let vault_space = 165;  // Standard token account size
system_program::create_account(ctx, lamports, vault_space, &token_program)?;

// Fails for Token-2022 with extensions!
token_interface::initialize_account3(ctx)?;
```

**Attack/Impact**:
- Token-2022 with extensions need more space
- Initialization fails with InvalidAccountData
- Users cannot stake Token-2022 NFTs
- Entire functionality blocked

**Secure Implementation**:
```rust
// SECURE: Dynamic space calculation
fn get_token_account_space(mint: &AccountInfo) -> Result<usize> {
    if mint.owner == &spl_token_2022::ID {
        // Calculate space including extensions
        let required_extensions = detect_extensions(mint)?;
        ExtensionType::try_calculate_account_len::<Account>(&required_extensions)
    } else {
        Ok(165)  // Legacy SPL Token
    }
}
```

**Real-World Impact**: Found in Cyfrin audit of Doryoku - blocked staking of Raydium positions.

### 8. Missing Mutability for Rent Recipients

**Description**: Accounts receiving rent refunds must be marked mutable, otherwise closure operations fail.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Boss not mutable, can't receive rent!
pub struct CloseOffer<'info> {
    #[account(mut, close = boss)]
    pub offer: Account<'info, Offer>,
    
    pub boss: Signer<'info>,  // BUG: Missing #[account(mut)]!
}
```

**Secure Implementation**:
```rust
// SECURE: Rent recipient must be mutable
#[account(mut)]
pub boss: Signer<'info>,
```

**Real-World Impact**: Found in Quantstamp audit of ONRE - prevented legitimate account closures.

### 9. Missing Signer Requirements

**Description**: Authority accounts not requiring signatures allow unauthorized operations.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Authority doesn't need to sign!
pub struct Withdraw<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    /// CHECK: Authority validated in handler
    pub authority: AccountInfo<'info>,  // NOT a Signer!
}
```

**Secure Implementation**:
```rust
// SECURE: Requires signature
pub authority: Signer<'info>,
```

### 10. Reentrancy via CPI

**Description**: State updates after external calls enable reentrancy attacks.

**Example Vulnerable Code**:
```rust
// VULNERABLE: State updated after external call
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    transfer_tokens(&ctx.accounts.token_program, amount)?;  // External call first
    ctx.accounts.user_account.balance -= amount;  // State update after!
    Ok(())
}
```

**Secure Implementation**:
```rust
// SECURE: Checks-Effects-Interactions pattern
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    // 1. Checks
    require!(ctx.accounts.user_account.balance >= amount);
    
    // 2. Effects (state updates FIRST)
    ctx.accounts.user_account.balance -= amount;
    
    // 3. Interactions (external calls LAST)
    transfer_tokens(&ctx.accounts.token_program, amount)?;
    Ok(())
}
```

### 11. Fee Bypass via User-Controlled Parameters

**Description**: Allowing users to set fee parameters during order creation enables them to bypass protocol fees entirely.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Maker controls all fee parameters
pub fn create(ctx: Context<Create>, order: OrderConfig) -> Result<()> {
    // Maker can set protocol_fee = 0, integrator_fee = 0
    // Or provide invalid fee recipient accounts
    require!(
        (order.fee.protocol_fee > 0) == ctx.accounts.protocol_dst_ata.is_some(),
        Error::InconsistentConfig
    );
    // But no enforcement of minimum fees!
}
```

**Attack Scenario**:
1. Maker creates order with `protocol_fee = 0` and `integrator_fee = 0`
2. Or provides their own account as `protocol_dst_ata`
3. Protocol receives no fees despite facilitating the trade
4. Maker captures full value intended for protocol

**Secure Implementation**:
```rust
// SECURE: Protocol-enforced minimum fees
pub fn create(ctx: Context<Create>, order: OrderConfig) -> Result<()> {
    // Protocol sets minimum fees
    const MIN_PROTOCOL_FEE: u16 = 30;  // 0.3%
    const MAX_TOTAL_FEE: u16 = 500;    // 5%
    
    require!(
        order.fee.protocol_fee >= MIN_PROTOCOL_FEE,
        Error::ProtocolFeeTooLow
    );
    
    require!(
        order.fee.protocol_fee + order.fee.integrator_fee <= MAX_TOTAL_FEE,
        Error::TotalFeeTooHigh
    );
    
    // Verify protocol fee recipient is correct
    require!(
        ctx.accounts.protocol_dst_ata.owner == PROTOCOL_FEE_WALLET,
        Error::InvalidFeeRecipient
    );
}
```

**Real-World Impact**: Found in Quantstamp audit of 1inch Fusion - makers could bypass all protocol fees.

### 12. Surplus Fee Bypass via Parameter Manipulation

**Description**: Surplus fees can be bypassed by inflating the estimated amount parameter, preventing the surplus condition from triggering.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Surplus fee only applies if actual > estimated
fn get_fee_amounts(
    surplus_percentage: u8,
    dst_amount: u64,
    estimated_dst_amount: u64,  // User-controlled!
) -> Result<(u64, u64)> {
    let mut protocol_fee = base_fee;
    
    // Surplus fee only if we exceed estimate
    if actual_dst_amount > estimated_dst_amount {
        protocol_fee += (actual_dst_amount - estimated_dst_amount)
            * surplus_percentage / 100;
    }
    // Maker sets estimated_dst_amount = u64::MAX to never pay surplus!
}
```

**Attack Scenario**:
1. Maker sets `estimated_dst_amount` to maximum possible value
2. Condition `actual > estimated` never triggers
3. Surplus fees (meant to capture positive slippage) never collected
4. Protocol loses revenue from favorable price movements

**Secure Implementation**:
```rust
// SECURE: Validate estimated amount is realistic
fn validate_order(order: &Order) -> Result<()> {
    // Estimated should be reasonably close to minimum
    const MAX_SLIPPAGE_RATIO: u64 = 110;  // 10% max difference
    
    require!(
        order.estimated_dst_amount <= 
            order.min_dst_amount * MAX_SLIPPAGE_RATIO / 100,
        Error::UnrealisticEstimate
    );
    
    // Or use oracle price for validation
    let oracle_price = get_oracle_price()?;
    let expected = order.src_amount * oracle_price / PRECISION;
    require!(
        order.estimated_dst_amount.abs_diff(expected) < threshold,
        Error::EstimateDeviatesFromOracle
    );
}
```

**Real-World Impact**: Found in Quantstamp audit of 1inch Fusion - allowed complete bypass of surplus fees.

### 13. Inconsistent Token Type Handling

**Description**: Different handling of native SOL vs SPL tokens in fee payments creates inconsistencies and potential issues.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Fees always in SPL tokens, even when maker wants native SOL
pub fn fill(ctx: Context<Fill>, order: Order) -> Result<()> {
    // Take fees (always as SPL tokens)
    if protocol_fee > 0 {
        transfer_checked(
            ctx.accounts.taker_dst_ata,  // SPL token account
            ctx.accounts.protocol_dst_ata,
            protocol_fee
        )?;
    }
    
    // Pay maker
    if order.native_dst_asset {
        // Maker receives native SOL
        system_program::transfer(
            ctx.accounts.taker,
            ctx.accounts.maker,
            maker_amount
        )?;
    } else {
        // Maker receives SPL tokens
        transfer_checked(/*...*/)? ;
    }
    // Inconsistency: fees in SPL, payment in SOL!
}
```

**Impact**:
- When `native_dst_asset = true`, maker may not have SPL token accounts
- Fees fail to transfer, blocking the trade
- Or fees go to unintended/uncontrolled accounts

**Secure Implementation**:
```rust
// SECURE: Consistent token type for all transfers
pub fn fill(ctx: Context<Fill>, order: Order) -> Result<()> {
    if order.native_dst_asset {
        // All transfers in native SOL
        if protocol_fee > 0 {
            system_program::transfer(
                ctx.accounts.taker,
                ctx.accounts.protocol_wallet,  // SOL wallet
                protocol_fee
            )?;
        }
        
        system_program::transfer(
            ctx.accounts.taker,
            ctx.accounts.maker,
            maker_amount
        )?;
    } else {
        // All transfers in SPL tokens
        // ... existing SPL transfer logic
    }
}
```

**Real-World Impact**: Found in Quantstamp audit of 1inch Fusion - could cause failed transactions or lost fees.

### 14. Price Update Race Conditions

**Description**: Updating prices between withdrawal request and actual withdrawal causes amount calculation inaccuracies and potential fund drainage.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Price can change between request and withdrawal
pub fn request_withdrawal(ctx: Context, amount: u64) -> Result<()> {
    // User requests withdrawal at current price
    let sol_amount = convert_to_sol(amount, current_price);
    batch.add_withdrawal(sol_amount);
}

pub fn withdraw(ctx: Context) -> Result<()> {
    // Price updated here!
    fund.update_token_prices(ctx.remaining_accounts)?;
    
    // Recalculates with NEW price - mismatch!
    let sol_amount = convert_to_sol(user.amount, NEW_PRICE);
    transfer_sol(sol_amount)?;
}
```

**Attack/Impact**:
- User requests withdrawal at price P1
- Price updates to P2 before actual withdrawal
- Withdrawal uses P2, causing:
  - Underflow errors blocking withdrawals
  - Over-withdrawal draining rent-exempt reserves
  - Artificially inflated token values

**Secure Implementation**:
```rust
// SECURE: Lock withdrawal amount at request time
pub fn request_withdrawal(ctx: Context, amount: u64) -> Result<()> {
    let sol_amount = convert_to_sol(amount, current_price);
    // Store the calculated SOL amount
    withdrawal_request.locked_sol_amount = sol_amount;
}

pub fn withdraw(ctx: Context) -> Result<()> {
    // Use the locked amount, ignore price changes
    transfer_sol(withdrawal_request.locked_sol_amount)?;
}
```

**Real-World Impact**: Found in Quantstamp audit of Fragmetric - could drain protocol reserves through price manipulation.

### 15. Single Point of Failure in State Updates

**Description**: One failed update in a collection blocks all operations for the entire collection.

**Example Vulnerable Code**:
```rust
// VULNERABLE: One closed pool blocks everything
pub fn update_all_reward_pools(&mut self) -> Result<()> {
    for pool in self.get_all_pools() {
        if pool.is_closed() {
            return Err(Error::PoolClosed);  // Stops ALL updates!
        }
        pool.update()?;
    }
}

pub fn deposit(ctx: Context) -> Result<()> {
    // This fails if ANY pool is closed
    update_all_reward_pools()?;  
    // Deposit never happens!
}
```

**Attack/Impact**:
- Admin closes one reward pool
- ALL deposits, withdrawals, transfers fail
- Complete protocol DoS
- Users' funds locked indefinitely

**Secure Implementation**:
```rust
// SECURE: Skip closed pools, continue processing
pub fn update_all_reward_pools(&mut self) -> Result<()> {
    for pool in self.get_all_pools() {
        if pool.is_closed() {
            continue;  // Skip this pool, process others
        }
        pool.update()?;
    }
}

// Or use separate error handling
pub fn update_with_fallback(&mut self) -> Result<()> {
    let mut failed_pools = vec![];
    for pool in self.get_all_pools() {
        match pool.update() {
            Ok(_) => {},
            Err(e) if e == Error::PoolClosed => {
                failed_pools.push(pool.id);
                continue;
            },
            Err(e) => return Err(e),
        }
    }
    emit!(PoolsSkipped { pools: failed_pools });
}
```

**Real-World Impact**: Found in Quantstamp audit of Fragmetric - closing one pool DoS'd entire protocol.

### 16. Signature Replay Attacks

**Description**: Signatures without expiry or nonce can be replayed to gain unauthorized benefits.

**Example Vulnerable Code**:
```rust
// VULNERABLE: No expiry or uniqueness check
pub struct DepositMetadata {
    pub wallet_provider: String,
    pub contribution_accrual_rate: u8,  // No expiry!
}

pub fn verify_signature(metadata: &DepositMetadata) -> Result<()> {
    // Verifies admin signed this metadata
    ed25519_verify(admin_key, metadata)?;
    // But signature can be reused forever!
}
```

**Attack Scenario**:
1. User obtains valid signature for 2x accrual rate
2. Signature has no expiry timestamp
3. User reuses signature indefinitely
4. Or shares signature with other users
5. Protocol gives excessive rewards

**Secure Implementation**:
```rust
// SECURE: Add expiry and user binding
pub struct DepositMetadata {
    pub wallet_provider: String,
    pub contribution_accrual_rate: u8,
    pub expiry_timestamp: i64,        // Add expiry
    pub user_pubkey: Pubkey,          // Bind to specific user
    pub nonce: u64,                   // Prevent replay
}

pub fn verify_signature(metadata: &DepositMetadata) -> Result<()> {
    // Check expiry
    require!(
        Clock::get()?.unix_timestamp < metadata.expiry_timestamp,
        Error::SignatureExpired
    );
    
    // Check user binding
    require!(
        ctx.accounts.user.key() == metadata.user_pubkey,
        Error::SignatureMismatch
    );
    
    // Check nonce hasn't been used
    require!(
        !used_nonces.contains(&metadata.nonce),
        Error::NonceReused
    );
    
    ed25519_verify(admin_key, metadata)?;
    used_nonces.insert(metadata.nonce);
}
```

**Real-World Impact**: Found in Quantstamp audit of Fragmetric - allowed unlimited reward rate exploitation.

### 17. Input Validation Against Wrong Variable

**Description**: Validation checks comparing wrong variables allow invalid states and DoS conditions.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Compares self to self instead of input!
pub fn set_capacity_amount(&mut self, capacity_amount: u64) -> Result<()> {
    // Bug: should compare capacity_amount, not self.capacity_amount
    if self.capacity_amount < self.accumulated_deposit_amount {
        return Err(Error::InvalidUpdate);
    }
    self.capacity_amount = capacity_amount;
}
```

**Attack/Impact**:
- Admin tries to update capacity
- Validation always uses old value
- If mistakenly set too low, permanently stuck
- Cannot update capacity ever again
- Protocol parameters frozen

**Secure Implementation**:
```rust
// SECURE: Validate the input parameter
pub fn set_capacity_amount(&mut self, capacity_amount: u64) -> Result<()> {
    // Compare the INPUT against current state
    require!(
        capacity_amount >= self.accumulated_deposit_amount,
        Error::CapacityTooLow
    );
    self.capacity_amount = capacity_amount;
}
```

**Real-World Impact**: Found in Quantstamp audit of Fragmetric - could permanently lock protocol parameters.

### 18. Inconsistent Flag Checks Blocking Operations

**Description**: Using the same flag for different operations can inadvertently block legitimate actions.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Same flag blocks both request AND claim
pub fn request_withdrawal(ctx: Context) -> Result<()> {
    require!(withdrawal_enabled_flag, Error::WithdrawalsDisabled);
    // Process request...
}

pub fn withdraw(ctx: Context) -> Result<()> {
    // Bug: checking same flag for different operation!
    require!(withdrawal_enabled_flag, Error::WithdrawalsDisabled);
    // User can't claim already processed withdrawals!
}
```

**Attack/Impact**:
- Admin disables new withdrawal requests
- Flag also blocks claiming existing withdrawals
- Users with processed withdrawals can't access funds
- Funds locked despite being approved

**Secure Implementation**:
```rust
// SECURE: Separate flags for different operations
pub struct Config {
    pub new_withdrawals_enabled: bool,
    pub claim_withdrawals_enabled: bool,
}

pub fn request_withdrawal(ctx: Context) -> Result<()> {
    require!(config.new_withdrawals_enabled, Error::NewWithdrawalsDisabled);
    // Process request...
}

pub fn withdraw(ctx: Context) -> Result<()> {
    // Different flag for claiming
    require!(config.claim_withdrawals_enabled, Error::ClaimsDisabled);
    // Or no check at all for already approved withdrawals
    transfer_approved_amount()?;
}
```

**Real-World Impact**: Found in Quantstamp audit of Fragmetric - could lock users' approved withdrawals.

### 19. Cross-Sale Receipt Redemption

**Description**: Receipt PDAs derived without sale address allow tokens purchased from one sale to be redeemed from another sale.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Receipt PDA missing sale address in seeds
seeds = [
    Receipt::PREFIX.as_bytes(),
    &buyer.key.to_bytes()
    // MISSING: sale address!
]
```

**Attack Scenario**:
1. Attacker creates mock sale with worthless tokens at cheap price
2. Attacker buys 1000000 mock tokens, gets receipt
3. Receipt records amount but not sale address
4. Legitimate sale ends, redemptions open
5. Attacker redeems mock receipt against legitimate sale
6. Drains 1000000 legitimate tokens

**Secure Implementation**:
```rust
// SECURE: Include sale address in receipt PDA seeds
seeds = [
    Receipt::PREFIX.as_bytes(),
    &sale.key().to_bytes(),      // CRITICAL: Bind to specific sale
    &buyer.key.to_bytes()
]
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - allowed draining legitimate sales with fake receipts.

### 20. Locked Payment Funds

**Description**: Collected payments remain locked in Sale PDAs with no withdrawal mechanism for organizers.

**Example Vulnerable Code**:
```rust
// VULNERABLE: No way to withdraw collected payments
pub fn purchase_tokens(ctx: Context, amount: u64) -> Result<()> {
    // Payments transferred to Sale PDA or ATA
    transfer_payment_to_sale()?;
    // But no instruction to withdraw these funds!
}

// Missing: withdraw_payments instruction
```

**Attack/Impact**:
- Sale collects SOL/SPL token payments
- No mechanism to transfer to organizer/treasury
- Funds permanently locked in Sale PDA
- Protocol becomes insolvent

**Secure Implementation**:
```rust
// SECURE: Add payment withdrawal mechanism
pub fn withdraw_payments(ctx: Context<WithdrawPayments>) -> Result<()> {
    require!(ctx.accounts.sale.ended, Error::SaleNotEnded);
    require!(ctx.accounts.authority.key() == ctx.accounts.sale.admin);
    
    // Transfer collected SOL
    **ctx.accounts.sale.to_account_info().lamports.borrow_mut() -= amount;
    **ctx.accounts.treasury.lamports.borrow_mut() += amount;
    
    // Transfer collected SPL tokens
    token::transfer(
        CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            Transfer {
                from: ctx.accounts.sale_payment_ata.to_account_info(),
                to: ctx.accounts.treasury_ata.to_account_info(),
                authority: ctx.accounts.sale.to_account_info(),
            },
            &[&[/* sale PDA seeds */]]
        ),
        token_amount
    )?;
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - all collected payments locked permanently.

### 21. Incorrect CPI Authority

**Description**: Using wrong authority for token transfers prevents legitimate operations from completing.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Buyer used as authority for sale's token transfer
token::transfer(
    CpiContext::new(
        purchase_program.to_account_info(),
        token::Transfer {
            from: config_purchase_ata.to_account_info(),  // Sale's ATA
            to: buyer_purchase_ata.to_account_info(),
            authority: buyer.to_account_info(),  // WRONG! Buyer doesn't control sale's ATA
        },
    ),
    num_tokens_pending,
)
```

**Attack/Impact**:
- All redemptions fail with unauthorized error
- Users cannot claim purchased tokens
- Tokens locked in sale account
- Complete DoS of redemption functionality

**Secure Implementation**:
```rust
// SECURE: Use sale PDA as authority with signer seeds
token::transfer(
    CpiContext::new_with_signer(
        purchase_program.to_account_info(),
        token::Transfer {
            from: config_purchase_ata.to_account_info(),
            to: buyer_purchase_ata.to_account_info(),
            authority: sale.to_account_info(),  // CORRECT: Sale PDA controls its ATA
        },
        &[&[/* sale PDA seeds */]]
    ),
    num_tokens_pending,
)
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - blocked all token redemptions.

### 22. Wrong Amount in Token Transfers

**Description**: Using calculated values instead of actual parameters causes incorrect token transfers.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Transferring calculated amount instead of parameter
pub fn deposit_tokens(params: DepositParams) -> Result<()> {
    token::transfer(
        /* ... */,
        sale.calculate_base_purchase_cost(params.amount_to_deposit),  // WRONG!
        // Should transfer params.amount_to_deposit
    )
}
```

**Attack/Impact**:
- Transfers significantly different amount than intended
- May transfer too little (underfunding sale)
- May transfer too much (draining depositor)
- Breaks sale economics completely

**Secure Implementation**:
```rust
// SECURE: Transfer exact parameter amount
token::transfer(
    /* ... */,
    params.amount_to_deposit,  // Use the actual parameter
)
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - incorrect deposit amounts.

### 23. Missing Token Transfers in Restaking

**Description**: Restaking expired withdrawals mints LST tokens but doesn't transfer corresponding base tokens, locking funds.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Mints LST but doesn't transfer base tokens
pub fn restake_expired_withdrawal() -> Result<()> {
    // Mint LST tokens back to user
    mint_lst_tokens(user, amount)?;
    
    // BUG: Base tokens remain in window_base_token_account!
    // Missing: transfer from window to pair account
}
```

**Attack/Impact**:
- Base tokens locked in withdrawal window account
- Window cannot be closed (non-zero balance)
- Accumulating locked funds
- Protocol insolvency over time

**Secure Implementation**:
```rust
// SECURE: Transfer base tokens when restaking
pub fn restake_expired_withdrawal() -> Result<()> {
    mint_lst_tokens(user, amount)?;
    
    // Transfer base tokens out of window
    token::transfer(
        window_base_token_account,
        pair_base_token_account,
        amount
    )?;
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance Liquid Staking - locked base tokens.

### 24. Sale Updates During Active Sales

**Description**: Critical sale parameters can be modified while sale is ongoing or about to start, affecting buyers' expectations.

**Example Vulnerable Code**:
```rust
// VULNERABLE: No restriction on updating active sales
pub fn update_sale(ctx: Context<UpdateSale>, params: UpdateParams) -> Result<()> {
    // No check if sale already started!
    sale.purchase_mint = params.purchase_mint;
    sale.payment_mint = params.payment_mint;
    sale.token_price = params.token_price;
    // Buyers' transactions use these new values!
}
```

**Attack Scenario**:
1. Buyer sees sale at price X
2. Guardian updates price to 2X before buyer's tx processes
3. Buyer pays double the expected amount
4. Complete loss of trust in protocol

**Secure Implementation**:
```rust
// SECURE: Lock parameters before sale starts
pub fn update_sale(ctx: Context<UpdateSale>, params: UpdateParams) -> Result<()> {
    require!(!sale.is_start_time_reached(), Error::SaleAlreadyStarted);
    
    // Only allow updates before sale begins
    sale.purchase_mint = params.purchase_mint;
    // ... other updates
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - allowed rug-pull scenarios.

### 25. Premature Sale Termination

**Description**: Guardians can end sales before the official end time, preventing legitimate purchases.

**Example Vulnerable Code**:
```rust
// VULNERABLE: No check for end time
pub fn end_sale(ctx: Context<EndSale>) -> Result<()> {
    // Guardian can end at any time!
    sale.state = SaleState::Ended;
}
```

**Attack/Impact**:
- Malicious guardian ends sale early
- Users planning to buy are locked out
- Unfair advantage to early buyers
- Potential insider trading

**Secure Implementation**:
```rust
// SECURE: Enforce end time
pub fn end_sale(ctx: Context<EndSale>) -> Result<()> {
    require!(sale.is_end_time_reached(), Error::SalePeriodNotComplete);
    sale.state = SaleState::Ended;
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - allowed premature sale termination.

### 26. Unimplemented Freeze Functionality

**Description**: Code checks for frozen state but no mechanism exists to actually freeze/unfreeze sales.

**Example Vulnerable Code**:
```rust
// Has freeze check...
pub fn purchase_tokens() -> Result<()> {
    require!(!sale.is_frozen(), Error::SaleFrozen);
    // ...
}

// But no freeze instruction exists!
// Missing: freeze_sale() and unfreeze_sale()
```

**Attack/Impact**:
- False sense of security (freeze protection doesn't exist)
- No emergency pause mechanism
- Cannot stop malicious sales
- Dead code confuses auditors/developers

**Secure Implementation**:
```rust
// SECURE: Implement freeze mechanism
pub fn freeze_sale(ctx: Context<FreezeSale>) -> Result<()> {
    require_admin!(ctx.accounts.authority);
    ctx.accounts.sale.state = SaleState::Frozen;
    emit!(SaleFrozen { sale: ctx.accounts.sale.key() });
}

pub fn unfreeze_sale(ctx: Context<UnfreezeSale>) -> Result<()> {
    require_admin!(ctx.accounts.authority);
    ctx.accounts.sale.state = SaleState::Active;
    emit!(SaleUnfrozen { sale: ctx.accounts.sale.key() });
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - freeze checks without implementation.

### 27. Invalid Sale Parameter Combinations

**Description**: Sale initialization accepts impossible parameter combinations that break functionality.

**Example Vulnerable Code**:
```rust
// VULNERABLE: No validation of parameter relationships
pub fn initialize_sale(params: SaleParams) -> Result<()> {
    sale.max_tokens_per_user = params.max_tokens_per_user;
    sale.max_tokens_total = params.max_tokens_total;
    // Allows max_per_user > max_total!
    
    sale.start_time = params.start_time;
    sale.end_time = params.end_time;
    // Allows end_time < start_time!
    
    sale.max_price_feed_age = params.max_price_feed_age;
    // Allows 0, making purchases impossible!
}
```

**Attack/Impact**:
- Sales with impossible conditions
- Zero price feed age blocks all purchases
- Negative duration sales
- Users unable to participate as intended

**Secure Implementation**:
```rust
// SECURE: Comprehensive parameter validation
pub fn initialize_sale(params: SaleParams) -> Result<()> {
    // Time validation
    require!(params.start_time > Clock::get()?.unix_timestamp, Error::InvalidStartTime);
    require!(params.end_time > params.start_time, Error::InvalidDuration);
    require!(params.end_time - params.start_time >= MIN_DURATION, Error::DurationTooShort);
    
    // Token limits validation
    require!(params.max_tokens_per_user <= params.max_tokens_total, Error::InvalidTokenLimits);
    require!(params.max_tokens_total > 0, Error::ZeroTokens);
    
    // Price validation
    require!(params.token_price > 0, Error::ZeroPrice);
    require!(params.max_price_feed_age >= MIN_FEED_AGE, Error::FeedAgeTooLow);
    
    // Mint validation
    require!(params.purchase_mint.is_initialized(), Error::UninitializedMint);
    require!(params.payment_mint.is_initialized(), Error::UninitializedMint);
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - allowed broken sale configurations.

### 28. Missing Discriminator in Space Calculation

**Description**: PDA initialization doesn't account for 8-byte Anchor discriminator in space allocation.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Forgets 8-byte discriminator
#[account(
    init,
    payer = payer,
    space = std::mem::size_of::<SaleData>()  // Missing +8!
)]
pub sale: Account<'info, SaleData>,
```

**Attack/Impact**:
- Account initialization may fail
- Data serialization errors
- Potential buffer overflows
- Unpredictable behavior

**Secure Implementation**:
```rust
// SECURE: Include discriminator
#[account(
    init,
    payer = payer,
    space = 8 + std::mem::size_of::<SaleData>()  // 8-byte discriminator
)]
pub sale: Account<'info, SaleData>,

// Or use Anchor's helper
#[account(
    init,
    payer = payer,
    space = SaleData::LEN
)]
pub sale: Account<'info, SaleData>,

impl SaleData {
    pub const LEN: usize = 8 + std::mem::size_of::<Self>();
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - risked initialization failures.

### 29. Dust Attack on Window Closure

**Description**: Malicious users can send tiny amounts to prevent account closure due to strict zero-balance checks.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Strict zero check enables DoS
pub fn close_withdrawal_window() -> Result<()> {
    require!(
        window_base_token_account.amount == 0,  // Attacker sends 1 token!
        StakingError::WindowHasActiveRequests
    );
    // Close account...
}
```

**Attack Scenario**:
1. Protocol tries to close withdrawal window
2. Attacker sends 1 base token to window account
3. Closure fails due to non-zero balance
4. Window permanently uncloseable
5. Rent continues draining

**Secure Implementation**:
```rust
// SECURE: Handle dust amounts
pub fn close_withdrawal_window() -> Result<()> {
    // Option 1: Allow dust threshold
    const DUST_THRESHOLD: u64 = 100;  // Small amount
    require!(
        window_base_token_account.amount <= DUST_THRESHOLD,
        StakingError::WindowHasActiveRequests
    );
    
    // Option 2: Sweep remaining tokens first
    if window_base_token_account.amount > 0 {
        token::transfer(
            window_base_token_account,
            treasury_account,
            window_base_token_account.amount
        )?;
    }
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - enabled permanent DoS via dust.

### 30. Missing Slippage Protection

**Description**: Dynamic oracle pricing without user-specified maximum payment amount exposes users to price volatility.

**Example Vulnerable Code**:
```rust
// VULNERABLE: No max payment parameter
pub fn purchase_tokens(amount_to_purchase: u64) -> Result<()> {
    // Get current price from oracle
    let sol_price = get_pyth_price()?;
    
    // User has no control over final cost!
    let cost = amount_to_purchase * sale.token_price / sol_price;
    transfer_sol(cost)?;
}
```

**Attack/Impact**:
- Price spikes between submission and execution
- User pays significantly more than expected
- Oracle manipulation attacks
- MEV sandwich attacks

**Secure Implementation**:
```rust
// SECURE: User specifies maximum payment
pub fn purchase_tokens(
    amount_to_purchase: u64,
    max_payment: u64  // User's slippage protection
) -> Result<()> {
    let sol_price = get_pyth_price()?;
    let cost = amount_to_purchase * sale.token_price / sol_price;
    
    // Protect user from excessive slippage
    require!(cost <= max_payment, Error::SlippageExceeded);
    
    transfer_sol(cost)?;
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - exposed users to price manipulation.

### 31. Unrestricted Sale Creation DoS

**Description**: Anyone can create sales with minimal cost, enabling spam attacks and ID exhaustion.

**Example Vulnerable Code**:
```rust
// VULNERABLE: No restrictions or fees
pub fn initialize_sale(id: u64) -> Result<()> {
    // Anyone can create with any ID!
    let sale = Sale {
        id,  // Global ID space exhaustible
        // ...
    };
}
```

**Attack Scenario**:
1. Attacker creates thousands of spam sales
2. Exhausts ID space or clutters UI
3. Creates sales with offensive content
4. Impersonates legitimate sales
5. Complete platform DoS

**Secure Implementation**:
```rust
// SECURE: Add creation fees and restrictions
pub fn initialize_sale(ctx: Context<InitializeSale>) -> Result<()> {
    // Option 1: Creation fee
    const CREATION_FEE: u64 = 1_000_000_000;  // 1 SOL
    system_program::transfer(
        ctx.accounts.creator,
        ctx.accounts.protocol_treasury,
        CREATION_FEE
    )?;
    
    // Option 2: Refundable deposit
    const DEPOSIT: u64 = 10_000_000_000;  // 10 SOL
    ctx.accounts.sale.deposit = DEPOSIT;
    ctx.accounts.sale.creator = ctx.accounts.creator.key();
    
    // Option 3: Creator in PDA seeds (prevents global exhaustion)
    // seeds = [b"sale", creator.key(), local_id]
    
    // Option 4: Permissioned creation
    require!(
        is_authorized_creator(ctx.accounts.creator.key()),
        Error::UnauthorizedCreator
    );
}
```

**Real-World Impact**: Found in Quantstamp audit of Exceed Finance - enabled spam attack vector.

### 32. Preemptive Account Creation DoS

**Description**: Malicious actors can pre-create expected PDA accounts to cause DoS for legitimate operations that need to initialize those accounts.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Lock escrow creation without checking existence
pub fn lock_pool() -> Result<()> {
    // Create lock escrow - fails if already exists!
    let escrow_instruction = Instruction {
        program_id: meteora_program_id,
        accounts: escrow_accounts,
        data: get_function_hash("global", "create_lock_escrow").into(),
    };
    
    invoke_signed(&escrow_instruction, /*...*/)?;  // Fails if exists!
}

// Lock escrow PDA doesn't require owner signature
#[account(
    init,
    seeds = [
        "lock_escrow".as_ref(),
        pool.key().as_ref(),
        owner.key().as_ref(),  // Owner is UncheckedAccount!
    ],
    bump,
    payer = payer,
)]
pub lock_escrow: UncheckedAccount<'info>,
pub owner: UncheckedAccount<'info>,  // No Signer required!
```

**Attack Scenario**:
1. Protocol needs to create lock_escrow for pool operations
2. Attacker pre-creates the lock_escrow account
3. Legitimate lock_pool operation fails with account already exists error
4. Pool locking mechanism permanently DoS'd

**Secure Implementation**:
```rust
// SECURE: Check existence before creation
pub fn lock_pool() -> Result<()> {
    // Check if lock_escrow already exists
    if ctx.accounts.lock_escrow.data_is_empty() {
        // Only create if doesn't exist
        let escrow_instruction = Instruction {
            program_id: meteora_program_id,
            accounts: escrow_accounts,
            data: get_function_hash("global", "create_lock_escrow").into(),
        };
        
        invoke_signed(&escrow_instruction, /*...*/)?;
    }
    // Continue with lock operation...
}

// Or use init_if_needed
#[account(
    init_if_needed,
    seeds = [/*...*/],
    bump,
    payer = payer,
)]
pub lock_escrow: Account<'info, LockEscrow>,
```

**Real-World Impact**: Found in C4 audit of Pump Science - lock_pool operation could be permanently DoS'd.

### 33. Missing State Variable Updates

**Description**: Critical state variables are not updated in update functions, leaving them stuck at default/initial values permanently.

**Example Vulnerable Code**:
```rust
// VULNERABLE: migration_token_allocation never updated
impl Global {
    pub fn update_settings(&mut self, params: GlobalSettingsInput) {
        self.initial_virtual_token_reserves = params.initial_virtual_token_reserves;
        self.mint_decimals = params.mint_decimals;
        self.fee_receiver = params.fee_receiver;
        // BUG: migration_token_allocation NOT updated!
        // self.migration_token_allocation remains at default
    }
}

pub struct GlobalSettingsInput {
    pub migration_token_allocation: u64,  // Provided but ignored!
    // other fields...
}
```

**Attack/Impact**:
- Admin attempts to update migration_token_allocation
- Value provided in input but never applied
- Migration process uses wrong allocation forever
- Token distribution incorrect during migration

**Secure Implementation**:
```rust
// SECURE: Update all relevant fields
impl Global {
    pub fn update_settings(&mut self, params: GlobalSettingsInput) {
        self.initial_virtual_token_reserves = params.initial_virtual_token_reserves;
        self.mint_decimals = params.mint_decimals;
        self.fee_receiver = params.fee_receiver;
        self.migration_token_allocation = params.migration_token_allocation;  // FIXED!
    }
}
```

**Real-World Impact**: Found in C4 audit of Pump Science - migration_token_allocation stuck at default value.

### 34. Dynamic Fee Calculation After Amount Lock-in

**Description**: Fees are calculated before final amounts are determined, leading to incorrect fee collection when amounts change during execution.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Fee calculated before amount finalization
pub fn swap(exact_in_amount: u64) -> Result<()> {
    // Calculate fee on initial amount
    let fee_lamports = bonding_curve.calculate_fee(exact_in_amount, clock.slot)?;
    let buy_amount_applied = exact_in_amount - fee_lamports;
    
    // Apply buy - amount might change!
    let buy_result = bonding_curve.apply_buy(buy_amount_applied)?;
    
    // Last buy adjusts price and changes actual SOL amount
    if token_amount >= self.real_token_reserves {
        // Recompute with different amount
        sol_amount = recomputed_sol_amount;  // Different from original!
        // But fee was already calculated on wrong amount!
    }
}
```

**Attack/Impact**:
- User performs last buy on bonding curve
- Fee calculated on original amount
- Price adjustment changes actual SOL amount
- Fee becomes incorrect (too high or too low)
- Protocol loses revenue or overcharges users

**Secure Implementation**:
```rust
// SECURE: Recalculate fee after amount finalization
pub fn swap(exact_in_amount: u64) -> Result<()> {
    let initial_fee = bonding_curve.calculate_fee(exact_in_amount, clock.slot)?;
    let buy_amount_applied = exact_in_amount - initial_fee;
    
    let buy_result = bonding_curve.apply_buy(buy_amount_applied)?;
    
    // Check if amount changed
    if buy_result.sol_amount != buy_amount_applied {
        // Recalculate fee on actual amount
        let actual_total = buy_result.sol_amount + initial_fee;
        let correct_fee = bonding_curve.calculate_fee(actual_total, clock.slot)?;
        
        // Adjust fee collection
        fee_lamports = correct_fee;
        
        // Revalidate user has sufficient balance
        require!(
            ctx.accounts.user.get_lamports() >= actual_total + min_rent,
            Error::InsufficientBalance
        );
    }
}
```

**Real-World Impact**: Found in C4 audit of Pump Science - last buy on bonding curve charged wrong fees.

### 35. Rent Inclusion in Balance Comparisons

**Description**: Comparing account balances that include rent against values that don't, leading to incorrect validation of invariants.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Comparing rent-inclusive balance with rent-exclusive value
pub fn check_invariant(sol_escrow: &AccountInfo, bonding_curve: &BondingCurve) -> Result<()> {
    // Get raw lamports which includes rent
    let sol_escrow_lamports = sol_escrow.lamports();
    
    // Compare against reserves which don't include rent
    if sol_escrow_lamports < bonding_curve.real_sol_reserves {
        return Err(Error::InvariantFailed);
    }
    // Passes even when actual SOL (minus rent) is insufficient!
}
```

**Attack/Impact**:
- real_sol_reserves = 100 SOL
- Actual available SOL = 99.998 SOL
- Rent = 0.002 SOL
- Total lamports = 100 SOL (includes rent)
- Check passes (100 >= 100) but should fail
- Protocol invariant violated

**Secure Implementation**:
```rust
// SECURE: Subtract rent before comparison
pub fn check_invariant(sol_escrow: &AccountInfo, bonding_curve: &BondingCurve) -> Result<()> {
    let sol_escrow_lamports = sol_escrow.lamports();
    
    // Calculate rent-exempt balance
    let rent_exemption = Rent::get()?.minimum_balance(sol_escrow.data_len());
    
    // Get actual available SOL (excluding rent)
    let available_sol = sol_escrow_lamports.saturating_sub(rent_exemption);
    
    // Compare like with like
    if available_sol < bonding_curve.real_sol_reserves {
        return Err(Error::InvariantFailed);
    }
}
```

**Real-World Impact**: Found in C4 audit of Pump Science - bonding curve invariant check incorrectly validated.

### 36. Abrupt Fee Transitions

**Description**: Fee calculation formulas create discontinuous jumps at phase boundaries instead of smooth transitions.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Abrupt 7.76% fee drop at slot boundary
pub fn calculate_fee(&self, amount: u64, current_slot: u64) -> Result<u64> {
    let slots_passed = current_slot - self.start_slot;
    
    if slots_passed < 150 {
        // Phase 1: 99% fee
        sol_fee = bps_mul(9900, amount, 10_000).unwrap();
    } else if slots_passed >= 150 && slots_passed <= 250 {
        // Phase 2: Linear decrease formula
        let fee_bps = (-8_300_000_i64)
            .checked_mul(slots_passed as i64)?
            .checked_add(2_162_600_000)?
            .checked_div(100_000)?;
        sol_fee = bps_mul(fee_bps as u64, amount, 10_000).unwrap();
        // At slot 250: fee = 8.76%
    } else if slots_passed > 250 {
        // Phase 3: 1% fee - ABRUPT DROP from 8.76%!
        sol_fee = bps_mul(100, amount, 10_000).unwrap();
    }
}
```

**Attack/Impact**:
- Slot 250: Users pay 8.76% fee
- Slot 251: Users pay 1% fee
- 7.76% instant advantage for waiting one slot
- Creates MEV opportunities
- Unfair to users transacting at boundary

**Secure Implementation**:
```rust
// SECURE: Calibrated coefficients for smooth transition
pub fn calculate_fee(&self, amount: u64, current_slot: u64) -> Result<u64> {
    let slots_passed = current_slot - self.start_slot;
    
    if slots_passed < 150 {
        sol_fee = bps_mul(9900, amount, 10_000).unwrap();
    } else if slots_passed >= 150 && slots_passed <= 250 {
        // Recalibrated formula to reach exactly 1% at slot 250
        // New coefficients ensure smooth transition
        let fee_bps = (-9_800_000_i64)  // Adjusted multiplier
            .checked_mul(slots_passed as i64)?
            .checked_add(2_470_000_000)?  // Adjusted constant
            .checked_div(100_000)?;
        sol_fee = bps_mul(fee_bps as u64, amount, 10_000).unwrap();
        // At slot 250: fee = 1.0% (matches Phase 3)
    } else {
        sol_fee = bps_mul(100, amount, 10_000).unwrap();
    }
}
```

**Real-World Impact**: Found in C4 audit of Pump Science - 7.76% fee discontinuity at slot 250-251 boundary.

### 37. Proportional Distribution Causing Token Lock

**Description**: When distributing tokens proportionally based on claimed vs sale supply, unclaimed tokens remain permanently locked in protocol accounts.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Unclaimed tokens locked forever
pub fn claim_token() -> Result<()> {
    // If claimed_supply < sale_supply, users get proportional amount
    let adjusted_tokens = ((user_stats.tokens_purchased as f64 
        / token_stats.claimed_supply as f64)
        * (token_stats.sale_supply.min(token_stats.claimed_supply) as f64))
        as u64;
    
    transfer(tokens, adjusted_tokens)?;
    // Difference between sale_supply and claimed_supply locked forever!
}

pub fn deposit_token() -> Result<()> {
    // Full sale_supply deposited initially
    transfer(token_stats.sale_supply)?;
}
```

**Attack/Impact**:
- sale_supply = 10000, claimed_supply = 8000
- Users only receive 8000 total tokens
- 2000 tokens permanently locked in stats_token
- Protocol loses funds permanently

**Secure Implementation**:
```rust
// SECURE: Allow recovery of unclaimed tokens
pub fn claim_token() -> Result<()> {
    let adjusted_tokens = calculate_proportional_amount();
    transfer(tokens, adjusted_tokens)?;
}

pub fn recover_unclaimed_tokens() -> Result<()> {
    require!(claim_period_ended, Error::ClaimPeriodActive);
    
    let unclaimed = token_stats.sale_supply - token_stats.claimed_supply;
    if unclaimed > 0 {
        transfer_to_authority(unclaimed)?;
    }
}
```

**Real-World Impact**: Found in Pashov audit of DeSci Launchpad - unclaimed tokens permanently locked.

### 38. Missing State Updates in Refund Functions

**Description**: Refund/withdrawal functions that don't update global state variables leave tokens permanently locked.

**Example Vulnerable Code**:
```rust
// VULNERABLE: withdraw doesn't update claimed_supply
pub fn withdraw_tokens() -> Result<()> {
    require!(!user_stats.is_claimed);
    require!(token_stats.revenue < token_stats.min_threshold);
    
    user_stats.is_claimed = true;  // Mark as claimed
    
    // Refund payment tokens
    let refund_amount = calculate_refund(user_stats.tokens_purchased);
    transfer(payment_tokens, refund_amount)?;
    
    // BUG: claimed_supply NOT reduced!
    // BUG: tokens_purchased NOT returned to authority!
}
```

**Attack/Impact**:
- User had tokens_purchased = 1000
- claimed_supply = 5000 before withdrawal
- After withdrawal, only 4000 tokens claimable
- 1000 tokens permanently locked

**Secure Implementation**:
```rust
// SECURE: Update all relevant state
pub fn withdraw_tokens() -> Result<()> {
    require!(!user_stats.is_claimed);
    require!(token_stats.revenue < token_stats.min_threshold);
    
    user_stats.is_claimed = true;
    
    // Update global state
    token_stats.claimed_supply -= user_stats.tokens_purchased;
    
    // Return tokens to authority
    transfer_to_authority(user_stats.tokens_purchased)?;
    
    // Refund payment
    let refund_amount = calculate_refund(user_stats.tokens_purchased);
    transfer(payment_tokens, refund_amount)?;
}
```

**Real-World Impact**: Found in Pashov audit of DeSci Launchpad - withdraw_tokens locked tokens permanently.

### 39. Admin Front-Running User Withdrawals

**Description**: Admin functions that can be called to block legitimate user withdrawals by changing protocol state.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Admin can block user withdrawals
pub fn withdraw_token() -> Result<()> {
    require!(token_stats.revenue < token_stats.min_threshold);  // Must be below threshold
    // Process withdrawal...
}

pub fn claim_revenue() -> Result<()> {
    // Admin can call this even if below threshold!
    transfer(all_revenue_to_admin)?;
    // Now withdraw_token will fail!
}
```

**Attack Scenario**:
1. Sale ends with revenue below min_threshold
2. Users should be able to withdraw
3. Admin front-runs with claim_revenue
4. User withdrawals now fail
5. Users lose their funds

**Secure Implementation**:
```rust
// SECURE: Prevent admin from blocking withdrawals
pub fn claim_revenue() -> Result<()> {
    // Only allow if threshold met
    require!(
        token_stats.revenue >= token_stats.min_threshold,
        Error::ThresholdNotMet
    );
    
    // Or add cooldown period
    require!(
        Clock::get()?.unix_timestamp > token_stats.end_time + WITHDRAWAL_PERIOD,
        Error::WithdrawalPeriodActive
    );
    
    transfer(revenue_to_admin)?;
}
```

**Real-World Impact**: Found in Pashov audit of DeSci Launchpad - admin could block user refunds.

### 40. Inconsistent Claim/Withdraw Logic

**Description**: Allowing both token claims and payment withdrawals when minimum threshold isn't met creates inconsistent states and locked funds.

**Example Vulnerable Code**:
```rust
// VULNERABLE: Both operations allowed below threshold
pub fn claim_tokens() -> Result<()> {
    // No check for min_threshold!
    transfer(tokens_to_user)?;
}

pub fn withdraw_payment() -> Result<()> {
    require!(revenue < min_threshold);
    transfer(payment_back_to_user)?;
}
```

**Attack/Impact**:
- Some users claim tokens below threshold
- Some users withdraw payments
- Uncollected payments remain locked
- Inconsistent final state

**Secure Implementation**:
```rust
// SECURE: Consistent threshold enforcement
pub fn claim_tokens() -> Result<()> {
    // Only allow claims if threshold met
    require!(
        token_stats.revenue >= token_stats.min_threshold,
        Error::ThresholdNotMet
    );
    transfer(tokens_to_user)?;
}

pub fn withdraw_payment() -> Result<()> {
    // Only allow withdrawals if threshold NOT met
    require!(
        token_stats.revenue < token_stats.min_threshold,
        Error::ThresholdMet
    );
    transfer(payment_back_to_user)?;
}
```

**Real-World Impact**: Found in Pashov audit of DeSci Launchpad - inconsistent claim/withdraw logic.

## Detection Strategies

### Automated Scanning Commands

```bash
# Missing Test Coverage
find . -name "*.rs" -path "*/tests/*" | wc -l  # Count test files
rg "#\[test\]" --type rust | wc -l  # Count test functions
rg "unimplemented!\(\)|todo!\(\)" --type rust -C 2  # Find incomplete tests

# PDA Validation Issues
rg "#\[account\(mut\)" --type rust | grep -v "seeds\|has_one"
rg "Receipt::PREFIX|receipt.*seeds" --type rust -C 3  # Check receipt PDAs

# Integer Arithmetic Issues  
rg "[\+\-\*/]" --type rust | grep -v "checked_\|saturating_\|wrapping_"

# Division Before Multiplication (Precision Loss)
rg "checked_div.*\n.*checked_div" --type rust

# Partial Interval Edge Cases
rg "price_fix_duration|number_of_intervals|current_interval" --type rust

# Stale State Variables
rg "last_|previous_|cached_|temp_|cumulative_" --type rust -C 2

# Non-Deterministic Token Accounts (Phantom Vaults)
rg "TokenAccount" --type rust -A 5 | grep -v "associated_token\|seeds"

# Hard-coded Token Account Sizes
rg "165|82" --type rust | grep -i "token\|account\|space"

# Fee Parameter Manipulation
rg "protocol_fee|integrator_fee|surplus" --type rust -C 3
rg "estimated.*amount|min.*amount" --type rust

# Native vs SPL Token Inconsistencies
rg "native_dst_asset|native_mint" --type rust -C 5
rg "system_program::transfer.*transfer_checked" --type rust -C 10

# Price Update Race Conditions
rg "update.*price|price.*update" --type rust -C 5
rg "request_withdrawal.*withdraw" --type rust -C 10

# Single Points of Failure
rg "for.*pool.*update|for.*in.*get.*pools" --type rust -C 5
rg "is_closed.*return Err" --type rust

# Signature Replay Vulnerabilities
rg "ed25519|verify.*signature" --type rust -C 5
rg "metadata.*expiry|nonce" --type rust

# Wrong Variable Validation
rg "if self\.\w+ [<>]=? self\." --type rust
rg "set_.*amount.*self\..*amount" --type rust -C 3

# Inconsistent Flag Usage
rg "enabled_flag|enabled.*check" --type rust -C 5

# Missing Signer Checks
rg "AccountInfo" --type rust | grep -v "CHECK:\|Signer"

# CPI and External Calls
rg "invoke\|cpi::\|transfer" --type rust -C 3

# Exceed Finance Specific Issues
rg "withdraw_payments|payment.*withdraw" --type rust  # Check payment withdrawal
rg "deposit_tokens.*calculate_base_purchase_cost" --type rust -C 3  # Wrong amounts
rg "restake.*expired" --type rust -C 5  # Missing transfers
rg "update_sale|end_sale" --type rust -C 3  # Sale manipulation
rg "is_frozen\(\)|freeze.*sale" --type rust  # Unimplemented freeze
rg "max_tokens_per_user.*max_tokens_total" --type rust -C 2  # Invalid params
rg "space.*size_of" --type rust | grep -v "8 \+"  # Missing discriminator
rg "window_base_token_account.*amount == 0" --type rust  # Dust DoS
rg "max_payment|slippage" --type rust  # Slippage protection
rg "initialize_sale" --type rust -C 5  # Unrestricted creation

# Pump Science / C4 Specific Issues
rg "create_lock_escrow|lock_escrow" --type rust -C 3  # Preemptive creation DoS
rg "update_settings.*migration_token_allocation" --type rust -C 5  # Missing updates
rg "calculate_fee.*apply_buy" --type rust -C 5  # Fee before amount finalization
rg "lamports\(\).*real_sol_reserves" --type rust -C 3  # Rent in comparisons
rg "slots_passed.*fee_bps" --type rust -C 5  # Fee transition discontinuities
rg "data_is_empty\(\)|init_if_needed" --type rust  # Account existence checks

# DeSci Launchpad / Pashov Specific Issues
rg "claimed_supply.*sale_supply" --type rust -C 3  # Proportional distribution locks
rg "withdraw.*is_claimed.*claimed_supply" --type rust -C 5  # Missing state updates
rg "claim_revenue.*min_threshold" --type rust -C 3  # Admin front-running
rg "claim_token.*withdraw_token" --type rust -C 5  # Inconsistent logic
rg "adjusted_tokens.*proportional" --type rust  # Token lock issues
```

### Manual Review Checklist

#### Testing Coverage
- [ ] Comprehensive test suite exists
- [ ] Unit tests for all functions
- [ ] Integration tests with mainnet fork
- [ ] Negative test cases included
- [ ] Edge cases covered
- [ ] Access control verified in tests
- [ ] State changes and invariants asserted
- [ ] Fuzz testing for financial calculations

#### Account Validation
- [ ] Every mutable PDA has seeds constraints
- [ ] Seeds include ALL security-relevant parameters
- [ ] Authority/signer is in seeds for multi-tenant systems
- [ ] Governing state/context account is in seeds when applicable
- [ ] Token accounts are deterministic (PDA or ATA)
- [ ] Receipt PDAs include sale/context address in seeds

#### Arithmetic Operations
- [ ] All arithmetic uses checked_* methods
- [ ] Multiplications before divisions
- [ ] No precision loss in financial calculations
- [ ] Edge cases handled (max values, zero, negatives)

#### State Management
- [ ] State updates before external calls
- [ ] All related state variables updated together
- [ ] No stale values used in calculations
- [ ] Proper initialization checks

#### Access Control
- [ ] Signers required for authority operations
- [ ] Owner validation for account modifications
- [ ] Context isolation between different authorities
- [ ] No privilege escalation paths
- [ ] CPI authorities are correct (PDA controls its own accounts)
- [ ] Sale parameters locked after start
- [ ] End time enforced for termination
- [ ] Freeze/unfreeze actually implemented if checked

#### Fee Management
- [ ] Protocol fees have enforced minimums
- [ ] Fee recipients are validated/fixed
- [ ] Surplus conditions cannot be bypassed
- [ ] Fee parameters validated against manipulation
- [ ] Consistent token type for fees and payments
- [ ] Payment withdrawal mechanism exists
- [ ] Collected funds can be retrieved by organizers

#### Operational Continuity
- [ ] Single failures don't block all operations
- [ ] Closed/failed components are handled gracefully
- [ ] Price updates don't affect locked amounts
- [ ] Signatures include expiry and nonce
- [ ] Input validation uses correct variables
- [ ] Different flags for different operations
- [ ] Dust amounts don't block account closure
- [ ] Base tokens transferred when restaking
- [ ] Slippage protection for oracle-based pricing
- [ ] Sale creation has anti-spam measures
- [ ] Account existence checked before creation attempts
- [ ] All state variables updated in update functions
- [ ] Fees recalculated if amounts change
- [ ] Rent excluded from balance comparisons
- [ ] Fee transitions are smooth without discontinuities
- [ ] Unclaimed tokens can be recovered
- [ ] Withdrawals update all relevant state
- [ ] Admin cannot front-run user withdrawals
- [ ] Consistent threshold logic for claims/withdrawals

## Testing Patterns

### Test Template for Vulnerabilities

```rust
#[test]
fn test_pda_validation() {
    // Setup
    let attacker = Keypair::new();
    let victim = Keypair::new();
    let victim_pda = create_pda(victim.pubkey());
    
    // Attack attempt
    let result = program.modify_pda(attacker, victim_pda);
    
    // Verify protection
    assert!(result.is_err(), "VULNERABLE: Cross-authority attack succeeded!");
}

#[test]
fn test_phantom_vault() {
    // Create official vault
    let official_vault = create_ata(state, mint);
    
    // Try to create phantom vault
    let phantom = create_token_account(state, mint, attacker_authority);
    
    // Attempt to use phantom
    let result = program.deposit(phantom, amount);
    assert!(result.is_err(), "VULNERABLE: Phantom vault accepted!");
}

#[test]
fn test_arithmetic_overflow() {
    let result = program.calculate(u64::MAX, u64::MAX);
    assert!(result.is_err() || result.unwrap() <= u64::MAX);
}
```

## Severity Classification

| Vulnerability Class | Impact | Likelihood | Priority |
|---------------------|--------|------------|----------|
| Missing test suite | Critical | High | P0 |
| Cross-sale receipt redemption | Critical | High | P0 |
| Locked payment funds | Critical | High | P0 |
| Incorrect CPI authority | Critical | High | P0 |
| Missing PDA seeds | Critical | High | P0 |
| Non-deterministic token accounts | Critical | High | P0 |
| Missing signer | Critical | High | P0 |
| Fee bypass via user parameters | Critical | High | P0 |
| Wrong amount in transfers | Critical | High | P0 |
| Missing token transfers in restaking | Critical | High | P0 |
| Preemptive account creation DoS | Critical | High | P0 |
| Missing state variable updates | Critical | High | P0 |
| Proportional distribution token lock | Critical | High | P0 |
| Missing state updates in refunds | Critical | High | P0 |
| Admin front-running withdrawals | Critical | High | P0 |
| Division before multiplication | High | High | P0 |
| Stale state variables | High | High | P0 |
| Partial interval edge cases | High | High | P0 |
| Hard-coded Token-2022 sizes | High | High | P0 |
| Precision loss in finance | High | High | P0 |
| Surplus fee manipulation | High | High | P0 |
| Price update race conditions | Critical | High | P0 |
| Single point of failure DoS | Critical | High | P0 |
| Signature replay attacks | Critical | High | P0 |
| Inconsistent claim/withdraw logic | High | High | P1 |
| Dynamic fee calculation errors | High | High | P1 |
| Rent inclusion in comparisons | High | High | P1 |
| Abrupt fee transitions | Medium | High | P1 |
| Sale updates during active sales | High | High | P1 |
| Premature sale termination | High | High | P1 |
| Unimplemented freeze functionality | Medium | High | P1 |
| Invalid sale parameter combinations | High | High | P1 |
| Missing discriminator in space | Medium | High | P1 |
| Dust attack on window closure | Medium | High | P1 |
| Missing slippage protection | High | High | P1 |
| Unrestricted sale creation DoS | High | High | P1 |
| Integer overflow | High | Medium | P1 |
| Price manipulation | Critical | Medium | P1 |
| Wrong variable validation | High | High | P1 |
| Inconsistent flag checks | High | High | P1 |
| Token type inconsistency | Medium | High | P1 |
| Missing mutability for rent | Medium | High | P1 |
| Reentrancy | High | Low | P2 |
| Double initialization | Medium | Low | P3 |

## Real-World Audit Findings

### Critical Findings
- **Pashov - DeSci Launchpad**:
  - Proportional distribution causing permanent token lock
  - Missing state updates in withdraw_tokens locking funds
  - Admin front-running user withdrawals
- **C4 - Pump Science**:
  - Preemptive account creation DoS for lock_pool operations
  - Missing state variable updates (migration_token_allocation)
- **Quantstamp - Exceed Finance**: 
  - Missing test suites in both programs
  - Cross-sale receipt redemption allowing token theft
  - Locked payment funds with no withdrawal mechanism
  - Incorrect CPI authority blocking all redemptions
  - Wrong amounts in token transfers
  - Missing base token transfers in restaking
- **Pashov - Saguaro Gatekeeper**: Missing PDA validation allowed cross-authority bitmap corruption
- **Quantstamp - Liquid Collective**: Missing state context in seeds enabled privilege escalation
- **Cyfrin - Doryoku**: Non-deterministic token accounts created phantom vault vulnerability
- **Quantstamp - Neutral Trade**: Division before multiplication caused systematic fee undercharging
- **Quantstamp - 1inch Fusion**: User-controlled fee parameters allowed complete fee bypass
- **Quantstamp - Fragmetric**: Price race conditions, single point of failure DoS, signature replay attacks

### High Severity Findings
- **Pashov - DeSci Launchpad**:
  - Inconsistent claim/withdraw logic below threshold
- **C4 - Pump Science**:
  - Dynamic fee calculation errors on last buy
  - Rent inclusion in balance comparisons breaking invariants
  - Abrupt 7.76% fee transition at slot boundary
- **Quantstamp - Exceed Finance**:
  - Sale parameter updates during active sales
  - Premature sale termination capability
  - Invalid parameter combinations accepted
  - Dust attack DoS vulnerability
  - Missing slippage protection
  - Unrestricted sale creation DoS
- **Quantstamp - ONRE**: Partial intervals caused users to overpay beyond maximum price
- **Cyfrin - Doryoku**: Hard-coded Token-2022 sizes blocked entire functionality
- **Quantstamp - Neutral Trade**: Stale state variables caused share price distortion
- **Quantstamp - 1inch Fusion**: Surplus fee bypass via parameter manipulation, token type inconsistencies
- **Quantstamp - Fragmetric**: Wrong variable validation, inconsistent flag checks blocking withdrawals

### Medium Severity Findings
- **Quantstamp - Exceed Finance**:
  - Unimplemented freeze functionality
  - Missing discriminator in space calculations

## Quick Reference

### Anti-Patterns to Avoid
```rust
// ❌ Missing test suite
// No tests directory or #[test] functions

// ❌ Receipt PDA without sale context
seeds = [Receipt::PREFIX, buyer.key()]  // Missing sale!

// ❌ No payment withdrawal mechanism
// Collected funds locked in Sale PDA forever

// ❌ Wrong CPI authority
authority: buyer.to_account_info()  // For sale's tokens!

// ❌ Wrong transfer amount
transfer(calculate_cost(amount))  // Not the parameter!

// ❌ Missing PDA validation
#[account(mut)]
pub pda: AccountLoader<'info, Data>,

// ❌ Unchecked arithmetic
let result = a + b;

// ❌ Missing signer
pub authority: AccountInfo<'info>,

// ❌ State after external call
transfer()?;
state.balance -= amount;

// ❌ Non-deterministic token account
constraint = vault.owner == state.key()

// ❌ Hard-coded sizes
let space = 165;

// ❌ User-controlled fees
let protocol_fee = order.fee;  // No minimum!

// ❌ Bypassable surplus condition
if actual > user_estimated {  // User sets estimated = MAX
    apply_surplus_fee();
}

// ❌ Price changes between operations
request_withdrawal(amount, current_price);
// ... later ...
withdraw(amount, NEW_PRICE);  // Mismatch!

// ❌ One failure blocks all
if pool.is_closed() {
    return Err(Error::AllPoolsBlocked);
}

// ❌ Replayable signatures
verify_signature(metadata);  // No expiry/nonce!

// ❌ Sale updates during active period
// No check for sale.is_start_time_reached()

// ❌ Dust blocking closure
require!(account.amount == 0)  // 1 token DoS!

// ❌ No slippage protection
let cost = amount * price / oracle_price;  // No max!

// ❌ Unrestricted creation
// Anyone can spam create sales

// ❌ No existence check before creation
invoke_signed(&create_instruction)?;  // Fails if exists

// ❌ Missing state updates
self.mint_decimals = params.mint_decimals;
// Forgot: self.important_field = params.important_field

// ❌ Fee before amount finalization
let fee = calculate_fee(amount);
let final_amount = adjust_amount();  // Changed!

// ❌ Rent included in comparison
if account.lamports() < expected_balance

// ❌ Abrupt fee transitions
if slot <= 250 { return 8.76%; }
else { return 1%; }  // 7.76% jump!
```

### Secure Patterns
```rust
// ✅ Comprehensive test suite
#[cfg(test)]
mod tests {
    #[test]
    fn test_all_scenarios() { /* ... */ }
}

// ✅ Receipt with sale context
seeds = [Receipt::PREFIX, sale.key(), buyer.key()]

// ✅ Payment withdrawal mechanism
pub fn withdraw_payments() -> Result<()> {
    transfer_to_treasury(collected_amount)?;
}

// ✅ Correct CPI authority
authority: sale.to_account_info()  // With signer seeds

// ✅ Exact parameter amounts
transfer(params.amount_to_deposit)  // Not calculated!

// ✅ Proper PDA validation
#[account(mut, seeds = [...], bump)]
pub pda: AccountLoader<'info, Data>,

// ✅ Checked arithmetic
let result = a.checked_add(b).ok_or(Error::Overflow)?;

// ✅ Required signer
pub authority: Signer<'info>,

// ✅ State before external call
state.balance -= amount;
transfer()?;

// ✅ Deterministic token account
let (vault, _) = Pubkey::find_program_address(&[b"vault"], program_id);

// ✅ Dynamic sizes
let space = calculate_token_account_space(mint)?;

// ✅ Protocol-enforced fees
const MIN_FEE: u16 = 30;
require!(fee >= MIN_FEE);

// ✅ Validated estimates
require!(estimated <= min * MAX_SLIPPAGE_RATIO / 100);

// ✅ Locked prices for withdrawals
withdrawal.locked_sol_amount = calculate_at_current_price();

// ✅ Graceful failure handling
if pool.is_closed() { continue; }  // Skip, don't fail

// ✅ Non-replayable signatures
require!(metadata.expiry > now && !used_nonces.contains(nonce));

// ✅ Sale parameter locking
require!(!sale.is_start_time_reached(), Error::SaleStarted);

// ✅ Dust tolerance
const DUST_THRESHOLD: u64 = 100;
require!(account.amount <= DUST_THRESHOLD);

// ✅ Slippage protection
require!(cost <= max_payment, Error::SlippageExceeded);

// ✅ Creation restrictions
const CREATION_FEE: u64 = 1_000_000_000;  // 1 SOL

// ✅ Check existence before creation
if account.data_is_empty() {
    invoke_signed(&create_instruction)?;
}

// ✅ Update all state variables
self.migration_token_allocation = params.migration_token_allocation;

// ✅ Recalculate fee after finalization
if final_amount != initial_amount {
    fee = calculate_fee(final_amount);
}

// ✅ Exclude rent from comparisons
let available = lamports - rent_exemption;
if available < expected_balance

// ✅ Smooth fee transitions
// Coefficients calibrated for continuity at boundaries
```

## References

- Pashov Audit Report: DeSci Launchpad (Token distribution and withdrawal vulnerabilities)
- Code4rena Audit Report: Pump Science (Bonding curve and migration vulnerabilities)
- Quantstamp Audit Report: Exceed Finance (Early Purchase & Liquid Staking programs)
- Pashov Audit Report: Saguaro Gatekeeper (Critical PDA validation flaws)
- Quantstamp Audit Reports: Liquid Collective, Neutral Trade, ONRE, 1inch Fusion, Fragmetric
- Cyfrin Audit Report: Doryoku (Phantom vaults and Token-2022)
- Anchor Framework Documentation
- SPL Token-2022 Documentation
- Solana Security Best Practices
- Neodyme Security Workshop
- Soteria & Sec3 Automated Scanners
- Ed25519 Program Documentation

## Version History

- v3.2: Added Pashov DeSci Launchpad findings - token locks, state updates, admin front-running
- v3.1: Added C4 Pump Science findings - preemptive DoS, state updates, fee calculations, rent handling
- v3.0: Added Exceed Finance findings - comprehensive token sale and liquid staking vulnerabilities
- v2.5: Added Fragmetric findings - price race conditions, DoS patterns, signature replay
- v2.4: Added 1inch Fusion findings - fee bypass patterns and token type inconsistencies
- v2.3: Added Doryoku findings - phantom vaults and Token-2022 sizing
- v2.2: Added ONRE findings - partial intervals and mutability
- v2.1: Added Neutral Trade findings - stale state and precision loss
- v2.0: Comprehensive vulnerability patterns for systematic bug hunting
- v1.0: Initial PDA validation patterns from Pashov and Quantstamp audits