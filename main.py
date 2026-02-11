from google import genai

# Tamari API Key ahiya muko
client = genai.Client(api_key="AIzaSyCj31C_zDtJDMkjApU_YfTFm1j0t_5E7Kw")

print("--- Checking Available Models ---")
try:
    # Google ne puchiye chiye ke kaya model available che
    for model in client.models.list():
        if "generateContent" in model.supported_actions:
            print(f"Model Name: {model.name}")
            
except Exception as e:
    print(f"Error: {e}")