# SMTPer
# SMTP Image Sender Script

A tool for sending images via email using raw SMTP sockets. The script allows users to configure various sending options and workflows.

## Features

- **SSL Support**: Optionally create a secure connection to the SMTP server.
- **Custom SMTP Server**: Specify the server address and port.
- **Verbose Mode**: Output SMTP commands and server responses in real time.
- **Directory Selection**: Choose the folder containing images to send.
- **Email Subject Customization**: Set a custom subject line for the message.
- **Authentication Methods**: Support for LOGIN, PLAIN, and XOAUTH2 mechanisms.
- **Attachment Handling**: Automatically encode images in Base64 and attach them with correct MIME types.
- **Fallback Methods**: If primary authentication or sending fails, handles errors.

## Workflow

1. **Argument Parsing**  
   - Help (`-h`, `--help`)  
   - From address (`-f`, `--from`)  
   - To address (`-t`, `--to`)  
   - SMTP server (`-s`, `--server`)  
   - Subject (`--subject`)  
   - Enable authentication (`--auth`)  
   - Verbose mode (`-v`, `--verbose`)  
   - Image directory (`-d`, `--directory`)  
   - SSL/TLS (`--ssl`)

2. **Connection Establishment**  
   - Create a TCP or SSL socket to the specified server and port.  
   - Send `EHLO` and parse server capabilities (e.g., SIZE, AUTH, PIPELINING, STARTTLS).

3. **Authentication (Optional)**  
   - Choose from available methods based on server response:  
     - LOGIN: Base64 username/password exchange.  
     - PLAIN: Single string authentication with email and password.  
     - XOAUTH2: OAuth 2.0 bearer token.  
   - Prompt the user for credentials as needed.

4. **Email Composition**  
   - Construct a multipart MIME message with a unique boundary string.  
   - Iterate over image files in the specified directory.  
   - Encode each image in Base64, attach with correct `Content-Type`, and name.

5. **Sending the Email**  
   - Issue SMTP commands: `MAIL FROM`, `RCPT TO`, and `DATA`.  
   - Transmit the composed MIME payload.  
   - Terminate data with a single dot line and send `QUIT`.

## Usage Examples

- **Basic usage** (no SSL, no authentication):  
  ```bash
  python smtp.py -f sender@example.com -t recipient@example.com -s smtp.example.com --directory /path/to/images
  ```

- **Secure SSL connection with authentication and verbose logging**:  
  ```bash
  python smtp.py -f sender@example.com -t recipient@example.com -s smtp.example.com --ssl --auth -v
  ```

## Error Handling

- **Server errors (5xx)**: Display error details, send `QUIT`, and exit.
- **Client errors (4xx)**: Display client error, optionally `QUIT`, and exit.
- **Invalid input**: Show help message and abort if required parameters are missing.
- **Missing directory**: Inform the user if the specified directory does not exist.

## Requirements

- Python 3.x (no third-party libraries required)
- Standard libraries: `ssl`, `socket`, `base64`, `os`, `sys`

## Notes

- Major SMTP providers (e.g., `smtp.mail.ru`, `smtp.yandex.ru`) require SSL.
- Ensure the image directory contains only supported image files.
- Use verbose mode for troubleshooting SMTP command exchanges.
