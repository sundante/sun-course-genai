"""
bigram.py, annotated line by line.

Code: Andrej Karpathy, from the lecture "Let's build GPT: from scratch, in code,
      spelled out" (https://www.youtube.com/watch?v=kCc8FmEb1nY), published at
      https://github.com/karpathy/ng-video-lecture under the MIT License.
      The code below is his; the only additions are the explanatory comments.
Notes: LearnGenAI (https://learngenai.sunmintz.com). The line-by-line notes are
      ours; this file is not affiliated with or endorsed by Andrej Karpathy.
      Thank you to Andrej Karpathy for the lecture and the code.

------------------------------------------------------------------------------
MIT License (bigram.py, as stated in the ng-video-lecture README)

Copyright (c) Andrej Karpathy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
------------------------------------------------------------------------------

Shapes use B = batch, T = time (sequence length), C = channels (vocab size, 65).
"""
import torch
import torch.nn as nn
from torch.nn import functional as F

# hyperparameters
batch_size = 32  # how many independent sequences will we process in parallel?
block_size = 8   # what is the maximum context length for predictions?
max_iters = 3000
eval_interval = 300
learning_rate = 1e-2
device = 'cuda' if torch.cuda.is_available() else 'cpu'
eval_iters = 200
# ------------

torch.manual_seed(1337)

# wget https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt
with open('input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# here are all the unique characters that occur in this text
chars = sorted(list(set(text)))
vocab_size = len(chars)
# create a mapping from characters to integers
stoi = { ch:i for i,ch in enumerate(chars) }
itos = { i:ch for i,ch in enumerate(chars) }
encode = lambda s: [stoi[c] for c in s]  # encoder: take a string, output a list of integers
decode = lambda l: ''.join([itos[i] for i in l])  # decoder: take a list of integers, output a string

# Train and test splits
data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9*len(data))  # first 90% will be train, rest val
train_data = data[:n]
val_data = data[n:]


# data loading
# Builds one random batch. split is 'train' or 'val' and decides which slice of the data
# to read from.
def get_batch(split):
    # generate a small batch of data of inputs x and targets y
    # Pick the source tensor. Validation batches come from the final 10% the model never
    # trains on.
    data = train_data if split == 'train' else val_data
    # batch_size random start positions, e.g. 4 of them, shape (B,). The upper bound
    # len(data) - block_size keeps every chunk and its shifted target inside the tensor.
    ix = torch.randint(len(data) - block_size, (batch_size,))
    # Slice block_size tokens from each start, then stack the B one-dimensional slices
    # as the rows of a new 2-D tensor: (B, T), e.g. (4, 8).
    x = torch.stack([data[i:i+block_size] for i in ix])
    # The same chunks shifted one position right. y[b, t] is the token that follows x[b,
    # :t+1], so one (B, T) pair packs B × T training examples.
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    # Move both to the GPU when there is one. The model and its inputs must live on the
    # same device.
    x, y = x.to(device), y.to(device)
    # Inputs and targets, both (B, T) tensors of int64 token ids.
    return x, y


# Decorator: nothing inside records a computation graph. Evaluation needs no gradients,
# so this saves memory and time.
@torch.no_grad()
# One batch's loss is noisy. This averages many batches to get a steadier reading for
# both splits.
def estimate_loss():
    # Will hold {'train': mean_loss, 'val': mean_loss}.
    out = {}
    # Switches layers such as dropout to inference behavior. The bigram has none, but
    # the GPT later in the lecture does.
    model.eval()
    # Measure both splits the same way so they can be compared. Val far above train is
    # the sign of overfitting.
    for split in ['train', 'val']:
        # Pre-allocated slots for eval_iters (200) loss values.
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            # A fresh random batch from this split.
            X, Y = get_batch(split)
            # Forward pass with targets, so a loss comes back.
            logits, loss = model(X, Y)
            # .item() turns the 0-dimensional loss tensor into a plain Python float.
            losses[k] = loss.item()
        # The average over 200 batches.
        out[split] = losses.mean()
    # Back to training mode before control returns to the training loop.
    model.train()
    return out


# Subclassing nn.Module lets PyTorch find every parameter inside, move them with
# .to(device), and save or load them.
class BigramLanguageModel(nn.Module):

    # Runs once, when the model is created: m = BigramLanguageModel(65).
    def __init__(self, vocab_size):
        # Runs nn.Module's own setup first. Without it the layer assigned below is never
        # registered, m.parameters() comes back empty, and the optimizer has nothing to
        # train.
        super().__init__()
        # each token directly reads off the logits for the next token from a lookup table
        # A learnable (65, 65) weight matrix, initialized from N(0, 1). Row i belongs to
        # token i, the current character. Its 65 columns are scores for each possible
        # next character. 65 × 65 = 4,225 parameters, and this table is the entire
        # model. An embedding's width is normally a free choice (n_embd in the GPT).
        # Here it is set to vocab_size so a row can be read directly as next-character
        # logits.
        self.token_embedding_table = nn.Embedding(vocab_size, vocab_size)

    # Called whenever you write self(idx) or m(xb, yb): nn.Module's __call__ runs
    # forward for you. idx is (B, T) token ids. targets is (B, T) ids of the correct
    # next tokens, or None during generation.
    def forward(self, idx, targets=None):

        # idx and targets are both (B,T) tensor of integers
        # The lookup. Each integer in idx is replaced by its row of the table, which
        # adds a third dimension: (B, T) → (B, T, C) with C = 65. No arithmetic happens.
        # It is row indexing, equal to one_hot(idx) @ weight but much cheaper. logits[b,
        # t] is the score vector for the token after idx[b, t].
        logits = self.token_embedding_table(idx) # (B,T,C)

        # Generation mode: there is no answer to compare against.
        if targets is None:
            # So there is no loss. logits keep their (B, T, C) shape, which generate()
            # relies on when it slices out the last time step.
            loss = None
        # Training or evaluation mode: measure how wrong the scores are.
        else:
            # Unpack the three dimensions, e.g. 4, 8, 65.
            B, T, C = logits.shape
            # F.cross_entropy wants class scores in dimension 1, shape (N, C). Merging
            # batch and time gives N = B × T = 32 independent predictions: (32, 65).
            # .view reshapes without copying data.
            logits = logits.view(B*T, C)
            # Flatten the targets the same way, (B, T) → (32,), so row n of logits lines
            # up with targets[n].
            targets = targets.view(B*T)
            # For each row: softmax the 65 scores, take the probability given to the
            # correct id, and compute −ln of it. Then average over the 32 rows. 0 would
            # be perfect. A uniform guess gives −ln(1/65) ≈ 4.17. The random starting
            # table gives about 4.88: confidently wrong, slightly worse than guessing.
            loss = F.cross_entropy(logits, targets)

        # Mind the shape difference: with targets, logits come back flattened to (B·T,
        # C); without them they stay (B, T, C).
        return logits, loss

    # Extends a context one token at a time. idx is the (B, T) starting context, e.g.
    # torch.zeros((1, 1)), a single newline. Returns a (B, T + max_new_tokens) tensor.
    def generate(self, idx, max_new_tokens):
        # idx is (B, T) array of indices in the current context
        # One pass per new token. The loop counter itself is unused, hence _.
        for _ in range(max_new_tokens):
            # get the predictions
            # Forward pass on the whole sequence so far. No targets, so loss is None and
            # logits are (B, T, C): a next-token score row for every position. Only the
            # last row gets used. That is wasted work for a bigram, which ignores
            # history, but this exact loop is reused unchanged for the GPT, where every
            # earlier position matters.
            logits, loss = self(idx)
            # focus only on the last time step
            # Every batch row, the last time step, all 65 channels. Indexing a dimension
            # with a single integer removes that dimension, so (B, T, C) → (B, C).
            # Writing logits[:, -1:, :] would keep it, giving (B, 1, C).
            logits = logits[:, -1, :] # becomes (B, C)
            # apply softmax to get probabilities
            # softmax(z)ⱼ = exp(zⱼ) / Σₖ exp(zₖ), taken along dim=-1, the 65 channels.
            # Every value becomes positive and each row sums to 1. The order is
            # preserved: the highest logit is still the most likely character. Adding
            # the same constant to every logit changes nothing, so only the differences
            # between logits matter.
            probs = F.softmax(logits, dim=-1) # (B, C)
            # sample from the distribution
            # A weighted random draw, one per batch row: a character with probability
            # 0.30 is picked about 30% of the time. Sampling instead of taking the
            # argmax keeps the text varied; argmax would always produce the same, often
            # looping, output. Returns int64 ids of shape (B, 1), already 2-D, ready to
            # concatenate.
            idx_next = torch.multinomial(probs, num_samples=1) # (B, 1)
            # append sampled index to the running sequence
            # Join along dim=1, the time axis: (B, T) + (B, 1) → (B, T+1). The new token
            # becomes the last token on the next pass. Feeding each output back in as
            # the next input is what autoregressive generation means.
            idx = torch.cat((idx, idx_next), dim=1) # (B, T+1)
        # The original context followed by max_new_tokens sampled ids.
        # decode(idx[0].tolist()) turns the first row back into text.
        return idx


# Create the model. The table starts random.
model = BigramLanguageModel(vocab_size)
# Move every parameter to the GPU if there is one. For a Module, .to() works in place
# and returns the same object, so m and model are one model under two names.
m = model.to(device)

# create a PyTorch optimizer
# AdamW keeps running averages of each parameter's gradient and squared gradient and
# scales every update by them. model.parameters() hands it the 4,225 table entries. The
# script uses lr = 1e-2; the notebook used 1e-3 for 10,000 steps.
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

# One optimization step per iteration.
for iter in range(max_iters):

    # every once in a while evaluate the loss on train and val sets
    # Every eval_interval (300) steps, stop to report progress.
    if iter % eval_interval == 0:
        losses = estimate_loss()
        print(f"step {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

    # sample a batch of data
    # A new random (32, 8) batch every step, so the model keeps seeing different
    # examples.
    xb, yb = get_batch('train')

    # evaluate the loss
    # Forward pass with targets: one number summarizing how wrong the table is on this
    # batch.
    logits, loss = model(xb, yb)
    # PyTorch adds new gradients onto old ones by default, so clear them first.
    # set_to_none releases the memory instead of filling it with zeros.
    optimizer.zero_grad(set_to_none=True)
    # Backpropagation: for every table entry, work out how the loss would change if that
    # entry moved. Only rows for characters that appeared in xb receive a non-zero
    # gradient.
    loss.backward()
    # Move each parameter a little against its gradient. Over thousands of steps the
    # rows drift toward Shakespeare's real next-character statistics.
    optimizer.step()

# generate from the model
context = torch.zeros((1, 1), dtype=torch.long, device=device)
print(decode(m.generate(context, max_new_tokens=500)[0].tolist()))
