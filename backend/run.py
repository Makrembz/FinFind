#!/usr/bin/env python
"""
FinFind API Server Runner

Usage:
    python run.py [--reload] [--host HOST] [--port PORT]
    
Options:
    --reload    Enable auto-reload for development
    --host      Host to bind (default: 0.0.0.0)
    --port      Port to bind (default: 8000)
"""

import argparse
import uvicorn
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="Run FinFind API Server")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", "8000")),
        help="Port to bind (default: 8000)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "info"),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level"
    )
    
    args = parser.parse_args()
    
    # Load environment variables from .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("python-dotenv not installed, skipping .env loading")
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                     FinFind API Server                           ║
╠══════════════════════════════════════════════════════════════════╣
║  Starting server with:                                           ║
║    Host: {args.host:<54} ║
║    Port: {args.port:<54} ║
║    Reload: {str(args.reload):<52} ║
║    Workers: {args.workers:<51} ║
║    Log Level: {args.log_level:<48} ║
╠══════════════════════════════════════════════════════════════════╣
║  Endpoints:                                                      ║
║    API Docs: http://{args.host}:{args.port}/docs{' ' * 32}║
║    ReDoc:    http://{args.host}:{args.port}/redoc{' ' * 31}║
║    Health:   http://{args.host}:{args.port}/health{' ' * 30}║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    uvicorn.run(
        "app.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()
