# Travel Agent Tutorial

This guide provides step-by-step instructions for setting up and running a Travel Agent in Dify, using the "llm_en_v_1_3_1" model.

## Prerequisites

Before starting, ensure you have the following:

1. Dify installed and running via Docker (not running on localhost)
2. Access to a LLM endpoint
3. Model "llm_en_v_1_3_1" accessible from your endpoint

## Step 1: Add LLM Model to Dify

1. Click the user icon located in the top-right corner of the interface
2. Select "Settings" from the dropdown menu
3. Navigate to the "Model Provider" tab
4. Install the "OpenAI-API-compatible" model if not already installed
5. In the "OpenAI-API-compatible" model, click "Add Model" and configure as follows:
   - **Model Type**: LLM
   - **Model Name**: llm_en_v_1_3_1
   - **API Key**: leave blank
   - **API endpoint URL**: `http://<your-server-ip>:5001/openai/v1`
   - **Model context size**: 4096

## Step 2: Set up the MCP Agent

1. At the top of the Dify interface, navigate to the "Tool" tab
2. Click the "Custom" tab
3. Click "Create Custom Tool"
4. Set the "Name" field to "Call MCP Tool"
5. Ensure the MCP Server is running. You can start it by entering the following in your terminal:
   ```bash
   python server.py
   ```
6. Set the "Schema" field to the following configuration:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Call MCP Tool",
    "version": "1.0.0",
    "description": "Call various MCP tools via MCP Server"
  },
  "servers": [
    {
      "url": "http://host.docker.internal:8000"
    }
  ],
  "paths": {
    "/mcp/execute": {
      "post": {
        "summary": "Call MCP Tool",
        "description": "Call MCP Tool",
        "operationId": "callTool",
        "parameters": [
          {
            "name": "Accept",
            "in": "header",
            "required": true,
            "description": "Client must accept both application/json and text/event-stream",
            "schema": {
              "type": "string",
              "example": "application/json, text/event-stream"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "jsonrpc": {
                    "type": "string"
                  },
                  "id": {
                    "type": "integer"
                  },
                  "method": {
                    "type": "string",
                    "enum": [
                      "tools/list", "tools/call"
                    ],
                    "description": "Method to execute"
                  },
                  "params": {
                    "type": "object",
                    "description": "Parameters for the method"
                  }
                },
                "required": [
                  "method"
                ]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "result": {
                      "type": "string",
                      "description": "Result of the operation"
                    }
                  }
                }
              },
              "text/event-stream": {
                "schema": {
                  "type": "string",
                  "description": "Server-sent events stream"
                }
              }
            }
          },
          "400": {
            "description": "Bad Request"
          },
          "406": {
            "description": "Not Acceptable - Client must accept both application/json and text/event-stream",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "error": {
                      "type": "string",
                      "example": "Client must accept both application/json and text/event-stream content types"
                    }
                  }
                }
              }
            }
          },
          "500": {
            "description": "Internal Server Error",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "error": {
                      "type": "string",
                      "description": "Error message"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

7. Click "Save" when you finish

## Step 3: Integrate the LLM and MCP Agent via Dify

### Create a temporary chatflow

1. On the main interface, locate the "Create App" box
2. Click "Create from Blank"
3. Select "Chatflow"
4. Name the chatflow "temp"

### Add a "Call Tool" block

1. Right click the "Answer" block
2. Select "Change Block"
3. Under the "Tools" tab, select "Call MCP Tool"
4. Connect the "Call Tool" block to the LLM block

### Export temporary chatflow

1. Click on the chatflow name in the top-left corner
2. Click "Export DSL"
3. Move "temp.yml" to the project folder

### Import Travel Agent yml

1. In the project folder, run:
   ```bash
   python generate_yml.py
   ```
2. On the main interface, locate the "Create App" box
3. Click "Import DSL file"
4. Select the file "Travel Agent.yml" in the project folder

## Configuration Notes

- Make sure to replace `<your-server-ip>` with your actual server IP address
- Ensure all required credentials are properly configured in the final step
- The MCP server must be running before attempting to use the agent

## Troubleshooting

- If you encounter connection issues, verify that Docker is not running on localhost
- Ensure the MCP server is accessible at the specified URL
- Check that all required ports are open and accessible