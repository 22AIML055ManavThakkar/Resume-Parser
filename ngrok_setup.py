# Automatically sets up and runs Streamlit through ngrok

import subprocess
import shlex

# Streamlit run command
command = "streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
process = subprocess.Popen(shlex.split(command))
