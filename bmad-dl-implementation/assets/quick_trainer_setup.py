"""
quick_trainer_setup.py — BMAD DL Lifecycle
Ready-to-run Lightning Trainer configuration for standard DL training runs.

Covers: callbacks (early stopping, checkpointing, LR monitor),
        loggers (CSV + optional TensorBoard/W&B), and hardware-aware device selection.

Usage:
    python3 assets/quick_trainer_setup.py          # prints recommended config
    python3 assets/quick_trainer_setup.py --run    # launches a training run (demo)

Or import and call build_trainer() in your training script:

    from assets.quick_trainer_setup import build_trainer
    from src.models.your_model import YourModel
    from src.data.your_datamodule import YourDataModule

    trainer = build_trainer(max_epochs=50, experiment_name="run_001")
    model = YourModel(num_classes=2)
    dm = YourDataModule(data_dir="data/")
    trainer.fit(model, dm)
    trainer.test(model, dm)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ── Lightning import ──────────────────────────────────────────────────────────

try:
    import lightning as L
    from lightning.pytorch.callbacks import (
        EarlyStopping, ModelCheckpoint, LearningRateMonitor, RichProgressBar,
    )
    from lightning.pytorch.loggers import CSVLogger
    LIGHTNING_PKG = "lightning"
except ImportError:
    try:
        import pytorch_lightning as L
        from pytorch_lightning.callbacks import (
            EarlyStopping, ModelCheckpoint, LearningRateMonitor,
        )
        from pytorch_lightning.loggers import CSVLogger
        RichProgressBar = None
        LIGHTNING_PKG = "pytorch_lightning"
    except ImportError:
        L = None  # type: ignore
        LIGHTNING_PKG = None


def _detect_accelerator() -> tuple[str, int]:
    """Return (accelerator, devices) based on available hardware."""
    try:
        import torch
        if torch.cuda.is_available():
            return "gpu", torch.cuda.device_count()
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps", 1
    except ImportError:
        pass
    return "cpu", 1


def build_trainer(
    max_epochs: int = 50,
    experiment_name: str = "experiment",
    log_dir: str | Path = "logs/",
    monitor_metric: str = "val/loss",
    monitor_mode: str = "min",
    early_stopping_patience: int = 10,
    gradient_clip_val: float = 1.0,
    accumulate_grad_batches: int = 1,
    precision: str = "16-mixed",
) -> "L.Trainer":
    """
    Build a Lightning Trainer with standard callbacks and logging.

    Args:
        max_epochs: Maximum training epochs.
        experiment_name: Name used for checkpoint dir and CSV log subdir.
        log_dir: Root directory for logs and checkpoints.
        monitor_metric: Metric to monitor for early stopping and checkpointing.
        monitor_mode: "min" (for loss) or "max" (for accuracy/F1).
        early_stopping_patience: Stop after N epochs without improvement.
        gradient_clip_val: Max gradient norm (0.0 to disable clipping).
        accumulate_grad_batches: Simulate larger batch size via gradient accumulation.
        precision: Training precision ("32", "16-mixed", "bf16-mixed").

    Returns:
        Configured Lightning Trainer.
    """
    if L is None:
        raise ImportError(
            "PyTorch Lightning not installed.\n"
            "  pip install lightning   (recommended)\n"
            "  or: pip install pytorch-lightning"
        )

    log_dir = Path(log_dir)
    ckpt_dir = log_dir / "checkpoints" / experiment_name
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    accelerator, devices = _detect_accelerator()

    # ── Callbacks ─────────────────────────────────────────────────────────────
    callbacks = [
        ModelCheckpoint(
            dirpath=ckpt_dir,
            filename=f"{experiment_name}-{{epoch:02d}}-{{{monitor_metric}:.4f}}",
            monitor=monitor_metric,
            mode=monitor_mode,
            save_top_k=3,
            save_last=True,
            verbose=True,
        ),
        EarlyStopping(
            monitor=monitor_metric,
            mode=monitor_mode,
            patience=early_stopping_patience,
            verbose=True,
        ),
        LearningRateMonitor(logging_interval="epoch"),
    ]
    if RichProgressBar is not None:
        callbacks.append(RichProgressBar())

    # ── Loggers ───────────────────────────────────────────────────────────────
    csv_logger = CSVLogger(save_dir=str(log_dir), name=experiment_name)

    loggers = [csv_logger]

    # Optional: TensorBoard logger
    try:
        if LIGHTNING_PKG == "lightning":
            from lightning.pytorch.loggers import TensorBoardLogger
        else:
            from pytorch_lightning.loggers import TensorBoardLogger
        loggers.append(TensorBoardLogger(save_dir=str(log_dir), name=experiment_name))
    except (ImportError, Exception):
        pass  # TensorBoard not required

    # ── Precision ─────────────────────────────────────────────────────────────
    # Fall back to 32-bit on CPU (mixed precision not supported)
    if accelerator == "cpu" and precision != "32":
        precision = "32"

    trainer = L.Trainer(
        max_epochs=max_epochs,
        accelerator=accelerator,
        devices=devices,
        precision=precision,
        gradient_clip_val=gradient_clip_val if gradient_clip_val > 0 else None,
        accumulate_grad_batches=accumulate_grad_batches,
        callbacks=callbacks,
        logger=loggers,
        log_every_n_steps=10,
        deterministic=False,  # set True for full reproducibility (slower)
    )

    return trainer


def print_config(max_epochs: int, experiment_name: str, log_dir: str) -> None:
    accelerator, devices = _detect_accelerator()
    print(f"""
┌─────────────────────────────────────────────────────┐
│  BMAD DL — Quick Trainer Configuration              │
├─────────────────────────────────────────────────────┤
│  Lightning package : {LIGHTNING_PKG or 'NOT INSTALLED':<30} │
│  Hardware          : {accelerator.upper()} ({devices} device(s)){'':<19} │
│  Max epochs        : {max_epochs:<30} │
│  Experiment name   : {experiment_name:<30} │
│  Log directory     : {log_dir:<30} │
├─────────────────────────────────────────────────────┤
│  Callbacks active:                                  │
│    ✓ ModelCheckpoint  (top-3 + last)                │
│    ✓ EarlyStopping    (patience=10)                 │
│    ✓ LearningRateMonitor                            │
│    ✓ RichProgressBar  (if available)                │
│  Loggers active:                                    │
│    ✓ CSVLogger                                      │
│    ✓ TensorBoardLogger (if tensorboard installed)   │
└─────────────────────────────────────────────────────┘

  Quick start in your training script:

    from assets.quick_trainer_setup import build_trainer
    trainer = build_trainer(max_epochs=50, experiment_name="run_001")
    trainer.fit(model, datamodule)
    trainer.test(model, datamodule)

  After training, parse results with:

    python3 scripts/parse_training_logs.py \\
        logs/{experiment_name}/version_0/metrics.csv \\
        docs/prd/01_PRD.md
""")


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick Trainer Setup — BMAD DL Lifecycle")
    parser.add_argument("--run", action="store_true", help="Launch a demo training run")
    parser.add_argument("--max-epochs", type=int, default=50)
    parser.add_argument("--experiment-name", type=str, default="run_001")
    parser.add_argument("--log-dir", type=str, default="logs/")
    args = parser.parse_args()

    if args.run:
        if L is None:
            print("Error: PyTorch Lightning not installed.", file=sys.stderr)
            return 2
        print("Demo run requires a model and datamodule. See module docstring.")
        return 1

    print_config(args.max_epochs, args.experiment_name, args.log_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
