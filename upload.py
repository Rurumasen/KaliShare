import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL path and query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        # Handle file download request
        if parsed_path.path == '/download' and 'file' in query_params:
            filename = query_params['file'][0]
            if os.path.isfile(filename):
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(os.path.getsize(filename)))
                self.end_headers()

                with open(filename, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "File not found")
                return

        # Handle file view request
        if parsed_path.path == '/view' and 'file' in query_params:
            filename = query_params['file'][0]
            if os.path.isfile(filename):
                # Determine the MIME type of the file
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type is None:
                    mime_type = 'application/octet-stream'

                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', str(os.path.getsize(filename)))
                self.end_headers()

                with open(filename, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "File not found")
                return

        # Serve the main HTML page with file upload form and file list
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()

        # Get the list of files in the current directory
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        file_rows = ''.join(
            f'''
            <tr>
                <td><a href="/view?file={f}" style="color: blue; text-decoration: none;">{f}</a></td>
                <td><a href="/download?file={f}" style="color: green; text-decoration: none;">Download</a></td>
            </tr>
            ''' for f in files
        )

        # HTML content with enhanced design and table layout
        html_content = f'''
        <html>
        <head>
            <title>File Manager</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    padding: 0;
                    background-color: #f9f9f9;
                }}
                h1 {{
                    color: #333;
                }}
                form {{
                    margin-bottom: 20px;
                }}
                input[type="file"] {{
                    margin-right: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                a {{
                    color: #007BFF;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .green {{
                    color: green;
                }}
            </style>
        </head>
        <body>
            <h1>File Manager</h1>
            <form enctype="multipart/form-data" method="post">
                <input name="file" type="file" required/>
                <input type="submit" value="Upload File"/>
            </form>

            <h2>Files Available</h2>
            <table>
                <thead>
                    <tr>
                        <th>File Name</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {file_rows or '<tr><td colspan="2">No files available</td></tr>'}
                </tbody>
            </table>
        </body>
        </html>
        '''
        self.wfile.write(html_content.encode())

    def do_POST(self):
        # Handle file upload
        content_length = int(self.headers['Content-Length'])
        boundary = self.headers['Content-Type'].split("boundary=")[-1].encode()
        remainbytes = content_length
        line = self.rfile.readline()
        remainbytes -= len(line)

        if boundary not in line:
            self.send_error(400, "Content NOT begin with boundary")
            return

        line = self.rfile.readline()  # Content-Disposition
        remainbytes -= len(line)
        fn = line.decode().split('filename="')[-1].split('"')[0]

        if not fn:
            self.send_error(400, "No filename provided")
            return

        self.rfile.readline()  # Content-Type
        remainbytes -= len(line)
        self.rfile.readline()  # blank line
        remainbytes -= len(line)

        out = open(fn, 'wb')
        preline = self.rfile.readline()
        remainbytes -= len(preline)

        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                out.write(preline[:-1])  # remove last \n
                break
            else:
                out.write(preline)
                preline = line

        out.close()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()

        # HTML response with JavaScript alert
        response_html = '''
        <html>
        <head>
            <title>Upload Successful</title>
            <script>
                // Show an alert message
                alert("File uploaded successfully!");
                // Redirect back to the main page after the alert is closed
                window.location.href = "/";
            </script>
        </head>
        <body>
            <p>If you are not redirected automatically, <a href="/">click here</a>.</p>
        </body>
        </html>
        '''
        self.wfile.write(response_html.encode())

def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        # Create a temporary socket to get the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Connect to a public DNS server (Google DNS)
            ip = s.getsockname()[0]
        return ip
    except Exception:
        return "127.0.0.1"  # Fallback to localhost if IP cannot be determined

if __name__ == '__main__':
    # Get the local IP address
    local_ip = get_local_ip()
    print(f"Server started at http://{local_ip}:8080/")
    
    # Start the HTTP server
    httpd = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
    print("Listening on port 8080...")
    httpd.serve_forever()
