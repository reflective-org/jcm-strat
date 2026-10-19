#!/usr/bin/env bash
# Recreate the /dev/nvidia* device nodes after a node reboot (Voltage Park host, GPU-Operator driver).
#
# The driver runs as a container and creates its nodes under /run/nvidia/driver/dev; the host's /dev
# loses them on every reboot (seen 2026-09-14 and 2026-09-16). nvidia-smi still lists the GPUs, but
# CUDA's cuInit fails with CUDA_ERROR_NO_DEVICE and JAX silently runs on the CPU (a chain segment then
# takes ~16 h instead of 31 min). Run this ONCE after a reboot, as a user with sudo:
#
#     sudo bash scripts/restore_nvidia_dev.sh
#
# Major/minor numbers are read from the driver container's own nodes, so nothing is hard-coded.
# Claude Code's auto mode refuses to run mknod itself, hence this script.
set -euo pipefail
SRC=/run/nvidia/driver/dev
[ -d "$SRC" ] || { echo "no $SRC - is the GPU-Operator driver container running?" >&2; exit 1; }
for node in "$SRC"/nvidia*; do
  name=$(basename "$node"); [ -c "$node" ] || continue
  if [ -e "/dev/$name" ]; then echo "exists  /dev/$name"; continue; fi
  major=$(stat -c %t "$node"); minor=$(stat -c %T "$node")          # hex
  mknod -m 666 "/dev/$name" c "$((16#$major))" "$((16#$minor))"
  echo "created /dev/$name c $((16#$major)) $((16#$minor))"
done
if [ -d "$SRC/nvidia-caps" ] && [ ! -d /dev/nvidia-caps ]; then
  mkdir -p /dev/nvidia-caps
  for node in "$SRC"/nvidia-caps/*; do
    name=$(basename "$node"); major=$(stat -c %t "$node"); minor=$(stat -c %T "$node")
    mknod -m 666 "/dev/nvidia-caps/$name" c "$((16#$major))" "$((16#$minor))"; echo "created /dev/nvidia-caps/$name"
  done
fi
echo "check: python -c 'import jax; print(jax.devices())' should list the H100s"
