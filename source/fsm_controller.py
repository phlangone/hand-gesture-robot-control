import time
from enum import Enum

class FSMState(Enum):
    DISABLED = 1
    ENABLED = 2
    AWAIT_CONFIRM = 3
    RUNNING = 4

class FSMController:
    def __init__(self):
        self.state = FSMState.DISABLED
        
        # Timing parameters
        self.START_HOLD_TIME = 3.0
        self.STOP_HOLD_TIME = 3.0
        self.CONFIRM_TIMEOUT = 5.0
        self.EXEC_PULSE_TIME = 0.20
        self.MAX_RUNNING_TIME = 15.0
        self.GESTURE_CONFIRM_COUNT = 15
        
        # State variables
        self.gesture_counter = 0
        self.confirm_counter = 0
        self.start_hold_since = None
        self.stop_hold_since = None
        self.awaiting_confirm_since = None
        self.running_since = None
        self.pending_selection = None
        
        self.log_messages = []

    def update(self, static_gesture, dynamic_gesture, robot_controller):
        """Update FSM state based on current gestures"""
        now = time.time()
        new_log_messages = []
        
        # Handle stop gesture (Close hand)
        if static_gesture == 'Close':
            if self.stop_hold_since is None:
                self.stop_hold_since = now
            if now - self.stop_hold_since >= self.STOP_HOLD_TIME:
                if self.state != FSMState.DISABLED:
                    new_log_messages.append(f"STOP >= {self.STOP_HOLD_TIME:.1f}s -> DESABILITADO")
                    robot_controller.set_enabled(False)
                    self._transition_to(FSMState.DISABLED, now)
                self.stop_hold_since = None
        else:
            self.stop_hold_since = None

        # State machine logic 
        if self.state == FSMState.DISABLED:
            self._handle_disabled_state(static_gesture, now, robot_controller, new_log_messages)
            
        elif self.state == FSMState.ENABLED:
            self._handle_enabled_state(dynamic_gesture, now, new_log_messages)
            
        elif self.state == FSMState.AWAIT_CONFIRM:
            self._handle_await_confirm_state(dynamic_gesture, now, robot_controller, new_log_messages)
            
        elif self.state == FSMState.RUNNING:
            self._handle_running_state(now, robot_controller, new_log_messages)
        
        self.log_messages.extend(new_log_messages)

    def _handle_disabled_state(self, static_gesture, now, robot_controller, log_messages):
        """Handle DISABLED state transitions"""
        if static_gesture == 'Open':
            if self.start_hold_since is None:
                self.start_hold_since = now
            elif now - self.start_hold_since >= self.START_HOLD_TIME:
                log_messages.append(f"START >= {self.START_HOLD_TIME:.1f}s -> HABILITADO")
                robot_controller.set_enabled(True)
                self._transition_to(FSMState.ENABLED, now)
        else:
            self.start_hold_since = None

    def _handle_enabled_state(self, dynamic_gesture, now, log_messages):
        """Handle ENABLED state transitions"""
        if dynamic_gesture in ['CW', 'CCW']:
            if self.pending_selection == dynamic_gesture:
                self.gesture_counter += 1
            else:
                self.pending_selection = dynamic_gesture
                self.gesture_counter = 1  
            
            if self.gesture_counter >= self.GESTURE_CONFIRM_COUNT:
                self.awaiting_confirm_since = now
                self._transition_to(FSMState.AWAIT_CONFIRM, now)
                log_messages.append(f"Seleção inicial '{self.pending_selection}' -> Aguardando confirmação.")
                self.gesture_counter = 0  
        else:
            self.pending_selection = None
            self.gesture_counter = 0

    def _handle_await_confirm_state(self, dynamic_gesture, now, robot_controller, log_messages):
        """Handle AWAIT_CONFIRM state transition"""
        if dynamic_gesture == self.pending_selection:
            self.confirm_counter += 1  
        else:
            self.confirm_counter = 0  
        
        if self.confirm_counter >= self.GESTURE_CONFIRM_COUNT:
            is_prog2 = (self.pending_selection == 'CCW')
            robot_controller.set_program_selection(is_prog2)
            
            log_messages.append(f"Seleção '{self.pending_selection}' confirmada. Executando.")
            
            try:
                robot_controller.pulse_execute(self.EXEC_PULSE_TIME)
            except Exception as e:
                log_messages.append(f"Erro ao executar pulso: {e}")
            
            robot_controller.set_program_selection(False)
            self._transition_to(FSMState.RUNNING, now)
            self.confirm_counter = 0 
        
        elif self.awaiting_confirm_since and (now - self.awaiting_confirm_since > self.CONFIRM_TIMEOUT):
            log_messages.append("Timeout de confirmação. Retornando para HABILITADO.")
            self._transition_to(FSMState.ENABLED, now)

    def _handle_running_state(self, now, robot_controller, log_messages):
        """Handle RUNNING state transitions"""
        try:
            program_finished = robot_controller.get_program_finished()
            if program_finished:
                log_messages.append("Programa finalizado. Retornando para HABILITADO.")
                self._transition_to(FSMState.ENABLED, now)
            elif self.running_since and (now - self.running_since > self.MAX_RUNNING_TIME):
                log_messages.append("Timeout de execução. Retornando para HABILITADO.")
                self._transition_to(FSMState.ENABLED, now)
        except Exception as e:
            log_messages.append(f"Erro ao verificar status do programa: {e}")

    def _transition_to(self, new_state, now):
        """Transition to new state and reset relevant variables"""
        old_state = self.state
        self.state = new_state
        
        if new_state == FSMState.DISABLED:
            self.start_hold_since = self.awaiting_confirm_since = None
            self.pending_selection = self.running_since = None
            self.gesture_counter = 0
            self.confirm_counter = 0
            
        elif new_state == FSMState.ENABLED:
            if old_state == FSMState.DISABLED:
                self.start_hold_since = self.awaiting_confirm_since = None
                self.pending_selection = None
            elif old_state == FSMState.AWAIT_CONFIRM:
                self.awaiting_confirm_since = None
                self.pending_selection = None
                self.confirm_counter = 0
            elif old_state == FSMState.RUNNING:
                self.running_since = None
                self.pending_selection = None
            
        elif new_state == FSMState.AWAIT_CONFIRM:
            self.running_since = None
            self.gesture_counter = 0
            
        elif new_state == FSMState.RUNNING:
            self.running_since = now
            self.awaiting_confirm_since = None
            self.pending_selection = None
            self.confirm_counter = 0

    def get_log_messages(self):
        """Get accumulated log messages and clear buffer"""
        messages = self.log_messages.copy()
        self.log_messages.clear()
        return messages