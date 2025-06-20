from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import get_peft_model, LoraConfig, TaskType
import torch
import os

# --- 1) ENVIRONMENT SETUP ---
os.environ["TRANSFORMERS_NO_TF"] = "1"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- 2) LOAD DATASET ---
dataset = load_dataset("json", data_files="../data/tenpct_jsn.jsonl", split="train")

# --- 3) MODEL & TOKENIZER ---
# model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16).to(device)

# Disable cache for gradient checkpointing
model.config.use_cache = False

# --- 4) APPLY LoRA & ENABLE GRADIENT FLOW ---
lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    task_type=TaskType.CAUSAL_LM,
    lora_dropout=0.1,
    bias="none",
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ]
)

model = get_peft_model(model, lora_config)
model.enable_input_require_grads()  # 🔑 Fix for checkpoint + PEFT :contentReference[oaicite:6]{index=6}
model.gradient_checkpointing_enable()

# Force LoRA adapters to require gradients
for n, p in model.named_parameters():
    if "lora_" in n:
        p.requires_grad = True

model.print_trainable_parameters()

# --- 5) TOKENIZATION ---
def tokenize(example):
    prompt = f"{example['instruction']}\n{example['input']}\nAnswer:"
    full = prompt + " " + example["output"]
    enc = tokenizer(full, truncation=True, padding="max_length", max_length=256)
    enc["labels"] = enc["input_ids"].copy()
    return enc



dataset = dataset.map(tokenize, remove_columns=dataset.column_names)

# --- 6) TRAINING SETUP ---
training_args = TrainingArguments(
    output_dir="./finetuned-deepseekr1-stance",
    per_device_train_batch_size=1,
    num_train_epochs=3,
    logging_dir="./logs",
    save_total_limit=1,
    logging_steps=100,
    save_steps=500,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
)

# --- 7) LOSS CHECK BEFORE TRAINING ---
first_batch = next(iter(trainer.get_train_dataloader()))
model.eval()
with torch.no_grad():
    out = model(
        input_ids=first_batch["input_ids"].to(model.device),
        attention_mask=first_batch["attention_mask"].to(model.device),
        labels=first_batch["labels"].to(model.device),
    )
    print("\n🎯 Loss check before training:")
    print("Loss:", out.loss)
    print("Has grad_fn?", out.loss.requires_grad)  # Should be True!

# --- 8) TRAIN ---
trainer.train()


# --- 9) MANUAL SAVE ---
trainer.save_model("./finetuned-deepseekr1-stance")  # ✅ Save the model weights
tokenizer.save_pretrained("./finetuned-deepseekr1-stance")  # ✅ Save tokenizer too
