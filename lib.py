import os
import time
import requests
import json
from openai import OpenAI

class APIConnection:
    def __init__(self):
        self.headers = None

    def get_connection(self):
        if self.headers is None:
            print("Logging in...")
            json_data = {
                "email": "ffm@example.com",
                "password": "passwordffm"
            }

            url_user = 'http://127.0.0.1:8000/api/v1.0/user/login'
            response = requests.post(url_user, json=json_data, timeout=120)

            if response.status_code == 200:
                data = response.json()
                token = data.get('data', {}).get('id_token')

                if not token:
                    raise ValueError("Failed to retrieve token from response")

                self.headers = {'Authorization': f'Bearer {token}'}
            else:
                raise ValueError(f"Authentication failed: {response.status_code}")

        return self.headers

client = OpenAI()
api_connection = APIConnection()


def check_openai_api_key():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")


def compute_kpi_by_machine_id(machine_id: str, kpi_id: str, start_date: str, end_date: str, granularity_op: str) -> dict:
    headers = api_connection.get_connection()

    url = f'http://127.0.0.1:8000/api/v1.0/kpi/machine/{machine_id}/compute/'
    params = {
        'kpi_id': kpi_id,
        'start_date': start_date,
        'end_date': end_date,
        'granularity_op': granularity_op
    }

    response = requests.get(url, headers=headers, params=params, timeout=120)
    result = response.json()

    return result

def push_file_in_vector_store(file_path: str, verbose=False) -> str:
    check_openai_api_key()

    vector_store = client.beta.vector_stores.create(name="DB data")

    file_paths = [file_path]
    file_streams = [open(path, "rb") for path in file_paths]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id, files=file_streams
    )

    if verbose:
        print(file_batch.status)
        print(file_batch.file_counts)

    return vector_store.id

def link_vector_store(vector_store_id: str) -> str:
    assistant = client.beta.assistants.create(
    name="Comparison Assistant",
    instructions="""
    You are an assistant for a production site that uses machines to manufacture products. User can ask questions about the site, machines, and KPIs. Also the user can ask to compute KPIs for some machines.
    In those situations, i.e. when the user asks about KPIs'computation and/or comparison, you should:
    1. Use the `file_search` tool to retrieve the machine IDs for the listed machines.
    2. Use the `file_search` tool to retrieve the KPI IDs for the listed KPIs.
    3. Use the `compute_kpi_by_machine_id` function using the machines and KPIs' IDs retrieved in the previous steps.
    4. Present the comparison in a clear and concise manner.
    If the user asks for something out of your knowledge, let him know that you can't help with that, and ask for another request, specifying what you can do.

    You can also be asked to answer questions about cost prediction (eur/kwh) for a category of machines, utilization rate and energy efficiency rate (in terms of percentage) for a specific machine. In those cases, you should:
    1. Use the `file_search` tool to retrieve the data for a specific machine or category.
    2. Inform the user with the data retrieved.

    You also must be able to create new KPIs that have to make sense. This can be requested by the user in form of a suggestion (e.g. "Can you suggest a KPI for machine X?"), as well as a more direct command (e.g. "Create a new KPI that represents cost per cycle). Keep in mind that you have to give a resulting formula to compute the proposed KPI, and it must use the available ones. The formulas should be usable by an automated system that can query a dataset (e.g. "cost per cycle" will translate to cost / cycles). When suggesting new KPIs keep it simple, don't make huge KPIs that are hard to understand or compute.
    So, this is the process you must follow:
    1. Use the `file_search` tool to retrieve the KPIs available in the system.
    2. Use the retrieved KPIs to suggest a new KPI. You can use only the available KPIs to create the new one, using exactly their names (in the same format) and the operations available in Python (e.g. `+`, `-`, `*`, `/`, `**`, `//`, `%`).
    3. Present the new KPI in a clear and concise manner.
    """,
    model="gpt-4o-mini",
    tools=[
        {"type": "file_search"},
        {
            "type": "function",
            "function": {
                "name": "compute_kpi_by_machine_id",
                "description": "Computes KPI for a specific machine based on provided parameters",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "machine_id": {"type": "string", "description": "Machine ID"},
                        "kpi_id": {"type": "string", "description": "KPI ID"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD HH:MM:SS)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD HH:MM:SS)"},
                        "granularity_op": {"type": "string", "description": "Granularity operation (e.g., 'avg')"}
                    },
                    "additionalProperties": False,
                    "required": ["machine_id", "kpi_id", "start_date", "end_date", "granularity_op"]
                }
            }
        }
    ])
    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
        )
    return assistant.id

def start_thread() -> str:
    thread = client.beta.threads.create()
    return thread.id

def query_rag(thread_id: str, assistant_id, query: str, verbose=False) -> str:
    
    # Step 1: User Request
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=query
    )

    # Step 2: Run the Assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Step 3: Process Required Actions
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if verbose:
            print(run_status.status)

        if run_status.status == "completed":
            break  # Done

        if run_status.status == "failed":
            if verbose:
                print("Run failed.")
            break

        if run_status.status == "requires_action":
            required_action = run_status.required_action

            if required_action.type == "submit_tool_outputs":
                tool_calls = required_action.submit_tool_outputs.tool_calls

                tool_outputs = []  # Store all outputs for submission

                for tool_call in tool_calls:
                    if tool_call.type == "function" and tool_call.function.name == "compute_kpi_by_machine_id":
                        # Extract tool call ID and JSON arguments
                        tool_call_id = tool_call.id
                        function_arguments = json.loads(tool_call.function.arguments)  # Parse JSON string

                        if verbose:
                            print(f"Calling compute_kpi_by_machine_id for call_id: {tool_call_id}...")

                        # Step 4: Call the external function (you need to implement this part)
                        kpi_result = compute_kpi_by_machine_id(  # Placeholder function
                            machine_id=function_arguments["machine_id"],
                            kpi_id=function_arguments["kpi_id"],
                            start_date=function_arguments["start_date"],
                            end_date=function_arguments["end_date"],
                            granularity_op=function_arguments["granularity_op"]
                        )

                        if verbose:
                            print(f"Computed KPI for call_id {tool_call_id}: {kpi_result}")

                        # Convert output dictionary to JSON string
                        tool_output_json = json.dumps(kpi_result)

                        # Append result for submission
                        tool_outputs.append({
                            "tool_call_id": tool_call_id,
                            "output": tool_output_json
                        })

                # Step 5: Submit all computed KPI values together
                if tool_outputs:
                    if verbose:
                        print(f"Submitting {len(tool_outputs)} computed KPI results to the assistant...")
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs  # Submitting all results
                    )

        time.sleep(2)  # Avoid excessive polling

    # Step 6: Retrieve Final Response from the Assistant
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return messages.data[0].content[0].text.value
