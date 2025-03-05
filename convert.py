import json
import csv

# Read the JSON file
with open('chat_data.json', 'r') as json_file:
    data = json.load(json_file)

# Create and write to CSV file
with open('insurance_faq.csv', 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    
    # Write header
    writer.writerow(['ID', 'Question', 'Answer'])
    
    # Write data
    for faq in data['insurance_faq']:
        id = faq['id']
        question = faq['question']
        for answer in faq['answers']:
            writer.writerow([id, question, answer]) 