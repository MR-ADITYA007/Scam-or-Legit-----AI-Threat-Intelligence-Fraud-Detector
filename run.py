import os
import sys
import subprocess

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    requirements_file = os.path.join(backend_dir, "requirements.txt")
    
    print("=" * 65)
    print(" [SCAM OR LEGIT?] - AI-POWERED SUSPICION ANALYZER")
    print("=" * 65)
    
    # Check dependencies
    print("\n[INFO] Checking Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], check=True)
    except Exception as e:
        print(f"[NOTE] Note during package install: {e}")
        
    print("\n[STARTING] Starting FastAPI & RAG Engine on http://localhost:8000 ...\n")
    
    os.chdir(backend_dir)
    sys.path.append(backend_dir)
    
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
