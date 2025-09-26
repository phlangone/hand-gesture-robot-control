import time
import logging
from typing import Optional, Tuple

try:
    import rtde_receive
    import rtde_control
    import rtde_io
    import dashboard_client
    RTDE_AVAILABLE = True
except ImportError:
    RTDE_AVAILABLE = False
    print("RTDE library not available. Using simulation mode.")

class RobotController:
    def __init__(self, host: str = '192.168.0.160', port: int = 30004, frequency: int = 10):
        self.host = host
        self.port = port
        self.frequency = frequency
        self.rtde_io = None             # IO interface
        self.rtde_c = None              # Control interface
        self.rtde_r = None              # Receive interface
        self.dashboard_client = None    # Dashboard interface
        self.connected = False
        self.simulation_mode = not RTDE_AVAILABLE
        
        self.connect()

    def connect(self) -> bool:
        """Connect to the robot using RTDE"""
        if self.simulation_mode:
            print("SIMULATION MODE: Robot controller initialized in simulation")
            self.connected = True
            return True
            
        try:
            # Create RTDE interfaces
            self.rtde_io = rtde_io.RTDEIOInterface(self.host)
            self.rtde_r = rtde_receive.RTDEReceiveInterface(self.host, frequency=self.frequency)
            self.rtde_c = rtde_control.RTDEControlInterface(self.host, frequency=self.frequency)
            self.rtde_dash = dashboard_client.DashboardClient(hostname=self.host, verbose=True)

            # Test connection
            print(f"RTDE Connected to {self.host}")

            # Connect dashboard interface
            self.rtde_dash.connect()

            # Send start program command
            self.rtde_dash.loadURP("Futurecom/main.urp")
            self.rtde_dash.play()

            # Set initial digital outputs to False
            self._set_all_outputs_false()
            
            self.connected = True

            return True
            
        except Exception as e:
            print(f"RTDE Connection failed: {e}")
            self.connected = False
            self.simulation_mode = True
            return False

    def _set_all_outputs_false(self):
        """Set all digital outputs to False"""
        if self.connected and not self.simulation_mode:
            try:
                # Standard digital outputs (0-7)
                for i in range(8):
                    self.rtde_io.setStandardDigitalOut(i, False)
                # Configurable digital outputs (8-15)  
                for i in range(8, 16):
                    self.rtde_io.setConfigurableDigitalOut(i, False)
                # Tool digital outputs (0-1)
                for i in range(2):
                    self.rtde_io.setToolDigitalOut(i, False)
            except Exception as e:
                print(f"Error setting initial outputs: {e}")

    def pulse_execute(self, pulse_time: float = 0.50) -> bool:
        """Pulse digital output to execute program"""
        try:
            if self.connected and not self.simulation_mode:
                # Set DO6 to True
                self.rtde_io.setStandardDigitalOut(6, True)
                time.sleep(pulse_time)
                # Set DO6 to False
                self.rtde_io.setStandardDigitalOut(6, False)
                return True
            else:
                print(f"SIMULATION: Pulso DO[6] por {pulse_time}s")
                return True
                
        except Exception as e:
            print(f"Error pulsing DO6: {e}")
            return False

    def set_program_selection(self, is_prog2: bool) -> bool:
        """Set program selection output (DO5)"""
        try:
            if self.connected and not self.simulation_mode:
                self.rtde_io.setStandardDigitalOut(5, is_prog2)
                return True
            else:
                print(f"SIMULATION: Set DO5 to {is_prog2}")
                return True
                
        except Exception as e:
            print(f"Error setting DO5: {e}")
            return False

    def set_enabled(self, enabled: bool) -> bool:
        """Set enabled state output (DO4)"""
        try:
            if self.connected and not self.simulation_mode:
                self.rtde_io.setStandardDigitalOut(4, enabled)
                return True
            else:
                print(f"SIMULATION: Set DO4 to {enabled}")
                return True
                
        except Exception as e:
            print(f"Error setting DO4: {e}")
            return False

    def get_program_finished(self) -> bool:
        """Check if program has finished (DI7)"""
        try:
            if self.connected and not self.simulation_mode:
                return self.rtde_r.getDigitalOutState(7)
            else:
                # In simulation, return finished after a delay
                return True
                
        except Exception as e:
            print(f"Error reading DI7: {e}")
            return False

    def get_robot_status(self) -> Optional[dict]:
        """Get comprehensive robot status"""
        if not self.connected or self.simulation_mode:
            return {
                'simulation': True,
                'connected': False,
                'safety_status': 'SIMULATION',
                'robot_mode': 'SIMULATION',
                'program_running': False
            }
            
        try:
            return {
                'simulation': False,
                'connected': True,
                'safety_status': self.rtde_r.getSafetyStatusBits(),
                'robot_mode': self.rtde_r.getRobotMode(),
                'program_running': self.rtde_r.isProgramRunning(),
                'actual_q': self.rtde_r.getActualQ(),  # Joint positions
                'actual_tcp_pose': self.rtde_r.getActualTCPPose(),  # TCP pose
                'digital_inputs': self.rtde_r.getActualDigitalInputBits(),
                'digital_outputs': self.rtde_r.getActualDigitalOutputBits()
            }
        except Exception as e:
            print(f"Error getting robot status: {e}")
            return None

    def send_move_command(self, pose: list, velocity: float = 0.1, acceleration: float = 0.1) -> bool:
        """Send movement command to robot (optional functionality)"""
        if self.simulation_mode:
            print(f"SIMULATION: Move to {pose}")
            return True
            
        try:
            if self.connected:
                # Move to specified pose (x, y, z, rx, ry, rz)
                self.rtde_c.moveL(pose, velocity, acceleration)
                return True
        except Exception as e:
            print(f"Error sending move command: {e}")
            
        return False

    def stop_robot(self) -> bool:
        """Stop robot movement"""
        if self.connected and not self.simulation_mode:
            try:
                self.rtde_c.stopL(10.0)  # Deceleration of 10 m/s²
                return True
            except Exception as e:
                print(f"Error stopping robot: {e}")
        return False

    def cleanup(self):
        """Cleanup robot connection"""
        try:
            if self.connected and not self.simulation_mode:
                # Send stop program command
                self.rtde_dash.stop()

                # Set all outputs to False before disconnecting
                self._set_all_outputs_false()
                
                # Stop any movement
                self.stop_robot()
                
                # Disconnect
                if self.rtde_c:
                    self.rtde_c.disconnect()
                if self.rtde_r:
                    self.rtde_r.disconnect()
                if self.rtde_io:
                    self.rtde_io.disconnect()
                if self.rtde_dash:
                    self.rtde_dash.disconnect()
                    
                print("RTDE connection closed properly")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.connected = False

    def is_connected(self) -> bool:
        """Check if robot is connected"""
        return self.connected and not self.simulation_mode

    def get_connection_info(self) -> dict:
        """Get connection information"""
        return {
            'host': self.host,
            'port': self.port,
            'connected': self.connected,
            'simulation_mode': self.simulation_mode,
            'rtde_available': RTDE_AVAILABLE
        }