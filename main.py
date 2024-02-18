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
        default_index = (
            agent_names.index(previously_selected_agent) + 1
        )  # add 1 for the empty string at index 0
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
            value=5
            if "conversation_results" not in prompt
            else int(prompt["conversation_results"]),
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
            value=0
            if "inject_memories_from_collection_number" not in prompt
            else int(prompt["inject_memories_from_collection_number"]),
            key=f"inject_memories_from_collection_number_{step_number}",
        )
        context_results = ui.number_input(
            "How many long term memories to inject (Default is 5)",
            min_value=1,
            value=5
            if "context_results" not in prompt
            else int(prompt["context_results"]),
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
                value=3
                if "websearch_depth" not in prompt
                else int(prompt["websearch_depth"]),
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
    prompt_category = ui.selectbox(
        "Select Prompt Category",
        prompt_categories,
        index=prompt_categories.index("Default"),
        key=f"step_{step_number}_prompt_category",
    )
    available_prompts = ApiClient.get_prompts(prompt_category=prompt_category)
    try:
        custom_input_index = available_prompts.index("Custom Input")
    except:
        custom_input_index = 0
    prompt_name = ui.selectbox(
        "Select Custom Prompt",
        available_prompts,
        index=available_prompts.index(prompt.get("prompt_name", ""))
        if "prompt_name" in prompt
        else custom_input_index,
        key=f"step_{step_number}_prompt_name",
    )
    prompt_content = ApiClient.get_prompt(
        prompt_name=prompt_name, prompt_category=prompt_category
    )
    ui.markdown(
        f"""
**Prompt Content**
        """
    )
    prompt_args_values = prompt_options(prompt=prompt, step_number=step_number)
    if prompt_name:
        prompt_args = ApiClient.get_prompt_args(
            prompt_name=prompt_name, prompt_category=prompt_category
        )
        args = build_args(args=prompt_args, prompt=prompt, step_number=step_number)
        new_prompt = {
            "prompt_name": prompt_name,
            "prompt_category": prompt_category,
            **args,
            **prompt_args_values,
        }
        return new_prompt

def build_args(args: dict, prompt: dict, step_number: int):
    pass  # This function needs to be implemented based on your specific requirements.

def predefined_memory_collections():
    pass  # Implement this function if necessary.


with ui.header().classes(replace='row items-center bg-gray-900 text-white') as header:
    ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
    with ui.tabs().classes('bg-gray-900') as tabs:
        ui.tab('Agents')
        ui.tab('Instruct')
        ui.tab('chains')
        ui.tab('prompts')

with ui.footer(value=False).classes('bg-gray-900 text-white') as footer:
    ui.label('Footer')

with ui.left_drawer().classes('bg-blue-900 text-white') as left_drawer:
    ui.label('AGIXT')
    ui.button(on_click=lambda: left_drawer.toggle(), icon='home').props('flat color=blue')

with ui.tab_panels(tabs, value='A').classes('w-full text-black'):
    with ui.tab_panel('Agents'):
        ui.label('Select an agent:')
        select1 = agent_selection()
    with ui.tab_panel('Instruct'):
        ui.label('Content of B')
    with ui.tab_panel('chains'):
        ui.label('Content of C')
    with ui.tab_panel('prompts'):
        ui.label('Content of D')

ui.run()
