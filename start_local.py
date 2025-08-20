"""
Local development startup script
Starts both backend and frontend for local testing
"""
import subprocess
import sys
import os
import time
from pathlib import Path
import threading

def start_backend():
    """Start FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    backend_path = Path(__file__).parent / 'backend'
    
    # Change to backend directory
    os.chdir(str(backend_path))
    
    # Install dependencies if needed
    try:
        import uvicorn
        print("✅ Backend dependencies available")
    except ImportError:
        print("📦 Installing backend dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # Start backend server
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'app.main:app', 
            '--reload', 
            '--host', '0.0.0.0', 
            '--port', '8000'
        ])
    except KeyboardInterrupt:
        print("🛑 Backend stopped")

def start_frontend():
    """Start Next.js frontend"""
    print("🎨 Starting Next.js frontend...")
    frontend_path = Path(__file__).parent / 'frontend'
    
    # Change to frontend directory  
    os.chdir(str(frontend_path))
    
    # Install dependencies if needed
    if not (frontend_path / 'node_modules').exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(['npm', 'install'])
    
    # Start frontend server
    try:
        subprocess.run(['npm', 'run', 'dev'])
    except KeyboardInterrupt:
        print("🛑 Frontend stopped")

def main():
    """Start both services"""
    print("🔧 VIX/SPY Iron Condor Trading Dashboard - Local Development")
    print("=" * 60)
    print()
    
    choice = input("Start (B)ackend only, (F)rontend only, or (A)ll? [A]: ").strip().upper() or 'A'
    
    if choice == 'B':
        start_backend()
    elif choice == 'F':
        start_frontend()
    elif choice == 'A':
        print("🚀 Starting both backend and frontend...")
        print("📝 Backend will be available at: http://localhost:8000")
        print("🎨 Frontend will be available at: http://localhost:3000")
        print("📊 API docs will be available at: http://localhost:8000/docs")
        print()
        print("Press Ctrl+C to stop all services")
        print("-" * 60)
        
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # Give backend time to start
        time.sleep(5)
        
        # Start frontend in main thread
        try:
            start_frontend()
        except KeyboardInterrupt:
            print("\n🛑 Stopping all services...")
    else:
        print("❌ Invalid choice")
        sys.exit(1)

if __name__ == "__main__":
    main()