#!/bin/bash
# Pixel 设备 RPi5 一键安装脚本
# 在 Raspberry Pi 5 上运行：bash setup_rpi.sh

set -e
echo "=== Pixel 设备环境安装 ==="

# 系统依赖
sudo apt-get update -qq
sudo apt-get install -y \
    python3-pip python3-venv \
    portaudio19-dev libsndfile1 \
    ffmpeg libmp3lame0 \
    espeak-ng \
    git

# 安装 Ollama
if ! command -v ollama &> /dev/null; then
    echo "安装 Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 启动 Ollama 服务
sudo systemctl enable ollama
sudo systemctl start ollama
sleep 3

# 下载 Gemma 4 E2B（7.2GB，需要时间）
echo "下载 Gemma 4 E2B 模型（约 7.2GB）..."
ollama pull gemma4:e2b

# Python 虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt

# 配置文件
if [ ! -f .env ]; then
    cp .env.example .env
    echo "请编辑 .env 文件填入 Supabase 配置（可选）"
fi

# 设置开机自启动
SERVICE_FILE="/etc/systemd/system/pixel.service"
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Pixel AI Device
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/.venv/bin/python main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pixel

echo ""
echo "=== 安装完成 ==="
echo "启动: sudo systemctl start pixel"
echo "日志: journalctl -u pixel -f"
echo "手动测试: source .venv/bin/activate && python main.py"
