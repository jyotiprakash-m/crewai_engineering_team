import gradio as gr
import time
import threading
import random
from Racing import Racing

# Initialize the Racing class
racing_game = Racing()
race_thread = None

def add_car(car_id, car_type):
    try:
        racing_game.add_car(car_id, car_type)
        return f"Car {car_id} ({car_type}) added successfully!"
    except ValueError as e:
        return str(e)

def setup_track(track_name, length, num_obstacles):
    try:
        # Generate random obstacles
        obstacles = []
        for i in range(int(num_obstacles)):
            pos = random.randint(1, int(length) - 1)
            severity = random.choice(["mild", "moderate", "severe"])
            obstacles.append({"position": pos, "type": "bump", "severity": severity})
        
        racing_game.setup_track(track_name, int(length), obstacles)
        return f"Track '{track_name}' setup with {num_obstacles} obstacles."
    except ValueError as e:
        return str(e)

def start_race():
    global race_thread
    
    try:
        racing_game.start_race()
        
        # Create a thread to simulate car movement
        race_thread = threading.Thread(target=race_simulation)
        race_thread.daemon = True
        race_thread.start()
        
        return "Race started! Cars are moving..."
    except ValueError as e:
        return str(e)

def race_simulation():
    while racing_game.race_status == 'In Progress':
        for car in racing_game.cars:
            if car.finish_time is None:
                # Random speed between 1 and 5 meters per step
                speed = random.uniform(1, 5)
                try:
                    racing_game.update_car_position(car.car_id, speed)
                except ValueError:
                    # Race might have been completed in another thread
                    break
        time.sleep(0.1)  # Small delay between updates

def get_race_status():
    status = f"Race Status: {racing_game.race_status}\n\n"
    
    if racing_game.track:
        status += f"{racing_game.track}\n\n"
    
    status += "Cars:\n"
    for car in racing_game.cars:
        status += f"{car}\n"
        if car.finish_time:
            status += f"  Finish time: {car.finish_time:.2f} seconds\n"
    
    if racing_game.race_status == 'Finished':
        status += "\nRace Results:\n"
        try:
            results = racing_game.get_race_results()
            for pos, (car_id, time) in enumerate(results.items(), 1):
                status += f"{pos}. Car {car_id}: {time:.2f} seconds\n"
        except ValueError as e:
            status += f"Cannot display results: {str(e)}"
    
    return status

def reset_race():
    global racing_game, race_thread
    
    # Stop any ongoing race
    if race_thread and race_thread.is_alive():
        racing_game.race_status = 'Finished'  # Force the simulation to end
        race_thread.join(1.0)  # Wait for thread to terminate
    
    # Create new racing instance
    racing_game = Racing()
    return "Game reset! Ready for new setup."

# Create Gradio interface
with gr.Blocks(title="Car Racing Simulator") as app:
    gr.Markdown("# 🏎️ Car Racing Game Simulator")
    
    with gr.Tab("Setup"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Add Cars")
                car_id = gr.Textbox(label="Car ID", placeholder="car1")
                car_type = gr.Dropdown(["sports", "suv", "truck", "formula1"], label="Car Type")
                add_car_btn = gr.Button("Add Car")
            
            with gr.Column():
                gr.Markdown("### Setup Track")
                track_name = gr.Textbox(label="Track Name", placeholder="Mountain Pass")
                track_length = gr.Number(label="Track Length (meters)", value=100)
                num_obstacles = gr.Slider(minimum=0, maximum=20, value=5, step=1, label="Number of Obstacles")
                setup_track_btn = gr.Button("Setup Track")
        
        setup_output = gr.Textbox(label="Setup Output")
    
    with gr.Tab("Race"):
        start_race_btn = gr.Button("Start Race", variant="primary")
        race_status = gr.Textbox(label="Race Status", lines=15)
        refresh_btn = gr.Button("Refresh Status")
        reset_btn = gr.Button("Reset Game", variant="secondary")
    
    # Connect components
    add_car_btn.click(add_car, inputs=[car_id, car_type], outputs=setup_output)
    setup_track_btn.click(setup_track, inputs=[track_name, track_length, num_obstacles], outputs=setup_output)
    start_race_btn.click(start_race, outputs=race_status)
    refresh_btn.click(get_race_status, outputs=race_status)
    reset_btn.click(reset_race, outputs=race_status)
    
# Launch the app
if __name__ == "__main__":
    app.launch()