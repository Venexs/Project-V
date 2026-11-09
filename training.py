import torch
import glob
import os
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer

# --- 0. Setup and Install Dependencies (Run this in your environment first!) ---
# !pip install transformers accelerate peft bitsandbytes datasets trl

# --- 1. Configuration for 6GB VRAM ---
YOUR_NAME = "James"
MODEL_ID = "microsoft/Phi-3-mini-4k-instruct" 
DATA_FOLDER = "Json Data"
OUTPUT_DIR = "./james_ai_self_finetuned"

# --- 2. Data Loading (Handles Multiple .jsonl Files with different schemas) ---
try:
    data_files = os.path.join(DATA_FOLDER, "*.jsonl")
    print(f"Loading data from pattern: {data_files}")

    # Load all .jsonl files in the directory and merge them
    dataset = load_dataset(
        "json",
        data_files=data_files,
        split="train"
    )

    # Keep only 'text' column for training, drop extra columns
    if 'rating' in dataset.column_names:
        dataset = dataset.remove_columns(['rating', 'ai_response', 'user_input'])

    print(f"✅ Successfully loaded {len(dataset)} total examples for training.")

except Exception as e:
    print(f"🚨 ERROR loading dataset: {e}")
    print("Please ensure the 'Json Data' folder exists and contains valid '.jsonl' files.")
    exit()

# --- 3. QLoRA and Model Loading (VRAM Optimization) ---

# QLoRA: 4-bit quantization configuration
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",       # Normal Float 4-bit
    bnb_4bit_compute_dtype=torch.bfloat16, # Recommended for modern GPUs
    bnb_4bit_use_double_quant=True     # Extra VRAM saving technique
)

print(f"Starting download and 4-bit quantization of {MODEL_ID}...")

# Download and load the model with 4-bit quantization
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="cuda:0", 
    low_cpu_mem_usage=True 
)

# CRITICAL VRAM SAVING & Warning Fix:
model.config.use_cache = False  
model.enable_input_require_grads() 
# NEW LINE TO ADDRESS THE WARNING:
model.config.reorder_and_upcast_attn = False
model.config.use_reentrant = False # <--- ADD THIS LINE TO CLEAR THE WARNING

print("Model loaded and configured with QLoRA and Gradient Checkpointing.")

# Load Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token 
tokenizer.padding_side = "right"

# --- 3. QLoRA and Model Loading (VRAM Optimization) ---

# LoRA Configuration: Reduce Rank to 4
lora_config = LoraConfig(
    r=4,                            # <--- CHANGED: Max VRAM saving for the adapter
    lora_alpha=16,
    target_modules="all-linear",    
    bias="none",
    task_type="CAUSAL_LM",
)

# Training Arguments (Optimized for 6GB VRAM)
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=5,              
    per_device_train_batch_size=1,   
    gradient_accumulation_steps=8,   
    optim="paged_adamw_8bit",        
    logging_steps=10,
    learning_rate=2e-4,              
    bf16=False,                      # <-- **SET TO FALSE** (GPU doesn't support it)
    fp16=True,                       # <-- **SET TO TRUE** (Use widely supported Float16)
    save_strategy="epoch",
    gradient_checkpointing=True,     
    report_to="none"                 
)


# --- 5. Initialize and Run the Trainer ---

print("Initializing Supervised Fine-Tuning Trainer...")
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    peft_config=lora_config,
    dataset_text_field="text",  # Data from raw_data_maker.py is pre-formatted Phi-3 text
    max_seq_length=512,
    tokenizer=tokenizer,
)

print("\n\n#####################################################################")
print("############# STARTING FINE-TUNING OF THE JAMES AI SELF #############")
print("#####################################################################\n")

# Start the training process
trainer.train()

# --- 6. Save the Final Adapter Weights ---
final_adapter_path = os.path.join(OUTPUT_DIR, "james_ai_self_adapter")
trainer.model.save_pretrained(final_adapter_path)
tokenizer.save_pretrained(final_adapter_path)
print(f"\n\n✅ Training Complete! Your 'James AI Self' adapter weights are saved to: {final_adapter_path}")
print("Next step: Use these saved weights for inference (talking to your AI Self).")