"""SimpleCNN - a small convolutional classifier for 28x28 grayscale images (MNIST).

Kept intentionally small and readable: two conv+pool blocks followed by a
single fully-connected classification head. This mirrors the shape of the
"Rebuild the Accenture CNN image classifier in raw PyTorch" exercise -
correct and runnable, not overengineered.
"""

import torch.nn as nn


class SimpleCNN(nn.Module):
    """A small CNN for single-channel 28x28 image classification.

    Architecture:
        Conv2d(1, 16, 3) -> ReLU -> MaxPool2d(2)   # 28x28 -> 13x13
        Conv2d(16, 32, 3) -> ReLU -> MaxPool2d(2)  # 13x13 -> 5x5
        Flatten -> Linear(32 * 5 * 5, 128) -> ReLU -> Dropout
        Linear(128, num_classes)
    """

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2),
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 5 * 5, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x
