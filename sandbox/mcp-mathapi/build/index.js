import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, } from "@modelcontextprotocol/sdk/types.js";
const server = new Server({
    name: "MathAPI",
    version: "1.0.0",
}, {
    capabilities: {
        tools: {},
    },
});
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "calculate",
                description: "Add, subtract, multiply or divide two numbers",
                inputSchema: {
                    type: "object",
                    properties: {
                        operation: {
                            type: "string",
                            enum: ["add", "subtract", "multiply", "divide"],
                            description: "The mathematical operation to perform",
                        },
                        a: {
                            type: "number",
                            description: "The first number",
                        },
                        b: {
                            type: "number",
                            description: "The second number",
                        },
                    },
                    required: ["operation", "a", "b"],
                },
            },
        ],
    };
});
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name !== "calculate") {
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
    const args = request.params.arguments;
    if (typeof args.a !== "number" || typeof args.b !== "number") {
        throw new Error("Arguments 'a' and 'b' must be numbers");
    }
    let result;
    switch (args.operation) {
        case "add":
            result = args.a + args.b;
            break;
        case "subtract":
            result = args.a - args.b;
            break;
        case "multiply":
            result = args.a * args.b;
            break;
        case "divide":
            if (args.b === 0) {
                throw new Error("Cannot divide by zero");
            }
            result = args.a / args.b;
            break;
        default:
            throw new Error(`Unknown operation: ${args.operation}. Must be add, subtract, multiply, or divide.`);
    }
    return {
        content: [
            {
                type: "text",
                text: String(result),
            },
        ],
    };
});
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
}
main().catch((error) => {
    console.error("Server error:", error);
    process.exit(1);
});
