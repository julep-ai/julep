import express, { Request, Response } from 'express';
import cors from 'cors';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import type { Transport } from '@modelcontextprotocol/sdk/shared/transport.js';

// AIDEV-NOTE: HTTP transport implementation for MCP server behind Traefik proxy

export class HttpServerTransport implements Transport {
  private app: express.Application;
  private server?: any;
  
  onmessage?: (message: unknown) => void;
  onerror?: (error: Error) => void;
  onclose?: () => void;

  constructor(private port: number = 3000) {
    console.log(`HttpServerTransport: Creating transport for port ${port}`);
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware() {
    this.app.use(cors({
      origin: '*',
      methods: ['GET', 'POST', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Developer-Id'],
    }));
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
  }

  private setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req: Request, res: Response) => {
      res.json({ status: 'ok', service: 'julep-mcp' });
    });

    // MCP protocol endpoint
    this.app.post('/', async (req: Request, res: Response) => {
      try {
        const message = req.body;
        
        if (!message || typeof message !== 'object') {
          res.status(400).json({
            error: 'Invalid request body',
            details: 'Request body must be a valid JSON-RPC message'
          });
          return;
        }

        // Create a promise to wait for the response
        const responsePromise = new Promise<any>((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Request timeout'));
          }, 30000); // 30 second timeout

          // Temporarily override send to capture the response
          const originalSend = this.send.bind(this);
          this.send = async (response: any) => {
            clearTimeout(timeout);
            this.send = originalSend; // Restore original send
            resolve(response);
          };
        });

        // Process the message
        if (this.onmessage) {
          this.onmessage(message);
        }

        // Wait for and send the response
        const response = await responsePromise;
        res.json(response);
      } catch (error) {
        console.error('Error processing request:', error);
        res.status(500).json({
          error: 'Internal server error',
          details: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    });

    // MCP server info endpoint
    this.app.get('/', (req: Request, res: Response) => {
      res.json({
        name: 'julep-unified-mcp',
        version: '1.0.0',
        transport: 'http',
        endpoints: {
          health: '/health',
          protocol: '/',
        },
        documentation: 'https://github.com/julep-ai/julep/tree/main/mcp'
      });
    });
  }

  async start(): Promise<void> {
    console.log(`HttpServerTransport.start() called for port ${this.port}`);
    
    // Check if server is already started
    if (this.server) {
      console.log(`MCP HTTP server already running on port ${this.port}`);
      return;
    }
    
    return new Promise((resolve, reject) => {
      console.log(`HttpServerTransport: Attempting to listen on port ${this.port}`);
      this.server = this.app.listen(this.port, () => {
        console.log(`MCP HTTP server listening on port ${this.port}`);
        resolve();
      }).on('error', (err) => {
        console.error(`HttpServerTransport: Failed to start on port ${this.port}:`, err);
        reject(err);
      });
    });
  }

  async close(): Promise<void> {
    if (this.server) {
      return new Promise((resolve) => {
        this.server.close(() => {
          if (this.onclose) {
            this.onclose();
          }
          resolve();
        });
      });
    }
  }

  async send(message: unknown): Promise<void> {
    // Messages are sent as responses to HTTP requests
    // This will be overridden per request in the POST handler
    console.log('Send called outside of request context:', message);
  }
}