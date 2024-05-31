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

with ui.header().classes('bg-gradient-to-r from-blue-800 to-indigo-800 text-white p-8 shadow-lg flex justify-between items-center') as header:
    ui.label('AGIXT').classes('text-4xl font-bold tracking-wider')
    ui.input(placeholder='Search...', on_change=lambda e: search_function(e.value)).classes('bg-white text-black rounded-md p-2')
    with ui.row().classes('flex items-center space-x-4'):
        ui.button(on_click=lambda: left_drawer.toggle()).props('flat color=white icon=menu').classes('focus:outline-none hover:bg-blue-700 transition duration-200 ease-in-out')
        ui.image('user-avatar.png').classes('h-10 w-10 rounded-full').on('click', lambda: user_menu.toggle())
    with ui.menu().classes('bg-white text-black rounded-md shadow-lg') as user_menu:
        ui.menu_item('Profile').on('click', lambda: open_profile())
        ui.menu_item('Settings').on('click', lambda: open_settings())
        ui.menu_item('Logout').on('click', lambda: logout())

with ui.tabs().classes('bg-white shadow-xl rounded-lg overflow-hidden') as tabs:
    ui.tab('Interact', icon='chat').classes('flex items-center text-blue-800 hover:text-blue-900 font-semibold px-8 py-4 border-b-4 border-transparent hover:border-blue-800 transition duration-300 ease-in-out')
    ui.tab('Agents', icon='people').classes('flex items-center text-blue-800 hover:text-blue-900 font-semibold px-8 py-4 border-b-4 border-transparent hover:border-blue-800 transition duration-300 ease-in-out')
    ui.tab('Chains', icon='link').classes('flex items-center text-blue-800 hover:text-blue-900 font-semibold px-8 py-4 border-b-4 border-transparent hover:border-blue-800 transition duration-300 ease-in-out')
    ui.tab('Prompts', icon='description').classes('flex items-center text-blue-800 hover:text-blue-900 font-semibold px-8 py-4 border-b-4 border-transparent hover:border-blue-800 transition duration-300 ease-in-out')

with ui.footer().classes('bg-gray-900 text-white p-8 flex justify-between items-center'):
    ui.label('© 2024 AGIXT. All rights reserved.').classes('text-lg')
    with ui.row().classes('flex space-x-4'):
        ui.link().classes('text-white hover:text-blue-300').props('icon=facebook').on('click', lambda: open_social('facebook'))
        ui.link().classes('text-white hover:text-blue-300').props('icon=twitter').on('click', lambda: open_social('twitter'))
        ui.link().classes('text-white hover:text-blue-300').props('icon=linkedin').on('click', lambda: open_social('linkedin'))

with ui.left_drawer().classes('bg-gray-900 text-white p-12 w-80 transform transition-transform duration-300 ease-in-out translate-x-0') as left_drawer:
    ui.label('Navigation').classes('text-4xl font-bold mb-12')
    ui.link('Home').on('click', left_drawer.toggle).classes('block py-6 text-2xl text-white hover:text-blue-300 transition duration-300 ease-in-out')
    ui.link('Settings').on('click', left_drawer.toggle).classes('block py-6 text-2xl text-white hover:text-blue-300 transition duration-300 ease-in-out')
    ui.label('Powered by').classes('text-lg uppercase tracking-wide text-gray-400 mt-12 mb-4')
    ui.image('agixt-logo.png').classes('h-12')

def update_interaction_mode():
    chat_container.visible = (mode_select.value == 'Chat')
    chain_container.visible = (mode_select.value == 'Chain')

with ui.tab_panels(tabs, value='Interact').classes('p-12'):
    with ui.tab_panel('Interact'):
        ui.label('Select an agent:').classes('text-3xl font-bold mb-8')
        select1 = agent_selection().classes('mb-8 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-800 transition duration-300 ease-in-out')
        
        ui.label('Select an interaction mode:').classes('text-3xl font-bold mb-8')
        mode_select = ui.select(['Chat', 'Chain'], on_change=lambda e: update_interaction_mode()).classes('mb-8 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-800 transition duration-300 ease-in-out')

        chat_container = ui.column().classes('mt-8 p-8 bg-white rounded-lg shadow-lg transition duration-500 ease-in-out transform hover:-translate-y-2 hover:scale-105').props('visible=False')
        with chat_container:
            ui.label('Chat with the agent:').classes('text-3xl font-bold mb-8')
            input1 = ui.input(label='Message', placeholder='Type your message here...', on_change=lambda e: None).classes('mb-6 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-800 transition duration-300 ease-in-out')
            ui.button('Send', on_click=lambda: chat(select1.value, input1.value, "default")).classes('bg-gradient-to-r from-blue-800 to-indigo-800 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3 px-8 rounded-md transition duration-300 ease-in-out')

        chain_container = ui.column().classes('mt-8 p-8 bg-white rounded-lg shadow-lg transition duration-500 ease-in-out transform hover:-translate-y-2 hover:scale-105').props('visible=False')
        with chain_container:
            ui.label('Select a chain:').classes('text-3xl font-bold mb-8')
            chains = ApiClient.get_chains()
            select2 = ui.select(chains).classes('mb-6 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-800 transition duration-300 ease-in-out')
            input2 = ui.input(label='Chain Input', placeholder='Type your input here...', on_change=lambda e: None).classes('mb-6 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-800 transition duration-300 ease-in-out')
            ui.button('Run Chain', on_click=lambda: run_chain(select1.value, select2.value, input2.value)).classes('bg-gradient-to-r from-blue-800 to-indigo-800 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3 px-8 rounded-md transition duration-300 ease-in-out')

    with ui.tab_panel('Agents'):
        ui.label('Manage Your Agents').classes('text-3xl font-bold mb-8')
        # Add more detailed content and interactive elements for Agents tab

    with ui.tab_panel('Chains'):
        ui.label('Manage Your Chains').classes('text-3xl font-bold mb-8') 

    with ui.tab_panel('Prompts'):
        ui.label('Manage Your Prompts').classes('text-3xl font-bold mb-8')
        # Add more detailed content and interactive elements for Prompts tab

def search_function(value):
    # Implement this function based on your specific requirements
    pass

def open_profile():
    # Implement this function based on your specific requirements
    pass

def open_settings():
    # Implement this function based on your specific requirements
    pass

def logout():
    # Implement this function based on your specific requirements
    pass

def open_social(platform):
    # Implement this function based on your specific requirements
    pass








ui.run()