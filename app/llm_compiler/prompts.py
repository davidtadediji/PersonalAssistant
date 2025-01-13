from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

base_planner_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Given a user query, create a plan to solve it with the utmost parallelizability. Each plan should comprise an action from the following {num_tools} types:
        {tool_descriptions}
        {num_tools}. join(): Collects and combines results from prior actions.

        ### Guidelines:
        - **join()** should always be the last action in the plan and will be called in two scenarios:
          1. If the answer can be determined by gathering the outputs from tasks to generate the final response.
          2. If the answer cannot be determined in the planning phase before executing the plans.

        ### Action Rules:
        - Each action described above contains input/output types and descriptions. You MUST strictly adhere to these.
        - Each action in the plan should strictly be one of the provided types. Follow Python conventions for each action.
        - Each action MUST have a unique ID, which is strictly increasing.
        - Inputs for actions can either be constants or outputs from preceding actions. Use the format `$id` to denote the ID of the previous action whose output will be the input.
        - Always call `join()` as the last action in the plan. Say `<END_OF_PLAN>` after calling `join()`.
        - Ensure the plan maximizes parallelizability.
        - Only use the provided action types. If a query cannot be addressed using these, invoke the `join()` action for the next steps.
        - Never introduce new actions other than the ones provided.
        """
    ),  # Initial system message
    MessagesPlaceholder(variable_name="messages"),  # Message history
    (
        "system",
        """
        Remember, ONLY respond with the task list in the correct format! For example:
        idx. tool(parameter_name=args)
        <END_OF_PLAN>
        
        you have to add the parameter name!
        """
    ),  # Final system message
])

joiner_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Process user interactions and determine appropriate responses. Follow these guidelines:

        ### Input Analysis:
        1. **Review what has been done:**
           - What information was stored or retrieved?
           - What actions were completed?
           - What results or errors occurred?

        2. **Evaluate the current state:**
           - Is the interaction complete based on what's been done?
           - Was the user's intent fulfilled?
           - Is more information or action needed?

        ### Response Decision:
        **Finish when:**
        - Required actions are complete.
        - The user's intent has been fulfilled.
        - No meaningful follow-up is needed.
        - The natural conversation flow suggests completion.

        **Replan when:**
        - Critical information is missing.
        - Actions failed or are incomplete.
        - The user's intent hasn't been fulfilled.
        - Follow-up is clearly needed.

        ### Output Format:
        **Thought:** <Brief analysis of what's been done and whether it fulfills the interaction needs>
        **Action:** <Choose one>
        1. **Finish(response):** Returns the final response and completes the interaction.
        2. **Replan(reason):** Continues with a new plan, stating specific needs.

        ### Guidelines:
        - Do not categorize interactions into fixed types.
        - Let the completed actions and results guide the response.
        - Consider the natural conversation flow.
        - Only replan if there's a clear need for more information or actions.
        """
    ),  # Initial system message
    MessagesPlaceholder(variable_name="messages"),  # This is where the message history gets inserted
    (
        "system",
        """
        Using the above previous actions, decide whether to replan or finish. If all the required information is present, you may finish. If you have made many attempts to find the information without success, admit so and respond with whatever information you have gathered so the user can work effectively with you.

        **Note:** Where appropriate, a search engine tool could be defaulted to after several attempts at using a more specific tool to accomplish a task but fail.
        """
    ),  # Final system message
])