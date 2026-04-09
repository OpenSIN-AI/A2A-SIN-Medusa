import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
const server = new Server({
    name: "ipapi-mcp-server",
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
                name: "get_ip_location",
                description: "Get geolocation data for a given IP address",
                inputSchema: {
                    type: "object",
                    properties: {
                        ip: {
                            type: "string",
                            description: "The IP address to look up (e.g., '8.8.8.8')",
                        },
                    },
                    required: ["ip"],
                },
            },
        ],
    };
});
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name !== "get_ip_location") {
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
    const ip = request.params.arguments?.ip;
    if (!ip || typeof ip !== "string") {
        throw new Error("Invalid or missing IP address argument");
    }
    try {
        const response = await fetch(`https://ipapi.co/${ip}/json/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(data.reason || "Failed to fetch IP data");
        }
        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({
                        ip: data.ip,
                        city: data.city,
                        region: data.region,
                        country: data.country_name,
                        country_code: data.country,
                        latitude: data.latitude,
                        longitude: data.longitude,
                        org: data.org
                    }, null, 2),
                },
            ],
        };
    }
    catch (error) {
        return {
            content: [
                {
                    type: "text",
                    text: `Error fetching IP data: ${error.message}`,
                },
            ],
            isError: true,
        };
    }
});
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
}
main().catch((error) => {
    console.error("Server error:", error);
    process.exit(1);
});
