import subprocess

subprocess.run(["rasa", "run", "-m", "models", "--endpoints", "endpoint.yml", "--port", "5002", "--credentials", "credentials.yml", "--cors", "*", "--enable-api"])