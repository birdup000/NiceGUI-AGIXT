import os
import logging
from nicegui import ui
from agixtsdk import AGiXTSDK

base_uri = "http://localhost:7437"
ApiClient = AGiXTSDK(base_uri=base_uri)

def agent_selection(key: str = "select_learning_agent", heading: str = "", current_agent: str = None):
    # Load the previously selected agent name
    try:
        with open(os.path.join("session.txt"), "r") as f:
            previously_selected_agent = f.read().strip()
    except FileNotFoundError:
        previously_selected_agent = None

    # Get the list of agent names
    agent_names = [agent["name"] for agent in ApiClient.get_agents()]

    # If the previously selected agent is in the list, use it as the default
    if previously_selected_agent in agent_names:
        default_index = agent_names.index(previously_selected_agent) + 1  # add 1 for the empty string at index 0
    else:
        default_index = 0

    # Create the selectbox
    selected_agent = ui.select([None] + agent_names, value=previously_selected_agent)
    ui.label(heading)

    if key == "select_learning_agent":
        # If the selected agent has changed, save the new selection
        if selected_agent.value != previously_selected_agent:
            with open(os.path.join("session.txt"), "w") as f:
                f.write(selected_agent.value)
            try:
                ui.rerun()
            except Exception as e:
                logging.info(e)
    return selected_agent

def prompt_options(prompt: dict = {}, step_number: int = 0):
    if prompt == {}:
        ops = False
    else:
        for opt in [
            "shots",
            "context_results",
            "browse_links",
            "websearch",
            "websearch_depth",
            "disable_memory",
            "inject_memories_from_collection_number",
            "conversation_results",
        ]:
            if opt not in prompt:
                ops = False
                break
            else:
                ops = True
    advanced_options = ui.checkbox(
        "Show Advanced Options", value=ops, key=f"advanced_options_{step_number}"
    )
    if advanced_options:
        conversation_results = ui.number_input(
            "How many conversation results to inject (Default is 5)",
            min_value=1,
            value=5 if "conversation_results" not in prompt else int(prompt["conversation_results"]),
            key=f"conversation_results_{step_number}",
        )
        shots = ui.number_input(
            "Shots (How many times to ask the agent)",
            min_value=1,
            value=1 if "shots" not in prompt else int(prompt["shots"]),
            key=f"shots_{step_number}",
        )
        predefined_memory_collections()
        inject_memories_from_collection_number = ui.number_input(
            "Inject memories from collection number (Default is 0)",
            min_value=0,
            value=0 if "inject_memories_from_collection_number" not in prompt else int(prompt["inject_memories_from_collection_number"]),
            key=f"inject_memories_from_collection_number_{step_number}",
        )
        context_results = ui.number_input(
            "How many long term memories to inject (Default is 5)",
            min_value=1,
            value=5 if "context_results" not in prompt else int(prompt["context_results"]),
            key=f"context_results_{step_number}",
        )
        browse_links = ui.checkbox(
            "Enable Browsing Links in the user input",
            value=False if "browse_links" not in prompt else prompt["browse_links"],
            key=f"browse_links_{step_number}",
        )
        websearch = ui.checkbox(
            "Enable websearch",
            value=False if "websearch" not in prompt else prompt["websearch"],
            key=f"websearch_{step_number}",
        )
        if websearch:
            websearch_depth = ui.number_input(
                "Websearch depth",
                min_value=1,
                value=3 if "websearch_depth" not in prompt else int(prompt["websearch_depth"]),
                key=f"websearch_depth_{step_number}",
            )
        else:
            websearch_depth = 0
        if "disable_memory" not in prompt:
            enable_memory = ui.checkbox(
                "Enable Memory Training (Any messages sent to and from the agent will be added to memory if enabled.)",
                value=False,
                key=f"enable_memory_{step_number}",
            )
        else:
            enable_memory = ui.checkbox(
                "Enable Memory Training (Any messages sent to and from the agent will be added to memory if enabled.)",
                value=True if prompt["disable_memory"] == False else False,
                key=f"enable_memory_{step_number}",
            )
    else:
        shots = 1
        context_results = 5
        browse_links = False
        websearch = False
        websearch_depth = 0
        enable_memory = False
        inject_memories_from_collection_number = 0
        conversation_results = 5
    return {
        "shots": shots,
        "context_results": context_results,
        "browse_links": browse_links,
        "websearch": websearch,
        "websearch_depth": websearch_depth,
        "disable_memory": (True if enable_memory == False else False),
        "inject_memories_from_collection_number": inject_memories_from_collection_number,
        "conversation_results": conversation_results,
    }

def prompt_selection(prompt: dict = {}, step_number: int = 0):
    prompt_categories = ApiClient.get_prompt_categories()
    prompt_category = ui.select(
        prompt_categories,
        label="Select Prompt Category",
        value=prompt.get("prompt_category", "Default"),
        key=f"step_{step_number}_prompt_category",
    )
    available_prompts = ApiClient.get_prompts(prompt_category=prompt_category.value)
    try:
        custom_input_index = available_prompts.index("Custom Input")
    except ValueError:
        custom_input_index = 0
    prompt_name = ui.select(
        available_prompts,
        label="Select Custom Prompt",
        value=prompt.get("prompt_name", ""),
        key=f"step_{step_number}_prompt_name",
    )
    prompt_content = ApiClient.get_prompt(
        prompt_name=prompt_name.value, prompt_category=prompt_category.value
    )
    ui.markdown("**Prompt Content**")
    ui.markdown(prompt_content)
    prompt_args_values = prompt_options(prompt=prompt, step_number=step_number)
    if prompt_name.value:
        prompt_args = ApiClient.get_prompt_args(
            prompt_name=prompt_name.value, prompt_category=prompt_category.value
        )
        args = build_args(args=prompt_args, prompt=prompt, step_number=step_number)
        new_prompt = {
            "prompt_name": prompt_name.value,
            "prompt_category": prompt_category.value,
            **args,
            **prompt_args_values,
        }
        return new_prompt

def build_args(args: dict, prompt: dict, step_number: int):
    # Implement this function based on your specific requirements
    pass

def predefined_memory_collections():
    # Implement this function if necessary
    pass

def chat(agent_name: str, user_input: str, conversation: str):
    try:
        response = ApiClient.chat(
            agent_name=agent_name,
            user_input=user_input,
            conversation=conversation
        )
        return response
    except Exception as e:
        ui.notify(f"Error: {str(e)}", color="negative")
        return None

def run_chain(agent_name: str, chain_name: str, user_input: str):
    try:
        response = ApiClient.run_chain(
            chain_name=chain_name,
            user_input=user_input,
            agent_name=agent_name,
            all_responses=False,
            from_step=1,
            chain_args={}
        )
        return response
    except Exception as e:
        ui.notify(f"Error: {str(e)}", color="negative")
        return None

with ui.header().classes(replace='row items-center justify-between bg-blue-900 text-white p-4') as header:
    ui.label('AGIXT').classes('text-2xl font-bold')
    ui.button(on_click=lambda: left_drawer.toggle()).props('flat color=white')

with ui.tabs().classes('bg-gray-200 text-black') as tabs:
    ui.tab('Interact')
    ui.tab('Agents')
    ui.tab('Chains')
    ui.tab('Prompts')

with ui.footer().classes('bg-gray-900 text-white p-4') as footer:
    ui.label('Footer')

with ui.left_drawer().classes('bg-blue-800 text-white p-4') as left_drawer:
    ui.label('Navigation').classes('text-xl font-bold mb-4')
    ui.link('Home').on('click', left_drawer.toggle).classes('block py-2 text-white hover:text-blue-200')

def update_interaction_mode():
    chat_container.visible = (mode_select.value == 'Chat')
    chain_container.visible = (mode_select.value == 'Chain')

with ui.tab_panels(tabs, value='Interact').classes('w-full h-full'):
    with ui.tab_panel('Interact'):
        ui.label('Select an agent:')
        select1 = agent_selection()

        mode_select = ui.select(['Chat', 'Chain'], label='Interaction Mode', on_change=lambda e: update_interaction_mode())
        
        # Containers are hidden by default
        chat_container = ui.column().classes('w-full h-full').props('visible=False')
        with chat_container:
            input1 = ui.input(label='Message', placeholder='Type your message here...', on_change=lambda e: None)
            ui.button('Send', on_click=lambda: chat(select1.value, input1.value, "default"))

        chain_container = ui.column().classes('w-full h-full').props('visible=False')
        with chain_container:
            ui.label('Select a chain:')
            chains = ApiClient.get_chains()
            select2 = ui.select(chains)
            input2 = ui.input(label='Chain Input', placeholder='Type your input here...', on_change=lambda e: None)
            ui.button('Run Chain', on_click=lambda: run_chain(select1.value, select2.value, input2.value))

    with ui.tab_panel('Agents'):
        ui.label('Content of Agents')
    with ui.tab_panel('Chains'):
        ui.label('Content of Chains')
    with ui.tab_panel('Prompts'):
        ui.label('Content of Prompts')

ui.run()
