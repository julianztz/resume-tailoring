项目基础层结构总结（Phase 1 - Foundation Layer）

当前项目已经建立了四个核心基础模块，分别负责配置管理、数据结构定义、日志系统以及系统入口控制。这些模块共同构成了系统的基础设施层（Infrastructure Layer），为后续功能开发提供稳定的结构支撑。

1. Config Layer（配置层）

config.py 提供了统一的配置加载与访问接口。
从 .env 和 settings.yaml 读取配置
将配置解析为结构化对象（Pydantic）
对外提供统一访问入口（load_settings()）

👉 设计目标：
避免各模块直接读取环境变量或配置文件
集中管理配置来源
支持未来多环境 / 多 provider 扩展

2. Schema Layer（数据结构层）
schemas.py 定义了系统中所有核心数据模型。
基于 Pydantic，实现：
类型约束
默认值管理
数据结构统一

关键模型包括：
JDInput：原始 JD 输入
JDParsed：结构化 JD
ExperienceItem：经验单元
MatchResult：匹配分析结果
ApplyRecommendation：决策建议
TailoredResumeDraft：定制简历草稿

👉 设计目标：
建立模块之间的数据契约（data contract）
保证数据传递的一致性与可预测性
降低模块耦合

3. Logger Layer（日志系统）
logger.py 提供统一日志工厂函数 setup_logger()。

功能包括：
统一日志格式
console（Rich）输出
文件持久化（logs/app.log）
避免重复 handler

👉 设计目标：
替代 print，提供结构化日志能力
支持调试、追踪、问题定位
为 LLM 调用和 pipeline 执行提供可观测性

4. CLI Entry Layer（系统入口）
main.py 使用 Typer 构建命令行接口。
定义 CLI 应用对象
使用 @app.command() 注册功能
每个 command 对应一个功能模块

👉 设计目标：
提供统一系统入口
支持 command-driven 开发模式
方便测试、脚本化和后续自动化 pipeline