# Tools: 工具定义与执行分离架构

## 📁 目录结构

```
tools/
├── definitions/         # 工具接口定义（YAML，按类别分文件）
│   ├── source.yaml     # Source 类工具（信息源类）
│   ├── processor.yaml  # Processor 类工具（加工/逻辑类）
│   ├── action.yaml     # Action 类工具（动作/执行类）
│   └── alternatives.yaml  # 工具可替换关系定义
│
├── plugins/            # 插件实现（一个工具一个文件）
│   ├── __init__.py
│   ├── get_weather_openweather.py
│   ├── get_weather_weatherapi.py
│   ├── get_stock_yahoo_finance.py
│   └── ...
│
├── loader.py           # 统一工具定义加载器
├── alternatives_loader.py  # 工具替代关系加载器
└── README.md           # 本文件
```

## 🎯 设计原则

### 1. **定义与实现分离**
- **YAML 文件**：描述工具接口（双范式支持：Function Calling + MCP）
- **Python 插件**：实现执行逻辑（确定性的输入输出映射）

### 2. **单一真实来源**
- 所有参数定义以 `definitions/*.yaml` 为准
- ToolExecutor（位于 `core/executor.py`）自动基于 YAML 验证参数，确保一致性

### 3. **按类组织，统一加载**
- 工具定义按语义类别分文件（便于**人工检查**）
- Loader 自动聚合所有文件（便于**程序使用和按类采样**）

---

## 🔧 工具类别说明

| 类别 | 定义 | 典型工具 |
|------|------|---------|
| **Source** | 负责从外部环境读取信息 | `get_weather`, `get_stock_yahoo_finance`, `search_news` |
| **Processor** | 负责在内存中对数据进行转换、清洗或计算 | `calculator`, `translator`, `json_formatter` |
| **Action** | 负责对外部环境产生副作用或执行实质性业务操作 | `send_email`, `book_ticket`, `write_database` |

---

## 📁 双维度分类体系

工具库采用**类别 (Category) + 领域 (Domain)** 的双维度分类体系。

### 1. 类别分类 (Category)

按照工具的**功能特性**分类：

| 类别 | 定义 | 特点 | 示例 |
|------|------|------|------|
| **Source** | 信息源类 | 从外部环境读取信息，操作通常是幂等的 | `get_weather`, `get_stock_yahoo_finance`, `search_calendar` |
| **Processor** | 加工/逻辑类 | 在内存中对数据进行转换、清洗或计算 | `calculator`, `temperature_converter`, `get_exchange_rate` |
| **Action** | 动作/执行类 | 对外部环境产生副作用或执行实质性业务操作 | `send_email`, `schedule_meeting`, `book_ticket` |

### 2. 领域分类 (Domain)

按照工具的**应用场景**分类：

| 领域 | 说明 | 典型任务场景 | 示例工具 |
|------|------|--------------|------------|
| **Financial** | 金融财务 | 股票查询、汇率转换、投资分析 | `get_stock_yahoo_finance`, `get_exchange_rate`, `get_stock_price_and_convert` |
| **Travel** | 旅行出行 | 天气查询、行程规划、温度转换 | `get_weather_openweather`, `get_weather_weatherapi`, `temperature_converter` |
| **Office** | 办公协作 | 邮件发送、会议安排、日历查询 | `send_email`, `schedule_meeting`, `search_calendar` |
| **General** | 通用领域 | 跨领域的基础计算和处理 | `calculator` |

### 3. 分类的用途

#### **ToolDAG 构造**
在生成 ToolDAG 时，使用领域分类进行**情境桶采样 (Context-Aware Sampling)**：
- 锁定一个特定领域（如 "Financial"）
- 从该领域的 Source、Processor、Action 中采样
- 生成语义连贯的工具链（如：股价查询 → 汇率转换 → 发送邮件）

#### **数据流验证**
- 同领域工具更容易形成合法的数据流
- 跨领域工具需要额外的兼容性检查

#### **任务多样性**
- 通过切换领域生成不同场景的任务
- 避免所有任务都集中在单一领域

### 4. 当前工具清单

| 工具名称 | 类别 | 领域 | 文件位置 |
|---------|------|------|----------|
| `get_weather_openweather` | Source | Travel | `source.yaml` |
| `get_weather_weatherapi` | Source | Travel | `source.yaml` |
| `get_stock_yahoo_finance` | Source | Financial | `source.yaml` |
| `search_calendar` | Source | Office | `source.yaml` |
| `get_exchange_rate` | Processor | Financial | `processor.yaml` |
| `calculator` | Processor | General | `processor.yaml` |
| `get_stock_price_and_convert` | Processor | Financial | `processor.yaml` |
| `temperature_converter` | Processor | Travel | `processor.yaml` |
| `send_email` | Action | Office | `action.yaml` |
| `schedule_meeting` | Action | Office | `action.yaml` |

### 5. 添加新工具的分类指南

#### 步骤 1: 确定类别 (Category)

根据工具的主要功能选择：
- 是否读取外部信息？ → **Source**
- 是否对数据进行处理？ → **Processor**
- 是否产生外部副作用？ → **Action**

#### 步骤 2: 确定领域 (Domain)

根据工具的应用场景选择：
- 金融相关？ → **Financial**
- 旅行相关？ → **Travel**
- 办公相关？ → **Office**
- 通用工具？ → **General**
- 其他领域？ → 新增领域标签（如 IoT, Shopping 等）

#### 步骤 3: 在 YAML 中添加分类

```yaml
- name: my_new_tool
  description: "工具描述"
  category: Processor     # 类别: Source, Processor, Action
  domain: Financial       # 领域
  substitutes: []
  paradigms:
    # ... 工具定义
```

### 6. 设计原则

1. **类别互斥**：每个工具只能属于一个类别
2. **领域唯一**：每个工具只能属于一个主要领域
3. **General 保守使用**：只有真正与领域无关的工具才标记为 General
4. **新领域谨慎添加**：确保有足够多的工具支撑一个新领域

### 7. 未来扩展

计划支持的新领域：

| 领域 | 说明 | 潜在工具 |
|------|------|----------|
| **IoT** | 物联网/智能家居 | `control_light`, `set_thermostat`, `query_sensor` |
| **Shopping** | 电商购物 | `search_product`, `compare_price`, `add_to_cart` |
| **Health** | 健康医疗 | `track_steps`, `log_meal`, `schedule_appointment` |
| **Education** | 教育学习 | `search_course`, `submit_assignment`, `check_grade` |

---

## 📚 使用指南

### **人工检查某类工具**

直接打开对应的 YAML 文件查看：

```bash
# 查看所有 Source 类工具
cat definitions/source.yaml

# 查看所有 Processor 类工具
cat definitions/processor.yaml
```

### **在代码中按类采样**

使用 `loader.py` 进行按类别查询和采样：

```python
from tools.loader import ToolLoader

loader = ToolLoader("tools/definitions")

# 获取所有 Source 类工具
source_tools = loader.get_tools_by_category("Source")

# 随机采样 2 个 Processor 工具（用于 DAG 生成）
processors = loader.sample_by_category("Processor", n=2, seed=42)

# 按名称获取工具
tool = loader.get_tool_by_name("get_weather_openweather")

# 查看类别统计
stats = loader.get_category_stats()  # {"Source": 4, "Processor": 4, ...}
```

### **执行工具（带自动验证）**

使用 `core/executor.py` 中的 ToolExecutor 执行工具，会自动进行 Schema 验证：

```python
from core.executor import ToolExecutor
from core.context import ExecutionContext

executor = ToolExecutor(
    plugins_dir="tools/plugins",
    definitions_dir="tools/definitions"
)

# 创建执行上下文
context = ExecutionContext(user_input={"city": "东京"})

# 自动验证参数并执行
result = executor.execute("get_weather_openweather", {"city": "东京"}, context, step=1)
# 返回: {'temperature_celsius': 20, 'condition': 'Clear'}

# 如果参数不匹配 schema，返回验证错误
result = executor.execute("get_weather_openweather", {}, context, step=1)
# 返回: {'error': 'Validation failed', 'validation_errors': ["Missing required parameter: 'city'"]}
```

### **使用 ToolCorpus（Pipeline 中使用）**

在数据构造 Pipeline 中使用 `tool_corpus.py`：

```python
from src.tool_corpus import load_tool_corpus

# 传入目录路径，自动加载所有 YAML 文件
corpus = load_tool_corpus('tools/definitions')

# 获取双范式格式
fc_tools = corpus.format_tools_for_function_calling(['get_weather_openweather'])
mcp_text = corpus.format_tools_for_mcp(['get_weather_openweather', 'calculator'])
```

---

## 🛠️ 扩展指南

### **添加新工具**

#### 步骤 1: 在对应类别的 YAML 文件中添加定义

编辑 `definitions/<category>.yaml`（如 `source.yaml`）：

```yaml
tools:
  - name: my_new_tool
    description: "工具的简短描述"
    category: Source  # Source, Processor, Action
    substitutes: []   # 可替代此工具的其他工具列表
    paradigms:
      function_call:
        spec:
          name: "my_new_tool"
          description: "详细的功能描述"
          parameters:
            type: "object"
            properties:
              param1:
                type: "string"
                description: "参数说明"
            required: ["param1"]
      mcp:
        prompt_signature: "my_new_tool(param1: string) -> dict"
        prompt_description: "MCP 格式的描述，说明参数和返回值"
```

#### 步骤 2: 创建插件实现

在 `plugins/my_new_tool.py` 中：

```python
TOOL_NAME = "my_new_tool"

def execute(arguments: dict, context) -> dict:
    """
    执行工具逻辑

    Args:
        arguments: 工具参数（已由 ToolExecutor 验证）
        context: ExecutionContext，提供上下文数据访问

    Returns:
        工具执行结果（dict）
    """
    param1 = arguments.get("param1")

    # 可以从 context 获取前序步骤的输出
    previous_data = context.get("some_key")

    # 实现工具逻辑
    result = do_something(param1)

    return {"result": result}
```

#### 步骤 3: 测试

```python
from core.executor import ToolExecutor
from core.context import ExecutionContext

executor = ToolExecutor(
    plugins_dir="tools/plugins",
    definitions_dir="tools/definitions"
)

context = ExecutionContext()

# 自动加载新工具并验证参数
result = executor.execute("my_new_tool", {"param1": "value"}, context, step=1)
print(result)
```

---

## 🔍 内置插件列表

当前提供的插件（位于 `plugins/` 目录）：

| 插件 | 工具名称 | 类别 | 说明 |
|------|---------|------|------|
| `get_weather_openweather.py` | `get_weather_openweather` | Source | 获取城市天气 |
| `get_weather_weatherapi.py` | `get_weather_weatherapi` | Source | 网络搜索天气 |
| `get_stock_yahoo_finance.py` | `get_stock_yahoo_finance` | Source | 获取股票价格 |
| `search_calendar.py` | `search_calendar` | Source | 查询日历空闲时段 |
| `get_exchange_rate.py` | `get_exchange_rate` | Processor | 获取货币汇率 |
| `calculator.py` | `calculator` | Processor | 数学计算 |
| `temperature_converter.py` | `temperature_converter` | Processor | 温度单位转换 |
| `get_stock_price_and_convert.py` | `get_stock_price_and_convert` | Processor | 股价查询+货币转换（组合工具） |
| `send_email.py` | `send_email` | Action | 发送邮件 |
| `schedule_meeting.py` | `schedule_meeting` | Action | 安排会议 |

---

## 🎨 插件接口规范

每个插件文件必须导出：

```python
# 1. 工具名称常量
TOOL_NAME = "tool_name"

# 2. execute 函数
def execute(arguments: dict, context) -> dict:
    """
    Args:
        arguments: 参数字典（已通过 Schema 验证）
        context: ExecutionContext，提供上下文数据访问

    Returns:
        结果字典
    """
    pass
```

### **ExecutionContext 提供的方法**

```python
# 1. 获取上下文数据（从累积数据或用户输入）
value = context.get("key", default=None)

# 2. 获取指定步骤的输出
step_output = context.get_from_step(step=1, key="price")

# 3. 获取最后一步的输出
last_output = context.get_last_output()

# 4. 查找可替换工具的输出（用于保证一致性）
if hasattr(context, 'find_alternative_output'):
    existing = context.find_alternative_output(
        alternative_tools=["tool1", "tool2"],
        arguments={"param": "value"}
    )
    if existing:
        return existing

# 5. 访问完整的执行历史
for record in context.history:
    print(record.tool_name, record.output)
```
