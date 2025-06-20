from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch
import warnings
warnings.filterwarnings('ignore')

# Load tokenizer from base model
# tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
tokenizer = AutoTokenizer.from_pretrained("google/gemma-3-1b-it")

# Load base model
# base_model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
base_model = AutoModelForCausalLM.from_pretrained("google/gemma-3-1b-it")
# model = PeftModel.from_pretrained(base_model, "./finetuned-tinyllama-stance")
model = PeftModel.from_pretrained(base_model, "./finetuned-gemma-stance")
model = model.to("cuda" if torch.cuda.is_available() else "cpu")
model.eval()

# Load 10% subset of training data
dataset = load_dataset("json", data_files="../data/tenpct_jsn.jsonl", split="train")
eval_dataset = dataset.shuffle(seed=42).select(range(int(1 * len(dataset))))

def extract_result(text):
    text = text.lower()
    if 'disapprove' in text:
        return 'disapprove'
    elif 'neutral' in text:
        return 'neutral'

    return 'approve'

# Inference function
def generate_output(prompt):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True).to(model.device)
    with torch.no_grad():
        # outputs = model.generate(**inputs, max_new_tokens=10)
        outputs = model.base_model.generate(
            **inputs,
            max_new_tokens=10,
            do_sample=False
        )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return extract_result(decoded.split("Answer:")[-1].strip())




# Evaluation
predictions = []
references = []
for ex in eval_dataset:
    prompt = f"{ex['instruction']}\n{ex['input']}\nAnswer:"
    pred = generate_output(prompt)
    predictions.append(pred)
    references.append(ex["output"])

    # print(f"Prompt: {prompt}\nPredictions: {pred}")

# Accuracy
correct = sum([p.lower() == r.lower() for p, r in zip(predictions, references)])
print("PREDS: ", predictions)
print("CORRECT: ", references)
accuracy = correct / len(predictions)
print("END")

print(f"\n✅ Evaluation completed on {len(predictions)} samples")
print(f"Accuracy: {accuracy:.2%}")
