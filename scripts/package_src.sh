#!/usr/bin/env bash
# 把【源码工程】打包成 tar.gz，方便拷到其它机器部署。
# 不含 build/install/log（部署机自己编译）。
# 用法: ./scripts/package_src.sh  [输出目录(默认 /tmp)]
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
OUT="${1:-/tmp}"
NAME="tb3_lecture_src_$(date +%Y%m%d).tar.gz"
cd "$WS_ROOT"
tar --exclude='./build' --exclude='./install' --exclude='./log' \
    --exclude='__pycache__' --exclude='*.pyc' \
    -czf "$OUT/$NAME" README.md DEMO_GUIDE.md PROJECT_PLAN.md DEVELOPMENT_LOG.md INSTALL_NOTES.md scripts src
echo "已打包: $OUT/$NAME"
echo "目标机部署: 见 INSTALL_NOTES.md"
