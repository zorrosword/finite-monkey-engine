# 使用 Pre-Postcondition 验证漏洞的方法

## 核心思想

通过定义和验证函数的**契约（Contract）**，来判断是否存在漏洞：
- **Precondition（前置条件）**：函数调用前必须满足的条件
- **Postcondition（后置条件）**：函数成功返回后保证满足的条件
- **Invariant（不变量）**：整个执行过程中必须保持的属性

## 应用到 LayerZero 漏洞验证

### 步骤 1：为关键函数定义契约

#### 函数 1: `get_effective_msglib_ptb_builder`

```move
/// @precondition: lib 是一个有效的地址
/// @postcondition: 
///   - 要么返回一个已注册的 builder 地址 (is_registered(result) == true)
///   - 要么 abort with EBuilderNotFound
/// @ensures: never returns an unregistered address
public fun get_effective_msglib_ptb_builder(
    self: &EndpointPtbBuilder, 
    oapp: address, 
    lib: address
): address {
    let builder = *table_ext::borrow_with_default!(
        &self.oapp_configs, 
        OAppConfigKey { oapp, lib }, 
        &DEFAULT_BUILDER
    );
    if (builder != DEFAULT_BUILDER) {
        builder  
        // @assert: is_registered(builder) by precondition of set_msglib_ptb_builder
    } else {
        self.get_default_msglib_ptb_builder(lib)
        // @assert: either returns registered address or aborts
    }
}
```

**关键后置条件**：
```
POSTCOND_1: ∀ result. (function_returns(result) ⟹ is_registered(result))
POSTCOND_2: ∨ function_aborts_with(EBuilderNotFound)
```

#### 函数 2: `get_default_msglib_ptb_builder`

```move
/// @precondition: lib 是一个有效的地址
/// @postcondition:
///   - 要么返回 default_configs[lib] (must be registered)
///   - 要么 abort with EBuilderNotFound (if lib not in default_configs)
/// @ensures: never returns @0x0 or unregistered address
public fun get_default_msglib_ptb_builder(
    self: &EndpointPtbBuilder, 
    lib: address
): address {
    *table_ext::borrow_or_abort!(&self.default_configs, lib, EBuilderNotFound)
    // @assert: if exists, must be registered (by set_default_msglib_ptb_builder)
}
```

**关键后置条件**：
```
POSTCOND_1: (lib ∈ default_configs) ⟹ is_registered(default_configs[lib])
POSTCOND_2: (lib ∉ default_configs) ⟹ abort(EBuilderNotFound)
```

#### 函数 3: `get_msglib_ptb_builder_info`

```move
/// @precondition: builder 必须是已注册的地址
/// @postcondition: 返回 builder 的信息
/// @aborts_if: !is_registered(builder) with EBuilderNotFound
public fun get_msglib_ptb_builder_info(
    self: &EndpointPtbBuilder, 
    builder: address
): &MsglibPtbBuilderInfo {
    assert!(self.is_msglib_ptb_builder_registered(builder), EBuilderNotFound);
    &self.registry.builder_infos[builder]
}
```

**前置条件**：
```
PRECOND: is_registered(builder) == true
```

### 步骤 2：验证调用链的契约兼容性

#### 在 `build_quote_ptb` 中的调用：

```move
// 调用 1
let msglib_ptb_builder_address = self.get_effective_msglib_ptb_builder(sender, quote_lib);

// 验证点：msglib_ptb_builder_address 满足什么条件？
// 根据 get_effective_msglib_ptb_builder 的后置条件：
//   - 要么 is_registered(msglib_ptb_builder_address) == true
//   - 要么函数已经 abort，不会执行到这里

// 调用 2
let msglib_ptb_builder_info = self.get_msglib_ptb_builder_info(msglib_ptb_builder_address);

// 验证点：get_msglib_ptb_builder_info 的前置条件是否满足？
// 前置条件：is_registered(msglib_ptb_builder_address) == true
// 由调用 1 的后置条件保证：✅ 满足
```

### 步骤 3：形式化验证

使用霍尔逻辑（Hoare Logic）：

```
{P} C {Q}
```
表示：如果前置条件 P 成立，执行命令 C，则后置条件 Q 成立。

#### 验证链条：

```
// get_default_msglib_ptb_builder 的契约
{lib is valid}
  get_default_msglib_ptb_builder(lib)
{(result is registered) ∨ abort}

// get_effective_msglib_ptb_builder 的契约
{oapp, lib are valid}
  if builder != DEFAULT_BUILDER then
    return builder  // {builder is registered}
  else
    return get_default_msglib_ptb_builder(lib)  // {result is registered ∨ abort}
{(result is registered) ∨ abort}

// build_quote_ptb 的验证
{sender, dst_eid are valid}
  builder := get_effective_msglib_ptb_builder(sender, quote_lib)
  // 现在：(builder is registered) ∨ (aborted, 不会继续执行)
  
  // 如果执行到这里，说明没有 abort，因此 builder is registered
  {builder is registered}
  
  info := get_msglib_ptb_builder_info(builder)
  // 前置条件满足：✅ builder is registered
  
{success ∨ abort}
```

### 步骤 4：漏洞判定规则

**规则 1：契约兼容性检查**
```python
def is_vulnerable(caller_function, callee_function):
    """检查调用是否违反契约"""
    # 获取调用点的状态
    call_site_state = get_state_at_call_site(caller_function, callee_function)
    
    # 获取被调用函数的前置条件
    preconditions = get_preconditions(callee_function)
    
    # 检查前置条件是否满足
    for precond in preconditions:
        if not call_site_state.satisfies(precond):
            return True  # 漏洞：前置条件不满足
    
    return False  # 安全：前置条件满足
```

**规则 2：属性验证**

对于这个案例，关键属性是：
```
PROPERTY: ∀ address passed to get_msglib_ptb_builder_info, 
          address must be registered
```

验证：
```python
def verify_property():
    # 获取 get_effective_msglib_ptb_builder 的后置条件
    postcond = get_postcondition('get_effective_msglib_ptb_builder')
    
    # 检查后置条件是否保证属性
    if postcond.guarantees('result is registered OR abort'):
        # 如果返回，则保证 registered
        # 如果 abort，则不会继续执行
        return "SAFE"
    else:
        return "VULNERABLE"
```

## 实现方案

### 方案 1：基于规范的验证（Specification-based）

```python
class FunctionContract:
    def __init__(self, function_name):
        self.function_name = function_name
        self.preconditions = []
        self.postconditions = []
        self.aborts_when = []
    
    def add_precondition(self, condition):
        """添加前置条件"""
        self.preconditions.append(condition)
    
    def add_postcondition(self, condition):
        """添加后置条件"""
        self.postconditions.append(condition)
    
    def add_abort_condition(self, condition):
        """添加 abort 条件"""
        self.aborts_when.append(condition)
    
    def guarantees_on_return(self, property):
        """检查正常返回时是否保证某个属性"""
        return any(postcond.implies(property) for postcond in self.postconditions)

# 定义契约
get_effective_builder_contract = FunctionContract('get_effective_msglib_ptb_builder')
get_effective_builder_contract.add_postcondition(
    Property('is_registered(result) OR aborted')
)

get_builder_info_contract = FunctionContract('get_msglib_ptb_builder_info')
get_builder_info_contract.add_precondition(
    Property('is_registered(builder)')
)

# 验证调用
def verify_call_safety(caller_contracts, callee_contract, call_site):
    """验证调用是否安全"""
    # 获取调用点的状态属性
    state_properties = caller_contracts.get_properties_at(call_site)
    
    # 检查被调用函数的前置条件
    for precond in callee_contract.preconditions:
        if not state_properties.satisfies(precond):
            return False, f"Precondition not satisfied: {precond}"
    
    return True, "Safe"

# 对于 build_quote_ptb 中的调用：
result, message = verify_call_safety(
    caller_contracts=build_quote_ptb_contract,
    callee_contract=get_builder_info_contract,
    call_site="line 251"
)

if not result:
    print(f"VULNERABLE: {message}")
else:
    print(f"SAFE: {message}")
```

### 方案 2：基于类型系统的验证（Type-based）

使用细化类型（Refinement Types）：

```python
# 定义细化类型
RegisteredAddress = {a: address | is_registered(a)}
MaybeRegisteredAddress = {a: address | True}

# 函数签名加上细化类型
def get_effective_msglib_ptb_builder(
    self: EndpointPtbBuilder,
    oapp: address,
    lib: address
) -> RegisteredAddress | Abort:
    """
    返回类型保证：
    - 要么返回 RegisteredAddress
    - 要么 Abort
    """
    pass

def get_msglib_ptb_builder_info(
    self: EndpointPtbBuilder,
    builder: RegisteredAddress  # 要求输入必须是已注册地址
) -> MsglibPtbBuilderInfo:
    pass

# 类型检查
def build_quote_ptb(...):
    builder: RegisteredAddress | Abort = get_effective_msglib_ptb_builder(...)
    # 类型系统保证：
    # - 如果 builder 是值，则类型是 RegisteredAddress
    # - 如果 Abort，则不会继续执行
    
    # 因此这里的调用是类型安全的
    info = get_msglib_ptb_builder_info(builder)  # ✅ 类型匹配
```

### 方案 3：基于符号执行的验证（Symbolic Execution）

```python
class SymbolicState:
    def __init__(self):
        self.path_conditions = []
        self.variable_constraints = {}
    
    def add_constraint(self, var, constraint):
        """添加变量约束"""
        if var not in self.variable_constraints:
            self.variable_constraints[var] = []
        self.variable_constraints[var].append(constraint)
    
    def check_satisfiable(self, condition):
        """检查条件是否可满足"""
        # 使用 SMT solver (如 Z3)
        return solver.check(self.path_conditions + [condition])

# 符号执行 get_effective_msglib_ptb_builder
def symbolic_execute_get_effective_builder(state):
    builder = symbolic_var('builder')
    
    # Path 1: builder != DEFAULT_BUILDER
    state1 = state.copy()
    state1.add_constraint(builder, 'builder != @0x0')
    state1.add_constraint(builder, 'is_registered(builder)')  # 由 set_msglib_ptb_builder 保证
    yield state1, builder
    
    # Path 2: builder == DEFAULT_BUILDER
    state2 = state.copy()
    state2.add_constraint(builder, 'builder == @0x0')
    # 调用 get_default_msglib_ptb_builder
    for sub_state, result in symbolic_execute_get_default_builder(state2):
        yield sub_state, result
    
    # Path 3: Abort path
    state3 = state.copy()
    state3.set_aborted()
    yield state3, None  # No return value

# 验证调用
def verify_with_symbolic_execution():
    initial_state = SymbolicState()
    
    # 符号执行调用链
    for state, builder_addr in symbolic_execute_get_effective_builder(initial_state):
        if not state.is_aborted():
            # 检查返回值是否满足后续调用的前置条件
            assert state.variable_constraints[builder_addr].includes('is_registered')
    
    print("Verification passed: all paths satisfy preconditions")
```

## 优势对比

| 方法 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| **规范验证** | - 清晰明确<br>- 易于理解<br>- 可组合 | - 需要手动标注规范<br>- 可能不够精确 | 有明确契约的代码 |
| **类型系统** | - 自动检查<br>- 编译时验证<br>- 零运行时开销 | - 需要类型推导<br>- 表达能力有限 | 类型安全语言 |
| **符号执行** | - 精确<br>- 自动化<br>- 找到具体反例 | - 计算开销大<br>- 路径爆炸 | 关键代码段 |

## 针对 LayerZero 案例的推荐方案

### 混合方案：规范验证 + 简单的符号执行

```python
class VulnerabilityChecker:
    def __init__(self):
        self.contracts = {}  # 函数契约库
        
    def check_vulnerability(self, function_code, vulnerability_description):
        """
        检查是否为漏洞的主流程
        """
        # 步骤 1：提取关键属性
        key_property = extract_property(vulnerability_description)
        # 例如："get_msglib_ptb_builder_info requires registered address"
        
        # 步骤 2：构建调用图
        call_graph = build_call_graph(function_code)
        
        # 步骤 3：为每个函数推导契约
        for func in call_graph.functions:
            self.infer_contract(func)
        
        # 步骤 4：检查关键调用点
        vulnerable_calls = []
        for call_site in call_graph.call_sites:
            if not self.verify_call(call_site):
                vulnerable_calls.append(call_site)
        
        # 步骤 5：判定
        if len(vulnerable_calls) == 0:
            return "NOT_VULNERABLE", "All preconditions satisfied"
        else:
            return "VULNERABLE", f"Precondition violations at: {vulnerable_calls}"
    
    def infer_contract(self, function):
        """推导函数契约"""
        contract = FunctionContract(function.name)
        
        # 分析返回语句
        for return_stmt in function.returns:
            # 推导返回值的属性
            property = infer_property(return_stmt)
            contract.add_postcondition(property)
        
        # 分析 abort 语句
        for abort_stmt in function.aborts:
            condition = infer_abort_condition(abort_stmt)
            contract.add_abort_condition(condition)
        
        self.contracts[function.name] = contract
        return contract
    
    def verify_call(self, call_site):
        """验证单个调用是否安全"""
        caller = call_site.caller
        callee = call_site.callee
        
        # 获取调用点的状态
        state = analyze_state_at(caller, call_site.location)
        
        # 获取被调用函数的契约
        callee_contract = self.contracts[callee.name]
        
        # 检查前置条件
        for precond in callee_contract.preconditions:
            if not state.satisfies(precond):
                return False  # 前置条件不满足
        
        return True  # 安全
```

## 应用示例

```python
# 对于 LayerZero 案例
checker = VulnerabilityChecker()

# 自动推导契约
checker.infer_contract(get_effective_msglib_ptb_builder)
# 推导结果：
#   postcondition: is_registered(result) OR abort

checker.infer_contract(get_msglib_ptb_builder_info)
# 推导结果：
#   precondition: is_registered(builder)

# 验证调用
is_vuln, reason = checker.check_vulnerability(
    function_code=build_quote_ptb_code,
    vulnerability_description="Missing validation of effective PTB builder"
)

# 结果：
# is_vuln = False
# reason = "Precondition is satisfied: get_effective_msglib_ptb_builder 
#           guarantees registered address or abort before call to 
#           get_msglib_ptb_builder_info"
```

## 总结

使用 Pre-Postcondition 方法的关键优势：

1. ✅ **避免复杂的路径分析**：不需要追踪所有执行路径
2. ✅ **形式化验证**：可以用数学方法证明正确性
3. ✅ **可组合性**：函数契约可以组合验证整个系统
4. ✅ **误报率低**：基于逻辑推导，不依赖启发式规则

这个方法特别适合验证配置管理、权限检查、资源分配等有明确契约的代码！

