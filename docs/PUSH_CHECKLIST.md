# 📋 Quick Reference: Push to GitHub Checklist

## Pre-Push Commands (Run in Order)

```bash
# 1. Navigate to project root
cd <repo-root>

# 2. Run quality checks (REQUIRED)
make prepush

# 3. Run Docker smoke test (REQUIRED)
docker compose up --build -d
sleep 30
curl -f http://localhost:8000/health
curl -I http://localhost:5173
docker compose exec backend pytest tests/ -v
docker compose down -v

# 4. Check for sensitive files (REQUIRED)
grep -r "API_KEY\|SECRET\|PASSWORD" --exclude-dir=.git --exclude="*.md" . | grep -v APP_DATA_PATH

# 5. Review what will be committed
git status
git status --short | head -n 50

# 6. Verify models are staged
ls models/*.joblib | wc -l  # Should show 10+

# 7. Commit everything
git add .
git commit -m "Complete Blenda Labs take-home assignment

- Full-stack video analytics dashboard
- ETL pipeline with validation
- 5 analysis methods (clustering, anomaly, predictive, trends, similarity)
- React/TypeScript dashboard with MAPIE conformal prediction
- SHAP explainability and model versioning
- Docker Compose orchestration
- Comprehensive testing and CI/CD
- All quality gates passing"

# 8. Set remote (first time only)
git remote add origin https://github.com/nasirtrekker/test-data-analytics-fullstack.git

# 9. Push to GitHub
git push -u origin main

# 10. Verify on GitHub
# Visit: https://github.com/nasirtrekker/test-data-analytics-fullstack
```

---

## ✅ Final Verification Checklist

Before pushing:
- [ ] `make prepush` - exits with 0 (success)
- [ ] Docker test - backend health returns `{"status":"healthy"}`
- [ ] Dashboard - frontend renders at http://localhost:5173
- [ ] Tests - all 5 pytest tests pass
- [ ] Security - no secrets found in grep check
- [ ] Models - `models/*.joblib` files staged and committed
- [ ] Git status - no unexpected files (no node_modules, .env, logs)

After pushing:
- [ ] GitHub repo accessible at URL
- [ ] README.md displays correctly
- [ ] All folders visible (backend/, frontend/, models/, notebooks/)
- [ ] CI/CD passes (if configured)

---

## ⚡ One-Line Commands

```bash
# Security check
grep -r "API_KEY\|SECRET\|PASSWORD" --exclude-dir=.git --exclude="*.md" . | grep -v APP_DATA_PATH

# Full smoke test
docker compose up --build -d && sleep 30 && curl -f http://localhost:8000/health && curl -I http://localhost:5173 && docker compose exec backend pytest tests/ -v && docker compose down -v

# Quick file count
git ls-files | wc -l

# Check sensitive files in .gitignore
cat .gitignore | grep -E "\.env|\.key|\.pem|secret"
```

---

## 🆘 Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Port already in use | `docker compose down -v && lsof -ti:8000 \| xargs kill -9` |
| node_modules staged | `git reset HEAD frontend/node_modules && echo "frontend/node_modules/" >> .gitignore` |
| Push rejected | `git pull origin main --allow-unrelated-histories` then push |
| Auth failed (HTTPS) | Use personal access token from https://github.com/settings/tokens |
| Large files rejected | Add to Git LFS: `git lfs track "*.joblib"` |

---

## 📧 Reviewer Quick Start (Include in Email)

```
Testing Instructions:
1. git clone https://github.com/nasirtrekker/test-data-analytics-fullstack.git
2. cd test-data-analytics-fullstack
3. docker compose up --build -d
4. Wait 30 seconds
5. curl http://localhost:8000/health
6. Open http://localhost:5173 in browser
7. docker compose exec backend pytest tests/ -v
8. docker compose down -v

See README.md Quick Start guide for details.
```

---

For detailed instructions, see [PUSH_TO_GITHUB.md](PUSH_TO_GITHUB.md)
