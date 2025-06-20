from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import get_peft_model, LoraConfig, TaskType
import os
import torch 


os.environ["TRANSFORMERS_NO_TF"] = "1"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# Load dataset
dataset = load_dataset("json", data_files="stance_finetune_data.jsonl", split="train")

# Load tokenizer and model
model_name = "google/gemma-3-4b-pt"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=True)
model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=True).to(device)

# Apply LoRA config
lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    task_type=TaskType.CAUSAL_LM,
    lora_dropout=0.1,
    bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
)
model = get_peft_model(model, lora_config).to(device)

# Tokenize
def tokenize(example):
    prompt = f"{example['instruction']}\n{example['input']}\nAnswer:"
    return tokenizer(prompt + " " + example["output"], truncation=True, padding="max_length", max_length=512)

dataset = dataset.map(tokenize)

# Trainer setup
training_args = TrainingArguments(
    output_dir="./finetuned-gemma-stance",
    per_device_train_batch_size=4,
    num_train_epochs=3,
    logging_dir="./logs",
    save_total_limit=1,
    save_steps=500,
    logging_steps=100
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
)

trainer.train()
