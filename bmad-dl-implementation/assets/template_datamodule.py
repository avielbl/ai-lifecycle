"""
template_datamodule.py — BMAD DL Lifecycle
PyTorch Lightning LightningDataModule template.

Handles train/val/test dataset loading, transforms, and DataLoader creation
in a clean, reproducible, and Lightning-compatible way.

Usage:
    Copy to src/data/your_datamodule.py and implement the TODO sections.
    Then pass it directly to the Trainer — no manual DataLoaders needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch
from torch.utils.data import DataLoader, Dataset, random_split

try:
    import lightning as L
    LightningDataModule = L.LightningDataModule
except ImportError:
    try:
        import pytorch_lightning as pl
        LightningDataModule = pl.LightningDataModule
    except ImportError:
        raise ImportError("Install PyTorch Lightning: pip install lightning")

try:
    from torchvision import transforms
    HAS_TORCHVISION = True
except ImportError:
    HAS_TORCHVISION = False


# ── TODO: Define or import your Dataset ───────────────────────────────────────
# Replace this stub with your actual Dataset class.

class YourDataset(Dataset):
    """
    Stub dataset — replace with your implementation.

    Expected output per __getitem__: (input_tensor, label_tensor)
    """

    def __init__(self, data_dir: Path, split: str = "train", transform=None):
        self.data_dir = data_dir
        self.split = split
        self.transform = transform

        # TODO: load file list, annotations, CSV rows, etc.
        self.samples: list = []   # list of (path_or_data, label)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        sample, label = self.samples[idx]
        # TODO: load image/array/features from `sample`
        # x = Image.open(sample).convert("RGB")
        # if self.transform:
        #     x = self.transform(x)
        # return x, label
        raise NotImplementedError("Implement __getitem__ in your Dataset")

# ── END TODO ──────────────────────────────────────────────────────────────────


class YourDataModule(LightningDataModule):
    """
    Template LightningDataModule.

    Replace 'YourDataModule' with a descriptive name (e.g. DefectDataModule).

    Args:
        data_dir: Root directory of your dataset.
        batch_size: Batch size for all DataLoaders.
        num_workers: Number of worker processes for data loading.
        val_split: Fraction of training data to use for validation
                   (only used when no explicit val/ directory exists).
        seed: Random seed for reproducibility.
        image_size: (H, W) for image resizing — set None to skip.
    """

    def __init__(
        self,
        data_dir: str | Path = "data/",
        batch_size: int = 32,
        num_workers: int = 4,
        val_split: float = 0.15,
        seed: int = 42,
        image_size: tuple[int, int] | None = (224, 224),
    ):
        super().__init__()
        self.save_hyperparameters()
        self.data_dir = Path(data_dir)

        # Built in setup()
        self.train_dataset: Optional[Dataset] = None
        self.val_dataset: Optional[Dataset] = None
        self.test_dataset: Optional[Dataset] = None

    # ── Transforms ────────────────────────────────────────────────────────────

    def _train_transform(self):
        """
        TODO: Define augmentation pipeline for training.
        """
        if not HAS_TORCHVISION:
            return None
        steps = []
        if self.hparams.image_size:
            steps.append(transforms.Resize(self.hparams.image_size))
        steps += [
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ]
        return transforms.Compose(steps)

    def _eval_transform(self):
        """
        TODO: Define deterministic transform for val/test (no augmentation).
        """
        if not HAS_TORCHVISION:
            return None
        steps = []
        if self.hparams.image_size:
            steps.append(transforms.Resize(self.hparams.image_size))
        steps += [
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ]
        return transforms.Compose(steps)

    # ── Setup ─────────────────────────────────────────────────────────────────

    def setup(self, stage: Optional[str] = None) -> None:
        """
        Called by Lightning before fit/test. Initializes dataset splits.

        stage: "fit" (train+val), "test", "predict", or None (all).
        """
        # TODO: Adjust split detection logic for your directory layout.
        # Option A — explicit split directories: data/train/, data/val/, data/test/
        has_split_dirs = (
            (self.data_dir / "train").exists() and
            (self.data_dir / "val").exists()
        )

        if stage in (None, "fit"):
            if has_split_dirs:
                self.train_dataset = YourDataset(
                    self.data_dir / "train", split="train",
                    transform=self._train_transform(),
                )
                self.val_dataset = YourDataset(
                    self.data_dir / "val", split="val",
                    transform=self._eval_transform(),
                )
            else:
                # Option B — random split from single dataset directory
                full_dataset = YourDataset(
                    self.data_dir, split="train",
                    transform=self._train_transform(),
                )
                val_size = int(len(full_dataset) * self.hparams.val_split)
                train_size = len(full_dataset) - val_size
                self.train_dataset, self.val_dataset = random_split(
                    full_dataset,
                    [train_size, val_size],
                    generator=torch.Generator().manual_seed(self.hparams.seed),
                )

        if stage in (None, "test"):
            test_dir = self.data_dir / "test"
            if test_dir.exists():
                self.test_dataset = YourDataset(
                    test_dir, split="test",
                    transform=self._eval_transform(),
                )

    # ── DataLoaders ───────────────────────────────────────────────────────────

    def train_dataloader(self) -> DataLoader:
        return DataLoader(
            self.train_dataset,
            batch_size=self.hparams.batch_size,
            shuffle=True,
            num_workers=self.hparams.num_workers,
            pin_memory=True,
            drop_last=True,
        )

    def val_dataloader(self) -> DataLoader:
        return DataLoader(
            self.val_dataset,
            batch_size=self.hparams.batch_size,
            shuffle=False,
            num_workers=self.hparams.num_workers,
            pin_memory=True,
        )

    def test_dataloader(self) -> DataLoader:
        if self.test_dataset is None:
            raise RuntimeError("No test dataset found. Check data_dir/test/ exists.")
        return DataLoader(
            self.test_dataset,
            batch_size=self.hparams.batch_size,
            shuffle=False,
            num_workers=self.hparams.num_workers,
            pin_memory=True,
        )
