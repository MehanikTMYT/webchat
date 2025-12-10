#!/bin/bash

# Скрипт для настройки локального окружения на Linux/Mac

echo "Начинаем настройку локального окружения на Linux/Mac..."

# Устанавливаем Python зависимости
echo "Устанавливаем Python зависимости..."
pip install -r requirements-local.txt

# Проверяем, установлен ли Rust
if command -v rustc &> /dev/null; then
    echo "Найден Rust: $(rustc --version)"
else
    echo "Rust не найден. Устанавливаем Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
fi

# Проверяем, установлен ли CUDA (для Linux)
if command -v nvcc &> /dev/null; then
    echo "Найден CUDA: $(nvcc --version | grep release)"
else
    echo "CUDA не найден. Убедитесь, что у вас установлена CUDA Toolkit для поддержки TensorRT"
fi

# Устанавливаем Rust зависимости
echo "Собираем Rust модуль..."
cd local-inference/rust-core
cargo build --release
cd ../..

echo "Настройка локального окружения завершена!"
echo "Теперь вы можете запустить локальный inference сервер командой:"
echo "cd local-inference && python llm_server.py"