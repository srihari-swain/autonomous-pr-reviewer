"""
A simplified test script to directly interact with the github-mcp-server 
in stdio mode using subprocess
"""
import os
import json
import subprocess
import logging
import time
import select
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_test")

# Load environment variables
load_dotenv('/home/srihari/Documents/GEnAi/fynd/.env')

def read_with_timeout(proc, timeout=5):
    """Read from subprocess stdout with timeout"""
    ready_to_read, _, _ = select.select([proc.stdout], [], [], timeout)
    if ready_to_read:
        return proc.stdout.readline()
    return None

def try_command(proc, command, command_id=None):
    """Try sending a command to the MCP server and read the response"""
    if command_id is None:
        command_id = f"cmd-{int(time.time())}"
    
    request = {
        "jsonrpc": "2.0",
        "id": command_id,
        "method": command
    }
    
    logger.info(f"Sending command: {command} (id: {command_id})")
    
    try:
        # Send request
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()
        
        # Try to read response with timeout
        logger.info("Waiting for response...")
        response = read_with_timeout(proc)
        
        if response:
            logger.info(f"Got response: {response.strip()}")
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse response as JSON: {response}")
                return None
        else:
            logger.warning("No response received within timeout")
            return None
    except Exception as e:
        logger.error(f"Error in command {command}: {str(e)}")
        return None

def main():
    # Get token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("Token not found")
        return
    
    logger.info(f"Token found, length: {len(token)}")
    logger.info(f"Token prefix: {token[:4]}...")
    
    # Server path
    server_path = "/home/srihari/Documents/GEnAi/githubmcp/github-mcp-server/github-mcp-server"
    
    # Environment for the server
    env = os.environ.copy()
    env["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
    env["GITHUB_TOOLSETS"] = "repos,issues,pull_requests,code_security"
    
    # Check stderr output from server for diagnostic info
    stderr_file = open("/home/srihari/Documents/GEnAi/githubmcp/server_stderr.log", "w")
    
    try:
        # Start server process with stderr redirected to file
        logger.info(f"Starting server: {server_path}")
        proc = subprocess.Popen(
            [server_path, "stdio", "--log-file", "/home/srihari/Documents/GEnAi/githubmcp/server.log"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            env=env,
            text=True,
            bufsize=1,
        )
        
        # Give server a moment to initialize
        logger.info("Waiting for server to initialize...")
        time.sleep(2)
        
        # Try different command variations
        commands_to_try = [
            "discover",
            "mcp.discover",
            "list",
            "tools.list",
            "schema",
            "system.listMethods"  # Common JSON-RPC system method
        ]
        
        for command in commands_to_try:
            result = try_command(proc, command)
            if result and "result" in result:
                logger.info(f"Success with command: {command}")
                if isinstance(result["result"], list):
                    logger.info(f"Found {len(result['result'])} tools/methods")
                    for item in result["result"]:
                        if isinstance(item, dict):
                            logger.info(f"Tool: {item.get('name', item)}")
                        else:
                            logger.info(f"Item: {item}")
                else:
                    logger.info(f"Result: {result['result']}")
                break
        
        # Let's check for any server errors in stderr
        logger.info("Checking for server stderr output...")
        stderr_file.flush()
        stderr_file.close()
        
        with open("/home/srihari/Documents/GEnAi/githubmcp/server_stderr.log", "r") as f:
            stderr_content = f.read()
            if stderr_content.strip():
                logger.info(f"Server stderr output:\n{stderr_content}")
            else:
                logger.info("No server stderr output found")
                
        # Read any actual log file if it was created
        log_path = "/home/srihari/Documents/GEnAi/githubmcp/server.log"
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                log_content = f.read()
                logger.info(f"Server log file content:\n{log_content}")
        else:
            logger.info("No server log file found")
        
        # Clean up
        proc.terminate()
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        if 'proc' in locals():
            proc.terminate()
        if not stderr_file.closed:
            stderr_file.close()

if __name__ == "__main__":
    main()
