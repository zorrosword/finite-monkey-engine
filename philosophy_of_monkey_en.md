# Reflections on the FiniteMonkey Engine (February 18, 2025)

# 1. Origins

The origin of this engine stems from a single prompt: "There is a vulnerability in this code, please find it." Back in the days of GPT-3.5 and GPT-4, interestingly, this prompt proved much more effective than asking "Is there a vulnerability in this code?"

Specifically, this effectiveness manifested in how, compared to question formats, this prompt seemed to better trigger the large model's reasoning ability or logical search capabilities, rather than just relying on memory from training datasets. Large models would be more inclined to actively search for vulnerabilities instead of making random guesses based on basic vulnerability knowledge.

At that time, I followed this workflow: I ask => model answers => I verify => if incorrect, I ask again with the same prompt until the vulnerability is found.

Based on this approach, I earned hundreds of thousands of RMB in bug bounties over two years. It also performed well in recent CodeHawks audits.

The core lies in how to significantly trigger LLM hallucinations - embracing and welcoming these hallucinations. I believe this is something very few people have realized.

# 2. Construction

In February 2024, exactly one year before writing this article, I decided to start building this engine. Although the concept of AI agents had already emerged, I didn't initially consider taking an agent-based approach. Instead, I viewed it as a tool to automate my manual workflow.

The initial workflow was as follows:
![image description]

Simply put, it involved brutally breaking projects down to function-level granularity for questioning, asking 10 times per function, and then validating each output by having GPT determine whether it was a false positive.

The results were poor, even worse than my manual approach. I realized it needed iteration.

# 3. Iterations

## 3.1 First Iteration: Validation and Detection Granularity

The first things to iterate on were the validation process and detection granularity. In the entire workflow, I discovered that the biggest difference from my personal workflow was that I never considered context when asking questions.

In other words, at the time, the context window (128k) was sufficient for me to simply throw an entire contract in and ask questions directly. However, in the tool, I was using function-level granularity, and this contextual difference led to very low detection rates.

I had considered using static methods for reasonable context extraction, such as using Slither to extract context for specific functions, but I didn't adopt this approach (explained later) and instead used ANTLR4.

Using ANTLR4, I processed each file to construct what I call a "business flow."

I had discussed the idea of business flow construction with Yuqiang before. He mentioned that using Slither to extract variable read/writes or function calls wasn't ideal. This was one reason I abandoned Slither and instead adopted a direct GPT questioning approach to extract business flows. The prompt used for extraction was:

```
Based on the code above, analyze the business flows that start with the {function_name} function, consisting of multiple function calls. The analysis should adhere to the following requirements:
        1. only output the one sub-business flows, and must start from {function_name}.
        2. The output business flows should only involve the list of functions of the contract itself (ignoring calls to other contracts or interfaces, as well as events).
        3. After step-by-step analysis, output one result in JSON format, with the structure: {{"{function_name}":[function1,function2,function3....]}}
        4. The business flows must include all involved functions without any omissions
```

This method of extracting business flows for questioning made the detection granularity relatively reasonable, though problems still existed that remain unresolved.

Similarly, validation followed the same principle. Initially, I used multiple prompts (such as asking whether there was a vulnerability or asking for a patch), but after extensive testing, the results weren't good. I later discovered that the key issue was still context completeness - you can't expect an LLM to verify something it knows nothing about.

## 3.2 Second Iteration: Context

Regarding the context issue, I had considered brutally expanding prompt inputs as a solution, but this proved ineffective because when projects get too large, you can't simply throw the entire project in - you need reasonable context extraction.

At this point, Cursor emerged. I was among Cursor's first users, and its Codebase QA feature caught my attention. I realized I needed reasonable context extraction, and Cursor's Codebase QA feature could fulfill this need.

Therefore, I investigated Cursor's Codebase QA feature in detail and discovered it was essentially a RAG extraction based on questions. This was familiar territory, as I had used RAG extensively while developing LLM4Vuln.

Implementing a Codebase QA intermediate component became crucial, and now it looks like this:

![image description]

Simply put, this component's function is to preprocess the codebase (project code) and extract the most relevant context for a given vulnerability input.

In this process, I implemented a relatively complex call tree and RAG covering the entire project code. The final output is a context text that I call a "context funnel."

Based on this context funnel, I can perform reasonable context extraction and then validate vulnerabilities.

## 3.3 Third Iteration: Model Selection

Throughout the project's development, including sections 3.1 and 3.2, I've tried almost all models, including the entire GPT family, Claude family, and the latest O1, O3, and R1. In practical implementation, we can't say which vulnerability detection model is absolutely best. Many factors must be considered, with the two most important being:

Time and cost

Since the goal is a directly productizable tool, we can't simply use the most powerful models, nor can we say reasoning models (like O1, O3, R1 with chain-of-thought capabilities) are necessarily better than non-reasoning models. Due to time and cost constraints, we can't expect a task to take several minutes or even close to 10 minutes to get an answer. Therefore, the current model selection is:

Claude for detection, DeepSeek O1 for validation

## 3.4 Fourth Iteration: Back to Detection

Thanks to ret2basic's inspiration, I realized that the original prompt wasn't perfect. A prompt completely dependent on the large model's capabilities is highly limited by the model's training data. Even if you can trigger its strongest reasoning and logical abilities, there are some vulnerabilities it won't notice.

So, returning to the original prompt, I needed a checklist. Where would it come from?

Thanks to SoloAudit, I crawled 24,000 audit vulnerabilities, and thanks to Dacien for compiling so many checklists. I processed these vulnerabilities and checklists, added them to my prompts, and formed a simple component called S.P.A.R.T (Smart Prompting for Automated Risk Tailoring).

This made the detection prompt more complete, though many adjustments were still needed.

# 4. Answering Questions: Why ANTLR4 Instead of Slither

This engine has some preset conditions, one key one being: "The best compiler is a large model."

I'm not denying Slither's power. I've spent a lot of time with Slither and developed many rules and optimizations. But Slither faces a problem: it's based on solc and is becoming increasingly heavy, demanding greater project completeness. This not only hinders my testing but also makes it difficult to extend to more languages.

ANTLR4 doesn't have this problem. A simple function breakdown and various combinations based on this breakdown can not only meet various business flow extraction needs but also extend the same code and architecture to more languages. After all, you only need to break the code down at function granularity.

Therefore, this engine currently supports many languages: not just Solidity but also Solidity decompiled pseudocode, Rust, Move, Go, Python, and potentially any language.

# 5. Design Philosophy

This is the most important part. Unlike most detection tools on the market and unlike my previous work with Yuqiang, Daoyuan, and Liuye, it's not based on traditional deterministic pattern recognition.

Traditional deterministic pattern recognition requires very fine-grained breakdown and definition of vulnerabilities, then pattern recognition based on large datasets. Whether it's GPTScan, PropertyGPT, or LLM4Vuln, they're all based on this approach.

This approach is based on expert experience, interpreting vulnerabilities as chain-of-thought or as functionality and key concepts for matching, guiding large models to think step by step. But this brings a problem:

1. It requires substantial expert experience and datasets. Expert experience is scarce, making it difficult to cover all vulnerabilities.
2. It's rule-driven, meaning it needs many rules, and the development and maintenance costs are very high. Only heaven knows how much effort Yuqiang put into writing those 11 detectors for GPTScan.
3. Being rule-driven means that stricter rules make it harder to cover all vulnerabilities, leading to endless rule testing.
4. The process requires many LLM queries. Thanks to Alan@Secure3's article, I realized that this complex process has a fatal problem: the law of error accumulation. Simply put, errors grow exponentially with process complexity. When LLM actions reach 30, even with 99% accuracy per action, the final accuracy drops to 73%. In reality, LLM accuracy is much worse—roughly 60-70% per action. This means that after just 10 actions, accuracy falls to 2%. Even with 5 actions, it's only 16%. This creates an accuracy ceiling for long-chain detection tasks.

To solve this problem, at least in the AI audit field, we need to escape the limitations of agent action links through the following methodology:

Shift from "finding the right answer" to "managing the possibility space"
A[Code Input] --> B{Possibility Space Construction}
B --> C[Vulnerability Hypothesis Cloud]
C --> D[Validation Convergence]
D --> E[Deterministic Conclusion]
(There may be more theoretical foundations to explore, which will be expanded upon later)

This approach's advantage is that we don't need to invest heavily in building complex rules. Instead, we construct a possibility space, then converge through validation to reach a deterministic conclusion.

Additionally, this approach effectively solves the law of error accumulation by reducing complexity.

Of course, there's a question to address: Is the vulnerability hypothesis cloud unlimited? In other words, if 10 iterations generate 10 different vulnerabilities, and 100 iterations generate 100 different vulnerabilities, doesn't this mean it's endless?

This relates to the project's name: Finite Monkey. It comes from the infinite monkey theorem, which assumes a monkey typing on a typewriter could produce anything, assuming an infinite possibility space.

But in this project, "finite monkey" reflects my discovery that an LLM's possibility space isn't infinite. In 10 iterations generating 10 vulnerabilities, they might be categorizable into 5 types. Even with further iterations, it's hard to generate new vulnerabilities—it might still be 5 types. In other words, the vulnerability hypothesis cloud is finite.

This makes things manageable. When possibilities are finite, vulnerabilities aren't endless but converge on certain types. This means vulnerability mining has convergence properties, though it also has divergence properties.

# 6. Conclusion

This is a fascinating project that has made me realize that building a possibility space, then converging through validation to reach a deterministic conclusion, might be a potential direction for AI agents.

Of course, this method may not suit all scenarios. For example, in coding, you can't expect to generate 10 answers and choose the best one (though it doesn't seem impossible), as the time cost would be relatively high.