下面整理了文章中提到的主要漏洞以及其成因和危害：

1. **内存覆盖问题（Memory Corruption from External Calls）**  
   - 在手写内联汇编保存数据时，如果不及时更新 Solidity 的 Free Memory Pointer（FMPA），外部调用返回的数据可能会写入当前 FMPA 指向的位置，从而覆盖已有数据。  
   - 例如，HasherImpl 合约在将变量 a 和 b 通过汇编写入内存后，没有更新 FMPA，导致后续调用 infoRetriever.getVal() 时返回的数据覆盖了之前存入 0x80 的 a 的值，最终计算的哈希出错。

2. **假设 FMPA 未改变导致的错误（Assuming Unchanged Free Memory Pointer Address）**  
   - 内联汇编代码在第一段获取了 FMPA，并用该地址作为哈希计算的起始点。然而，在中间的外部调用过程中，Solidity 会自动更新 FMPA，使得后续计算 keccak256 时使用的内存地址和范围不再包含最初通过内联汇编存入的数据。  
   - 这种错误假设 FMPA 不变就可能导致哈希操作计算了错误的数据或计算范围不正确。

3. **内存分配不足引发的内存破坏（Memory Corruption Due to Insufficient Allocation）**  
   - 在 ENS 的 Buffer 合约中，初始化 buffer 时没有预留足够的内存空间（例如遗漏了 32 字节的偏移），导致后续写入数据（如写入“append”数据）时可能会覆盖紧邻的其他内存变量。  
   - 举个例子，本例中 Buffer.init 函数更新 FMPA 时只写成 mstore(0x40, add(ptr, capacity))，而正确做法应为为 buffer 数据再额外预留 32 字节空间，防止覆盖比如相邻变量 foo 的长度。

4. **针对不存在合约的外部调用问题（External Call to Non-Existent Contract）**  
   - 当使用低级别调用（如 staticcall）调用一个没有代码部署的地址（比如一个普通的 EOAs）时，调用依然会成功，但返回的数据可能并不符合预期。  
   - 例子中 WalletVerifier 合约中对外部钱包合约调用没有判断 extcodesize，因此如果传入的是 EOA 地址，调用会“成功”，且返回数据可能被错误解释，从而导致签名验证出错。

5. **内联汇编中的算术溢出/下溢问题（Overflow/Underflow During Inline Assembly）**  
   - 在使用内联汇编中的 add、mul、sub 等指令时，由于没有 Solidity 内置的溢出/下溢保护操作，极限值计算容易发生溢出，导致结果错误。  
   - 如 DexPair 合约中的 getSwapQuote，当输入为 type(uint256).max 时，简单的加 1 可能会发生溢出（返回 0）而没有被检测出来。

6. **Uint128 溢出检测失效问题（Uint128 Overflow Evades Detection Due to Inline Assembly Using 256 Bits）**  
   - 如果函数参数使用 uint128，但在内联汇编中进行算术操作时实际上操作的是 256 位数值，这会导致溢出检测失效。  
   - 例如 DexPair 中的 getSwapQuoteUint128 函数：即使对 uint128 进行了加法并尝试比较检测溢出，由于汇编总是以 256 位计算，传入最大 uint128 值时内部运算结果不会触发 lt 检查，从而返回了错误的数值。  
   - 为解决这一问题，可以使用 addmod 限制运算范围，或在汇编代码外部再次检测返回值是否符合预期。

