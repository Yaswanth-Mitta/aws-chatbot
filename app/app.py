import boto3
import subprocess
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

def ask_bedrock(prompt):
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    response = bedrock_runtime.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    return result['content'][0]['text'].strip()

def run_command_from_claude(prompt):
    command_prompt = f"Give only the AWS CLI command without explanation to: {prompt}"
    command = ask_bedrock(command_prompt)

    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return f"Command: {command}\nOutput:\n{output.decode()}"
    except subprocess.CalledProcessError as e:
        return f"Command: {command}\nError:\n{e.output.decode()}"

@app.route('/', methods=['GET'])
def home():
    return '''
        <h2>Ask AWS Query</h2>
        <form method="POST" action="/ask">
            <input type="text" name="query" style="width: 400px;" placeholder="e.g., List all EC2 instances" required>
            <button type="submit">Submit</button>
        </form>
    '''

@app.route('/ask', methods=['POST'])
def web_form_handler():
    query = request.form.get("query")
    if not query:
        return "No query provided", 400

    aws_output = run_command_from_claude(query)

    return f'''
        <h2>Query Result</h2>
        <h3>Your Query:</h3>
        <pre>{query}</pre>
        <h3>Claude Output:</h3>
        <pre>{aws_output}</pre>
        <form method="GET" action="/">
            <button type="submit">Ask Another Question</button>
        </form>
    '''

@app.route('/api/ask', methods=['POST'])
def api_handler():
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    aws_output = run_command_from_claude(query)
    return jsonify({
        "your_query": query,
        "aws_output": aws_output
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6443)

