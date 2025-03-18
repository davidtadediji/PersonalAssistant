import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Set up OpenAI API
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)


# Retrieve the state of a fine-tuning job
def get_job_status_and_model_name(job_id):
    try:
        # Retrieve the job details
        job = client.fine_tuning.jobs.retrieve(job_id)

        # Print the job status
        print(f"Job ID: {job.id}")
        print(f"Status: {job.status}")

        # Check if the job is completed and the model name is available
        if job.status == "succeeded" and hasattr(job, "fine_tuned_model"):
            print(f"Fine-tuned model name: {job.fine_tuned_model}")
        else:
            print("The job is not yet completed or the model name is not available.")

        return job
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Replace with your fine-tuning job ID
job_id = "ftjob-QW0sNTC2DwV30KIcn4GpikTl"

# Get the job status and model name
job_details = get_job_status_and_model_name(job_id)

# Optionally, list events for the job
if job_details:
    print("\nListing events for the job:")
    events = client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id, limit=10)
    for event in events.data:
        print(f"- {event.message} (at {event.created_at})")
