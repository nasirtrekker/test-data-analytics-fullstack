#!/bin/bash

# Content Insights Demo - Local Mode with Tmux
# Starts training, MLflow UI, backend, and frontend in organized panes
# Usage: ./demo.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
SESSION_NAME="content-insights-demo"

echo "=========================================="
echo "📊 Content Insights Demo (Local + Tmux)"
echo "=========================================="
echo ""

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Run: ./setup_venv.sh"
    exit 1
fi

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ Tmux not installed. Install with: sudo apt-get install tmux"
    exit 1
fi

# Kill existing session if running
tmux kill-session -t $SESSION_NAME 2>/dev/null || true

echo "✓ Starting tmux session: $SESSION_NAME"
echo ""

# Create new session with 4 panes
tmux new-session -d -s $SESSION_NAME -x 220 -y 50

# Pane 1 (top-left): Training Pipeline
tmux send-keys -t $SESSION_NAME:0 "cd '$PROJECT_ROOT' && source $VENV_PATH/bin/activate && echo '🚂 Training Pipeline' && MLFLOW_TRACKING_URI=file:./mlruns python -m scripts.train_pipeline" Enter
sleep 2

# Split into 2 columns
tmux split-window -t $SESSION_NAME:0 -h

# Pane 2 (top-right): Backend API
tmux send-keys -t $SESSION_NAME:0.1 "cd '$PROJECT_ROOT/backend' && source $VENV_PATH/bin/activate && echo '🔧 Backend API (port 8000)' && export MLFLOW_TRACKING_URI=file:./mlruns && uvicorn app.main:app --reload --port 8000" Enter
sleep 2

# Split bottom row
tmux split-window -t $SESSION_NAME:0 -v

# Pane 3 (bottom-left): MLflow UI
tmux send-keys -t $SESSION_NAME:0.2 "cd '$PROJECT_ROOT' && source $VENV_PATH/bin/activate && echo '📈 MLflow UI (port 5000)' && sleep 3 && mlflow ui --backend-store-uri file:./mlruns --port 5000" Enter
sleep 2

# Pane 4 (bottom-right): Frontend
tmux split-window -t $SESSION_NAME:0.3 -h
tmux send-keys -t $SESSION_NAME:0.3 "cd '$PROJECT_ROOT/frontend' && echo '🎨 Frontend (port 5173)' && npm install --silent > /dev/null 2>&1 && npm run dev" Enter

# Layout: make it more balanced
tmux select-layout -t $SESSION_NAME:0 tiled

echo ""
echo "✅ Demo environment started in tmux session: $SESSION_NAME"
echo ""
echo "📍 Services:"
echo "  • Training Pipeline       → Watch training logs"
echo "  • MLflow UI               → http://localhost:5000"
echo "  • Backend API             → http://localhost:8000/docs"
echo "  • Frontend Dashboard      → http://localhost:5173"
echo ""
echo "🎮 Tmux Controls:"
echo "  • Attach to session: tmux attach -t $SESSION_NAME"
echo "  • Kill session:      tmux kill-session -t $SESSION_NAME"
echo "  • Navigate panes:    Ctrl+B → Arrow keys"
echo ""
echo "🌐 Open in browser:"
echo "  1. MLflow:   http://localhost:5000 → Experiments → content-insights-training"
echo "  2. Backend:  http://localhost:8000/docs"
echo "  3. Frontend: http://localhost:5173"
echo ""
echo "⏱️  Services will be ready in ~30-60 seconds..."
echo ""

# Auto-attach to session
sleep 3
tmux attach -t $SESSION_NAME
