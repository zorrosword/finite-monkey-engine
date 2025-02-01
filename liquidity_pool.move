module yuzuswap::liquidity_pool {

    use std::bcs;
    use std::signer;
    use std::string;
    use std::vector;

    use aptos_std::aptos_hash;
    use aptos_std::math128;
    use aptos_std::math64;
    use aptos_std::string_utils;
    use aptos_std::table::{Self, Table};
    use aptos_framework::account::{Self, SignerCapability};
    use aptos_framework::event;
    use aptos_framework::fungible_asset::{Self, FungibleStore, Metadata, FungibleAsset};
    use aptos_framework::object::{Self, Object, ExtendRef};
    use aptos_framework::primary_fungible_store;

    use yuzuswap::fixed_point;
    use yuzuswap::config;
    use yuzuswap::emergency;
    use yuzuswap::fa_helper;
    use yuzuswap::fee_tier;
    use yuzuswap::i128::{Self, I128};
    use yuzuswap::sqrt_price_math;
    use yuzuswap::swap_math;
    use yuzuswap::tick_bitmap;
    use yuzuswap::tick_math;
    use yuzuswap::tick;

    friend yuzuswap::position_nft_manager;
    friend yuzuswap::router;
    friend yuzuswap::reward_manager;

    // Errors codes.

    /// Wrong tokens ordering.
    const E_UNREACHABLE_CODE: u64 = 100;
    /// Wrong tokens ordering.
    const E_WRONG_TOKENS_ORDERING: u64 = 101;
    /// The pool is locked.
    const E_LOCKED_POOL: u64 = 102;
    /// The tick lower must be less than the tick upper.
    const E_TICK_LOWER_MUST_LESS_THAN_TICK_UPPER: u64 = 103;
    /// The tick is not spaced.
    const E_TICK_NOT_SPACED: u64 = 104;
    /// The tick exceeds the maximum tick.
    const E_EXCEED_MAX_TICK: u64 = 105;
    /// The liquidity exceeds the maximum liquidity per tick.
    const E_EXCEED_MAX_LIQUIDITY_PER_TICK: u64 = 106;
    /// Mismatch token.
    const E_TOKEN_MISMATCH: u64 = 107;
    /// Not enough token to add liquidity.
    const E_NOT_ENOUGH_TOKEN_TO_ADD_LIQUIDITY: u64 = 108;
    /// The swap amount must be greater than zero.
    const E_SWAP_AMOUNT_MUST_GREATER_THAN_ZERO: u64 = 109;
    /// Invalid limit sqrt price.
    const E_INVALID_LIMIT_SQRT_PRICE: u64 = 110;
    /// Invalid token to pay swap.
    const E_INVALID_PAY_SWAP_TOKEN: u64 = 111;
    /// Invalid pay swap amount.
    const E_INVALID_PAY_SWAP_AMOUNT: u64 = 112;
    /// The position does not exist.
    const E_POSITION_NOT_EXIST: u64 = 113;
    /// The position still has liquidity.
    const E_NOT_EMPTY_LIQUIDITY_POSITION: u64 = 114;
    /// The position still has owed fees.
    const E_NOT_EMPTY_FEE_POSITION: u64 = 115;
    /// The position still has rewards.
    const E_NOT_EMPTY_REWARD_POSITION: u64 = 116;
    /// Exceed max rewards per pool.
    const E_EXCEED_MAX_REWARDS_PER_POOL: u64 = 117;
    /// The user is not reward manager.
    const E_NOT_REWARD_MANAGER: u64 = 118;
    /// Invalid reward token.
    const E_INVALID_REWARD_TOKEN: u64 = 119;
    /// Not enough reward.
    const E_NOT_ENOUGH_REWARD: u64 = 120;

    // Constants.

    const MAX_U128: u256 = 0xffffffffffffffffffffffffffffffff;

    const MAX_REWARDS_PER_POOL: u64 = 3;

    // Structs.

    /// Stores resource account signer capability under Yuzuswap account.
    struct PoolAccountCap has key {
        signer_cap: SignerCapability,
    }

    struct LiquidityPools has key {
        all_pools: vector<Object<LiquidityPool>>,
    }

    #[resource_group_member(group = aptos_framework::object::ObjectGroup)]
    struct LiquidityPool has key {
        token_0_reserve: Object<FungibleStore>,
        token_1_reserve: Object<FungibleStore>,
        current_tick: u32,
        current_sqrt_price: u128,
        liquidity: u128,
        tick_bitmap: Table<u16, u256>,
        ticks: Table<u32, TickInfo>,
        positions: Table<vector<u8>, Position>,
        next_position_id: u64,
        fee_growth_global_0_x64: u128,
        fee_growth_global_1_x64: u128,
        protocol_fee_amount_0: u64,
        protocol_fee_amount_1: u64,
        reward_infos: vector<PoolRewardInfo>,
        reward_last_updated_at_seconds: u64,
        fee_rate: u64,
        tick_spacing: u32,
        max_liquidity_per_tick: u128,
        unlocked: bool,
        extend_ref: ExtendRef,
    }

    struct Position has store, drop {
        id: u64,
        tick_lower: u32,
        tick_upper: u32,
        liquidity: u128,
        fee_growth_inside_0_last_x64: u128,
        fee_growth_inside_1_last_x64: u128,
        tokens_owed_0: u64,
        tokens_owed_1: u64,
        reward_infos: vector<PositionRewardInfo>,
    }

    struct TickInfo has store, drop {
        liquditiy_gross: u128,
        liquidity_net: I128,
        fee_growth_outside_0_x64: u128,
        fee_growth_outside_1_x64: u128,
        reward_growths_outside: vector<u128>,
        initialized: bool,
    }

    struct PoolRewardInfo has copy, drop, store {
        token_metadata: Object<Metadata>,
        remaining_reward: u64,
        emissions_per_second: u64,
        growth_global: u128,
        manager: address,
    }

    struct PositionRewardInfo has copy, drop, store {
        reward_growth_inside_last: u128,
        amount_owed: u64,
    }

    struct SwapReciept {
        pool: Object<LiquidityPool>,
        token_metadata: Object<Metadata>,
        amount_in: u64,
    }

    // Events.

    #[event]
    struct CreatePoolEvent has drop, store {
        creator: address,
        pool: address,
        token_x: Object<Metadata>,
        token_y: Object<Metadata>,
        fee: u64,
        tick_spacing: u32,
    }

    #[event]
    struct AddLiquidityEvent has drop, store {
        user: address,
        pool: address,
        position_id: u64,
        liquidity: u128,
        amount_0: u64,
        amount_1: u64,
    }

    #[event]
    struct RemoveLiquidityEvent has drop, store {
        user: address,
        pool: address,
        position_id: u64,
        liquidity: u128,
        amount_0: u64,
        amount_1: u64,
    }

    #[event]
    struct SwapEvent has drop, store {
        pool: address,
        zero_for_one: bool,
        is_exact_in: bool,
        amount_in: u64,
        amount_out: u64,
        fee_amount: u64,
        sqrt_price_after: u128,
        liquidity_after: u128,
        tick_after: u32,
    }

    #[event]
    struct CollectFeeEvent has drop, store {
        user: address,
        pool: address,
        position_id: u64,
        amount_0: u64,
        amount_1: u64,
    }

    #[event]
    struct CollectProtocolFee has drop, store {
        admin: address,
        pool: address,
        amount_0: u64,
        amount_1: u64,
    }

    #[event]
    struct InitRewardEvent has drop, store {
        pool: address,
        reward_index: u64,
        manager: address,
    }

    #[event]
    struct UpdateRewardManagerEvent has drop, store {
        pool: address,
        reward_index: u64,
        manager: address,
    }

    #[event]
    struct UpdateRewardEmissionsEvent has drop, store {
        pool: address,
        reward_index: u64,
        manager: address,
        emissions_per_second: u64,
    }

    #[event]
    struct AddRewardEvent has drop, store {
        pool: address,
        reward_index: u64,
        manager: address,
        amount: u64,
    }

    #[event]
    struct RemoveRewardEvent has drop, store {
        pool: address,
        reward_index: u64,
        manager: address,
        amount: u64,
    }

    #[event]
    struct CollectRewardEvent has drop, store {
        user: address,
        pool: address,
        position_id: u64,
        reward_index: u64,
        amount: u64,
    }

    // Module initialization.

    fun init_module(owner: &signer) {
        let (_, signer_cap) = account::create_resource_account(owner, b"pool_account");
        move_to(owner, PoolAccountCap { signer_cap });
        move_to(owner, LiquidityPools { all_pools: vector[] });
    }

    // Public functions.

    public(friend) fun create_pool(
        sender: &signer,
        token_0: Object<Metadata>,
        token_1: Object<Metadata>,
        fee_rate: u64,
        sqrt_price: u128,
    ): Object<LiquidityPool>
    acquires PoolAccountCap, LiquidityPools {
        emergency::assert_no_emergency();

        assert!(fa_helper::is_sorted(token_0, token_1), E_WRONG_TOKENS_ORDERING);

        let tick_spacing = fee_tier::get_tick_spacing(fee_rate);
        let current_tick = tick_math::get_tick_at_sqrt_price(sqrt_price);

        let pool_account_cap = borrow_global<PoolAccountCap>(@yuzuswap);
        let pool_account = account::create_signer_with_capability(&pool_account_cap.signer_cap);

        let pool_seed = get_pool_seed(token_0, token_1, fee_rate);
        let pool_constructor_ref = &object::create_named_object(&pool_account, pool_seed);
        let pool_signer = &object::generate_signer(pool_constructor_ref);

        move_to(pool_signer, LiquidityPool {
            token_0_reserve: create_token_store(pool_signer, token_0),
            token_1_reserve: create_token_store(pool_signer, token_1),
            current_tick,
            current_sqrt_price: sqrt_price,
            liquidity: 0,
            tick_bitmap: table::new(),
            ticks: table::new(),
            positions: table::new(),
            next_position_id: 1,
            fee_growth_global_0_x64: 0,
            fee_growth_global_1_x64: 0,
            protocol_fee_amount_0: 0,
            protocol_fee_amount_1: 0,
            reward_infos: vector[],
            reward_last_updated_at_seconds: 0,
            fee_rate,
            tick_spacing,
            max_liquidity_per_tick: tick::tick_spacing_to_max_liquidity_per_tick(tick_spacing),
            unlocked: true,
            extend_ref: object::generate_extend_ref(pool_constructor_ref),
        });

        vector::push_back(
            &mut borrow_global_mut<LiquidityPools>(@yuzuswap).all_pools,
            object::object_from_constructor_ref(pool_constructor_ref),
        );

        event::emit(
            CreatePoolEvent {
                creator: signer::address_of(sender),
                pool: object::address_from_constructor_ref(pool_constructor_ref),
                token_x: token_0,
                token_y: token_1,
                fee: fee_rate,
                tick_spacing,
            },
        );

        object::object_from_constructor_ref<LiquidityPool>(pool_constructor_ref)
    }

    public fun open_position(
        user: &signer,
        pool: Object<LiquidityPool>,
        tick_lower: u32,
        tick_upper: u32,
    ): u64
    acquires LiquidityPool {
        emergency::assert_no_emergency();

        let pool_data = pool_data_mut(&pool);
        assert!(pool_data.unlocked, E_LOCKED_POOL);

        assert_ticks(tick_lower, tick_upper, pool_data.tick_spacing);

        let position_id = pool_data.next_position_id;
        let position_key = get_position_key(&signer::address_of(user), position_id);
        let position = Position {
            id: position_id,
            tick_lower,
            tick_upper,
            liquidity: 0,
            fee_growth_inside_0_last_x64: 0,
            fee_growth_inside_1_last_x64: 0,
            tokens_owed_0: 0,
            tokens_owed_1: 0,
            reward_infos: vector[],
        };

        table::add(&mut pool_data.positions, position_key, position);
        pool_data.next_position_id = pool_data.next_position_id + 1;

        position_id
    }

    public fun close_position(
        user: &signer,
        pool: Object<LiquidityPool>,
        position_id: u64,
    ) acquires LiquidityPool {
        emergency::assert_no_emergency();

        let pool_data = pool_data_mut(&pool);
        assert!(pool_data.unlocked, E_LOCKED_POOL);

        let user_address = signer::address_of(user);
        let position_key = get_position_key(&user_address, position_id);
        assert!(table::contains(&pool_data.positions, position_key), E_POSITION_NOT_EXIST);

        let position = table::borrow_mut(&mut pool_data.positions, position_key);

        assert!(position.liquidity == 0, E_NOT_EMPTY_LIQUIDITY_POSITION);
        assert!(position.tokens_owed_0 == 0, E_NOT_EMPTY_FEE_POSITION);
        assert!(position.tokens_owed_1 == 0, E_NOT_EMPTY_FEE_POSITION);
        for (i in 0..vector::length(&position.reward_infos)) {
            let reward_info = vector::borrow(&position.reward_infos, i);
            assert!(reward_info.amount_owed == 0, E_NOT_EMPTY_REWARD_POSITION);
        };

        table::remove(&mut pool_data.positions, position_key);
    }

    public fun add_liquidity(
        user: &signer,
        pool: Object<LiquidityPool>,
        position_id: u64,
        liquidity_delta: u128,
        token_0: &mut FungibleAsset,
        token_1: &mut FungibleAsset,
    ) acquires LiquidityPool {
        emergency::assert_no_emergency();

        let pool_data = pool_data_mut(&pool);
        assert!(pool_data.unlocked, E_LOCKED_POOL);

        assert!(
            fungible_asset::metadata_from_asset(token_0) == fungible_asset::store_metadata(pool_data.token_0_reserve)
                && fungible_asset::metadata_from_asset(token_1) == fungible_asset::store_metadata(pool_data.token_1_reserve),
            E_TOKEN_MISMATCH,
        );

        let user_address = signer::address_of(user);

        let (amount_0, amount_1) = modify_position(
            pool_data,
            user_address,
            position_id,
            i128::new(liquidity_delta, false),
        );

        assert!(fungible_asset::amount(token_0) >= amount_0, E_NOT_ENOUGH_TOKEN_TO_ADD_LIQUIDITY);
        assert!(fungible_asset::amount(token_1) >= amount_1, E_NOT_ENOUGH_TOKEN_TO_ADD_LIQUIDITY);

        let token_0_in = fungible_asset::extract(token_0, amount_0);
        let token_1_in = fungible_asset::extract(token_1, amount_1);
        fungible_asset::deposit(pool_data.token_0_reserve, token_0_in);
        fungible_asset::deposit(pool_data.token_1_reserve, token_1_in);

        event::emit(
            AddLiquidityEvent {
                user: user_address,
                pool: object::object_address(&pool),
                position_id,
                liquidity: liquidity_delta,
                amount_0,
                amount_1,
            },
        )
    }

    public fun remove_liquidity(
        user: &signer,
        pool: Object<LiquidityPool>,
        position_id: u64,
        liquidity_delta: u128,
    ): (FungibleAsset, FungibleAsset)
    acquires LiquidityPool, PoolAccountCap {
        emergency::assert_no_emergency();

        let pool_data = pool_data_mut(&pool);

        assert!(pool_data.unlocked, E_LOCKED_POOL);

        let user_address = signer::address_of(user);

        let (amount_0_out, amount_1_out) = modify_position(
            pool_data,
            user_address,
            position_id,
            i128::new(liquidity_delta, true),
        );

        event::emit(
            RemoveLiquidityEvent {
                user: user_address,
                pool: object::object_address(&pool),
                position_id,
                liquidity: liquidity_delta,
                amount_0: amount_0_out,
                amount_1: amount_1_out,
            },
        );

        let pool_account_signer = get_pool_account_signer();
        (
            fungible_asset::withdraw(&pool_account_signer, pool_data.token_0_reserve, amount_0_out),
            fungible_asset::withdraw(&pool_account_signer, pool_data.token_1_reserve, amount_1_out),
        )
    }

    public fun swap(
        trader: &signer,
        pool: Object<LiquidityPool>,
        zero_for_one: bool,
        is_exact_in: bool,
        specified_amount: u64,
        sqrt_price_limit: u128,
    ): (FungibleAsset, SwapReciept)
    acquires LiquidityPool, PoolAccountCap {
        emergency::assert_no_emergency();

        assert!(specified_amount > 0, E_SWAP_AMOUNT_MUST_GREATER_THAN_ZERO);

        let pool_data = pool_data_mut(&pool);

        assert!(pool_data.unlocked, E_LOCKED_POOL);
        // lock here and unlock in pay_swap function to guarantee that amount in reserves is correct, avoid error when
        // the user swaps and then immediately modifies the pool (swap in opposite direction, remove liquidity, etc.)
        // before paying the swap -> the token in reserves could not be enough to do those actions.
        pool_data.unlocked = false;

        if (zero_for_one) {
            assert!(
                sqrt_price_limit < pool_data.current_sqrt_price
                    && sqrt_price_limit >= tick_math::min_sqrt_price(),
                E_INVALID_LIMIT_SQRT_PRICE,
            );
        } else {
            assert!(
                sqrt_price_limit > pool_data.current_sqrt_price
                    && sqrt_price_limit <= tick_math::max_sqrt_price(),
                E_INVALID_LIMIT_SQRT_PRICE,
            )
        };

        let reward_growths_global = update_pool_reward_infos(pool_data);

        let tick_spacing = pool_data.tick_spacing;
        let current_sqrt_price = pool_data.current_sqrt_price;
        let current_tick = pool_data.current_tick;
        let liquidity = pool_data.liquidity;
        let remaining_amount = specified_amount;
        let calculated_amount = 0;

        let protocol_fee_rate = config::protocol_fee_rate();
        let fee_scale = config::fee_scale();
        let total_protocol_fee_amount = 0;
        let total_fee_amount = 0;
        let fee_rate = get_fee_rate(signer::address_of(trader), pool_data);
        let fee_growth_global_x64 = if (zero_for_one) {
            pool_data.fee_growth_global_0_x64
        } else {
            pool_data.fee_growth_global_1_x64
        };

        while (remaining_amount > 0 && current_sqrt_price != sqrt_price_limit) {
            let price_sqrt_start = current_sqrt_price;

            let (tick_next, is_initialized_tick) = tick_bitmap::get_next_initialized_tick_within_one_word(
                &pool_data.tick_bitmap,
                current_tick,
                tick_spacing,
                zero_for_one,
            );

            // ensure that we do not overshoot the min/max tick, as the tick bitmap is not aware of these bounds
            if (tick_next < tick::min_tick()) {
                tick_next = tick::min_tick();
            } else if (tick_next > tick::max_tick()) {
                tick_next = tick::max_tick();
            };

            let sqrt_price_next = tick_math::get_sqrt_price_at_tick(tick_next);

            let target_sqrt_price = if (zero_for_one) {
                math128::max(sqrt_price_limit, sqrt_price_next)
            } else {
                math128::min(sqrt_price_limit, sqrt_price_next)
            };
            let (sqrt_price, amount_in, amount_out, fee_amount) = swap_math::compute_swap_step(
                current_sqrt_price,
                target_sqrt_price,
                liquidity,
                remaining_amount,
                is_exact_in,
                fee_rate,
            );
            current_sqrt_price = sqrt_price;

            if (is_exact_in) {
                remaining_amount = remaining_amount - (amount_in + fee_amount);
                calculated_amount = calculated_amount + amount_out;
            } else {
                remaining_amount = remaining_amount - amount_out;
                calculated_amount = calculated_amount + (amount_in + fee_amount);
            };

            if (protocol_fee_rate > 0) {
                let protocol_fee_amount = math64::mul_div(fee_amount, protocol_fee_rate, fee_scale);
                total_protocol_fee_amount = total_protocol_fee_amount + protocol_fee_amount;

                fee_amount = fee_amount - protocol_fee_amount;
            };
            total_fee_amount = total_fee_amount + fee_amount;

            if (liquidity != 0) {
                fee_growth_global_x64 = fee_growth_global_x64 + ((fee_amount as u128) << 64) / liquidity;
            };

            // shift tick if we reached the next price
            if (sqrt_price == sqrt_price_next) {
                // if the tick is initialized, run the tick transition
                if (is_initialized_tick) {
                    // TODO: calculate oracle

                    let next_liquidity_net = cross_tick(
                        &mut pool_data.ticks,
                        tick_next,
                        if (zero_for_one) fee_growth_global_x64 else pool_data.fee_growth_global_0_x64,
                        if (zero_for_one) pool_data.fee_growth_global_1_x64 else fee_growth_global_x64,
                        &reward_growths_global,
                    );
                    // if we're moving leftward, we interpret liquidityNet as the opposite sign
                    // safe because liquidityNet cannot be type(int128).min
                    if (zero_for_one) {
                        // next_liquidity_net = -next_liquidity_net
                        next_liquidity_net = i128::new(
                            i128::abs(&next_liquidity_net),
                            !i128::is_negative(&next_liquidity_net),
                        );
                    };

                    liquidity = add_delta_liquidity(liquidity, &next_liquidity_net);
                };

                current_tick = if (zero_for_one) tick_next - 1 else tick_next;
            } else if (current_sqrt_price != price_sqrt_start) {
                current_tick = tick_math::get_tick_at_sqrt_price(sqrt_price);
            }
        };

        if (current_tick != pool_data.current_tick) {
            pool_data.current_tick = current_tick;
            pool_data.current_sqrt_price = current_sqrt_price;
        } else {
            pool_data.current_sqrt_price = current_sqrt_price;
        };

        pool_data.liquidity = liquidity;

        if (zero_for_one) {
            pool_data.fee_growth_global_0_x64 = fee_growth_global_x64;
            pool_data.protocol_fee_amount_0 = pool_data.protocol_fee_amount_0 + total_protocol_fee_amount;
        } else {
            pool_data.fee_growth_global_1_x64 = fee_growth_global_x64;
            pool_data.protocol_fee_amount_1 = pool_data.protocol_fee_amount_1 + total_protocol_fee_amount;
        };

        let (amount_in, amount_out) = if (is_exact_in) {
            (specified_amount - remaining_amount, calculated_amount)
        } else {
            (calculated_amount, specified_amount - remaining_amount)
        };

        event::emit(
            SwapEvent {
                pool: object::object_address(&pool),
                zero_for_one,
                is_exact_in,
                amount_in,
                amount_out,
                fee_amount: total_fee_amount,
                sqrt_price_after: pool_data.current_sqrt_price,
                liquidity_after: pool_data.liquidity,
                tick_after: pool_data.current_tick,
            }
        );

        // withdraw expected amount from reserves.
        let pool_account_signer = get_pool_account_signer();
        if (zero_for_one) {
            (
                fungible_asset::withdraw(&pool_account_signer, pool_data.token_1_reserve, amount_out),
                SwapReciept {
                    pool,
                    token_metadata: fungible_asset::store_metadata(pool_data.token_0_reserve),
                    amount_in,
                },
            )
        } else {
            (
                fungible_asset::withdraw(&pool_account_signer, pool_data.token_0_reserve, amount_out),
                SwapReciept {
                    pool,
                    token_metadata: fungible_asset::store_metadata(pool_data.token_1_reserve),
                    amount_in,
                },
            )
        }
    }

    public fun get_swap_receipt_amount(swap_receipt: &SwapReciept): u64 {
        swap_receipt.amount_in
    }

    public fun get_swap_receipt_token_metadata(swap_receipt: &SwapReciept): Object<Metadata> {
        swap_receipt.token_metadata
    }

    public fun pay_swap(
        token_in: FungibleAsset,
        reciept: SwapReciept,
    ) acquires LiquidityPool {
        let SwapReciept {
            pool,
            token_metadata,
            amount_in,
        } = reciept;

        assert!(token_metadata == fungible_asset::metadata_from_asset(&token_in), E_INVALID_PAY_SWAP_TOKEN);
        assert!(fungible_asset::amount(&token_in) == amount_in, E_INVALID_PAY_SWAP_AMOUNT);

        let pool_data = pool_data_mut(&pool);

        if (token_metadata == fungible_asset::store_metadata(pool_data.token_0_reserve)) {
            fungible_asset::deposit(pool_data.token_0_reserve, token_in);
        } else {
            fungible_asset::deposit(pool_data.token_1_reserve, token_in);
        };

        pool_data.unlocked = true;
    }

    public fun collect_fee(
        user: &signer,
        pool: Object<LiquidityPool>,
        position_id: u64,
        amount_0_requested: u64,
        amount_1_requested: u64,
    ): (FungibleAsset, FungibleAsset)
    acquires LiquidityPool, PoolAccountCap {
        emergency::assert_no_emergency();

        let pool_data = pool_data_mut(&pool);
        let user_address = signer::address_of(user);
        let position = get_position_mut(&mut pool_data.positions, user_address, position_id);

        // only update fee if the position has liquidity to avoid unnecessary computation
        if (position.liquidity > 0) {
            let (fee_growth_inside_0_x64, fee_growth_inside_1_x64) = get_fee_growth_inside_tick(
                &pool_data.ticks,
                position.tick_lower,
                position.tick_upper,
                pool_data.current_tick,
                pool_data.fee_growth_global_0_x64,
                pool_data.fee_growth_global_1_x64,
            );
            update_position_fee(position, fee_growth_inside_0_x64, fee_growth_inside_1_x64);
        };

        let amount_0 = math64::min(amount_0_requested, position.tokens_owed_0);
        position.tokens_owed_0 = position.tokens_owed_0 - amount_0;

        let amount_1 = math64::min(amount_1_requested, position.tokens_owed_1);
        position.tokens_owed_1 = position.tokens_owed_1 - amount_1;

        event::emit(
            CollectFeeEvent {
                user: user_address,
                pool: object::object_address(&pool),
                position_id,
                amount_0,
                amount_1,
            },
        );

        let pool_signer = get_pool_account_signer();
        (
            fungible_asset::withdraw(&pool_signer, pool_data.token_0_reserve, amount_0),
            fungible_asset::withdraw(&pool_signer, pool_data.token_1_reserve, amount_1),
        )
    }

    public fun collect_protocol_fee(
        admin: &signer,
        pool: Object<LiquidityPool>,
        amount_0_requested: u64,
        amount_1_requested: u64,
    ): (FungibleAsset, FungibleAsset)
    acquires LiquidityPool, PoolAccountCap {
        config::assert_pool_admin(admin);

        let pool_data = pool_data_mut(&pool);

        let amount_0 = math64::min(amount_0_requested, pool_data.protocol_fee_amount_0);
        pool_data.protocol_fee_amount_0 = pool_data.protocol_fee_amount_0 - amount_0;

        let amount_1 = math64::min(amount_1_requested, pool_data.protocol_fee_amount_1);
        pool_data.protocol_fee_amount_1 = pool_data.protocol_fee_amount_1 - amount_1;

        event::emit(
            CollectProtocolFee {
                admin: signer::address_of(admin),
                pool: object::object_address(&pool),
                amount_0,
                amount_1,
            },
        );

        let pool_signer = get_pool_account_signer();
        (
            fungible_asset::withdraw(&pool_signer, pool_data.token_0_reserve, amount_0),
            fungible_asset::withdraw(&pool_signer, pool_data.token_1_reserve, amount_1),
        )
    }

    public fun update_reward_manager(
        user: &signer,
        pool: Object<LiquidityPool>,
        reward_index: u64,
        new_manager: address,
    ) acquires LiquidityPool {
        let pool_data = pool_data_mut(&pool);
        let reward_info = vector::borrow(&pool_data.reward_infos, reward_index);
        assert!(reward_info.manager == signer::address_of(user), E_NOT_REWARD_MANAGER);

        let reward_info = vector::borrow_mut(&mut pool_data.reward_infos, reward_index);
        reward_info.manager = new_manager;

        event::emit(
            UpdateRewardManagerEvent {
                pool: object::object_address(&pool),
                reward_index,
                manager: new_manager,
            },
        );
    }

    public fun update_reward_emissions(
        user: &signer,
        pool: Object<LiquidityPool>,
        reward_index: u64,
        emissions_per_second: u64,
    ) acquires LiquidityPool {
        let pool_data = pool_data_mut(&pool);
        let reward_info = vector::borrow(&pool_data.reward_infos, reward_index);
        assert!(reward_info.manager == signer::address_of(user), E_NOT_REWARD_MANAGER);

        update_pool_reward_infos(pool_data);

        let reward_info = vector::borrow_mut(&mut pool_data.reward_infos, reward_index);
        reward_info.emissions_per_second = emissions_per_second;

        event::emit(
            UpdateRewardEmissionsEvent {
                pool: object::object_address(&pool),
                reward_index,
                manager: reward_info.manager,
                emissions_per_second,
            },
        );
    }

    public fun add_reward(
        user: &signer,
        pool: Object<LiquidityPool>,
        reward_index: u64,
        token: FungibleAsset,
    ) acquires LiquidityPool, PoolAccountCap {
        let pool_data = pool_data_mut(&pool);
        let reward_info = vector::borrow(&pool_data.reward_infos, reward_index);
        assert!(reward_info.manager == signer::address_of(user), E_NOT_REWARD_MANAGER);
        assert!(reward_info.token_metadata == fungible_asset::metadata_from_asset(&token), E_INVALID_REWARD_TOKEN);

        update_pool_reward_infos(pool_data);

        let reward_info = vector::borrow_mut(&mut pool_data.reward_infos, reward_index);
        let added_amount = fungible_asset::amount(&token);
        reward_info.remaining_reward = reward_info.remaining_reward + added_amount;

        let pool_acccount_address = get_pool_account_address();
        primary_fungible_store::deposit(pool_acccount_address, token);

        event::emit(
            AddRewardEvent {
                pool: object::object_address(&pool),
                reward_index,
                manager: reward_info.manager,
                amount: added_amount,
            },
        );
    }

    public fun remove_reward(
        user: &signer,
        pool: Object<LiquidityPool>,
        reward_index: u64,
        amount: u64,
    ): FungibleAsset
    acquires LiquidityPool, PoolAccountCap {
        let pool_data = pool_data_mut(&pool);
        let reward_info = vector::borrow(&pool_data.reward_infos, reward_index);
        assert!(reward_info.manager == signer::address_of(user), E_NOT_REWARD_MANAGER);

        update_pool_reward_infos(pool_data);

        let reward_info = vector::borrow_mut(&mut pool_data.reward_infos, reward_index);
        let real_amount = math64::min(reward_info.remaining_reward, amount);

        let pool_signer = get_pool_account_signer();
        let removed_reward = primary_fungible_store::withdraw(&pool_signer, reward_info.token_metadata, real_amount);

        reward_info.remaining_reward = reward_info.remaining_reward - real_amount;

        event::emit(
            RemoveRewardEvent {
                pool: object::object_address(&pool),
                reward_index,
                manager: reward_info.manager,
                amount: real_amount,
            },
        );

        removed_reward
    }

    public fun collect_reward(
        user: &signer,
        pool: Object<LiquidityPool>,
        position_id: u64,
        reward_index: u64,
        amount_requested: u64,
    ): FungibleAsset
    acquires LiquidityPool, PoolAccountCap {
        let pool_data = pool_data_mut(&pool);
        let reward_growths_global = update_pool_reward_infos(pool_data);

        let user_address = signer::address_of(user);
        let position = get_position_mut(&mut pool_data.positions, user_address, position_id);

        // only update position rewards if the position has liquidity to avoid unnecessary computation
        if (position.liquidity > 0) {
            let reward_growths_inside = get_reward_growths_inside(
                &pool_data.ticks,
                position.tick_lower,
                position.tick_upper,
                pool_data.current_tick,
                &reward_growths_global,
            );
            update_position_rewards(position, &reward_growths_inside);
        };

        let position_reward = vector::borrow_mut(&mut position.reward_infos, reward_index);

        let amount = math64::min(amount_requested, position_reward.amount_owed);
        position_reward.amount_owed = position_reward.amount_owed - amount;

        event::emit(
            CollectRewardEvent {
                user: user_address,
                pool: object::object_address(&pool),
                position_id,
                reward_index,
                amount,
            },
        );

        let pool_signer = get_pool_account_signer();
        let pool_reward = vector::borrow(&pool_data.reward_infos, reward_index);
        primary_fungible_store::withdraw(&pool_signer, pool_reward.token_metadata, amount)
    }

    fun modify_position(
        pool: &mut LiquidityPool,
        owner: address,
        position_id: u64,
        liquidity_delta: I128,
    ): (u64, u64) {
        if (i128::is_zero(&liquidity_delta)) {
            return (0, 0)
        };

        let position = update_position(
            pool,
            owner,
            position_id,
            liquidity_delta,
        );

        let (tick_lower, tick_upper) = (position.tick_lower, position.tick_upper);

        let amount0: u64 = 0;
        let amount1: u64 = 0;

        if (pool.current_tick < tick_lower) {
            amount0 = sqrt_price_math::get_amount_0_delta(
                tick_math::get_sqrt_price_at_tick(tick_lower),
                tick_math::get_sqrt_price_at_tick(tick_upper),
                i128::abs(&liquidity_delta),
                i128::is_positive(&liquidity_delta),
            );
        } else if (pool.current_tick < tick_upper) {
            // TODO: write oracle

            amount0 = sqrt_price_math::get_amount_0_delta(
                pool.current_sqrt_price,
                tick_math::get_sqrt_price_at_tick(tick_upper),
                i128::abs(&liquidity_delta),
                i128::is_positive(&liquidity_delta),
            );
            amount1 = sqrt_price_math::get_amount_1_delta(
                tick_math::get_sqrt_price_at_tick(tick_lower),
                pool.current_sqrt_price,
                i128::abs(&liquidity_delta),
                i128::is_positive(&liquidity_delta),
            );

            pool.liquidity = add_delta_liquidity(pool.liquidity, &liquidity_delta);
        } else {
            amount1 = sqrt_price_math::get_amount_1_delta(
                tick_math::get_sqrt_price_at_tick(tick_lower),
                tick_math::get_sqrt_price_at_tick(tick_upper),
                i128::abs(&liquidity_delta),
                i128::is_positive(&liquidity_delta),
            );
        };

        (amount0, amount1)
    }

    fun update_position(
        pool: &mut LiquidityPool,
        owner: address,
        position_id: u64,
        liquidity_delta: I128,
    ): &Position {
        let reward_growths_global = update_pool_reward_infos(pool);

        let position = get_position_mut(&mut pool.positions, owner, position_id);

        let flipped_tick_lower = false;
        let flipped_tick_upper = false;
        if (!i128::is_zero(&liquidity_delta)) {
            flipped_tick_lower = update_tick(
                &mut pool.ticks,
                position.tick_lower,
                pool.current_tick,
                liquidity_delta,
                pool.fee_growth_global_0_x64,
                pool.fee_growth_global_1_x64,
                false,
                pool.max_liquidity_per_tick,
            );
            flipped_tick_upper = update_tick(
                &mut pool.ticks,
                position.tick_upper,
                pool.current_tick,
                liquidity_delta,
                pool.fee_growth_global_0_x64,
                pool.fee_growth_global_1_x64,
                true,
                pool.max_liquidity_per_tick,
            );

            if (flipped_tick_lower) {
                tick_bitmap::flip_tick(&mut pool.tick_bitmap, position.tick_lower, pool.tick_spacing);
            };
            if (flipped_tick_upper) {
                tick_bitmap::flip_tick(&mut pool.tick_bitmap, position.tick_upper, pool.tick_spacing);
            };
        };

        let (fee_growth_inside_0_x64, fee_growth_inside_1_x64) =
            get_fee_growth_inside_tick(
                &pool.ticks,
                position.tick_lower,
                position.tick_upper,
                pool.current_tick,
                pool.fee_growth_global_0_x64,
                pool.fee_growth_global_1_x64,
            );
        let reward_growths_inside = get_reward_growths_inside(
            &pool.ticks,
            position.tick_lower,
            position.tick_upper,
            pool.current_tick,
            &reward_growths_global,
        );
        update_position_fee(position, fee_growth_inside_0_x64, fee_growth_inside_1_x64);
        update_position_rewards(position, &reward_growths_inside);

        position.liquidity = i128::as_u128(&i128::add(&liquidity_delta, &i128::new(position.liquidity, false)));

        // clear any tick data that is no longer needed
        if (i128::is_negative(&liquidity_delta)) {
            if (flipped_tick_lower) {
                clear_tick(&mut pool.ticks, position.tick_lower);
            };
            if (flipped_tick_upper) {
                clear_tick(&mut pool.ticks, position.tick_upper);
            };
        };

        position
    }

    fun update_position_fee(
        position: &mut Position,
        fee_growth_inside_0_x64: u128,
        fee_growth_inside_1_x64: u128,
    ) {
        let tokens_owed_0 = math128::mul_div(
            fee_growth_inside_0_x64 - position.fee_growth_inside_0_last_x64,
            position.liquidity,
            fixed_point::q64(),
        );
        let tokens_owed_1 = math128::mul_div(
            fee_growth_inside_1_x64 - position.fee_growth_inside_1_last_x64,
            position.liquidity,
            fixed_point::q64(),
        );

        position.fee_growth_inside_0_last_x64 = fee_growth_inside_0_x64;
        position.fee_growth_inside_1_last_x64 = fee_growth_inside_1_x64;

        // overflow is acceptable, have to withdraw before you hit "maximum of uint64" fees
        position.tokens_owed_0 = position.tokens_owed_0 + (tokens_owed_0 as u64);
        position.tokens_owed_1 = position.tokens_owed_1 + (tokens_owed_1 as u64);
    }

    fun update_tick(
        ticks: &mut Table<u32, TickInfo>,
        tick: u32,
        current_tick: u32,
        liquidity_delta: I128,
        fee_growth_global_0_x64: u128,
        fee_growth_global_1_x64: u128,
        is_tick_upper: bool,
        max_liquidity_per_tick: u128,
    ): bool {
        let tick_info = table::borrow_mut_with_default(ticks, tick, TickInfo {
            liquditiy_gross: 0,
            liquidity_net: i128::zero(),
            fee_growth_outside_0_x64: 0,
            fee_growth_outside_1_x64: 0,
            reward_growths_outside: vector[],
            initialized: false,
        });

        let liquidity_gross_before = tick_info.liquditiy_gross;
        let liquidity_gross_after = i128::as_u128(
            &i128::add(&liquidity_delta, &i128::new(liquidity_gross_before, false))
        );

        assert!(liquidity_gross_after <= max_liquidity_per_tick, E_EXCEED_MAX_LIQUIDITY_PER_TICK);

        let flipped = (liquidity_gross_before == 0) != (liquidity_gross_after == 0);
        if (liquidity_gross_before == 0) {
            // by convention, we assume that all growth before a tick was initialized happened _below_ the tick
            if (tick <= current_tick) {
                tick_info.fee_growth_outside_0_x64 = fee_growth_global_0_x64;
                tick_info.fee_growth_outside_1_x64 = fee_growth_global_1_x64;

                // TODO: calculate oracle
            };

            tick_info.initialized == true;
        };

        tick_info.liquditiy_gross = liquidity_gross_after;

        // when the lower (upper) tick is crossed left to right (right to left), liquidity must be added (removed)
        if (is_tick_upper) {
            tick_info.liquidity_net = i128::sub(&tick_info.liquidity_net, &liquidity_delta);
        } else {
            tick_info.liquidity_net = i128::add(&liquidity_delta, &tick_info.liquidity_net);
        };

        flipped
    }

    fun get_fee_growth_inside_tick(
        ticks: &Table<u32, TickInfo>,
        tick_lower: u32,
        tick_upper: u32,
        current_tick: u32,
        fee_growth_global_0_x64: u128,
        fee_growth_global_1_x64: u128,
    ): (u128, u128) {
        let tick_lower_info = borrow_tick_or_empty(ticks, tick_lower);
        let tick_upper_info = borrow_tick_or_empty(ticks, tick_upper);

        // calculate fee growth below
        let fee_growth_below_0_x64: u128;
        let fee_growth_below_1_x64: u128;
        if (current_tick >= tick_lower) {
            fee_growth_below_0_x64 = tick_lower_info.fee_growth_outside_0_x64;
            fee_growth_below_1_x64 = tick_lower_info.fee_growth_outside_1_x64;
        } else {
            fee_growth_below_0_x64 = fee_growth_global_0_x64 - tick_lower_info.fee_growth_outside_0_x64;
            fee_growth_below_1_x64 = fee_growth_global_1_x64 - tick_lower_info.fee_growth_outside_1_x64;
        };

        // calculate fee growth above
        let fee_growth_above_0_x64: u128;
        let fee_growth_above_1_x64: u128;
        if (current_tick < tick_upper) {
            fee_growth_above_0_x64 = tick_upper_info.fee_growth_outside_0_x64;
            fee_growth_above_1_x64 = tick_upper_info.fee_growth_outside_1_x64;
        } else {
            fee_growth_above_0_x64 = fee_growth_global_0_x64 - tick_upper_info.fee_growth_outside_0_x64;
            fee_growth_above_1_x64 = fee_growth_global_1_x64 - tick_upper_info.fee_growth_outside_1_x64;
        };

        let fee_growth_inside_0_x64 = fee_growth_global_0_x64 - fee_growth_below_0_x64 - fee_growth_above_0_x64;
        let fee_growth_inside_1_x64 = fee_growth_global_1_x64 - fee_growth_below_1_x64 - fee_growth_above_1_x64;

        (fee_growth_inside_0_x64, fee_growth_inside_1_x64)
    }

    fun cross_tick(
        ticks: &mut Table<u32, TickInfo>,
        tick: u32,
        fee_growth_global_0_x64: u128,
        fee_growth_global_1_x64: u128,
        reward_growths_global: &vector<u128>,
    ): I128 {
        let tick_info = table::borrow_mut(ticks, tick);
        tick_info.fee_growth_outside_0_x64 = fee_growth_global_0_x64 - tick_info.fee_growth_outside_0_x64;
        tick_info.fee_growth_outside_1_x64 = fee_growth_global_1_x64 - tick_info.fee_growth_outside_1_x64;

        update_reward_growths(&mut tick_info.reward_growths_outside, reward_growths_global);

        tick_info.liquidity_net
    }

    fun update_reward_growths(
        reward_growths_outside: &mut vector<u128>,
        reward_growths_global: &vector<u128>,
    ) {
        let reward_growths_outside_length = vector::length(reward_growths_outside);
        for (i in 0..vector::length(reward_growths_global)) {
            if (i >= reward_growths_outside_length) {
                vector::push_back(
                    reward_growths_outside,
                    *vector::borrow(reward_growths_global, i),
                );
            } else {
                let reward_growth_outside = vector::borrow_mut(reward_growths_outside, i);
                *reward_growth_outside = *vector::borrow(reward_growths_global, i) - *reward_growth_outside;
            };
        };
    }

    fun sub_reward_growths(
        reward_growths_global: &vector<u128>,
        reward_growths_outside: &vector<u128>,
    ): vector<u128> {
        let result = vector<u128>[];

        let reward_growths_outside_length = vector::length(reward_growths_outside);
        for (i in 0..vector::length(reward_growths_global)) {
            let reward_growth_outside = if (i >= reward_growths_outside_length) {
                0
            } else {
                *vector::borrow(reward_growths_outside, i)
            };

            vector::push_back(
                &mut result,
                *vector::borrow(reward_growths_global, i) - reward_growth_outside,
            );
        };

        result
    }

    public(friend) fun initialize_reward(
        user: &signer,
        pool: Object<LiquidityPool>,
        token_metadata: Object<Metadata>,
        manager: address,
    ) acquires LiquidityPool {
        config::assert_reward_admin(user);

        let pool_data = pool_data_mut(&pool);

        assert!(vector::length(&pool_data.reward_infos) < MAX_REWARDS_PER_POOL, E_EXCEED_MAX_REWARDS_PER_POOL);

        let poolRewardInfo = PoolRewardInfo {
            token_metadata,
            remaining_reward: 0,
            emissions_per_second: 0,
            growth_global: 0,
            manager,
        };
        vector::push_back(&mut pool_data.reward_infos, poolRewardInfo);

        event::emit(
            InitRewardEvent {
                pool: object::object_address(&pool),
                reward_index: vector::length(&pool_data.reward_infos) - 1,
                manager,
            },
        );
    }

    fun update_pool_reward_infos(pool: &mut LiquidityPool): vector<u128> {
        let current_time = 0x1::timestamp::now_seconds();
        // This should never happen.
        assert!(current_time >= pool.reward_last_updated_at_seconds, E_UNREACHABLE_CODE);

        let reward_infos = &mut pool.reward_infos;

        let reward_growths_global = 0x1::vector::empty<u128>();
        let elapsed_seconds = current_time - pool.reward_last_updated_at_seconds;

        for (i in 0..vector::length(reward_infos)) {
            let reward_info = vector::borrow_mut(reward_infos, i);
            if (pool.liquidity != 0 && elapsed_seconds != 0
                && reward_info.emissions_per_second != 0 && reward_info.remaining_reward != 0
            ) {
                let emitted_reward = elapsed_seconds * reward_info.emissions_per_second;
                emitted_reward = math64::min(emitted_reward, reward_info.remaining_reward);

                reward_info.remaining_reward = reward_info.remaining_reward - emitted_reward;

                let growth_reward = fixed_point::u64_to_x64_u128(emitted_reward) / pool.liquidity;
                reward_info.growth_global = reward_info.growth_global + growth_reward;
            };
            vector::push_back(&mut reward_growths_global, reward_info.growth_global);
        };

        pool.reward_last_updated_at_seconds = current_time;

        reward_growths_global
    }

    fun get_pool_reward_infos(pool: &LiquidityPool): vector<u128> {
        let current_time = 0x1::timestamp::now_seconds();
        // This should never happen.
        assert!(current_time >= pool.reward_last_updated_at_seconds, E_UNREACHABLE_CODE);

        let reward_infos = &pool.reward_infos;

        let reward_growths_global = 0x1::vector::empty<u128>();
        let elapsed_seconds = current_time - pool.reward_last_updated_at_seconds;

        for (i in 0..vector::length(reward_infos)) {
            let reward_info = vector::borrow(reward_infos, i);
            let reward_growth_global = reward_info.growth_global;
            if (pool.liquidity != 0 && elapsed_seconds != 0
                && reward_info.emissions_per_second != 0 && reward_info.remaining_reward != 0
            ) {
                let emitted_reward = elapsed_seconds * reward_info.emissions_per_second;
                emitted_reward = math64::min(emitted_reward, reward_info.remaining_reward);

                let growth_reward = fixed_point::u64_to_x64_u128(emitted_reward) / pool.liquidity;
                reward_growth_global = reward_info.growth_global + growth_reward;
            };
            vector::push_back(&mut reward_growths_global, reward_growth_global);
        };

        reward_growths_global
    }

    fun get_reward_growths_inside(
        ticks: &Table<u32, TickInfo>,
        tick_lower: u32,
        tick_upper: u32,
        current_tick: u32,
        reward_growths_global: &vector<u128>
    ): (vector<u128>) {
        let tick_lower_info = table::borrow(ticks, tick_lower);
        let tick_upper_info = table::borrow(ticks, tick_upper);

        // calculate reward growth below
        let reward_growths_below = if (current_tick >= tick_lower) {
            tick_lower_info.reward_growths_outside
        } else {
            sub_reward_growths(reward_growths_global, &tick_lower_info.reward_growths_outside)
        };

        // calculate fee growth above
        let reward_growths_above = if (current_tick < tick_upper) {
            tick_upper_info.reward_growths_outside
        } else {
            sub_reward_growths(reward_growths_global, &tick_upper_info.reward_growths_outside)
        };

        sub_reward_growths(
            &sub_reward_growths(reward_growths_global, &reward_growths_below),
            &reward_growths_above,
        )
    }

    fun update_position_rewards(
        position: &mut Position,
        reward_growths_inside: &vector<u128>,
    ) {
        for (i in 0..vector::length(reward_growths_inside)) {
            let liquidity = position.liquidity;
            let reward_growth_inside = *vector::borrow(reward_growths_inside, i);

            let position_reward = try_borrow_mut_reward_info(position, i);
            let amount_owed = math128::mul_div(
                reward_growth_inside - position_reward.reward_growth_inside_last,
                liquidity,
                fixed_point::q64()
            );

            position_reward.reward_growth_inside_last = reward_growth_inside;
            // overflow is acceptable, have to withdraw before you hit "maximum of uint64" fees
            position_reward.amount_owed = position_reward.amount_owed + (amount_owed as u64);
        };
    }

    fun try_borrow_mut_reward_info(position: &mut Position, i: u64): &mut PositionRewardInfo {
        let len = vector::length(&position.reward_infos);
        if (i >= len) {
            vector::push_back(&mut position.reward_infos, PositionRewardInfo {
                reward_growth_inside_last: 0,
                amount_owed: 0
            });
        };

        vector::borrow_mut(&mut position.reward_infos, i)
    }

    /// Returns the word and bit position of the tick within the bitmap.
    fun tick_bitmap_position(tick: u32): (u16, u8) {
        let word_position = ((tick >> 8) as u16);
        let bit_position = ((tick % 256) as u8);

        (word_position, bit_position)
    }

    fun clear_tick(ticks: &mut Table<u32, TickInfo>, tick: u32) {
        table::remove(ticks, tick);
    }

    fun assert_ticks(tick_lower: u32, tick_upper: u32, tick_spacing: u32) {
        assert!(tick_lower < tick_upper, E_TICK_LOWER_MUST_LESS_THAN_TICK_UPPER);
        assert!(
            tick::is_spaced_tick(tick_lower, tick_spacing) && tick::is_spaced_tick(tick_upper, tick_spacing),
            E_TICK_NOT_SPACED
        );
        assert!(tick_upper <= tick::max_tick(), E_EXCEED_MAX_TICK);
    }

    fun add_delta_liquidity(liquidity: u128, delta_liquidity: &I128): u128 {
        let liqudity_after = if (i128::is_positive(delta_liquidity)) {
            (liquidity as u256) + (i128::abs(delta_liquidity) as u256)
        } else {
            assert!(liquidity >= i128::abs(delta_liquidity), E_EXCEED_MAX_LIQUIDITY_PER_TICK);
            (liquidity as u256) - (i128::abs(delta_liquidity) as u256)
        };
        assert!(liqudity_after <= MAX_U128, 1);

        (liqudity_after as u128)
    }

    fun get_position_mut(
        positions: &mut Table<vector<u8>, Position>,
        owner: address,
        position_id: u64,
    ): &mut Position {
        let position_key = get_position_key(&owner, position_id);
        assert!(table::contains(positions, position_key), E_POSITION_NOT_EXIST);

        table::borrow_mut(positions, position_key)
    }

    fun get_position_key(
        owner: &address,
        position_id: u64,
    ): vector<u8> {
        let position_key_raw_data = string::bytes(
            &string_utils::format2(&b"{}-{}", *owner, position_id)
        );
        aptos_hash::keccak256(*position_key_raw_data)
    }

    fun get_fee_rate(trader: address, pool: &LiquidityPool): u64 {
        config::get_trader_fee_rate(trader, pool.fee_rate)
    }

    fun get_pool_account_address(): address acquires PoolAccountCap {
        account::get_signer_capability_address(&borrow_global<PoolAccountCap>(@yuzuswap).signer_cap)
    }

    fun get_pool_account_signer(): signer acquires PoolAccountCap {
        account::create_signer_with_capability(&borrow_global<PoolAccountCap>(@yuzuswap).signer_cap)
    }

    // Inline functions.

    inline fun pool_data_mut(pool: &Object<LiquidityPool>): &mut LiquidityPool {
        borrow_global_mut<LiquidityPool>(object::object_address(pool))
    }

    inline fun pool_data(pool: &Object<LiquidityPool>): &LiquidityPool {
        borrow_global<LiquidityPool>(object::object_address(pool))
    }

    inline fun get_pool_seed(token_0: Object<Metadata>, token_1: Object<Metadata>, fee: u64): vector<u8> {
        let seed = vector[];
        vector::append(&mut seed, b"pool");
        vector::append(&mut seed, bcs::to_bytes(&object::object_address(&token_0)));
        vector::append(&mut seed, bcs::to_bytes(&object::object_address(&token_1)));
        vector::append(&mut seed, bcs::to_bytes(&fee));
        seed
    }

    inline fun create_token_store(pool_signer: &signer, token: Object<Metadata>): Object<FungibleStore> {
        let constructor_ref = &object::create_object_from_object(pool_signer);
        fungible_asset::create_store(constructor_ref, token)
    }

    inline fun borrow_tick_or_empty(ticks: &Table<u32, TickInfo>, tick: u32): &TickInfo {
        if (table::contains(ticks, tick)) {
            table::borrow(ticks, tick)
        } else {
            &TickInfo {
                liquditiy_gross: 0,
                liquidity_net: i128::zero(),
                fee_growth_outside_0_x64: 0,
                fee_growth_outside_1_x64: 0,
                reward_growths_outside: vector[],
                initialized: false,
            }
        }
    }

    public(friend) fun get_pool_signer(pool: Object<LiquidityPool>): signer acquires LiquidityPool {
        object::generate_signer_for_extending(&pool_data(&pool).extend_ref)
    }

    // View functions.

    #[view]
    public fun get_pool(
        token_x: Object<Metadata>,
        token_y: Object<Metadata>,
        fee: u64,
    ): Object<LiquidityPool> acquires PoolAccountCap {
        object::address_to_object<LiquidityPool>(get_pool_address(token_x, token_y, fee))
    }

    #[view]
    public fun get_all_pools(): vector<Object<LiquidityPool>> acquires LiquidityPools {
        borrow_global<LiquidityPools>(@yuzuswap).all_pools
    }

    #[view]
    public fun count_pool(): u64 acquires LiquidityPools {
        vector::length(&borrow_global<LiquidityPools>(@yuzuswap).all_pools)
    }

    #[view]
    public fun get_pool_info(
        pool: Object<LiquidityPool>,
    ): (
        Object<Metadata>,
        Object<Metadata>,
        u128,
        u32,
        u128,
        u64,
        u32,
    )
    acquires LiquidityPool {
        let pool_data = pool_data(&pool);

        (
            fungible_asset::store_metadata(pool_data.token_0_reserve),
            fungible_asset::store_metadata(pool_data.token_1_reserve),
            pool_data.current_sqrt_price,
            pool_data.current_tick,
            pool_data.liquidity,
            pool_data.fee_rate,
            pool_data.tick_spacing,
        )
    }

    #[view]
    public fun rewards_count(
        pool: Object<LiquidityPool>,
    ): u64
    acquires LiquidityPool {
        vector::length(&pool_data(&pool).reward_infos)
    }

    struct TickView has copy, drop, store {
        tick: u32,
        liquidity_gross: u128,
        liquidity_net: I128,
        fee_growth_outside_0_x64: u128,
        fee_growth_outside_1_x64: u128,
        reward_growths_outside: vector<u128>,
    }

    #[view]
    public fun get_ticks(
        pool: Object<LiquidityPool>,
        start_tick: u32,
        limit: u32,
    ): (vector<TickView>)
    acquires LiquidityPool {
        let pool_data = pool_data(&pool);

        let tick_count = 0;
        let ticks = vector<TickView>[];
        let max_count = (((tick::max_tick() / pool_data.tick_spacing) >> 8) as u16);

        let tick_spacing = pool_data.tick_spacing;
        let tick_adjustment = tick::tick_adjustment(tick_spacing);
        let adjusted_start_tick = if (start_tick >= tick_adjustment) start_tick - tick_adjustment else 0;
        let compessed_start_tick = (math64::ceil_div((adjusted_start_tick as u64), (tick_spacing as u64)) as u32);

        let i = ((compessed_start_tick >> 8) as u16);
        let first_position_in_word = compessed_start_tick % 256;
        while (i <= max_count && tick_count < limit) {
            let word = *table::borrow_with_default(&pool_data.tick_bitmap, i, &0);
            if (word == 0) {
                i = i + 1;
                continue
            };

            let mask: u256;
            let j = first_position_in_word;
            while (j < 256) {
                mask = 1 << (j as u8);

                if (mask & word != 0) {
                    let tick: u32 = (((i as u32) << 8) + j) * pool_data.tick_spacing + tick_adjustment;
                    let tick_info = table::borrow(&pool_data.ticks, tick);

                    vector::push_back(&mut ticks, TickView {
                        tick,
                        liquidity_gross: tick_info.liquditiy_gross,
                        liquidity_net: tick_info.liquidity_net,
                        fee_growth_outside_0_x64: tick_info.fee_growth_outside_0_x64,
                        fee_growth_outside_1_x64: tick_info.fee_growth_outside_1_x64,
                        reward_growths_outside: tick_info.reward_growths_outside,
                    });
                    tick_count = tick_count + 1;

                    if (tick_count >= limit) {
                        break
                    };
                };

                j = j + 1;
            };
            first_position_in_word = 0;

            i = i + 1;
        };

        return ticks
    }

    #[view]
    public fun get_pool_address(
        token_x: Object<Metadata>,
        token_y: Object<Metadata>,
        fee: u64,
    ): address acquires PoolAccountCap {
        object::create_object_address(&get_pool_account_address(), get_pool_seed(token_x, token_y, fee))
    }

    #[view]
    public fun get_tokens(
        pool: Object<LiquidityPool>,
    ): (Object<Metadata>, Object<Metadata>)
    acquires LiquidityPool {
        (
            fungible_asset::store_metadata(pool_data(&pool).token_0_reserve),
            fungible_asset::store_metadata(pool_data(&pool).token_1_reserve),
        )
    }

    #[view]
    public fun get_reserves_size(pool: Object<LiquidityPool>): (u64, u64) acquires LiquidityPool {
        let pool_data = pool_data_mut(&pool);

        let amount_0 = fungible_asset::balance(pool_data.token_0_reserve);
        let amount_1 = fungible_asset::balance(pool_data.token_1_reserve);

        (amount_0, amount_1)
    }

    // Struct for view purpose.
    struct LiquidityPoolView has drop {
        pool_addr: address,
        token_0: address,
        token_1: address,
        token_0_decimals: u8,
        token_1_decimals: u8,
        token_0_reserve: u64,
        token_1_reserve: u64,
        current_tick: u32,
        current_sqrt_price: u128,
        liquidity: u128,
        fee_growth_global_0_x64: u128,
        fee_growth_global_1_x64: u128,
        reward_infos: vector<PoolRewardInfo>,
        fee_rate: u64,
        tick_spacing: u32,
    }

    #[view]
    public fun get_pool_view(pool: Object<LiquidityPool>): LiquidityPoolView acquires LiquidityPool {
        map_pool_view(&pool)
    }

    #[view]
    public fun get_pool_views(
        offset: u64,
        limit: u64,
    ): vector<LiquidityPoolView>
    acquires LiquidityPool, LiquidityPools {
        let pools = &borrow_global<LiquidityPools>(@yuzuswap).all_pools;

        let pool_views = vector<LiquidityPoolView>[];
        for (i in offset..math64::min(vector::length(pools), offset + limit)) {
            let pool = vector::borrow(pools, i);

            vector::push_back(&mut pool_views, map_pool_view(pool));
        };

        return pool_views
    }

    fun map_pool_view(pool: &Object<LiquidityPool>): LiquidityPoolView acquires LiquidityPool {
        let pool_data = pool_data(pool);

        let token_0_metadata = fungible_asset::store_metadata(pool_data.token_0_reserve);
        let token_1_metadata = fungible_asset::store_metadata(pool_data.token_1_reserve);

        LiquidityPoolView {
            pool_addr: object::object_address(pool),
            token_0: object::object_address( &token_0_metadata),
            token_1: object::object_address( &token_1_metadata),
            token_0_decimals: fungible_asset::decimals(token_0_metadata),
            token_1_decimals: fungible_asset::decimals(token_1_metadata),
            token_0_reserve: fungible_asset::balance(pool_data.token_0_reserve),
            token_1_reserve: fungible_asset::balance(pool_data.token_1_reserve),
            current_tick: pool_data.current_tick,
            current_sqrt_price: pool_data.current_sqrt_price,
            liquidity: pool_data.liquidity,
            fee_growth_global_0_x64: pool_data.fee_growth_global_0_x64,
            fee_growth_global_1_x64: pool_data.fee_growth_global_1_x64,
            reward_infos: pool_data.reward_infos,
            fee_rate: pool_data.fee_rate,
            tick_spacing: pool_data.tick_spacing,
        }
    }

    #[view]
    public fun get_position(
        owner: address,
        pool: Object<LiquidityPool>,
        position_id: u64,
    ): Position
    acquires LiquidityPool {
        let position = table::borrow(&pool_data(&pool).positions, get_position_key(&owner, position_id));

        Position {
            id: position.id,
            tick_lower: position.tick_lower,
            tick_upper: position.tick_upper,
            liquidity: position.liquidity,
            fee_growth_inside_0_last_x64: position.fee_growth_inside_0_last_x64,
            fee_growth_inside_1_last_x64: position.fee_growth_inside_1_last_x64,
            tokens_owed_0: position.tokens_owed_0,
            tokens_owed_1: position.tokens_owed_1,
            reward_infos: position.reward_infos,
        }
    }

    #[view]
    public fun get_position_with_pending_fees_and_rewards(
        owner: address,
        pool: Object<LiquidityPool>,
        position_id: u64,
    ): Position acquires LiquidityPool {
        let position = get_position(owner, pool, position_id);
        let pool_data = pool_data(&pool);

        let position_view = Position {
            id: position.id,
            liquidity: position.liquidity,
            tick_lower: position.tick_lower,
            tick_upper: position.tick_upper,
            fee_growth_inside_0_last_x64: position.fee_growth_inside_0_last_x64,
            fee_growth_inside_1_last_x64: position.fee_growth_inside_1_last_x64,
            tokens_owed_0: position.tokens_owed_0,
            tokens_owed_1: position.tokens_owed_1,
            reward_infos: position.reward_infos,
        };

        if (position.liquidity == 0) {
            return position_view
        };

        let (fee_growth_inside_0_x64, fee_growth_inside_1_x64) = get_fee_growth_inside_tick(
            &pool_data.ticks,
            position.tick_lower,
            position.tick_upper,
            pool_data.current_tick,
            pool_data.fee_growth_global_0_x64,
            pool_data.fee_growth_global_1_x64,
        );
        update_position_fee(&mut position_view, fee_growth_inside_0_x64, fee_growth_inside_1_x64);

        let reward_growths_global = get_pool_reward_infos(pool_data);
        let reward_growths_inside = get_reward_growths_inside(
            &pool_data.ticks,
            position.tick_lower,
            position.tick_upper,
            pool_data.current_tick,
            &reward_growths_global,
        );
        update_position_rewards(&mut position_view, &reward_growths_inside);

        position_view
    }

    #[view]
    public fun get_position_info(
        owner: address,
        pool: Object<LiquidityPool>,
        position_id: u64,
    ): (u128, u32, u32, u64, u64) acquires LiquidityPool {
        let pool_data = pool_data_mut(&pool);
        let position = get_position_mut(&mut pool_data.positions, owner, position_id);

        (
            position.liquidity,
            position.tick_lower,
            position.tick_upper,
            position.tokens_owed_0,
            position.tokens_owed_1,
        )
    }

    #[view]
    public fun quote_swap(
        trader: address,
        pool: Object<LiquidityPool>,
        zero_for_one: bool,
        is_exact_in: bool,
        specified_amount: u64,
        sqrt_price_limit: u128,
    ): (u64, u64, u64) acquires LiquidityPool {
        assert!(specified_amount > 0, E_SWAP_AMOUNT_MUST_GREATER_THAN_ZERO);

        let pool_data = pool_data(&pool);

        if (zero_for_one) {
            assert!(
                sqrt_price_limit < pool_data.current_sqrt_price
                    && sqrt_price_limit >= tick_math::min_sqrt_price(),
                E_INVALID_LIMIT_SQRT_PRICE,
            );
        } else {
            assert!(
                sqrt_price_limit > pool_data.current_sqrt_price
                    && sqrt_price_limit <= tick_math::max_sqrt_price(),
                E_INVALID_LIMIT_SQRT_PRICE,
            )
        };

        let tick_spacing = pool_data.tick_spacing;
        let current_sqrt_price = pool_data.current_sqrt_price;
        let current_tick = pool_data.current_tick;
        let liquidity = pool_data.liquidity;
        let remaining_amount = specified_amount;
        let calculated_amount = 0;
        let total_fee_amount = 0;
        let fee_rate = get_fee_rate(trader, pool_data);

        while (remaining_amount > 0 && current_sqrt_price != sqrt_price_limit) {
            let price_sqrt_start = current_sqrt_price;

            let (tick_next, is_initialized_tick) = tick_bitmap::get_next_initialized_tick_within_one_word(
                &pool_data.tick_bitmap,
                current_tick,
                tick_spacing,
                zero_for_one,
            );

            // ensure that we do not overshoot the min/max tick, as the tick bitmap is not aware of these bounds
            if (tick_next < tick::min_tick()) {
                tick_next = tick::min_tick();
            } else if (tick_next > tick::max_tick()) {
                tick_next = tick::max_tick();
            };

            let sqrt_price_next = tick_math::get_sqrt_price_at_tick(tick_next);

            let target_sqrt_price = if (zero_for_one) {
                math128::max(sqrt_price_limit, sqrt_price_next)
            } else {
                math128::min(sqrt_price_limit, sqrt_price_next)
            };
            let (sqrt_price, amount_in, amount_out, fee_amount) = swap_math::compute_swap_step(
                current_sqrt_price,
                target_sqrt_price,
                liquidity,
                remaining_amount,
                is_exact_in,
                fee_rate,
            );
            current_sqrt_price = sqrt_price;

            if (is_exact_in) {
                remaining_amount = remaining_amount - (amount_in + fee_amount);
                calculated_amount = calculated_amount + amount_out;
            } else {
                remaining_amount = remaining_amount - amount_out;
                calculated_amount = calculated_amount + (amount_in + fee_amount);
            };

            total_fee_amount = total_fee_amount + fee_amount;

            // shift tick if we reached the next price
            if (sqrt_price == sqrt_price_next) {
                if (is_initialized_tick) {
                    let next_liquidity_net = table::borrow(&pool_data.ticks, tick_next).liquidity_net;

                    if (zero_for_one) {
                        // next_liquidity_net = -next_liquidity_net
                        next_liquidity_net = i128::new(
                            i128::abs(&next_liquidity_net),
                            !i128::is_negative(&next_liquidity_net),
                        );
                    };

                    liquidity = add_delta_liquidity(liquidity, &next_liquidity_net);
                };

                current_tick = if (zero_for_one) tick_next - 1 else tick_next;
            } else if (current_sqrt_price != price_sqrt_start) {
                current_tick = tick_math::get_tick_at_sqrt_price(sqrt_price);
            }
        };

        let (amount_in, amount_out) = if (is_exact_in) {
            (specified_amount - remaining_amount, calculated_amount)
        } else {
            (calculated_amount, specified_amount - remaining_amount)
        };

        (amount_in, amount_out, total_fee_amount)
    }

    // Tests.

    #[test_only]
    friend yuzuswap::test_pool;
    #[test_only]
    friend yuzuswap::liquidity_pool_tests;
    #[test_only]
    friend yuzuswap::liquidity_pool_liquidity_tests;
    #[test_only]
    friend yuzuswap::liqudity_pool_swap_tests;
    #[test_only]
    friend yuzuswap::liquidity_pool_reward_tests;
    #[test_only]
    friend yuzuswap::position_nft_manager_tests;
    #[test_only]
    friend yuzuswap::router_tests;
    #[test_only]
    friend yuzuswap::router_swap_tests;

    #[test_only]
    public fun initialize_for_test(owner: &signer) {
        init_module(owner);
    }

    #[test_only]
    public fun get_fee(pool: Object<LiquidityPool>): u64 acquires LiquidityPool {
        pool_data(&pool).fee_rate
    }

    #[test_only]
    public fun get_tick_spacing(pool: Object<LiquidityPool>): u32 acquires LiquidityPool {
        pool_data(&pool).tick_spacing
    }

    #[test_only]
    public fun get_current_tick(pool: Object<LiquidityPool>): u32 acquires LiquidityPool {
        pool_data(&pool).current_tick
    }

    #[test_only]
    public fun get_current_sqrt_price(pool: Object<LiquidityPool>): u128 acquires LiquidityPool {
        pool_data(&pool).current_sqrt_price
    }

    #[test_only]
    public fun get_liquidity(pool: Object<LiquidityPool>): u128 acquires LiquidityPool {
        pool_data(&pool).liquidity
    }

    #[test_only]
    public fun get_fee_growth_global(pool: Object<LiquidityPool>): (u128, u128) acquires LiquidityPool {
        let pool_data = pool_data(&pool);

        (
            pool_data.fee_growth_global_0_x64,
            pool_data.fee_growth_global_1_x64,
        )
    }

    #[test_only]
    public fun is_position_exists(
        owner: address,
        pool: Object<LiquidityPool>,
        position_id: u64,
    ): bool
    acquires LiquidityPool {
        let pool_data = pool_data(&pool);
        let position_key = get_position_key(&owner, position_id);

        table::contains(&pool_data.positions, position_key)
    }

    #[test_only]
    public fun extract_position(
        position: &Position,
    ): (
        u64, u32, u32, u128, u128, u128, u64, u64,
        vector<PositionRewardInfo>,
    ) {
        (
            position.id,
            position.tick_lower,
            position.tick_upper,
            position.liquidity,
            position.fee_growth_inside_0_last_x64,
            position.fee_growth_inside_1_last_x64,
            position.tokens_owed_0,
            position.tokens_owed_1,
            position.reward_infos,
        )
    }

    #[test_only]
    public fun get_reward_info(
        pool: Object<LiquidityPool>,
        reward_index: u64,
    ): (Object<Metadata>, u64, u64, u128, address) acquires LiquidityPool {
        let pool_data = pool_data(&pool);
        let reward_info = vector::borrow(&pool_data.reward_infos, reward_index);

        (
            reward_info.token_metadata,
            reward_info.remaining_reward,
            reward_info.emissions_per_second,
            reward_info.growth_global,
            reward_info.manager,
        )
    }

    #[test_only]
    public fun extract_tick_view(tick_view: &TickView): (u32, u128, I128, u128, u128, vector<u128>) {
        (
            tick_view.tick,
            tick_view.liquidity_gross,
            tick_view.liquidity_net,
            tick_view.fee_growth_outside_0_x64,
            tick_view.fee_growth_outside_1_x64,
            tick_view.reward_growths_outside,
        )
    }
}
