import ssl
import base64
import sys
import os
import socket

def b64_encode(input):
    encoded_bytes = base64.b64encode(input.encode())
    return encoded_bytes.decode()

def send(socket_to_send, request, is_command=True, log=True):
    if log and verbose:
        print("Cl:", request)
        
    socket_to_send.send(bytes(request + '\r\n', 'utf-8'))
    
    if is_command:
        response = socket_to_send.recv(1024).decode()
        if verbose:
            print("Se:", response)
        return response

def handle_server_answer(answer):
    if not answer:
        return
    
    answer = list(filter(None, answer.split("\r\n")))
    code = int(answer[0][0:3])
    digits = [int(i) for i in str(code)]

    if digits[0] == 5:
        print("\r\nSERVER ERROR:", " ".join(answer))
        send(s, "QUIT")
        quit(5)
    elif digits[0] == 4:
        print("CLIENT ERROR:", " ".join(answer))
        if digits[1] == 2:
            send(s, "QUIT")
            quit(421)
        elif digits[1] == 5:
            send(s, "QUIT")
            quit("".join([str(i) for i in digits]))

def handle_input_arguments(arguments_list):
    args = {
        "valid": False,

        "from_address": "",
        "to_address": "",
        "port": "25",
        "subject": "Pics",
        "auth": False,
        "verbose": False,
        "directory": os.getcwd(),
        "ssl": False,
        "server": "",
    }

    i = 0
    while i < len(arguments_list):
        arg = arguments_list[i]
        if arg in ['-h', '--help']:
            print(help_msg)
            quit(0)
        elif arg == "--ssl":
            args["ssl"] = True
        elif arg in ['-s', '--server']:
            address = sys.argv[i + 1].split(":")
            args["server"] = address[0]
            if len(address) > 1:
                args["port"] = address[1]
            i += 1
        elif arg in ['-t', '--to']:
            args["to_address"] = arguments_list[i + 1]
            i += 1
        elif arg in ['-f', '--from']:
            args["from_address"] = arguments_list[i + 1]
            i += 1
        elif arg == "--subject":
            args["subject"] = arguments_list[i + 1]
            i += 1
        elif arg == "--auth":
            args["auth"] = True
        elif arg in ['-v', '--verbose']:
            args["verbose"] = True
        elif arg in ['-d', '--directory']:
            args["directory"] = arguments_list[i + 1]
            i += 1

        i += 1

    if args["server"] and args["to_address"] and args["from_address"] and os.path.isdir(args["directory"]):
        args["valid"] = True

    if args["ssl"]:
        args["port"] = 465

    return args

help_msg = """SMTP Image Sender Script. Commands:
  -h/--help          Show this help message
  -f/--from          Sender email address (default: ee-tester@mail.ru)
  -t/--to            Recipient email address
  -s/--server        SMTP server address[:port] (default port: 25)
  --subject          Email subject (default: "Pics")
  --auth             Enable authentication (will prompt during runtime)
  -v/--verbose       Enable verbose mode (show commands and responses)
  -d/--directory     Directory containing images to send
  --ssl              Enable SSL/TLS (default: off)
  [!] Major SMTP providers like smtp.mail.ru or smtp.yandex.ru require SSL

Example minimal invocation:
  python smtp.py -f sender@example.com -t recipient@example.com -s smtp.example.com --auth --ssl
"""

server_parameters = {
    "starttls": False,
    "pipelining": False,
    "isDone": False,
    "size": 0,
}

def handle_server_hello(hello):
    # Parse EHLO response for capabilities
    hello = [line[4::].split(" ") for line in hello.split("\r\n")]
    for line in hello:
        if line[0] == "SIZE":
            server_parameters["size"] = int(line[1])
        elif line[0] == "AUTH":
            server_parameters["auth"] = line[1::]
        elif line[0] == "PIPELINING":
            server_parameters["pipelining"] = True
        elif line[0] == "STARTTLS":
            server_parameters["starttls"] = True
    server_parameters["isDone"] = True

def create_socket(ssl_allowed, server, port):
    # Open TCP connection and wrap in SSL if requested
    working_socket = socket.create_connection((server, port))
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    result_socket = ssl_context.wrap_socket(working_socket, server_side=False) if ssl_allowed else working_socket
    # Receive initial server greeting
    hello = result_socket.recv(1024).decode()
    try:
        # Send EHLO and parse server features
        hello = send(result_socket, "EHLO anon")
        handle_server_hello(hello)
        if verbose:
            print('Se:', hello)
    except Exception:
        print("\n\nConnection was forcibly closed by remote host (try --ssl)")
        quit(-2)

    return result_socket

def initial(socket, email, auth_allowed):
    # Ensure authentication if server requires it
    if "auth" in server_parameters and server_parameters["auth"] and not auth_allowed:
        print("--Authentication is required for this server, try --auth flag--")
        quit(-4075)
    
    if auth_allowed:
        # Default to LOGIN if no methods provided
        if not server_parameters.get("auth"):
            print("--Server did not advertise auth methods; using AUTH LOGIN by default--")
            send(socket, "AUTH LOGIN")
            send(socket, b64_encode(email))
            print("--Enter your password--")
            password = input()
            send(socket, b64_encode(password), True, False)
            return
        
        # Prompt user to select auth method
        options = [f"{i}. {op}" for i, op in enumerate(server_parameters["auth"])]
        print("--", " ".join(options), "--")
        print("--Select preferred method index--")
        option = server_parameters["auth"][int(input())]
        if option == "LOGIN":
            send(socket, "AUTH LOGIN")
            send(socket, b64_encode(email))
            print("--Enter your password--")
            password = input()
            send(socket, b64_encode(password), True, False)
        elif option == "PLAIN":
            send(socket, "AUTH PLAIN")
            email = email.replace("@", "\\@")
            print("--Enter your password--")
            password = b64_encode(input())
            send(socket, f"\0{email}\000{password}", True, False)
        elif option == "XOAUTH2":
            send(socket, "AUTH XOAUTH2")
            print("--Enter your OAuth2 token--")
            token = input()
            send(socket, b64_encode(f"user={email}\001Aauth=Bearer {token}\001\001"))

def send_pics(socket_to_send, args):
    # Begin SMTP transaction
    send(socket_to_send, "MAIL FROM: " + args["from_address"])
    send(socket_to_send, "RCPT TO: " + args["to_address"])
    send(socket_to_send, "DATA")
    
    boundary = "boundary-type-1234567892-alt"
    
    data = f"""From: {args['from_address']}
To: {args['to_address']}
Subject: {args['subject']}
MIME-Version: 1.0
Content-Type: multipart/related;
  boundary="{boundary}"\r\n
"""

    attachments = []
    
    if os.path.exists(args["directory"]):
        filenames = next(os.walk(args["directory"]), (None, None, []))[2]
        
        for filename in filenames:
            with open(os.path.join(args["directory"], filename), "rb") as image_file:
                _, extension = os.path.splitext(filename)
                extension_name = extension.replace(".", "")
                encoded = base64.b64encode(image_file.read())
                
            attachments.append(f"""--{boundary}
Content-Transfer-Encoding: base64
Content-Type: image/{extension_name}
Content-Disposition: attachment;filename="{filename.split('/')[-1]}"\r\n\r\n""")
            attachments.append(str(encoded)[2:-1])
            attachments.append(f"\r\n--{boundary}\r\n\r\n")

        attachments.append(f"--{boundary}--")
        data = data + "".join(attachments) + "\r\n."
        send(socket_to_send, data)
    else:
        print("Specified directory does not exist.")


args = handle_input_arguments(sys.argv)
if not args["valid"]:
    print("Invalid input, check -h/--help and try again.")
    quit()
verbose = args["verbose"]

# Establish connection and authenticate if needed
s = create_socket(args["ssl"], args["server"], args["port"])
initial(s, args["from_address"], args["auth"])
# Send images and quit
send_pics(s, args)
send(s, "QUIT")
print("DONE")
