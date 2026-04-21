# Fine-Tuning LLMs

## Fine-Tuning Taxonomy

### Concept

Fine-tuning adapts a pretrained base model for specific tasks or behaviors. The spectrum ranges from minimal (few-shot prompting) to maximal (full parameter updates).

```
Increasing parameter modification:
←─────────────────────────────────────────────────────────────→
Prompting   Prompt Tuning   Prefix Tuning   LoRA   Full Fine-Tune
(0 params)  (few params)    (more params)  (small %)  (all params)
```

**Key decision: fine-tune vs RAG vs prompt engineering?**

| Approach | Best for | Cost | Data needed |
|----------|---------|------|-------------|
| Prompt engineering | Behavior change, style, instruction framing | Free | None |
| RAG | Adding new factual knowledge | Medium | Documents |
| Fine-tuning | Consistent format/style, task specialization | High | Labeled examples |
| Full fine-tuning | Complete behavior overhaul, new domain | Very high | Large labeled dataset |

**Rule of thumb:** Try prompting first, RAG second, fine-tuning only when both are insufficient.

---

## Supervised Fine-Tuning (SFT)

### Concept

SFT trains the model on labeled (input, output) pairs using the standard CLM loss. The model learns to produce the desired output format and style.

**Instruction dataset format:**
```json
{
  "instruction": "Summarize this article in 2 sentences.",
  "input": "The transformer architecture was introduced...",
  "output": "Transformers use self-attention mechanisms...\nThis architecture now dominates NLP."
}
```

**Critical technique — loss masking:**

During SFT, you only compute the loss on the **completion tokens** (the output), not the instruction tokens. This is crucial:

```
Full sequence: [INST]Summarize this.[/INST] The model should focus on...
Loss mask:     [  0  ]  0  0   0  [  0  ]  1   1     1     1   1  ...
```

Why? You want the model to learn to generate good outputs, not to memorize the instruction phrasing. Computing loss on the instruction would also wastefully push the model toward strange completions of instruction fragments.

**Tricky Q:** *Why do you mask the instruction tokens during SFT loss computation?*  
If you include instruction tokens in the loss, you're computing gradients to "predict" arbitrary instruction text — but instructions vary across examples and have no consistent pattern to learn. More importantly, you want to optimize output quality, not instruction completion. Masking ensures gradients only flow from the target output.

**SFT data quality > quantity:**
- 1,000 high-quality diverse instruction-response pairs often outperform 100,000 noisy ones (LIMA paper, 2023)
- Diversity matters: different tasks, domains, lengths, and formats
- Consistency matters: the output should reflect the persona and format you want the model to learn

---

## RLHF — Reinforcement Learning from Human Feedback

### Concept

SFT teaches the model to produce outputs matching a dataset, but datasets can't capture all preferences. RLHF fine-tunes for **human preference** directly.

**The RLHF pipeline:**

```
Stage 1: Supervised Fine-Tuning (SFT)
  Base model → SFT on instruction dataset → SFT model

Stage 2: Reward Model Training
  Human annotators compare pairs of outputs: (response A vs response B) → prefer A
  Train a reward model: input = (prompt, response) → output = scalar reward score

Stage 3: Reinforcement Learning (PPO)
  Use PPO to fine-tune the SFT model to maximize reward
  Constraint: KL divergence from SFT model (prevents reward hacking)
  result_policy = argmax_θ [ E[reward(response)] - β * KL(π_θ || π_SFT) ]
```

**Why RLHF is hard:**
- Reward models are imperfect proxies for human preference — they can be gamed
- PPO is unstable: too many updates → reward hacking (model exploits reward model flaws)
- Expensive: requires thousands of human preference annotations
- Distribution shift: fine-tuned model wanders from the SFT distribution → capability regression

---

## DPO — Direct Preference Optimization

### Concept

DPO (Rafailov et al., 2023) achieves the same goal as RLHF but **without training a separate reward model** or running PPO. It reformulates the preference optimization problem into a direct supervised loss.

**Key insight:** The optimal policy under the RLHF objective has a closed-form relationship with the reward function. DPO rearranges this to optimize directly on preference pairs without explicitly computing rewards.

**DPO loss:**
```
L_DPO = -E[(chosen, rejected)] [ log σ( β * log(π_θ(y_w|x)/π_ref(y_w|x)) 
                                       - β * log(π_θ(y_l|x)/π_ref(y_l|x)) ) ]

Where:
  y_w = preferred (winning) response
  y_l = rejected (losing) response  
  π_ref = reference SFT model (frozen)
  β = temperature controlling how far policy deviates from reference
```

In plain English: increase the log-probability of preferred responses relative to the reference model; decrease the log-probability of rejected responses — all in one supervised loss without RL.

**Why DPO is preferred in 2024:**
- No separate reward model training
- No PPO instability
- Single training stage (like SFT)
- Competitive or superior results on most benchmarks
- Used by: LLaMA-3, Gemma 2 instruction tuning, Mistral models

| Method | Reward model? | RL training? | Stability | Used by |
|--------|--------------|-------------|-----------|---------|
| RLHF/PPO | Yes (separate) | Yes (PPO) | Difficult | GPT-3.5, early ChatGPT |
| DPO | No | No (supervised) | Easy | LLaMA-3, Gemma 2 |
| ORPO | No | No | Easiest | Some recent models |

---

## Parameter-Efficient Fine-Tuning (PEFT)

### Concept

Full fine-tuning updates all model parameters. For a 7B model, that's 7 billion gradients, a full copy of optimizer states, etc. PEFT methods update a tiny fraction of parameters.

**Why not full fine-tuning?**
1. **Cost:** Adam optimizer states = 3× model size in memory (momentum + variance + params)
2. **Catastrophic forgetting:** Full updates overwrite general capabilities
3. **Storage:** Each fine-tuned variant requires saving the full model
4. **Composability:** Hard to combine multiple task-specific fine-tunes

---

## LoRA — Low-Rank Adaptation

### Concept

LoRA (Hu et al., 2021) is the dominant PEFT method. The key insight: the change in weights during fine-tuning has low intrinsic rank — it can be approximated by two small matrices.

**The math:**
```
During full fine-tuning:
  W_new = W_0 + ΔW    (W_0 frozen, ΔW = same shape as W_0)

LoRA approximation:
  ΔW ≈ B × A    where B ∈ ℝ^{d×r}, A ∈ ℝ^{r×k}, rank r << min(d,k)

Forward pass:
  output = x·W_0 + x·(B·A) = x·W_0 + x·ΔW
```

- **W_0** (base model weights): **frozen** — never updated
- **A** (right matrix): initialized with random Gaussian
- **B** (left matrix): initialized with zeros → ΔW = B×A = 0 at start → training starts from the base model behavior
- **r** (rank): hyperparameter, typically 4–64. Lower rank = fewer parameters, potentially lower quality

**Parameter savings:**
```
Full weight: d × k (e.g., 4096 × 4096 = 16.8M)
LoRA:        r × k + d × r = r × (d + k) (e.g., r=16: 16 × 8192 = 131K)
Reduction:   16.8M → 131K = 128× fewer parameters to train
```

**LoRA is typically applied to:** Q and V projection matrices (most impactful), sometimes also K, O, and FFN layers.

**Scaling parameter alpha (α):**
```
output = x·W_0 + (α/r) × x·(B·A)
```
α controls the effective learning rate of the LoRA update. Often set to `r` (so α/r = 1) or `2r`.

---

## QLoRA — Quantized LoRA

### Concept

QLoRA (Dettmers et al., 2023) enables fine-tuning very large models on consumer hardware by:
1. **Quantizing the base model to NF4** (4-bit NormalFloat) — reduces base model memory by 4×
2. **Training LoRA adapters in BF16** — the adapters are small, full-precision
3. **Double quantization** — quantize the quantization constants themselves for extra savings

**Why NF4?** LLM weights have a distribution close to normal. NF4 places quantization bins at equal probability intervals of the normal distribution — better coverage of likely weight values than uniform INT4.

**VRAM comparison for fine-tuning LLaMA-3 8B:**
```
Full fine-tuning (BF16):    8B × 2 bytes = 16 GB weights
                            + 3× for optimizer = 48 GB total ≈ 4× A100-40GB

LoRA (BF16 base):           16 GB weights + ~0.3 GB adapters + optimizer ≈ 24 GB
                            Fits on 1× A100-40GB

QLoRA (NF4 base + BF16 LoRA): 8B × 0.5 bytes = 4 GB weights 
                                + BF16 adapters ≈ 6 GB total
                                Fits on 1× RTX 4090 (24 GB) ✓
```

### Code

```python
# QLoRA fine-tuning with PEFT + BitsAndBytes
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
import torch

# Step 1: Load base model in NF4 (4-bit quantization)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,   # quantize quantization constants
    bnb_4bit_quant_type="nf4",        # NormalFloat4
    bnb_4bit_compute_dtype=torch.bfloat16  # compute in BF16
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    quantization_config=bnb_config,
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")
tokenizer.pad_token = tokenizer.eos_token

# Step 2: Add LoRA adapters
lora_config = LoraConfig(
    r=16,                       # rank
    lora_alpha=32,              # scaling = alpha/r = 2
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # which layers
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Output: trainable params: X | all params: 1B | trainable%: ~0.5%

# Step 3: Training loop (simplified)
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./qlora_output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,  # effective batch = 4×4 = 16
    learning_rate=2e-4,
    fp16=False,         # can't use fp16 with NF4 loaded model
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
    optim="paged_adamw_32bit",  # memory-efficient optimizer for QLoRA
)
```

---

## Multi-Head Fine-Tuning

### Concept

Multi-head fine-tuning uses a **shared encoder backbone** with **multiple task-specific output heads**. This allows a single model to perform several tasks with minimal parameter overhead.

**Architecture:**
```
Input text
    ↓
Shared BERT/RoBERTa/LLaMA encoder
    ↓ hidden states
    ├── [CLS] → Classification head → Intent label
    ├── Token states → NER head → Entity labels per token  
    └── [CLS] → QA head → Start/End logit positions
```

**Implementation pattern:**

```python
import torch
import torch.nn as nn
from transformers import AutoModel

class MultiTaskModel(nn.Module):
    def __init__(self, model_name, num_classes_intent, num_entity_types, hidden_size=768):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        
        # Task head 1: sequence classification (intent)
        self.classification_head = nn.Sequential(
            nn.Dropout(0.1),
            nn.Linear(hidden_size, num_classes_intent)
        )
        
        # Task head 2: token classification (NER)
        self.ner_head = nn.Sequential(
            nn.Dropout(0.1),
            nn.Linear(hidden_size, num_entity_types)
        )
        
        # Task head 3: extractive QA (start/end positions)
        self.qa_head = nn.Linear(hidden_size, 2)  # 2 = start + end logits

    def forward(self, input_ids, attention_mask, task="classification"):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state  # [batch, seq, hidden]
        cls_embedding = hidden_states[:, 0, :]     # [batch, hidden] — CLS token
        
        if task == "classification":
            return self.classification_head(cls_embedding)
        elif task == "ner":
            return self.ner_head(hidden_states)    # per-token logits
        elif task == "qa":
            logits = self.qa_head(hidden_states)   # [batch, seq, 2]
            return logits[:, :, 0], logits[:, :, 1]  # start, end
        else:
            raise ValueError(f"Unknown task: {task}")

# Multi-task training strategy
model = MultiTaskModel("bert-base-uncased", num_classes_intent=10, num_entity_types=9)

# Option 1: Joint training — interleave batches from all tasks
# Option 2: Sequential training — train task 1 then task 2 (catastrophic forgetting risk!)
# Option 3: Task-specific learning rates
optimizer = torch.optim.AdamW([
    {"params": model.encoder.parameters(), "lr": 2e-5},      # small lr for shared encoder
    {"params": model.classification_head.parameters(), "lr": 1e-4},  # larger for heads
    {"params": model.ner_head.parameters(), "lr": 1e-4},
    {"params": model.qa_head.parameters(), "lr": 1e-4},
])
```

**Multi-task interference mitigation:**
- **Gradient surgery (PCGrad):** Projects gradients from one task onto the perpendicular of conflicting gradients from another task — reduces destructive interference
- **Task-specific adapters:** Freeze the shared backbone and train separate LoRA adapters per task — no interference possible
- **Careful task weighting:** Weight task losses to prevent one task dominating gradient updates
- **Sample difficulty:** Easy tasks can hurt hard tasks if they dominate the batch — use balanced sampling

---

## PEFT Methods Comparison

| Method | Trainable params | Quality | Memory | When to use |
|--------|-----------------|---------|--------|-------------|
| Full fine-tune | 100% | Best | Very high | Plenty of data + compute |
| LoRA (r=16) | ~0.5–1% | Near full | Medium | Most fine-tuning tasks |
| QLoRA (NF4) | ~0.5–1% LoRA | Near LoRA | Low | Limited GPU (single 24GB) |
| Prefix tuning | ~0.1% | Good for generation | Low | Domain-specific generation |
| Prompt tuning | ~0.01% | Acceptable | Minimal | Very limited compute |
| Adapters | ~1–5% | Good | Medium | Multi-task with swappable modules |

---

## Study Notes

**Must-know for interviews:**
- SFT loss is masked on instruction tokens — gradients only from output tokens
- RLHF: reward model + PPO; DPO: direct preference on pairs without RL — DPO is now dominant
- LoRA: ΔW ≈ BA where rank r << min(d,k); base model is frozen; ~0.5% trainable params at r=16
- QLoRA = NF4 quantized base + BF16 LoRA adapters → enables 7B fine-tuning on a 24GB GPU
- Multi-head fine-tuning: shared encoder + task-specific heads; task interference → use gradient surgery or per-task LoRA adapters
- When to fine-tune: task-specific format/style that prompting can't achieve consistently

**Quick recall Q&A:**
- *Why mask instruction tokens in SFT?* To only optimize on output quality — instructions vary per example with no consistent target distribution.
- *What is the LoRA initialization strategy and why?* B=zeros, A=random → ΔW=BA=0 at init → training starts exactly from base model behavior.
- *What is NF4?* 4-bit NormalFloat — bins placed at equal probability intervals of a normal distribution, optimal for LLM weights.
- *What is the KL penalty in RLHF PPO?* KL(π_θ || π_SFT) penalizes deviating too far from the SFT model — prevents reward hacking.
- *Why is DPO easier than RLHF?* No separate reward model training; no PPO instability; single supervised training stage.
