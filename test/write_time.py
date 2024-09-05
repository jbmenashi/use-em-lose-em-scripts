from datetime import datetime

# Get the current time
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Write the current time to a text file
with open("current_time.txt", "a") as file:
    file.write(f"Current time: {current_time}\n")