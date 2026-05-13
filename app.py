from flask import Flask, render_template, request, redirect, url_for
import requests
import json

app = Flask(__name__)

with open('rubric.json', 'r') as file:
    rubric = json.load(file)
with open('rubric.json', 'r') as file:
    tcs = json.load(file)


@app.route('/home', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        # 1. Flatten the Context dictionary
        audit_context = {
            "fellow_name": form_data.get('fellow_name', 'Unknown'),
            "fellow_placement": form_data.get('placement', 'Not Specified'),
            "company_name": form_data.get('company_name', 'Unknown'),
            "transcript": form_data.get('transcript', '')
        }
        
        # --- 2. THE FLAT SCHEMA PROMPT ---
        prompt = f"""
        ### ROLE
        You are the Trinethra Performance Auditor for DeepThought. Analyze the supervisor interview transcript and evaluate the Fellow.

        ### RUBRIC RULES
        Use the following rubric to determine the Fellow's score and analyze their performance. Pay close attention to the 6 vs 7 boundary.
        {json.dumps(rubric)}

        ### AUDIT CONTEXT (EVALUATE THIS)
        {json.dumps(audit_context)}

        ### OUTPUT SCHEMA
        You MUST return ONLY a valid JSON object matching this EXACT flat structure. Do NOT nest objects. Do NOT include markdown formatting.
        {{
            "fellow_name": "{audit_context['fellow_name']}",
            "fellow_placement": "{audit_context['fellow_placement']}",
            "company_name": "{audit_context['company_name']}",
            "score_value": <number 1-10>,
            "score_label": "<string>",
            "score_band": "<Need Attention, Productivity, or Performance>",
            "score_justification": "<string>",
            "gaps": [ {{"dimension": "<string>", "detail": "<string>"}} ],
            "kpi_mapping": [ {{"kpi": "<string>", "evidence": "<string>"}} ],
            "evidence": [ {{"dimension": "<execution, systems_building, kpi_impact, or change_management>", "quote": "<string>", "signal": "<positive or negative>", "interpretation": "<string>"}} ],
            "follow_up_questions": [ {{"target_gap": "<string>", "question": "<string>", "looking_for": "<string>"}} ]
        }}
        """

        response = requests.post('http://localhost:11434/api/generate', json={
            'model': 'llama3.2:1b', 
            'prompt': prompt,
            'stream': False,
            'format': 'json'
        })
        
        # Extract the raw text response
        llm_output = response.json().get('response', '')
        print("--- RAW LLM OUTPUT ---")
        print(llm_output)
        
        # --- 3. THE BULLETPROOF JSON EXTRACTOR ---
        # Instead of regex, just find the first '{' and last '}'
        start_index = llm_output.find('{')
        end_index = llm_output.rfind('}')
        
        if start_index != -1 and end_index != -1:
            clean_json_str = llm_output[start_index:end_index+1]
        else:
            clean_json_str = llm_output # Fallback if braces aren't found

        try:
            # Safely parse the JSON
            parsed_data = json.loads(clean_json_str)
            
            # --- 4. MINIMAL SAFETY NET ---
            # Ensure arrays and keys exist so Jinja loops in HTML don't crash
            if 'score_value' not in parsed_data: parsed_data['score_value'] = 0
            if 'score_label' not in parsed_data: parsed_data['score_label'] = "Unknown"
            if 'score_band' not in parsed_data: parsed_data['score_band'] = "Unknown"
            if 'score_justification' not in parsed_data: parsed_data['score_justification'] = "No justification provided."
            if 'gaps' not in parsed_data: parsed_data['gaps'] = []
            if 'kpi_mapping' not in parsed_data: parsed_data['kpi_mapping'] = []
            if 'evidence' not in parsed_data: parsed_data['evidence'] = []
            if 'follow_up_questions' not in parsed_data: parsed_data['follow_up_questions'] = []
            print(parsed_data)
            return render_template('res.html', data=parsed_data)
            
        except Exception as e:
            # If the model hallucinates bad JSON, catch it politely
            print(f"JSON Parsing Error: {e}")
            return f"""
            <div style="padding: 40px; font-family: sans-serif;">
                <h2 style="color: red;">Error parsing AI response</h2>
                <p>The AI generated invalid data. Please go back and try again.</p>
                <p><b>Error Details:</b> {e}</p>
                <hr>
                <pre style="background: #eee; padding: 20px;">{llm_output}</pre>
            </div>
            """, 500

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)