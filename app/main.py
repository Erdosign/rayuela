from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os

# Import routers
from app.routers import novels, chapters, scenes

# Import database initialization
from app.database.connection import create_database

# Create FastAPI app
app = FastAPI(
    title="Novel Writing App API",
    description="A comprehensive API for managing novel writing projects, chapters, and scenes",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API prefix
app.include_router(novels.router, prefix="/api")
app.include_router(chapters.router, prefix="/api")
app.include_router(scenes.router, prefix="/api")

# Load Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    try:
        create_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        
@app.get("/projects")
async def projects_list_page(request: Request):
    """Web interface: Projects list page"""
    # TODO: Fetch actual projects from database
    projects = []  # Replace with actual database call
    return templates.TemplateResponse("projects_list.html", {
        "request": request,
        "projects": projects,
        "total_words": 0,
        "in_progress_count": 0,
        "completed_count": 0
    })

@app.get("/projects/{project_id}")
async def project_detail_page(request: Request, project_id: int):
    """Web interface: Project detail page"""
    # TODO: Fetch actual project from database
    project = {
        "id": project_id,
        "title": "Sample Project",
        "description": "This is a sample project",
        "genre": "fiction",
        "status": "in_progress"
    }  # Replace with actual database call
    
    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "project": project
    })

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Root endpoint with API information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Novel Writing App API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
            .get { background-color: #61affe; }
            .post { background-color: #49cc90; }
            .put { background-color: #fca130; }
            .patch { background-color: #50e3c2; }
            .delete { background-color: #f93e3e; }
            h1 { color: #333; }
            h2 { color: #666; border-bottom: 2px solid #eee; }
        </style>
    </head>
    <body>
        <h1>📚 Novel Writing App API</h1>
        <p>Welcome to the Novel Writing App API! This API helps you manage your novel writing projects, chapters, and scenes.</p>
        
        <h2>📖 API Documentation</h2>
        <ul>
            <li><a href="/api/docs" target="_blank">Interactive API Documentation (Swagger)</a></li>
            <li><a href="/api/redoc" target="_blank">ReDoc Documentation</a></li>
        </ul>
        
        <h2>🚀 Quick Start Endpoints</h2>
        
        <h3>Projects</h3>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/projects</code> - Get all projects
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/projects</code> - Create a new project
        </div>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/projects/{project_id}</code> - Get project details
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/api/projects/{project_id}</code> - Update project
        </div>
        <div class="endpoint">
            <span class="method delete">DELETE</span> <code>/api/projects/{project_id}</code> - Delete project
        </div>
        
        <h3>Chapters</h3>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/chapters/project/{project_id}</code> - Get chapters for a project
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/chapters</code> - Create a new chapter
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/api/chapters/{chapter_id}</code> - Update chapter
        </div>
        <div class="endpoint">
            <span class="method patch">PATCH</span> <code>/api/chapters/{chapter_id}/reorder</code> - Reorder chapter
        </div>
        <div class="endpoint">
            <span class="method delete">DELETE</span> <code>/api/chapters/{chapter_id}</code> - Delete chapter
        </div>
        
        <h3>Scenes</h3>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/scenes/chapter/{chapter_id}</code> - Get scenes for a chapter
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/scenes</code> - Create a new scene
        </div>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/scenes/{scene_id}</code> - Get scene details
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/api/scenes/{scene_id}</code> - Update scene
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/api/scenes/{scene_id}/content</code> - Update scene content
        </div>
        <div class="endpoint">
            <span class="method patch">PATCH</span> <code>/api/scenes/{scene_id}/reorder</code> - Reorder scene
        </div>
        <div class="endpoint">
            <span class="method delete">DELETE</span> <code>/api/scenes/{scene_id}</code> - Delete scene
        </div>
        
        <h2>💡 Example Usage</h2>
        <p>1. Create a project: <code>POST /api/projects</code></p>
        <p>2. Add chapters: <code>POST /api/chapters</code></p>
        <p>3. Create scenes: <code>POST /api/scenes</code></p>
        <p>4. Start writing: <code>PUT /api/scenes/{id}/content</code></p>
        
        <h2>✨ Features</h2>
        <ul>
            <li>📊 Automatic word count tracking</li>
            <li>📄 Drag-and-drop reordering for chapters and scenes</li>
            <li>📈 Project progress statistics</li>
            <li>💾 Auto-save functionality</li>
            <li>🏷️ Genre and metadata management</li>
        </ul>
        
        <p><strong>Ready to start writing your novel? Check out the <a href="/api/docs">API documentation</a> to get started!</strong></p>
    </body>
    </html>
    """