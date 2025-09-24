#!/usr/bin/env python3
import socket
import sys

def test_rtde_connection():
    print("=== RTDE Connection Test ===")
    
    # Testar se a biblioteca está disponível
    try:
        import rtde_receive
        import rtde_control
        print("RTDE library is available")
    except ImportError as e:
        print(f"RTDE library not available: {e}")
        print("Install with: pip install ur-rtde")
        return False
    
    # Testar conexão de rede com o robô
    robot_ip = 'localhost'
    port = 30004
    
    print(f"Testing connection to {robot_ip}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((robot_ip, port))
        sock.close()
        
        if result == 0:
            print("Network connection successful")
        else:
            print(f"Network connection failed (error code: {result})")
            return False
    except Exception as e:
        print(f"Network test error: {e}")
        return False
    
    # Tentar conectar com RTDE
    try:
        print("Attempting RTDE connection...")
        rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip)
        rtde_c = rtde_control.RTDEControlInterface(robot_ip)
        
        # Testar leitura de dados
        actual_q = rtde_r.getActualQ()
        
        print(f"RTDE connection successful!")
        print(f"  - Joint positions: {actual_q}")
        
        # Limpar conexão
        rtde_c.disconnect()
        rtde_r.disconnect()
        
        return True
        
    except Exception as e:
        print(f"RTDE connection failed: {e}")
        print("Check if robot is in Remote Control mode and RTDE is enabled")
        return False

if __name__ == "__main__":
    test_rtde_connection()