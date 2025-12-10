# PowerShell скрипт для настройки локального окружения на Windows

Write-Host "Начинаем настройку локального окружения на Windows..." -ForegroundColor Green

# Проверяем версию PowerShell
$psVersion = $PSVersionTable.PSVersion.Major
if ($psVersion -lt 5) {
    Write-Host "Требуется PowerShell версии 5 или выше" -ForegroundColor Red
    exit 1
}

# Проверяем, установлен ли Python
try {
    $pythonVersion = python --version
    Write-Host "Найден Python: $pythonVersion" -ForegroundColor Green
} 
catch {
    Write-Host "Python не найден. Пожалуйста, установите Python 3.8+" -ForegroundColor Red
    exit 1
}

# Устанавливаем Python зависимости
Write-Host "Устанавливаем Python зависимости..." -ForegroundColor Yellow
pip install -r requirements-local.txt

# Проверяем, установлен ли Rust
try {
    $rustVersion = rustc --version
    Write-Host "Найден Rust: $rustVersion" -ForegroundColor Green
} 
catch {
    Write-Host "Rust не найден. Устанавливаем Rust..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://win.rustup.rs/" -OutFile "rustup-init.exe"
    .\rustup-init.exe -y
    Remove-Item "rustup-init.exe"
}

# Проверяем, установлен ли CUDA
$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0"
if (Test-Path $cudaPath) {
    Write-Host "Найден CUDA: $cudaPath" -ForegroundColor Green
    $env:CUDA_PATH = $cudaPath
} else {
    Write-Host "CUDA не найден. Убедитесь, что у вас установлена CUDA Toolkit для поддержки TensorRT" -ForegroundColor Yellow
}

# Устанавливаем Rust зависимости
Write-Host "Собираем Rust модуль..." -ForegroundColor Yellow
cd local-inference/rust-core
cargo build --release
cd ../..

Write-Host "Настройка локального окружения завершена!" -ForegroundColor Green
Write-Host "Теперь вы можете запустить локальный inference сервер командой:" -ForegroundColor Cyan
Write-Host "cd local-inference && python llm_server.py" -ForegroundColor Cyan