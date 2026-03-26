"""
advanced_trainer_configs.py — BMAD DL Lifecycle
(Adapted from K-Dense claude-scientific-skills/pytorch-lightning/quick_trainer_setup.py)

10 ready-to-use Lightning Trainer configurations for different training scenarios.
Each function is self-contained — copy the one you need into your training script.

Configurations:
  1.  basic_trainer()              — Quick prototyping, CPU/auto hardware
  2.  debug_trainer()              — Fast dev run, anomaly detection
  3.  single_gpu_trainer()         — Production single GPU with checkpointing + logging
  4.  multi_gpu_ddp_trainer()      — Multi-GPU with DDP (models < 500M params)
  5.  large_model_fsdp_trainer()   — FSDP for large models (500M+ params)
  6.  deepspeed_trainer()          — DeepSpeed for very large models (10B+)
  7.  hparam_search_trainer()      — Lightweight for hyperparameter sweeps
  8.  overfit_test_trainer()       — Overfit on N batches to verify model capacity
  9.  cluster_time_limited_trainer()— SLURM/cluster jobs with wall-clock limit
  10. reproducible_trainer()       — Deterministic, full-precision for publications

Usage in your training script:
    from assets.advanced_trainer_configs import single_gpu_trainer
    trainer = single_gpu_trainer(max_epochs=50, experiment_name="run_001")
    trainer.fit(model, datamodule)
    trainer.test(model, datamodule)
"""

from __future__ import annotations

from pathlib import Path

try:
    import lightning as L
    from lightning.pytorch.callbacks import (
        ModelCheckpoint, EarlyStopping, LearningRateMonitor,
        DeviceStatsMonitor, RichProgressBar,
    )
    from lightning.pytorch import loggers as pl_loggers
    from lightning.pytorch.strategies import DDPStrategy, FSDPStrategy
    LIGHTNING_PKG = "lightning"
except ImportError:
    try:
        import pytorch_lightning as L
        from pytorch_lightning.callbacks import (
            ModelCheckpoint, EarlyStopping, LearningRateMonitor,
        )
        from pytorch_lightning import loggers as pl_loggers
        from pytorch_lightning.strategies import DDPStrategy, FSDPStrategy
        RichProgressBar = DeviceStatsMonitor = None
        LIGHTNING_PKG = "pytorch_lightning"
    except ImportError:
        raise ImportError("Install: pip install lightning")


# ══════════════════════════════════════════════════════════════════════════════
# 1. BASIC TRAINER — Quick prototyping
# ══════════════════════════════════════════════════════════════════════════════

def basic_trainer(max_epochs: int = 10) -> "L.Trainer":
    """
    Minimal trainer for quick prototyping.
    Auto-selects GPU/CPU, minimal logging.
    """
    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="auto",
        devices="auto",
        enable_progress_bar=True,
        logger=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 2. DEBUG TRAINER — Fast dev run + anomaly detection
# ══════════════════════════════════════════════════════════════════════════════

def debug_trainer() -> "L.Trainer":
    """
    Debug trainer: runs 1 batch through train/val/test to find bugs fast.
    Enables gradient anomaly detection (NaN/Inf catching).
    """
    return L.Trainer(
        fast_dev_run=True,
        accelerator="cpu",
        detect_anomaly=True,
        log_every_n_steps=1,
        enable_progress_bar=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 3. SINGLE GPU TRAINER — Production single GPU
# ══════════════════════════════════════════════════════════════════════════════

def single_gpu_trainer(
    max_epochs: int = 100,
    experiment_name: str = "experiment",
    version: str | None = None,
    log_dir: str | Path = "logs/",
    monitor: str = "val/loss",
    monitor_mode: str = "min",
    patience: int = 10,
) -> "L.Trainer":
    """
    Production-ready single GPU trainer.
    Features: mixed precision, checkpointing (top-3 + last), early stopping,
              LR monitor, CSV + TensorBoard loggers.
    """
    log_dir = Path(log_dir)
    ckpt_dir = log_dir / "checkpoints" / experiment_name

    callbacks = [
        ModelCheckpoint(
            dirpath=ckpt_dir,
            filename=f"{experiment_name}-{{epoch:02d}}-{{{monitor}:.4f}}",
            monitor=monitor, mode=monitor_mode,
            save_top_k=3, save_last=True, verbose=True,
        ),
        EarlyStopping(monitor=monitor, mode=monitor_mode, patience=patience, verbose=True),
        LearningRateMonitor(logging_interval="epoch"),
    ]
    if RichProgressBar is not None:
        callbacks.append(RichProgressBar())

    # TensorBoard required — version= prevents fold/run log collision
    loggers = [
        pl_loggers.TensorBoardLogger(save_dir=str(log_dir), name=experiment_name, version=version),
        pl_loggers.CSVLogger(save_dir=str(log_dir), name=experiment_name, version=version),
    ]
    log_path = Path(log_dir) / experiment_name / (version or "version_0")
    print(f"GPU: {__import__('torch').cuda.get_device_name(0) if __import__('torch').cuda.is_available() else 'WARNING: No GPU detected'}")
    print(f"Logs → {log_path}/   run: tensorboard --logdir={log_dir}")

    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="gpu", devices=1,
        precision="16-mixed",
        gradient_clip_val=1.0,
        callbacks=callbacks, logger=loggers,
        log_every_n_steps=10,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 4. MULTI-GPU DDP TRAINER — Distributed Data Parallel
# ══════════════════════════════════════════════════════════════════════════════

def multi_gpu_ddp_trainer(
    max_epochs: int = 100,
    num_gpus: int = 4,
    experiment_name: str = "experiment",
    log_dir: str | Path = "logs/",
    monitor: str = "val/loss",
    monitor_mode: str = "min",
) -> "L.Trainer":
    """
    Multi-GPU training with DDP strategy.
    Best for: standard DL models < 500M parameters.
    Syncs batch norm across GPUs automatically.
    """
    log_dir = Path(log_dir)
    ckpt_dir = log_dir / "checkpoints" / experiment_name

    callbacks = [
        ModelCheckpoint(
            dirpath=ckpt_dir,
            filename=f"{experiment_name}-{{epoch:02d}}-{{{monitor}:.4f}}",
            monitor=monitor, mode=monitor_mode,
            save_top_k=3, save_last=True,
        ),
        EarlyStopping(monitor=monitor, mode=monitor_mode, patience=10),
        LearningRateMonitor(logging_interval="step"),
    ]

    loggers = [pl_loggers.CSVLogger(save_dir=str(log_dir), name=experiment_name)]

    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="gpu", devices=num_gpus,
        strategy=DDPStrategy(
            find_unused_parameters=False,
            gradient_as_bucket_view=True,
        ),
        precision="16-mixed",
        gradient_clip_val=1.0,
        sync_batchnorm=True,
        callbacks=callbacks, logger=loggers,
        log_every_n_steps=50,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 5. LARGE MODEL FSDP TRAINER — Fully Sharded Data Parallel
# ══════════════════════════════════════════════════════════════════════════════

def large_model_fsdp_trainer(
    max_epochs: int = 100,
    num_gpus: int = 8,
    experiment_name: str = "large_model",
    log_dir: str | Path = "logs/",
    cpu_offload: bool = False,
) -> "L.Trainer":
    """
    FSDP trainer for large models (500M+ parameters).
    Shards model weights across GPUs — each GPU holds a fraction of params.
    Set cpu_offload=True if you run out of GPU memory even with FSDP.
    Requires BF16 capable hardware (A100/H100).
    """
    import torch.nn as nn
    log_dir = Path(log_dir)
    ckpt_dir = log_dir / "checkpoints" / experiment_name

    callbacks = [
        ModelCheckpoint(
            dirpath=ckpt_dir,
            filename=f"{experiment_name}-{{epoch:02d}}-{{val_loss:.4f}}",
            monitor="val/loss", mode="min",
            save_top_k=3, save_last=True,
        ),
        LearningRateMonitor(logging_interval="step"),
    ]

    loggers = [pl_loggers.CSVLogger(save_dir=str(log_dir), name=experiment_name)]

    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="gpu", devices=num_gpus,
        strategy=FSDPStrategy(
            sharding_strategy="FULL_SHARD",
            activation_checkpointing_policy={
                nn.TransformerEncoderLayer,
                nn.TransformerDecoderLayer,
            },
            cpu_offload=cpu_offload,
        ),
        precision="bf16-mixed",
        gradient_clip_val=1.0,
        accumulate_grad_batches=4,
        callbacks=callbacks, logger=loggers,
        log_every_n_steps=10,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 6. DEEPSPEED TRAINER — Very large models (10B+)
# ══════════════════════════════════════════════════════════════════════════════

def deepspeed_trainer(
    max_epochs: int = 100,
    num_gpus: int = 8,
    stage: int = 3,
    experiment_name: str = "xlarge_model",
    log_dir: str | Path = "logs/",
) -> "L.Trainer":
    """
    DeepSpeed trainer for very large models (>10B parameters).
    Stage 3 shards optimizer states, gradients, AND parameters across GPUs.
    Requires: pip install deepspeed
    """
    log_dir = Path(log_dir)
    ckpt_dir = log_dir / "checkpoints" / experiment_name

    callbacks = [
        ModelCheckpoint(
            dirpath=ckpt_dir, save_top_k=3, save_last=True,
            every_n_train_steps=1000,
        ),
        LearningRateMonitor(logging_interval="step"),
    ]
    loggers = [pl_loggers.CSVLogger(save_dir=str(log_dir), name=experiment_name)]

    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="gpu", devices=num_gpus,
        strategy=f"deepspeed_stage_{stage}",
        precision="16-mixed",
        gradient_clip_val=1.0,
        accumulate_grad_batches=4,
        callbacks=callbacks, logger=loggers,
        log_every_n_steps=10,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 7. HYPERPARAMETER SEARCH TRAINER — Lightweight sweep runner
# ══════════════════════════════════════════════════════════════════════════════

def hparam_search_trainer(max_epochs: int = 20) -> "L.Trainer":
    """
    Lightweight trainer for hyperparameter sweeps (Optuna, Ray Tune, W&B Sweeps).
    No checkpointing, no heavy logging, uses 50% of batches for speed.
    """
    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="auto", devices=1,
        enable_checkpointing=False,
        logger=False,
        enable_progress_bar=False,
        limit_train_batches=0.5,
        limit_val_batches=0.5,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 8. OVERFIT TEST TRAINER — Verify model capacity
# ══════════════════════════════════════════════════════════════════════════════

def overfit_test_trainer(num_batches: int = 10, max_epochs: int = 100) -> "L.Trainer":
    """
    Overfit on a tiny subset to verify the model CAN learn.
    If it can't overfit on 10 batches, there's a model/optimizer bug.
    """
    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="auto", devices=1,
        overfit_batches=num_batches,
        log_every_n_steps=1,
        enable_progress_bar=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 9. CLUSTER TIME-LIMITED TRAINER — SLURM/HPC wall-clock aware
# ══════════════════════════════════════════════════════════════════════════════

def cluster_time_limited_trainer(
    max_time_hours: float = 23.5,
    max_epochs: int = 1000,
    checkpoint_dir: str | Path = "checkpoints/",
) -> "L.Trainer":
    """
    Time-aware trainer for SLURM/HPC jobs.
    Saves last checkpoint automatically when time limit approaches.
    Resume from last.ckpt on re-submission.

    Usage:
        trainer = cluster_time_limited_trainer(max_time_hours=23.5)
        trainer.fit(model, dm, ckpt_path="checkpoints/last.ckpt")  # resumes if exists
    """
    from datetime import timedelta
    checkpoint_dir = Path(checkpoint_dir)

    callbacks = [
        ModelCheckpoint(
            dirpath=checkpoint_dir,
            save_top_k=3, save_last=True,
            every_n_epochs=5, verbose=False,
        ),
    ]
    if RichProgressBar is not None:
        callbacks.append(RichProgressBar())

    return L.Trainer(
        max_epochs=max_epochs,
        max_time=timedelta(hours=max_time_hours),
        accelerator="gpu", devices="auto",
        callbacks=callbacks,
        log_every_n_steps=50,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 10. REPRODUCIBLE TRAINER — Deterministic results for publications
# ══════════════════════════════════════════════════════════════════════════════

def reproducible_trainer(
    seed: int = 42,
    max_epochs: int = 100,
    experiment_name: str = "reproducible",
    log_dir: str | Path = "logs/",
) -> "L.Trainer":
    """
    Fully deterministic trainer for reproducible research.
    Uses full FP32 precision, deterministic CUDA ops.
    NOTE: Slower than mixed precision — only use for final publication runs.
    """
    L.seed_everything(seed, workers=True)
    log_dir = Path(log_dir)

    callbacks = [
        ModelCheckpoint(
            dirpath=log_dir / "checkpoints" / experiment_name,
            filename=f"{experiment_name}-{{epoch:02d}}-{{val_loss:.4f}}",
            monitor="val/loss", mode="min",
            save_top_k=3, save_last=True,
        ),
        LearningRateMonitor(logging_interval="epoch"),
    ]
    loggers = [
        pl_loggers.CSVLogger(save_dir=str(log_dir), name=experiment_name),
    ]

    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="gpu", devices=1,
        precision="32-true",
        deterministic=True,
        benchmark=False,
        callbacks=callbacks, logger=loggers,
        log_every_n_steps=50,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Quick selection guide
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
Advanced Trainer Configurations — BMAD DL Lifecycle
(Adapted from K-Dense AI claude-scientific-skills)

╔══════════════════════╦═════════════════════════════════════════════════╗
║ Scenario             ║ Use                                             ║
╠══════════════════════╬═════════════════════════════════════════════════╣
║ Quick test           ║ basic_trainer()                                 ║
║ Find bugs            ║ debug_trainer()                                 ║
║ Verify model learns  ║ overfit_test_trainer()                          ║
║ Hparam sweep         ║ hparam_search_trainer()                         ║
║ Production 1 GPU     ║ single_gpu_trainer()                            ║
║ Production N GPUs    ║ multi_gpu_ddp_trainer(num_gpus=4)               ║
║ Large model (500M+)  ║ large_model_fsdp_trainer(num_gpus=8)            ║
║ Very large (10B+)    ║ deepspeed_trainer(num_gpus=8, stage=3)          ║
║ SLURM cluster        ║ cluster_time_limited_trainer(max_time_hours=23) ║
║ Publication result   ║ reproducible_trainer(seed=42)                   ║
╚══════════════════════╩═════════════════════════════════════════════════╝

After training, analyze with:
    python3 scripts/parse_training_logs.py logs/<exp>/version_0/metrics.csv docs/prd/01_PRD.md
    python3 scripts/plot_training_curves.py logs/<exp>/version_0/metrics.csv
""")
