python -c 
import os
os.makedirs('templates', exist_ok=True)
templates = {'error.html': '<!DOCTYPE html><html><head><title>Error</title></head><body><h1>Error</h1><p>{{ message }}</p><a href=\"/\">Go Home</a></body></html>'}
for filename, content in templates.items():
    with open(os.path.join('templates', filename), 'w') as f:
        f.write(content)
    print(f'Created: templates/{filename}')
