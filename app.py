from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import re # Needed to clean up LLM output

app = Flask(__name__)

# Load the Rubric Rules once when the app starts
with open('rubric.json', 'r') as file:
    rubric = json.load(file)

@app.route('/home', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        audit_context = {
            "fellow": {
                "name": form_data.get('fellow_name'),
                "tenure": form_data.get('tenure', 'Not Specified'),
                "background": form_data.get('background', 'Not Specified'),
                "placement": form_data.get('placement', 'Not Specified'),
                "targetKpis": [k.strip() for k in form_data.get('targetKpis', '').split(',') if k.strip()]
            },
            "company": {
                "name": form_data.get('company_name'),
                "location": form_data.get('location', 'Not Specified'),
                "industry": form_data.get('industry', 'Not Specified'),
                "context": form_data.get('company_context', 'Not Specified')
            },
            "transcript": form_data.get('transcript')
        }
        
        # --- THE FIXED PROMPT ---
        prompt = f"""
        ### ROLE
        You are the Trinethra Performance Auditor for DeepThought. Analyze the supervisor interview transcript and evaluate the Fellow.

        ### RUBRIC RULES
        Use the following rubric to determine the Fellow's score and analyze their performance. Pay close attention to the 6 vs 7 boundary.
        {json.dumps(rubric)}

        ### AUDIT CONTEXT (EVALUATE THIS)
        {json.dumps(audit_context)}

        ### OUTPUT SCHEMA
        You MUST return ONLY a valid JSON object matching this exact structure. Do NOT include markdown formatting or introductory text.
        {{
            "fellow": {{"name": "{audit_context['fellow']['name']}", "placement": "{audit_context['fellow']['placement']}"}},
            "company": {{"name": "{audit_context['company']['name']}"}},
            "score": {{
                "value": <number 1-10>,
                "label": "<string>",
                "band": "<Need Attention, Performance Productivity, or>",
                "justification": "<string>"
            }},
            "gaps": [ {{"dimension": "<string>", "detail": "<string>"}} ],
            "kpiMapping": [ {{"kpi": "<string>", "evidence": "<string>", "systemOrPersonal": "<system or personal>"}} ],
            "evidence": [ {{"dimension": "<execution, systems_building, kpi_impact, or change_management>", "quote": "<string>", "signal": "<positive or negative>", "interpretation": "<string>"}} ],
            "followUpQuestions": [ {{"targetGap": "<string>", "question": "<string>", "lookingFor": "<string>"}} ]
        }}
        """

        # Call local Ollama
        response = requests.post('http://localhost:11434/api/generate', json={
            'model': 'llama3.2:1b',
            'prompt': prompt,
            'stream': False,
            'format': 'json' # This forces Ollama to output JSON
        })
        
        # Extract the raw text response
        llm_output = response.json().get('response', '')
        print("--- RAW LLM OUTPUT ---")
        print(llm_output)
        
        # Clean the output (strip markdown code blocks if the LLM ignores the format flag)
        clean_json_str = re.sub(r'^```json\s*', '', llm_output)
        clean_json_str = re.sub(r'\s*```$', '', clean_json_str).strip()

        try:
            # Safely parse the JSON
            parsed_data = json.loads(clean_json_str)
            return render_template('res.html', data=parsed_data)
        except json.JSONDecodeError as e:
            # If the 1B model hallucinates bad JSON, catch it so Flask doesn't crash
            print(f"JSON Parsing Error: {e}")
            return f"<h1>Error parsing LLM response</h1><pre>{llm_output}</pre>", 500

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)