"""
template_lightning_module.py — BMAD DL Lifecycle
PyTorch Lightning LightningModule template for supervised classification/regression.

Drop this file into your project and fill in the TODO sections.

Usage:
    Copy to src/models/your_model.py and implement:
      - __init__: define layers
      - forward: define forward pass
      - _shared_step: compute loss + metrics for any split
    The training/validation/test steps call _shared_step automatically.
"""

from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    import lightning as L
    LightningModule = L.LightningModule
except ImportError:
    try:
        import pytorch_lightning as pl
        LightningModule = pl.LightningModule
    except ImportError:
        raise ImportError(
            "Install PyTorch Lightning: pip install lightning\n"
            "  or: pip install pytorch-lightning"
        )


class YourModel(LightningModule):
    """
    Template LightningModule for image/tabular classification or regression.

    Replace 'YourModel' with a descriptive name (e.g. DefectClassifier, FruitNet).

    Args:
        num_classes: Number of output classes (use 1 for binary/regression).
        learning_rate: Initial learning rate for the optimizer.
        weight_decay: L2 regularization weight.
    """

    def __init__(
        self,
        num_classes: int = 2,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
    ):
        super().__init__()
        # Saves all __init__ args to self.hparams (enables checkpointing)
        self.save_hyperparameters()

        # ── TODO: Define your model architecture ──────────────────────────────
        # Example: simple two-layer MLP for tabular data
        self.encoder = nn.Sequential(
            nn.Linear(128, 64),   # TODO: replace 128 with your input dim
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),
        )
        self.classifier = nn.Linear(64, num_classes)
        # ── END TODO ──────────────────────────────────────────────────────────

        # Loss function
        if num_classes == 1:
            self.loss_fn = nn.BCEWithLogitsLoss()
        else:
            self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor, shape depends on your architecture.
        Returns:
            Logits tensor of shape (batch, num_classes) or (batch, 1).
        """
        # ── TODO: Implement forward pass ──────────────────────────────────────
        features = self.encoder(x)
        logits = self.classifier(features)
        return logits
        # ── END TODO ──────────────────────────────────────────────────────────

    def _shared_step(self, batch: Any, stage: str) -> torch.Tensor:
        """
        Common logic for train/val/test.

        Args:
            batch: Tuple of (inputs, labels) from your DataLoader.
            stage: One of "train", "val", "test".
        Returns:
            Loss tensor.
        """
        # ── TODO: Unpack batch to match your DataLoader output ────────────────
        x, y = batch  # e.g. (images, labels) or (features, targets)
        # ── END TODO ──────────────────────────────────────────────────────────

        logits = self(x)

        if self.hparams.num_classes == 1:
            loss = self.loss_fn(logits.squeeze(1), y.float())
            preds = (torch.sigmoid(logits.squeeze(1)) > 0.5).long()
        else:
            loss = self.loss_fn(logits, y.long())
            preds = logits.argmax(dim=1)

        acc = (preds == y).float().mean()

        # Log metrics — appears in TensorBoard / W&B / CSV logger
        self.log(f"{stage}/loss", loss, prog_bar=(stage == "val"), on_step=False, on_epoch=True)
        self.log(f"{stage}/acc", acc, prog_bar=True, on_step=False, on_epoch=True)

        return loss

    # ── Lightning hooks (do not rename these) ─────────────────────────────────

    def training_step(self, batch: Any, batch_idx: int) -> torch.Tensor:
        loss = self._shared_step(batch, "train")
        if torch.cuda.is_available():
            self.log("gpu/memory_allocated_gb", torch.cuda.memory_allocated() / 1e9,
                     on_step=True, on_epoch=False, prog_bar=False)
        return loss

    def validation_step(self, batch: Any, batch_idx: int) -> None:
        self._shared_step(batch, "val")

    def test_step(self, batch: Any, batch_idx: int) -> None:
        self._shared_step(batch, "test")

    def configure_optimizers(self) -> dict:
        """
        Set up optimizer and learning rate scheduler.
        Swap optimizer or scheduler as needed.
        """
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=self.hparams.learning_rate,
            weight_decay=self.hparams.weight_decay,
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=10,   # TODO: set to your total_epochs
            eta_min=1e-6,
        )
        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "monitor": "val/loss",
            },
        }
