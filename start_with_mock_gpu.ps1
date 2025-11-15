# PowerShell script to start LlamaController with mock GPU for testing
# The application will automatically detect and use tests/mock/nvidia-smi.bat

param(
    [string]$PythonPath = "python"
)

# Get the absolute path to the mock directory
$MockDir = Join-Path $PSScriptRoot "tests\mock"
$MockScript = Join-Path $MockDir "nvidia-smi.bat"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting LlamaController with Mock GPU" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if mock script exists
if (-not (Test-Path $MockScript)) {
    Write-Host "ERROR: Mock nvidia-smi script not found at: $MockScript" -ForegroundColor Red
    Write-Host "Make sure you're running this from the project root directory." -ForegroundColor Red
    exit 1
}

Write-Host "Mock GPU setup:" -ForegroundColor Green
Write-Host "  Mock script: $MockScript" -ForegroundColor Green
Write-Host "  Mock data: $(Join-Path $MockDir 'gpu_output.txt')" -ForegroundColor Green
Write-Host "  Note: Application will automatically detect and use mock GPU" -ForegroundColor Green
Write-Host ""

# Test if mock script works
Write-Host "Testing mock nvidia-smi..." -ForegroundColor Cyan
$TestOutput = & $MockScript 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Mock nvidia-smi works correctly" -ForegroundColor Green
    $gpuCount = ($TestOutput | Select-String "NVIDIA" | Measure-Object).Count
    Write-Host "  Detected GPUs in mock data: $gpuCount" -ForegroundColor Green
} else {
    Write-Host "ERROR: Mock nvidia-smi test failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Start the application
Write-Host "Starting LlamaController..." -ForegroundColor Cyan
Write-Host "Command: $PythonPath run.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "The application will automatically detect and use mock GPU." -ForegroundColor Yellow
Write-Host "Watch for [DEBUG] messages in the output below." -ForegroundColor Yellow
Write-Host ""

# Run the application
& $PythonPath run.py

Write-Host ""
Write-Host "LlamaController stopped." -ForegroundColor Cyan
