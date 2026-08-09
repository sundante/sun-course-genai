"""Raw PyTorch training script for a small CNN MNIST classifier.

Demonstrates, in one runnable file, every mechanic covered in the
11-Prog-Langs/PyTorch Notes: custom Dataset/DataLoader usage, a
hand-written training loop, model.train()/model.eval() switching,
checkpointing (model + optimizer state_dict, resumable), and mixed
precision via autocast + GradScaler (auto-disabled on CPU-only machines).

Usage:
    python train.py
    python train.py --epochs 5 --batch-size 64 --lr 1e-3 --checkpoint-every 2
    python train.py --resume checkpoints/model_epoch2.pt
"""

import argparse
import os

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import SimpleCNN

try:
    from torch.cuda.amp import autocast, GradScaler
    AMP_AVAILABLE = True
except ImportError:  # very old torch versions
    AMP_AVAILABLE = False


def parse_args():
    parser = argparse.ArgumentParser(description="Train a small CNN on MNIST in raw PyTorch.")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--data-dir", type=str, default="./data")
    parser.add_argument("--checkpoint-dir", type=str, default="./checkpoints")
    parser.add_argument("--checkpoint-every", type=int, default=2,
                         help="Save a checkpoint every N epochs.")
    parser.add_argument("--resume", type=str, default=None,
                         help="Path to a checkpoint to resume training from.")
    parser.add_argument("--num-workers", type=int, default=2)
    return parser.parse_args()


def get_dataloaders(data_dir: str, batch_size: int, num_workers: int):
    """Custom Dataset (via torchvision) wrapped in DataLoaders for train/val."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),  # MNIST mean/std
    ])

    train_ds = datasets.MNIST(root=data_dir, train=True, download=True, transform=transform)
    val_ds = datasets.MNIST(root=data_dir, train=False, download=True, transform=transform)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )
    return train_loader, val_loader


def save_checkpoint(path, epoch, model, optimizer, best_val_acc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "best_val_acc": best_val_acc,
    }, path)
    print(f"Checkpoint saved to {path}")


def load_checkpoint(path, model, optimizer, device):
    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    start_epoch = checkpoint["epoch"] + 1
    best_val_acc = checkpoint.get("best_val_acc", 0.0)
    print(f"Resumed from {path} at epoch {start_epoch}")
    return start_epoch, best_val_acc


def evaluate(model, loader, loss_fn, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            outputs = model(batch_x)
            loss = loss_fn(outputs, batch_y)
            total_loss += loss.item() * batch_x.size(0)
            correct += (outputs.argmax(dim=1) == batch_y).sum().item()
            total += batch_x.size(0)
    return total_loss / total, correct / total


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = AMP_AVAILABLE and device.type == "cuda"
    print(f"Using device: {device} | mixed precision: {use_amp}")

    train_loader, val_loader = get_dataloaders(args.data_dir, args.batch_size, args.num_workers)

    model = SimpleCNN(num_classes=10).to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()
    scaler = GradScaler(enabled=use_amp) if AMP_AVAILABLE else None

    start_epoch = 0
    best_val_acc = 0.0
    if args.resume:
        start_epoch, best_val_acc = load_checkpoint(args.resume, model, optimizer, device)

    for epoch in range(start_epoch, args.epochs):
        # ---- Training phase ----
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)

            optimizer.zero_grad()

            if use_amp:
                with autocast():
                    outputs = model(batch_x)
                    loss = loss_fn(outputs, batch_y)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                outputs = model(batch_x)
                loss = loss_fn(outputs, batch_y)
                loss.backward()
                optimizer.step()

            running_loss += loss.item() * batch_x.size(0)
            correct += (outputs.argmax(dim=1) == batch_y).sum().item()
            total += batch_x.size(0)

        train_loss = running_loss / total
        train_acc = correct / total

        # ---- Validation phase ----
        val_loss, val_acc = evaluate(model, val_loader, loss_fn, device)

        print(f"Epoch {epoch + 1}/{args.epochs} | "
              f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}")

        best_val_acc = max(best_val_acc, val_acc)

        if (epoch + 1) % args.checkpoint_every == 0 or (epoch + 1) == args.epochs:
            ckpt_path = os.path.join(args.checkpoint_dir, f"model_epoch{epoch + 1}.pt")
            save_checkpoint(ckpt_path, epoch, model, optimizer, best_val_acc)

    final_train_loss, final_train_acc = evaluate(model, train_loader, loss_fn, device)
    final_val_loss, final_val_acc = evaluate(model, val_loader, loss_fn, device)
    print(f"Final: train_acc={final_train_acc:.4f} val_acc={final_val_acc:.4f}")


if __name__ == "__main__":
    main()
