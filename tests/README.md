# 测试指南

本目录包含 LlamaController 项目的自动化测试。

## 测试结构

```
tests/
├── conftest.py              # Pytest 配置和共享 fixtures
├── test_config.py           # 配置管理测试
├── test_gpu_detection.py    # GPU 检测测试
├── test_api_endpoints.py    # API 端点集成测试
├── test_lifecycle.py        # 生命周期管理测试
├── test_api.py             # API 单元测试
└── mock/                   # Mock 数据用于测试
    ├── nvidia-smi.bat      # Mock GPU 检测脚本
    └── scenarios/          # 不同 GPU 场景
```

## 运行测试

### 运行所有单元测试（无需服务器）

```bash
pytest tests/ -v -m "not integration"
```

### 运行特定测试文件

```bash
# GPU 检测测试
pytest tests/test_gpu_detection.py -v

# 配置测试
pytest tests/test_config.py -v

# 生命周期测试
pytest tests/test_lifecycle.py -v
```

### 运行集成测试（需要服务器运行）

```bash
# 先启动服务器
python run.py

# 在另一个终端运行集成测试
pytest tests/test_api_endpoints.py -v -m integration
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=src/llamacontroller --cov-report=html --cov-report=term
```

覆盖率报告将生成在 `htmlcov/` 目录中。

## 测试标记

测试使用以下标记进行分类：

- `unit`: 单元测试（快速，无外部依赖）
- `integration`: 集成测试（需要运行的服务器）
- `slow`: 慢速运行的测试
- `gpu`: 需要 GPU 硬件的测试

### 运行特定标记的测试

```bash
# 只运行单元测试
pytest -v -m unit

# 跳过集成测试
pytest -v -m "not integration"

# 只运行 GPU 测试
pytest -v -m gpu
```

## CI/CD 集成

项目配置了 pytest，可以轻松集成到 CI/CD 流程中：

```bash
# CI 环境中运行
pytest tests/ -v -m "not integration" --tb=short
```

## Mock GPU 测试

测试使用 `tests/mock/nvidia-smi.bat` 来模拟 GPU 检测，无需实际 GPU 硬件。这使得测试可以在任何环境中运行，包括 CI/CD 管道。

Mock 数据位于 `tests/mock/scenarios/` 目录中，包含不同的 GPU 状态场景。

## 编写新测试

1. 在 `tests/` 目录中创建新的 `test_*.py` 文件
2. 使用 pytest 类和方法命名约定：
   - 类名：`TestXxx`
   - 方法名：`test_xxx`
3. 添加适当的测试标记
4. 使用 docstring 描述测试目的

示例：

```python
import pytest

class TestMyFeature:
    """Test my feature functionality."""
    
    def test_basic_functionality(self):
        """Test that basic functionality works."""
        result = my_function()
        assert result == expected_value
    
    @pytest.mark.integration
    def test_with_server(self):
        """Test that requires running server."""
        response = requests.get("http://localhost:3000/api/test")
        assert response.status_code == 200
```

## 调试测试

### 显示打印输出

```bash
pytest tests/ -v -s
```

### 进入调试器

```bash
pytest tests/ -v --pdb
```

### 运行失败时进入调试器

```bash
pytest tests/ -v --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
```

## 常见问题

### 测试失败：服务器未运行

集成测试需要服务器运行。确保在运行集成测试前启动服务器：

```bash
python run.py
```

### 测试失败：配置文件未找到

确保从项目根目录运行测试：

```bash
cd /path/to/llamacontroller
pytest tests/
```

### Mock GPU 检测不工作

确保 `tests/mock/nvidia-smi.bat` 文件存在且可执行。
