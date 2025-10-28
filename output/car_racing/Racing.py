from typing import List, Dict, Optional
import time

class Car:
    def __init__(self, car_id: str, car_type: str):
        self.car_id = car_id
        self.car_type = car_type
        self.position = 0.0
        self.speed = 0.0
        self.finish_time = None
    
    def __str__(self):
        return f"Car {self.car_id} ({self.car_type}) - Position: {self.position}m"

class Track:
    def __init__(self, track_name: str, length: int, obstacles: List[dict]):
        self.track_name = track_name
        self.length = length
        self.obstacles = obstacles
    
    def __str__(self):
        return f"Track: {self.track_name}, Length: {self.length}m, Obstacles: {len(self.obstacles)}"

class Racing:
    def __init__(self):
        """
        Initializes a Racing game instance with default settings.
        """
        self.cars = []
        self.track = None
        self.race_status = 'Not Started'
        self.results = {}
        self.start_time = None
    
    def add_car(self, car_id: str, car_type: str):
        """
        Adds a car to the race.
        
        Parameters:
        - car_id (str): Unique identifier for the car.
        - car_type (str): Type of the car (e.g., 'sports', 'suv').
        """
        # Check if a car with the given ID already exists
        if any(car.car_id == car_id for car in self.cars):
            raise ValueError(f"A car with ID {car_id} already exists in the race")
        
        # Add the new car
        self.cars.append(Car(car_id, car_type))
        
    def setup_track(self, track_name: str, length: int, obstacles: List[dict]):
        """
        Configures the race track.
        
        Parameters:
        - track_name (str): Name of the track.
        - length (int): Length of the track in meters.
        - obstacles (List[dict]): List of obstacles, each represented by a dictionary with details.
        """
        # Validate track parameters
        if length <= 0:
            raise ValueError("Track length must be positive")
        
        # Create the track
        self.track = Track(track_name, length, obstacles)
        
    def start_race(self):
        """
        Starts the race. Sets `race_status` to 'In Progress'.
        """
        # Check if the race can be started
        if not self.track:
            raise ValueError("Track must be set up before starting the race")
        
        if not self.cars:
            raise ValueError("At least one car must be added before starting the race")
        
        if self.race_status != 'Not Started':
            raise ValueError(f"Cannot start race with status '{self.race_status}'")
        
        # Start the race
        self.race_status = 'In Progress'
        self.start_time = time.time()
        
        # Reset car positions
        for car in self.cars:
            car.position = 0.0
            car.finish_time = None
        
        # Clear previous results
        self.results = {}
        
    def update_car_position(self, car_id: str, distance: float):
        """
        Updates the position of a car during the race.
        
        Parameters:
        - car_id (str): Unique identifier for the car being updated.
        - distance (float): Distance covered by the car since the last update.
        """
        # Check if the race is in progress
        if self.race_status != 'In Progress':
            raise ValueError(f"Cannot update positions when race is not in progress (current status: {self.race_status})")
        
        # Find the car
        car = next((c for c in self.cars if c.car_id == car_id), None)
        if not car:
            raise ValueError(f"No car with ID {car_id} found in the race")
        
        # Update position
        car.position += distance
        
        # Check if car has finished the race
        if car.position >= self.track.length and car.finish_time is None:
            car.finish_time = time.time() - self.start_time
            self.results[car_id] = car.finish_time
            
            # Check if all cars have finished
            if all(c.finish_time is not None for c in self.cars):
                self.complete_race()
                
    def complete_race(self):
        """
        Completes the race, finalizes the results, and sets `race_status` to 'Finished'.
        """
        if self.race_status != 'In Progress':
            raise ValueError(f"Cannot complete race with status '{self.race_status}'")
        
        # Set finish time for any cars that haven't finished yet
        current_time = time.time() - self.start_time
        for car in self.cars:
            if car.finish_time is None:
                car.finish_time = current_time
                self.results[car.car_id] = car.finish_time
        
        # Mark race as finished
        self.race_status = 'Finished'
        
    def get_race_results(self) -> Dict[str, float]:
        """
        Returns the results of the race as a dictionary with car ids and finish times.
        """
        if self.race_status != 'Finished':
            raise ValueError(f"Cannot get results when race status is '{self.race_status}'")
        
        # Sort results by finish time
        sorted_results = dict(sorted(self.results.items(), key=lambda item: item[1]))
        return sorted_results