# 检查引擎上下文完整性

## 从漏洞报告的"业务流程代码"中提取的关键函数

### 1. get_effective_msglib_ptb_builder
```move
fun get_effective_msglib_ptb_builder(self: &EndpointPtbBuilder, oapp: address, lib: address): address {
    let builder = *table_ext::borrow_with_default!(&self.oapp_configs, OAppConfigKey { oapp, lib }, &DEFAULT_BUILDER);
    if (builder != DEFAULT_BUILDER) {
        builder
    } else {
        self.get_default_msglib_ptb_builder(lib)
    }
}
```

### 2. get_default_msglib_ptb_builder
```move
fun get_default_msglib_ptb_builder(self: &EndpointPtbBuilder, lib: address): address {
    *table_ext::borrow_or_abort!(&self.default_configs, lib, EBuilderNotFound)
}
```

### 3. get_msglib_ptb_builder_info
```move
fun get_msglib_ptb_builder_info(self: &EndpointPtbBuilder, builder: address): &MsglibPtbBuilderInfo {
    assert!(self.is_msglib_ptb_builder_registered(builder), EBuilderNotFound);
    &self.registry.builder_infos[builder]
}
```

## 关键问题分析

从业务流程代码看，引擎**确实有完整的上下文**，包括：
1. ✅ get_effective_msglib_ptb_builder 的完整实现
2. ✅ get_default_msglib_ptb_builder 的完整实现  
3. ✅ get_msglib_ptb_builder_info 的完整实现
4. ✅ DEFAULT_BUILDER 常量定义

## 执行流程推理

正确的执行流程应该是：

```
build_quote_ptb()
  → get_effective_msglib_ptb_builder(sender, quote_lib)
      → 检查 oapp_configs[oapp, lib]
      → 如果没有，返回 DEFAULT_BUILDER
      → if (builder != DEFAULT_BUILDER) {
            return builder  // 不会执行
        } else {
            return get_default_msglib_ptb_builder(lib)  // 会执行这个
                → 检查 default_configs[lib]
                → 如果没有，**abort with EBuilderNotFound**  ❗❗❗
        }
```

**关键点**：在 `get_effective_msglib_ptb_builder` 函数内部，如果返回的是 DEFAULT_BUILDER，会**立即在 else 分支调用** `get_default_msglib_ptb_builder`，后者会 **abort**，不会返回 @0x0 给外层调用者。

## 结论

**这不是上下文不足的问题，而是推理能力不足的问题！**

引擎有完整的代码，但它没有正确理解：
- 条件分支的语义
- 嵌套函数调用的执行流程  
- abort 会中断执行流程，不会继续返回

引擎错误地认为 get_effective_msglib_ptb_builder 会返回 @0x0，但实际上在这之前就 abort 了。

