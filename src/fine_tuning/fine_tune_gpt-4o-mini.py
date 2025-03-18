# fine_tune_gpt4o_mini.py

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
# Set up OpenAI API
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Upload the dataset
train_file = client.files.create(
    file=open("actions.jsonl", "rb"),
    purpose="fine-tune"
)

print(f"Training file ID: {train_file.id}")

# Start the fine-tuning job
fine_tune_job = client.fine_tuning.jobs.create(
    training_file=train_file.id,
    model="gpt-4o-mini-2024-07-18",  # Replace with the correct model name
    hyperparameters={
        "n_epochs": 3,
        "batch_size": 3,
        "learning_rate_multiplier": 0.3
    }
)

print(f"Fine-tuning job ID: {fine_tune_job.id}")
print(f"Fine-tuning job status: {fine_tune_job.status}")

# Monitor the fine-tuning job
job_id = fine_tune_job.id
status = client.fine_tuning.jobs.retrieve(job_id)
print(f"Job status: {status.status}")

# Retrieve the fine-tuned model name once the job is complete
fine_tuned_model = client.fine_tuning.jobs.retrieve(job_id).fine_tuned_model
print(f"Fine-tuned model name: {fine_tuned_model}")
