# Features

What works today. Updated with every PR.

| Feature | Since | How |
|---|---|---|
| Reproducible environment from pinned submodules (jax-gcm `849893b`, dinosaur SL `bd99e39b`), Python 3.11, CUDA JAX, all under the repo | Phase 0 | `scripts/bootstrap_env.sh`, `scripts/check_env.sh`, `env/requirements.lock` |
| One-command tmux launch on GPU 0 with run isolation (`runs/<session>/`) | Phase 0 | `scripts/launch.sh` |
