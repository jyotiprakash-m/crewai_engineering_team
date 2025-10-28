import unittest
from unittest.mock import patch
import time
from Racing import Racing, Car, Track

class TestRacing(unittest.TestCase):
    
    def setUp(self):
        """Set up a fresh Racing instance for each test."""
        self.racing = Racing()
    
    def test_initialization(self):
        """Test that a Racing instance initializes correctly."""
        self.assertEqual(self.racing.cars, [])
        self.assertIsNone(self.racing.track)
        self.assertEqual(self.racing.race_status, 'Not Started')
        self.assertEqual(self.racing.results, {})
        self.assertIsNone(self.racing.start_time)
    
    def test_add_car(self):
        """Test adding a car to the race."""
        self.racing.add_car("car1", "sports")
        
        self.assertEqual(len(self.racing.cars), 1)
        self.assertEqual(self.racing.cars[0].car_id, "car1")
        self.assertEqual(self.racing.cars[0].car_type, "sports")
    
    def test_add_car_duplicate_id(self):
        """Test adding a car with a duplicate ID raises an error."""
        self.racing.add_car("car1", "sports")
        
        with self.assertRaises(ValueError):
            self.racing.add_car("car1", "suv")
    
    def test_setup_track(self):
        """Test setting up a track."""
        self.racing.setup_track("Test Track", 1000, [{"type": "oil", "position": 500}])
        
        self.assertEqual(self.racing.track.track_name, "Test Track")
        self.assertEqual(self.racing.track.length, 1000)
        self.assertEqual(len(self.racing.track.obstacles), 1)
        self.assertEqual(self.racing.track.obstacles[0]["type"], "oil")
    
    def test_setup_track_invalid_length(self):
        """Test that setting up a track with invalid length raises an error."""
        with self.assertRaises(ValueError):
            self.racing.setup_track("Invalid Track", 0, [])
        
        with self.assertRaises(ValueError):
            self.racing.setup_track("Invalid Track", -100, [])
    
    def test_start_race(self):
        """Test starting a race."""
        self.racing.setup_track("Test Track", 1000, [])
        self.racing.add_car("car1", "sports")
        
        with patch('time.time', return_value=100.0):
            self.racing.start_race()
            
            self.assertEqual(self.racing.race_status, "In Progress")
            self.assertEqual(self.racing.start_time, 100.0)
            self.assertEqual(self.racing.cars[0].position, 0.0)
            self.assertIsNone(self.racing.cars[0].finish_time)
            self.assertEqual(self.racing.results, {})
    
    def test_start_race_no_track(self):
        """Test that starting a race without a track raises an error."""
        self.racing.add_car("car1", "sports")
        
        with self.assertRaises(ValueError):
            self.racing.start_race()
    
    def test_start_race_no_cars(self):
        """Test that starting a race without cars raises an error."""
        self.racing.setup_track("Test Track", 1000, [])
        
        with self.assertRaises(ValueError):
            self.racing.start_race()
    
    def test_start_race_already_started(self):
        """Test that starting an already started race raises an error."""
        self.racing.setup_track("Test Track", 1000, [])
        self.racing.add_car("car1", "sports")
        self.racing.start_race()
        
        with self.assertRaises(ValueError):
            self.racing.start_race()
    
    def test_update_car_position(self):
        """Test updating a car's position."""
        self.racing.setup_track("Test Track", 1000, [])
        self.racing.add_car("car1", "sports")
        
        with patch('time.time', return_value=100.0):
            self.racing.start_race()
            
        with patch('time.time', return_value=105.0):  # 5 seconds elapsed
            self.racing.update_car_position("car1", 200.0)
            
            self.assertEqual(self.racing.cars[0].position, 200.0)
            self.assertIsNone(self.racing.cars[0].finish_time)  # Not finished yet
            self.assertEqual(self.racing.results, {})
    
    def test_update_car_position_finish(self):
        """Test updating a car's position causing it to finish."""
        self.racing.setup_track("Test Track", 1000, [])
        self.racing.add_car("car1", "sports")
        
        with patch('time.time', return_value=100.0):
            self.racing.start_race()
            
        with patch('time.time', return_value=110.0):  # 10 seconds elapsed
            self.racing.update_car_position("car1", 1000.0)  # Move to finish line
            
            self.assertEqual(self.racing.cars[0].position, 1000.0)
            self.assertEqual(self.racing.cars[0].finish_time, 10.0)  # 110 - 100
            self.assertEqual(self.racing.results, {"car1": 10.0})
            self.assertEqual(self.racing.race_status, "Finished")  # Race should be completed since all cars finished
    
    def test_update_car_position_race_not_started(self):
        """Test that updating a car's position when race hasn't started raises an error."""
        self.racing.add_car("car1", "sports")
        
        with self.assertRaises(ValueError):
            self.racing.update_car_position("car1", 100.0)
    
    def test_update_car_position_invalid_car(self):
        """Test that updating a non-existent car's position raises an error."""
        self.racing.setup_track("Test Track", 1000, [])
        self.racing.add_car("car1", "sports")
        self.racing.start_race()
        
        with self.assertRaises(ValueError):
            self.racing.update_car_position("nonexistent_car", 100.0)
    
    def test_complete_race(self):
        """Test completing a race."""
        self.racing.setup_track("Test Track", 1000, [])
        self.racing.add_car("car1", "sports")
        self.racing.add_car("car2", "suv")
        
        with patch('time.time', return_value=100.0):
            self.racing.start_race()
        
        with patch('time.time', return_value=115.0):  # 15 seconds elapsed
            # Move car1 to 800m (not finished)
            self.racing.update_car_position("car1", 800.0)
            
            # Complete the race
            self.racing.complete_race()
            
            self.assertEqual(self.racing.race_status, "Finished")
            # All cars should have finish times
            self.assertEqual(self.racing.cars[0].finish_time, 15.0)  # 115 - 100
            self.assertEqual(self.racing.cars[1].finish_time, 15.0)  # 115 - 100
            # Results should contain all cars
            self.assertEqual(self.racing.results, {"car1": 15.0, "car2": 15.0})
    
    def test_complete_race_not_started(self):
        """Test that completing a race that hasn't started raises an error."""
        with self.assertRaises(ValueError):
            self.racing.complete_race()
    
    def test_get_race_results(self):
        """Test getting race results."""
        self.racing.setup_track("Test Track", 1000, [])
        self.racing.add_car("car1", "sports")
        self.racing.add_car("car2", "suv")
        
        with patch('time.time') as mock_time:
            # Start race at t=100
            mock_time.return_value = 100.0
            self.racing.start_race()
            
            # car1 finishes at t=110 (10s elapsed)
            mock_time.return_value = 110.0
            self.racing.update_car_position("car1", 1000.0)
            
            # car2 finishes at t=115 (15s elapsed)
            mock_time.return_value = 115.0
            self.racing.update_car_position("car2", 1000.0)
            
            # Race should be automatically completed since all cars finished
            self.assertEqual(self.racing.race_status, "Finished")
            
            # Get results
            results = self.racing.get_race_results()
            
            # Results should be sorted by finish time
            expected_results = {"car1": 10.0, "car2": 15.0}
            self.assertEqual(results, expected_results)
    
    def test_get_race_results_not_finished(self):
        """Test that getting results when race isn't finished raises an error."""
        self.racing.setup_track("Test Track", 1000, [])
        self.racing.add_car("car1", "sports")
        self.racing.start_race()
        
        with self.assertRaises(ValueError):
            self.racing.get_race_results()


if __name__ == "__main__":
    unittest.main()